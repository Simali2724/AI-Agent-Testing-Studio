"""Coordinate evaluation phases, preserve evidence and summarize completed runs."""

import asyncio
import hashlib
import itertools
import json
import math
import random
import statistics
import time
import uuid
from datetime import datetime, timezone

from .. import database as db
from . import metering, pricing
from .catalog import build_cases
from .connectors import Connector, safe_error
from .cost_summary import summarize
from .judge import evaluate, pairwise
from .quota import ProviderQuotaUnavailable, quota_reason
from .scheduling import Halted, Runtime
from .scheduling import key as scheduling_key
from .schema import CATEGORIES

ACTIVE = {}
TASKS = set()


def now():
    return datetime.now(timezone.utc).isoformat()


MIN_COVERAGE = 0.8
SCORE_FORMULA = (
    "Quality: mean of evaluated case scores per category; overall: "
    "equal-weight mean of categories with evidence. Not tested is unscored, "
    "never failed. Coverage: evaluated / planned cases. Ranking requires "
    "minimum coverage in every selected category. Comparisons use only "
    "jointly evaluated cases with valid pairwise "
    "judgments."
)


def missing(reason):
    return {
        "status": "not_tested",
        "score": None,
        "reason": reason,
        "transcript": [],
        "estimated": False,
        "seconds": None,
        "cost": None,
    }


def scored(result):
    value = result.get("score")
    return (
        result.get("status") in ("passed", "failed")
        and type(value) in (int, float)
        and math.isfinite(value)
        and 0 <= value <= 100
    )


def mean_score(rows):
    values = [r["score"] for r in rows if scored(r)]
    return round(statistics.mean(values), 2) if values else None


def aggregate(run):
    threshold = run.get("config", {}).get("min_coverage", MIN_COVERAGE)
    run["scoring_version"] = "quality-coverage-v1"
    run["score_formula"] = SCORE_FORMULA
    # Normalize legacy missing-evidence zeros when displaying saved runs.
    for case in run["cases"]:
        for result in case["results"]:
            if result["status"] == "not_tested":
                result["score"] = None
    summaries = []
    for bot_index, target in enumerate(run["targets"]):
        categories = []
        for key in run["categories"]:
            rows = [c["results"][bot_index] for c in run["cases"] if c["category"] == key]
            measured = [r for r in rows if scored(r)]
            coverage = len(measured) / len(rows) if rows else 0
            categories.append(
                {
                    "id": key,
                    "name": CATEGORIES[key],
                    "score": mean_score(measured),
                    "coverage": round(coverage * 100, 2),
                    "rankable": bool(measured) and coverage >= threshold,
                    "total": len(rows),
                    "tested": len(measured),
                    "not_tested": len(rows) - len(measured),
                    "passed": sum(r["status"] == "passed" for r in measured),
                    "failed": sum(r["status"] == "failed" for r in measured),
                    "estimated": sum(r.get("estimated", False) for r in measured),
                    "needs_review": sum(r.get("needs_review", False) for r in measured),
                }
            )
        rows = [c["results"][bot_index] for c in run["cases"]]
        attempted = [turn for r in rows for turn in r["transcript"]]
        attempted += [
            turn
            for case in run["cases"]
            for attempt in case.get("previous_attempts", [])
            for turn in attempt["results"][bot_index].get("transcript", [])
        ]
        latencies = [t["seconds"] for t in attempted if "seconds" in t]
        timed_out = sum("timed out" in t.get("error", "").lower() for t in attempted)
        errors = sum(bool(t.get("error")) for t in attempted)
        available = [c["score"] for c in categories if c["score"] is not None]
        overall = round(statistics.mean(available), 2) if available else None
        risks = sorted(
            [c for c in categories if c["score"] is not None and c["score"] < 80],
            key=lambda c: c["score"],
        )[:3]
        strengths = sorted(
            [c for c in categories if c["rankable"] and c["score"] >= 80], key=lambda c: -c["score"]
        )[:3]
        incomplete = any(c["not_tested"] for c in categories)
        summaries.append(
            {
                "name": target["name"],
                "score": overall,
                "categories": categories,
                "incomplete": incomplete,
                "verdict": "Quality and coverage are reported separately.",
                "risks": risks,
                "strengths": strengths,
                "examples": [
                    c["id"] for c in run["cases"] if c["results"][bot_index]["status"] == "failed"
                ][:3],
                "requests": len(attempted),
                "errors": errors,
                "timeouts": timed_out,
                "error_rate": round(errors / len(attempted) * 100, 2) if attempted else None,
                "mean_seconds": round(statistics.mean(latencies), 3) if latencies else None,
                "p95_seconds": round(sorted(latencies)[int(0.95 * (len(latencies) - 1))], 3)
                if len(latencies) >= 20
                else None,
                "p99_seconds": round(sorted(latencies)[int(0.99 * (len(latencies) - 1))], 3)
                if len(latencies) >= 100
                else None,
                "cost": None,
                "request_metrics_basis": "Includes recorded previous attempts and retries; scores use the latest case evaluation.",
                "cost_reason": "See costs.bots for the separately metered target cost; historical runs may have no ledger.",
            }
        )
        summary = summaries[-1]
        speed_turns = [
            t
            for c in run["cases"]
            if c["category"] == "performance"
            for t in c["results"][bot_index]["transcript"]
        ]
        speed_times = [t["seconds"] for t in speed_turns if "seconds" in t]
        summary["sequential_speed"] = {
            "requests": len(speed_turns),
            "mean_seconds": round(statistics.mean(speed_times), 3) if speed_times else None,
            "errors": sum(bool(t.get("error")) for t in speed_turns),
            "basis": (
                "Performance category only; sequential and exclusive of other Studio run "
                "traffic. Queue/pacing time excluded. External traffic is "
                "uncontrolled."
            ),
        }
        summary.update(
            tested=sum(c["tested"] for c in categories),
            total=len(rows),
            coverage=round(100 * sum(c["tested"] for c in categories) / len(rows), 2)
            if rows
            else 0,
            min_coverage=threshold * 100,
            rankable=all(c["rankable"] for c in categories),
            missing_evidence=[c for c in categories if c["not_tested"]],
        )
        summary["verdict"] = (
            (
                "Not ranked: insufficient coverage. "
                if not summary["rankable"]
                else "Eligible for ranking. "
            )
            + f"Quality uses evaluated cases only. Coverage {summary['coverage']}%; at least {threshold * 100:g}% is required in every selected category."
        )
    run["summary"] = summaries
    if len(summaries) > 1:
        from .comparisons import compare

        run["comparison"] = compare(run, scored)
    agreements = []
    for i, target in enumerate(run["targets"]):
        planned = [c for c in run["cases"] if c.get("secondary_sample")]
        judged = [
            c["results"][i]["secondary_judge"]
            for c in planned
            if c["results"][i].get("secondary_judge", {}).get("status") == "judged"
        ]
        agreements.append(
            {
                "target": target["name"],
                "sampled": len(planned),
                "judged": len(judged),
                "unavailable": len(planned) - len(judged),
                "agreement_percent": round(100 * sum(r["agrees"] for r in judged) / len(judged), 2)
                if judged
                else None,
                "mean_absolute_score_difference": round(
                    statistics.mean(r["absolute_difference"] for r in judged), 2
                )
                if judged
                else None,
                "definition": (
                    "Agreement on pass/fail at 80; based on raw primary and secondary AI "
                    "scores, before exact-check overrides. Agreement is not evidence of "
                    "accuracy."
                ),
            }
        )
    run["judge_agreement"] = agreements
    from .baselines import regressions

    run["regressions"] = regressions(run, scored)
    run["costs"] = summarize(run)
    return run


def make_run(config):
    pricing.pin(config)
    cases = build_cases(config)
    eligible = [c for c in cases if c["category"] != "performance" and not c["prerequisite"]]
    selected = (
        {
            c["id"]
            for c in sorted(
                eligible,
                key=lambda c: hashlib.sha256(f"{config.seed}:{c['id']}".encode()).hexdigest(),
            )[: math.ceil(len(eligible) * config.secondary_sample_rate)]
        }
        if config.secondary_judge_enabled
        else set()
    )
    for c in cases:
        c["secondary_sample"] = c["id"] in selected
    for c in cases:
        c.update(
            results=[missing("Pending execution.") for _ in config.targets],
            pair={"status": "not_tested", "winner": None, "reason": "Pending execution."},
            completed=False,
        )
    public = config.model_dump(exclude={"judge_token", "secondary_judge_token", "targets"})
    public["targets"] = [t.model_dump(exclude={"token"}) for t in config.targets]
    run = {
        "id": str(uuid.uuid4()),
        "version": "blackbox-2-cost",
        "price_snapshot_id": config.price_snapshot_id,
        "setup_notes": config._setup_notes,
        "status": "queued",
        "started_at": now(),
        "finished_at": None,
        "targets": public["targets"],
        "categories": config.categories,
        "config": public,
        "cases": cases,
        "progress": 0,
        "stage": "Preparing",
        "score_formula": SCORE_FORMULA,
        "limitations": [
            "Template variations do not establish comprehensive security or fairness.",
            "AI rubric judgments are estimates, not human verification.",
            (
                "Costs use versioned prices. Unknown usage or pricing is not zero; "
                "opaque bot costs are incomplete "
                "estimates."
            ),
            "No host execution of uploaded ZIPs.",
            "Partial or ellipsis evidence is flagged for review; scores remain AI estimates.",
            "Browser completion uses stable assistant text and may not support all streaming widgets.",
        ],
    }
    from .baselines import snapshot

    run["baseline_ids"] = snapshot(run["targets"])
    return aggregate(run)


def save(run, config=None):
    if config:
        secrets = [t.token.get_secret_value() for t in config.targets if t.token]
        if config.judge_token:
            secrets.append(config.judge_token.get_secret_value())
        if config.secondary_judge_token:
            secrets.append(config.secondary_judge_token.get_secret_value())
        encoded = json.dumps(run)
        for secret in secrets:
            if secret:
                encoded = encoded.replace(secret, "[REDACTED]")
        clean = json.loads(encoded)
        for case in clean["cases"]:
            case["evidence_sha256"] = hashlib.sha256(
                json.dumps(case["results"], sort_keys=True).encode()
            ).hexdigest()
        db.save("blackbox", clean)
    else:
        db.save("blackbox", run)


async def joined(coroutines):
    """Await sibling tasks and cancel unfinished work when one exits early."""
    tasks = [asyncio.create_task(c) for c in coroutines]
    try:
        return await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


class EvaluationExecutor:
    """Own the mutable state of one evaluation; workers never share bot sessions.

    Scheduling, metering and connectors remain separate modules. This class
    coordinates them and guarantees that every exit path saves the evidence.
    """

    def __init__(self, run, config, connector_factory=Connector):
        self.run = run
        self.config = config
        self.stop = ACTIVE.setdefault(run["id"], asyncio.Event())
        self.runtime = Runtime(config, self.stop)
        self.clients = [connector_factory(target, config.timeout) for target in config.targets]
        self.unavailable = {}
        self.errors = [0] * len(self.clients)
        self.last_save = 0
        self.start = time.monotonic()

    def checkpoint(self):
        """Persist progress at most twice per second while cases are running."""
        self.run["progress"] = round(
            100
            * sum(c.get("completed", False) for c in self.run["cases"])
            / len(self.run["cases"]),
            1,
        )
        # Coalesce database/report work rather than serialize a whole run per fast case.
        if time.monotonic() - self.last_save >= 0.5:
            aggregate(self.run)
            save(self.run, self.config)
            self.last_save = time.monotonic()

    async def conversation_with_recovery(self, case, i, allowance):
        """Retry rate-limited conversations twice; retain attempts and metered costs."""
        for attempt in range(3):
            observation = await asyncio.wait_for(self.clients[i].conversation(case), allowance)
            reason = str(observation.get("error") or "").lower()
            if blocked := quota_reason(reason):
                error = ProviderQuotaUnavailable("Chatbot: " + blocked)
                error.observation = observation
                raise error
            rate_limited = "rate_limit" in reason or "429" in reason or "rate limit" in reason
            if not rate_limited or attempt == 2 or case["category"] == "performance":
                return observation
            case.setdefault("request_attempts", []).append(
                {"bot_index": i, "attempt": attempt + 1, "observation": observation, "at": now()}
            )
            self.run["stage"] = (
                "Provider rate limit: waiting 60 seconds before retrying " + case["name"]
            )
            self.checkpoint()
            await asyncio.sleep(60)
            self.runtime.check()

    async def target_result(self, case, i):
        """Collect and judge one conversation, retaining evidence on interruption."""
        if scored(case["results"][i]):
            return
        observation = case.get("resume_observations", {}).get(str(i))
        try:
            self.runtime.check()
            with metering.scope(
                self.run["id"],
                "compare" if len(self.clients) > 1 else "single",
                self.config,
                bot_slot="ABCD"[i],
                category=case["category"],
                test_case_id=case["id"],
            ):
                async with self.runtime.target(self.config.targets[i].url):
                    reason = self.unavailable.get(i) or case["prerequisite"]
                    if self.errors[i] >= 3:
                        reason = (
                            "Target circuit breaker opened after 3 consecutive failed conversations; "
                            "remaining requests were not "
                            "sent."
                        )
                    if reason:
                        case["results"][i] = missing(reason)
                        return
                    self.runtime.check()
                    # Network timeouts live inside connectors; allowance includes multi-turn pacing.
                    allowance = (self.config.timeout + 8 * self.config.request_pause_seconds) * len(
                        case["turns"]
                    ) + 10
                    if observation is None:
                        observation = await self.conversation_with_recovery(case, i, allowance)
                    self.errors[i] = self.errors[i] + 1 if observation.get("error") else 0
                    if self.errors[i] >= 3:
                        self.unavailable[i] = (
                            "Target circuit breaker opened after 3 consecutive failed conversations; "
                            "remaining requests were not "
                            "sent."
                        )
                self.runtime.check()
                judged = await evaluate(self.config, case, observation)
            case["results"][i] = {
                **judged,
                "status": "passed" if judged["score"] >= 80 else "failed",
                "transcript": observation["transcript"],
                "seconds": round(sum(t.get("seconds", 0) for t in observation["transcript"]), 3),
                "cost": None,
                "usage": observation.get("usage", []),
                "reason": judged["reason"],
                "timing_mode": "sequential_speed"
                if case["category"] == "performance"
                else "concurrent_quality",
            }
            if judged.get("budget_stop"):
                raise metering.BudgetLimit(judged["budget_stop"])
        except (metering.BudgetLimit, Halted, asyncio.CancelledError) as exc:
            if isinstance(exc, ProviderQuotaUnavailable):
                self.run["provider_reason"] = str(exc)
                self.stop.set()
            if isinstance(exc, metering.BudgetLimit):
                self.run["budget_reason"] = str(exc)
                self.stop.set()
            if getattr(exc, "judged_result", None):
                completed = exc.judged_result
                case["results"][i] = {
                    **completed,
                    "status": "passed" if completed["score"] >= 80 else "failed",
                    "transcript": [],
                    "seconds": None,
                    "cost": None,
                }
            if not scored(case["results"][i]):
                case["results"][i] = missing(
                    str(exc) or "Execution interrupted before evaluation completed."
                )
            observation = observation or getattr(exc, "observation", None)
            if observation:
                case["results"][i].update(
                    transcript=observation["transcript"],
                    seconds=sum(t.get("seconds", 0) for t in observation["transcript"]),
                )
            raise
        except Exception as exc:
            case["results"][i] = missing(safe_error(exc))
            if observation:
                case["results"][i].update(
                    transcript=observation["transcript"],
                    seconds=sum(t.get("seconds", 0) for t in observation["transcript"]),
                )
            else:
                self.errors[i] += 1

    async def process(self, case, speed=False):
        """Run one case for all targets, then compare the completed responses."""
        self.runtime.check()
        self.run["stage"] = ("Sequential speed check: " if speed else "Concurrent checks: ") + case[
            "name"
        ]
        # Per-case RNG is stable regardless of task completion order.
        seed = int(hashlib.sha256(f"{self.config.seed}:{case['id']}".encode()).hexdigest()[:16], 16)
        rng = random.Random(seed)
        order = list(range(len(self.clients)))
        rng.shuffle(order)
        if speed:
            for i in order:
                await self.target_result(case, i)
        else:
            await joined(self.target_result(case, i) for i in order)
        if len(self.clients) > 1:
            case["pairs"] = {}
            for a, b in itertools.combinations(range(len(self.clients)), 2):
                self.runtime.check()
                pair = {
                    "status": "not_tested",
                    "winner": None,
                    "reason": "One or both responses lack a valid score.",
                }
                if all(scored(case["results"][i]) for i in (a, b)):
                    try:
                        left, right = case["results"][a], case["results"][b]
                        if speed:
                            x, y = left["seconds"], right["seconds"]
                            pair = {
                                "status": "judged",
                                "winner": "tie" if abs(x - y) <= 0.1 else (0 if x < y else 1),
                                "reason": (
                                    "Measured sequential latency, 0.1-second tie margin; execution order "
                                    "randomized. Other Studio evaluations "
                                    "paused."
                                ),
                            }
                        elif not self.config.judge_enabled or any(
                            r.get("deterministic_score") == 0 for r in (left, right)
                        ):
                            x, y = left["score"], right["score"]
                            pair = {
                                "status": "judged",
                                "winner": "tie" if x == y else (0 if x > y else 1),
                                "reason": "Configured exact checks and combined scores; any exact failure overrides an AI preference.",
                            }
                        else:
                            with metering.scope(
                                self.run["id"],
                                "compare",
                                self.config,
                                bot_slot=None,
                                category=case["category"],
                                test_case_id=case["id"],
                            ):
                                pair = await pairwise(self.config, case, left, right, rng)
                    except metering.BudgetLimit as exc:
                        self.run["budget_reason"] = str(exc)
                        self.stop.set()
                        raise
                    except Halted:
                        raise
                    except Exception as exc:
                        pair = {"status": "not_tested", "winner": None, "reason": safe_error(exc)}
                case["pairs"][f"{a}:{b}"] = pair
            case["pair"] = case["pairs"]["0:1"]
        case["evidence_sha256"] = hashlib.sha256(
            json.dumps(case["results"], sort_keys=True).encode()
        ).hexdigest()
        case["completed"] = True
        self.checkpoint()

    async def quality_phase(self, cases):
        """Drain quality cases through a bounded queue under shared traffic access."""
        queue = asyncio.Queue()
        for case in cases:
            queue.put_nowait(case)

        async def worker():
            while not queue.empty():
                case = queue.get_nowait()
                async with self.runtime.shared.traffic.phase():
                    await self.process(case)

        await joined(worker() for _ in range(min(self.config.case_concurrency, len(cases))))

    async def detect_targets(self):
        """Discover interfaces without starting conversations for unavailable targets."""
        async with self.runtime.shared.traffic.phase():
            for i, client in enumerate(self.clients):
                self.runtime.check()
                try:
                    if not self.config.consent:
                        raise ValueError("Authorize sending test prompts to these targets.")
                    async with self.runtime.target(self.config.targets[i].url):
                        await asyncio.wait_for(client.detect(), self.config.timeout)
                    if getattr(client, "kind", "") == "web":
                        gate = self.runtime.shared.targets[
                            scheduling_key(self.config.targets[i].url)
                        ]
                        gate.leases[self.runtime.ident] = (
                            min(2, self.config.target_concurrency),
                            self.config.request_pause_seconds,
                        )
                except Exception as exc:
                    self.unavailable[i] = safe_error(exc)

    async def speed_phase(self):
        """Measure speed sequentially while other Studio requests are paused."""
        speed = [
            c
            for c in self.run["cases"]
            if not c.get("completed") and c["category"] == "performance"
        ]
        if speed:
            self.run["stage"] = "Waiting for exclusive sequential speed checks"
            self.checkpoint()
            async with self.runtime.shared.traffic.phase(exclusive=True):
                for case in speed:
                    await self.process(case, True)

    async def finish(self):
        """Finalize pending cases and release clients, scheduling leases and run state."""
        for case in self.run["cases"]:
            if not case["completed"]:
                for result in case["results"]:
                    if result["reason"] == "Pending execution.":
                        result["reason"] = (
                            self.run.get("provider_reason")
                            or self.run.get("budget_reason")
                            or "Run ended before this case was executed: " + self.run["status"]
                        )
                case["pair"]["reason"] = "Run ended before pairwise judging."
        self.run["duration_seconds"] = round(time.monotonic() - self.start, 3)
        self.run["progress"] = round(
            100
            * sum(c.get("completed", False) for c in self.run["cases"])
            / len(self.run["cases"]),
            1,
        )
        self.run["finished_at"] = now()
        self.run["stage"] = self.run.get("provider_reason") or self.run["status"]
        try:
            aggregate(self.run)
            save(self.run, self.config)
        finally:
            await asyncio.gather(*(c.close() for c in self.clients), return_exceptions=True)
            await self.runtime.close()
            ACTIVE.pop(self.run["id"], None)

    async def execute(self):
        """Run discovery, quality and exclusive speed phases; always clean up."""
        self.run["status"] = "running"
        save(self.run, self.config)
        try:
            with self.runtime.context():
                async with asyncio.timeout(self.config.max_minutes * 60):
                    await self.detect_targets()
                    await self.quality_phase(
                        [
                            c
                            for c in self.run["cases"]
                            if not c.get("completed") and c["category"] != "performance"
                        ]
                    )
                    await self.speed_phase()
                    self.run["status"] = "completed"
        except metering.BudgetLimit as exc:
            self.run.update(status="budget_limit", budget_reason=str(exc))
        except ProviderQuotaUnavailable as exc:
            self.run.update(status="provider_limit", provider_reason=str(exc))
        except Halted:
            self.run["status"] = "budget_limit" if self.run.get("budget_reason") else "stopped"
        except TimeoutError:
            self.run["status"] = "timed_out"
        except asyncio.CancelledError:
            self.run["status"] = "interrupted"
        except Exception as exc:
            self.run.update(status="error", error=safe_error(exc))
        finally:
            await self.finish()
        return self.run


async def execute(run, config, connector_factory=Connector):
    """Execute a prepared run with bounded concurrency and durable results."""
    return await EvaluationExecutor(run, config, connector_factory).execute()
