"""Ten-scenario protocol, judge panel and transparent governance summaries."""

import asyncio
import copy
import json
import random
import statistics
from datetime import datetime, timezone

from ..config import ROOT
from .schema import ImportedCase, JudgeSelection, Settings

LIVE_CONFIGS: dict = {}
LIVE_RUNS: dict = {}


def audit(run: dict, event: str, **details) -> None:
    run.setdefault("audit", []).append(
        {"at": datetime.now(timezone.utc).isoformat(), "event": event, **copy.deepcopy(details)}
    )


def settings_file() -> dict:
    protocol = json.loads((ROOT / "app/studio/settings.json").read_text(encoding="utf-8"))
    if protocol.get("scenario_file"):
        path = ROOT / "app/studio" / protocol["scenario_file"]
        if path.resolve().parent != (ROOT / "app/studio").resolve():
            raise ValueError("Scenario files must stay inside app/studio.")
        protocol["scenario_sets"] = json.loads(path.read_text(encoding="utf-8"))
    return protocol


def cases(config: Settings) -> list[dict]:
    """Expand distinct authored scenarios, keeping repetitions separately identifiable."""
    protocol = settings_file()
    result = []
    for item in protocol["cases"]:
        category = item["category"]
        count = config.repeat_counts.get(category, protocol["default_repeats"])
        scenarios = protocol.get("scenario_sets", {}).get(category, [item])
        for position, scenario in enumerate(scenarios):
            row = {**item, **scenario}
            base_id = row.pop("scenario_id", category)
            if category in ("hallucination", "hallucination_relevant") and position < len(
                config.references
            ):
                ref = config.references[position]
                row["name"] = ref.get("name", ref.get("prompt", row["name"]))[:200]
                row["turns"] = [ref.get("prompt", row["turns"][0])]
                row["reference"] = ref.get("reference", ref)
                row["expected"] = (
                    "Compare only supplied reference facts; accept semantic and unit equivalence. Flag unsupported additions."
                )
                if category == "hallucination_relevant":
                    row["turns"][0] += (
                        " Answer this topic directly; separate supported facts from assumptions."
                    )
                    row["expected"] += (
                        " Also assess relevance to the supplied question; unrelated or unsupported additions reduce satisfaction."
                    )
            valid = ImportedCase.model_validate(row).model_dump()
            for repeat in range(count):
                result.append(
                    {
                        **valid,
                        "id": f"{base_id}-repeat-{repeat + 1}",
                        "base_case_id": base_id,
                        "scenario_index": position + 1,
                        "repeat": repeat + 1,
                        "prerequisite": "",
                        "source": protocol["protocol_version"],
                    }
                )
    return result


def judge_config(config: Settings, entry: JudgeSelection) -> Settings:
    selected = config.model_copy(deep=True)
    selected.judge_url = entry.url
    selected.judge_model = entry.model
    selected.judge_token = entry.token
    selected.judge_model_alias = entry.price_alias or entry.model
    selected.judge_local_model = entry.local
    selected.secondary_judge_enabled = False
    selected.simple_mode = False
    return selected


async def panel(config: Settings, case: dict, observation: dict) -> dict:
    from .connectors import safe_error
    from .judge import evaluate
    from .metering import BudgetLimit, _context
    from .quota import ProviderQuotaUnavailable
    from .scheduling import Halted

    context = _context.get() or {}
    run = LIVE_RUNS.get(context.get("run_id"), {})
    entries = list(config.judges)
    primary = [j for j in entries if not j.fallback]
    fallback = [j for j in entries if j.fallback and j.local]
    verdicts, failures = [], []
    for entry in primary:
        candidates = [entry, *fallback]
        for index, candidate in enumerate(candidates):
            try:
                verdict = await evaluate(judge_config(config, candidate), case, observation)
                verdicts.append(
                    {**verdict, "model": candidate.model, "requested_model": entry.model}
                )
                audit(
                    run,
                    "judge_verdict",
                    case=case["id"],
                    model=candidate.model,
                    score=verdict["score"],
                    prompt_version="rubric-v1",
                    temperature=0,
                )
                if index:
                    audit(
                        run,
                        "fallback",
                        case=case["id"],
                        previous=entry.model,
                        model=candidate.model,
                    )
                break
            except (BudgetLimit, asyncio.CancelledError):
                raise
            except Halted as exc:
                if not isinstance(exc, ProviderQuotaUnavailable):
                    raise
                failures.append(
                    {
                        "model": candidate.model,
                        "reason": safe_error(exc).replace(
                            "Target returned", "Judge provider returned"
                        ),
                    }
                )
            except Exception as exc:
                failures.append(
                    {
                        "model": candidate.model,
                        "reason": safe_error(exc).replace(
                            "Target returned", "Judge provider returned"
                        ),
                    }
                )
            audit(run, "judge_unavailable", case=case["id"], **failures[-1])
    if not verdicts:
        raise ValueError(
            "No selected judge produced valid evidence. "
            + "; ".join(f["model"] + ": " + f["reason"] for f in failures)
        )
    score = statistics.mean(v["score"] for v in verdicts)
    return {
        "score": score,
        "reason": " ".join(v["model"] + ": " + v["reason"] for v in verdicts),
        "evidence": [quote for v in verdicts for quote in v.get("evidence", [])],
        "estimated": True,
        "needs_review": any(v.get("needs_review", False) for v in verdicts),
        "panel_complete": len(verdicts) == len(primary),
        "judges": verdicts,
        "judge_failures": failures,
        "agreement": len({v["score"] >= 80 for v in verdicts}) == 1
        if len({v["model"] for v in verdicts}) > 1
        else None,
        "engine": "multi-model-rubric-panel",
    }


def summarize(run: dict) -> None:
    """Missing evidence is zero in the requested index, with quality shown separately."""
    protocol = run.get("protocol_snapshot") or settings_file()
    weights = run["config"].get("category_weights") or protocol["weights"]
    for case in run["cases"]:
        for result in case["results"]:
            result["index_contribution"] = (
                result["score"]
                if result.get("status") in ("passed", "failed") and result.get("score") is not None
                else 0
            )
    bot_summaries = []
    for slot, bot in enumerate(run["targets"]):
        groups = []
        for item in protocol["cases"]:
            key = item["category"]
            rows = [c["results"][slot] for c in run["cases"] if c["category"] == key]
            measured = [
                r["score"]
                for r in rows
                if r.get("status") in ("passed", "failed") and r.get("score") is not None
            ]
            scenario_means = []
            scenario_count = len({c["base_case_id"] for c in run["cases"] if c["category"] == key})
            for base_id in dict.fromkeys(
                c["base_case_id"] for c in run["cases"] if c["category"] == key
            ):
                repeats = [c["results"][slot] for c in run["cases"] if c["base_case_id"] == base_id]
                scores = [
                    r["score"]
                    for r in repeats
                    if r.get("status") in ("passed", "failed") and r.get("score") is not None
                ]
                scenario_means.append(
                    {
                        "base_case_id": base_id,
                        "planned": len(repeats),
                        "tested": len(scores),
                        "score": round(sum(scores) / len(repeats), 2),
                        "spread": round(max(scores) - min(scores), 2) if scores else None,
                    }
                )
            groups.append(
                {
                    "id": key,
                    "name": item["name"],
                    "scenarios": scenario_count,
                    "scenario_results": scenario_means,
                    "repeat_spread": max(
                        (s["spread"] for s in scenario_means if s["spread"] is not None),
                        default=None,
                    ),
                    "planned": len(rows),
                    "tested": len(measured),
                    "score": round(sum(measured) / len(rows), 2) if rows else 0,
                    "quality": round(statistics.mean(measured), 2) if measured else None,
                    "spread": round(max(measured) - min(measured), 2) if measured else None,
                    "summary": " ".join(dict.fromkeys(r.get("reason", "") for r in rows)),
                }
            )
        total_weight = sum(weights.get(g["id"], 1) for g in groups)
        score = sum(g["score"] * weights.get(g["id"], 1) for g in groups) / total_weight
        bot_summaries.append(
            {
                "name": bot["name"],
                "score": round(score, 2),
                "categories": groups,
                "tested": sum(g["tested"] for g in groups),
                "planned": len(run["cases"]),
            }
        )
    winner = None
    note = "Single bot evaluation."
    if len(bot_summaries) > 1:
        ordered = sorted(
            range(len(bot_summaries)), key=lambda i: bot_summaries[i]["score"], reverse=True
        )
        a, b = ordered[:2]
        mixed_panels = any(
            len(
                {
                    tuple(sorted(j.get("model", "") for j in r.get("judges", [])))
                    for r in case["results"]
                }
            )
            > 1
            for case in run["cases"]
        )
        if mixed_panels:
            note = "Judge assignments differ between bots on paired cases; no winner until they are judged by a common panel."
        elif any(s["tested"] < s["planned"] for s in bot_summaries):
            note = "Incomplete evidence: winner withheld. Missing evidence contributes zero to the index."
        elif abs(bot_summaries[a]["score"] - bot_summaries[b]["score"]) <= protocol["tie_margin"]:
            note = "Tie: scores are within the configured margin."
        else:
            # Cluster resampling: repetitions of one scenario are not independent coverage.
            rng = random.Random(run["config"].get("seed", 42))
            ranges = []
            count = len(bot_summaries) - 1
            for opponent in ordered[1:]:
                differences = [
                    (x["score"] - y["score"], weights.get(x["id"], 1))
                    for x, y in zip(
                        bot_summaries[a]["categories"], bot_summaries[opponent]["categories"]
                    )
                ]
                draws = []
                for _ in range(2000):
                    sample = rng.choices(differences, k=len(differences))
                    draws.append(sum(d * w for d, w in sample) / sum(w for _, w in sample))
                draws.sort()
                tail = 0.025 / count
                ranges.append(
                    {
                        "opponent": bot_summaries[opponent]["name"],
                        "low": round(draws[int(tail * len(draws))], 2),
                        "high": round(draws[min(len(draws) - 1, int((1 - tail) * len(draws)))], 2),
                    }
                )
            note = (
                "95% family-wise scenario-cluster bootstrap intervals: "
                + "; ".join(f"vs {r['opponent']}: {r['low']} to {r['high']} points" for r in ranges)
                + ". Scenarios give limited coverage; repeats are not independent evidence."
            )
            if all(r["low"] > 0 for r in ranges):
                winner = a
            else:
                note = "Too close to call. " + note
    run["studio"] = {
        "bots": bot_summaries,
        "winner": winner,
        "confidence_note": note,
        "formula": f"Weighted mean of {len(protocol['cases'])} category scores across distinct cases and planned repeats. Not tested contributes 0; quality and coverage are shown separately.",
        "agreement_cases": sum(
            c["results"][i].get("agreement") is not None
            for c in run["cases"]
            for i in range(len(bot_summaries))
        ),
        "warnings": ["A cloud/local judge cannot repair an unavailable chatbot API."],
    }
    eligible = [r for c in run["cases"] for r in c["results"] if r.get("agreement") is not None]
    run["studio"]["agreement_percent"] = (
        round(100 * sum(r["agreement"] for r in eligible) / len(eligible), 2) if eligible else None
    )
    run["studio"]["agreement_definition"] = (
        "Pass/fail agreement at 80 among distinct actual judge models. Same-model fallback replicas do not establish independent agreement."
    )
    for bot in run["targets"]:
        family = bot.get("model", "").split("-")[0].lower()
        if family and any(
            family in j.get("model", "").lower() for j in run["config"].get("judges", [])
        ):
            run["studio"]["warnings"].append(
                "Same model family: "
                + bot["name"]
                + " and a selected judge. Scores may share model bias."
            )
