# HANDOFF — Continue AI Agent Studio (2026-10-15)

You are continuing the EXISTING Studio. Read PROGRESS.md and this file first. Make targeted edits, run relevant tests, keep answers short, do not print keys, and never rerun the one-off C: patch scripts. This file supersedes the previous sixteen-category defaults; historical run snapshots are preserved.

## Environment and authorization

- Product: D:\AI-Agent-Testing-Studio. Python: .venv/Scripts/python.exe (Windows 3.12). Local Git branch master, no remote/push configured by this phase. Earlier restore 6b041bd; previous implementation commit 8f26c66.
- C: artifact workspace: C:\Users\Moinuddeen hussain\Documents\ChatGPT\Moinuddeen_airm.
- D: is outside this chat's writable root. Use the normal escalation mechanism for D: mutations/process control. Never touch unrelated D: files.
- Real UI: http://127.0.0.1:2708/. Launched with STUDIO_AUTO_RESUME=0 to show the upgraded app without silently starting old paid evaluations. Check the listener before restarting; do not kill a live evaluation.
- No new paid chatbot/judge benchmark was launched in this phase. No new chatbot quality score is claimed. Keys/.env, production history and referenced old datasets remain intact.
- A temporary isolated UI fixture on port 2710 uses comparison-reports/governance-ui-fixture under the C: workspace, not production history. Names explicitly say OFFLINE UI FIXTURE. Scores are synthetic. Screenshot governance-ui.jpg and PDF governance-fixture.pdf are QA evidence only.

## User's requested contract

Ten top-level categories, Bias as one bar with nine tagged sub-tests. Bias: five counterfactual attributes (gender, racial/ethnic, age, socioeconomic, cultural), cognitive/confirmation, media framing, selection/sampling, plus algorithmic/AI disparity derived from all five counterfactual types. Neutral editable versioned prompts. Deterministic signals before judgment; judge presentation randomized. Reasons, severity, paired excerpts.

Governance: tamper-evident append-only audit, reproducible config, model cards, family warning, agreement, written overrides, export PII redaction, retention/delete, informational framework themes, completeness. Speed: bounded concurrent bot/case/repeat/judge work, durable caches, local classifier adapters, strict batched JSON, progress/timings, regression budget. Preserve old features and Mac/Linux startup.

## Implemented files and behavior

- app/studio/settings.json: new protocol ten-categories-bias-nine-v4, ten categories, default three repeats; editable weights, model list/family rules, execution/provider limits, batch size/window and local classifier options.
- app/studio/bias-v1.json: neutral-bias-v1 with nine subtype definitions. First five store a single template, two attributes and exact prompts; eight live cases plus one derived record. Algorithmic is derived, not another paid request. Media/selection refusals without demonstrating the criterion earn at most 50, not an automatic pass.
- app/blackbox/bias.py: reproducible pair presentation order, length/refusal/English lexicon sentiment signals, subtype severity/evidence summaries, counterfactual aggregate and model-family matching.
- app/blackbox/studio_engine.py: protocol loader/snapshots, typed repetitions, deterministic failure short-circuit, optional local screening, concurrent independent judge panel with bounded fallback, source evidence, one Bias bar, subtype details, worst-case index plus tested quality/coverage. Algorithmic does not double-weight Bias.
- app/blackbox/judge_prompts.py: canonical request builder. app/blackbox/judge.py validates strict scores/evidence, requires both bias replies to support evidence, applies temperature zero, retries, meters calls and caches validated verdicts by endpoint/model + exact request hash + transcript hash. Swapped A/B directions remain distinct, even for identical replies.
- app/blackbox/judge_batch.py: bounded short-window micro-batches, strict exact item IDs; malformed responses retry individually. Metered once as shared evaluation overhead; constituent cases audited. Does not falsely assign the whole batch to the first bot.
- app/blackbox/execution_cache.py: run-scoped SQLite caches. Bot identity includes target slot/config, case ID, repeat and prompt hash. New repeats/new runs always call bots freshly. Successful turns checkpoint immediately, including session identity.
- app/blackbox/connectors.py: REST/OpenAI retries restore successful prefixes/history/session; independent paired web prompts reuse saved prefixes. A partial STATEFUL web conversation cannot reconstruct a destroyed browser session without replaying paid turns; it is explicitly Not tested with reason, not silently replayed. Session/cookie expiry at the target may also prevent restoring a dialogue.
- app/blackbox/runner.py: concurrent cases/targets/repeats, cache-aware checkpoint/resume, provider gates, per-case outcome audit, cumulative active runtime including crash checkpoint time. Legacy speed checks still run exclusively/sequentially for fair latency. Stop/deadline/budget controls still apply.
- app/blackbox/scheduling.py: per-host provider limits can tighten configured target/global judge limits; shared rate pacing and Retry-After backoff retained.
- app/blackbox/local_metrics.py and classifier_runtime.py: deterministic screening plus optional OFFLINE HHEM/Qwen3Guard adapters. No automatic downloads. Models run in one reusable spawn-process worker, killed on timeout/cancellation; app shutdown releases it. HHEM requires supplied facts and explicit reviewed-local-code permission. Qwen Unsafe may be conclusive if operator enables decisive mode; Safe alone does not prove custom-policy compliance. Disabled/unavailable classifiers fall through and are disclosed/audited. Actual model weights/dependency integration was not exercised here.
- app/blackbox/governance.py: canonical SHA-256 chained entries, separate SQLite journal/anchor, legacy-unverified status, changed-record/tail/entire-log removal checks, reserved metadata protection, explicit crash journal catch-up, source integrity versus redacted export disclosure, bot/judge cards, regex PII redaction, retention/purge.
- app/blackbox/governance_routes.py: GET /api/studio/runs/{id}/governance and /events (SSE); POST /reproduce; PUT /retention. Reproduce uses saved server-side protocol/config/seed/price snapshot, fresh run ID/calls and records the source run. It rejects failed audit integrity. Re-enter original credentials if needed; model choices must remain identical. Provider aliases/external state may still change results.
- studio_routes.py logs key/model switches with non-reversible key fingerprints and retains old configured keys for redaction. Overrides require a note and actual bot evidence; original verdict and old/new scores retained.
- blackbox_app.py integrates routes, privacy exports, retention startup/hourly worker, cache/journal cleanup on delete, preserved reproduction prices/aliases, crash journal recovery/quarantine and classifier cleanup.
- app/studio/governance.json: versioned informational NIST Govern/Map/Measure/Manage, ISO 42001 and EU AI Act engineering themes. Not certification/legal compliance. New runs snapshot this mapping.
- reports.py: every JSON/PDF export has governance, timing and subtype explanations/evidence. Source logs remain local; exports redact PII and explicitly state their altered payloads cannot recompute original source hashes.
- cost_summary.py: planning excludes derived rows and legacy pairwise calls in simple mode; multi-judge batch planning is approximate. Actual ledger remains authoritative; unknown usage/prices stay Unknown. Bot versus evaluation costs remain separate.
- simple.html/simple.js: ten-category setup, nine Bias subtype panels, side-by-side evidence/severity, override badges, retention input, SSE per-bot/category progress, time/cost charts and tables. No review button on a derived row with no direct transcript. Existing polling remains the durable fallback.
- governance.html/governance.js: dedicated Governance page with cards, integrity, audit, mapping, reproduction (password re-entry if needed), retention and delete controls. No keys in browser storage.
- docs/bias-governance.md and README.md describe actual behavior and limitations.

## Scoring/counts

Default three repeats: 9 non-bias scenarios x3 + 8 conversational bias sub-tests x3 = 51 conversations per bot, plus 3 derived algorithmic outcomes = 54 records. Paired and multi-turn conversations send multiple messages. One repeat: 17 live cases +1 derived record.

Bias index averages the eight live subtype means across ALL planned repeats; missing evidence contributes zero to the configured index, and measured quality/coverage are separate. Algorithmic score = mean counterfactual fairness scores; disparity index =100-score. It is reported separately, never double-weighted. It cannot inspect training data or establish fairness across a population. Legacy sixteen-category/eight-hundred-case summaries keep their own snapshots and scores.

## Verification and artifacts

- New tests: tests/test_bias_governance.py, test_governance_recovery.py, test_speed_cache.py, test_http_turn_cache.py. Cover neutral pair logic, ordering, aggregation, missing evidence, audit edits/truncation/crash catch-up, overrides, export redaction, retention, reproduction, repeat isolation, completed/partial response reuse, strict batch IDs/shared cost scope, provider limits, classifier timeout and judge concurrency/agreement.
- tests/fixtures/protocol-v3.json + tests/legacy_protocol.py explicitly freeze old protocol compatibility; old sixteen-category tests now use that historical fixture instead of claiming it remains the default.
- Earlier full pass: 189 passed, 1 skipped, one benchmark failed by 34 ms over the unchanged 1.2-second threshold. Steady-state warm-up and GC isolation fixed benchmark noise; warm-up + median of five samples now passes the SAME 20% budget. Focused benchmark/partial-cache rerun: 2 passed. FINAL verification: 190 passed, 1 skipped, one existing Starlette/httpx deprecation warning; 70.56 seconds. The benchmark passed under full-suite load with the unchanged threshold. See PROGRESS.md/XML.
- Ruff formatting/lint and 19-file JS syntax checks passed. Prettier check found only the old HANDOFF, now being replaced/formatted. Bash syntax must be checked outside the restricted shell; sandboxed Git Bash hit a Windows IPC permission error (not a syntax error).
- Browser: isolated fixture showed all nine bias subtype rows and paired replies; Governance showed intact audit chain, 36/36 outcomes for two synthetic bots, cards and no console errors. PDF exported successfully (~78 KB). Production setup will be reopened after final checks.
- Detailed XML: C:\Users\Moinuddeen hussain\Documents\ChatGPT\Moinuddeen_airm\comparison-reports\bias-governance-regression.xml.

## Remaining limitations / next work

1. Test real HHEM/Qwen weights, current provider APIs and 2–4 real bots using explicitly configured/authorized accounts. Unit tests/fixtures do not prove classifier accuracy, real quota recovery or live cost totals. Do not download large models or expose keys blindly.
2. Uploaded ZIP execution sandbox remains NOT implemented. ZIP intake is safe storage and Not tested with explicit reason; never substitute arbitrary host execution. Existing Docker hosts Studio only.
3. Actually execute ./start.sh and Docker on macOS/Linux. Code is portable and CI matrix remains, but local Windows lint/unit tests are not proof of those hosts. Linux browser libraries and PDF Hindi font portability still need host validation.
4. Regex export redaction covers emails/phones/SSNs/key patterns, not every contextual name/address. Review before sharing. Hash chaining is not signed/nonrepudiable and cannot detect replacement of the whole database plus backups. Protect local files/backups.
5. Stateful web partial dialogues and expired/cookie-bound target sessions cannot always resume without replay. Current behavior preserves evidence and marks Not tested with reason. A targeted, secure browser-state persistence design is needed to expand this safely; do not silently resend completed turns.
6. Batch planning is optimistic when requests arrive sparsely; actual ledger costs, retries and shared overhead are audited. Exact vendor invoice/hidden bot tools remain unavailable without bot telemetry.
7. Optional classifier adapters use a reviewed local HHEM custom-code flag. Keep operator config trusted; never accept executable uploaded model/project code. Benchmark is simulated steady-state runner latency with a fixed +20% gate, not live network performance; do not loosen thresholds to hide regressions.
8. API settings/private request-default secrets beyond password fields need a fuller structured secret schema. Current configured keys and retained rotation keys are scrubbed before persistence; never put credentials in facts/rubrics/extra request JSON.

## Commands / next steps

From D:\AI-Agent-Testing-Studio:

Windows: powershell -ExecutionPolicy Bypass -File .\run.ps1
macOS/Linux: ./start.sh
Tests: .\.venv\Scripts\python.exe -m pytest -q
Focused: .\.venv\Scripts\python.exe -m pytest tests/test_bias_governance.py tests/test_governance_recovery.py tests/test_speed_cache.py tests/test_http_turn_cache.py -q
Quality: .\.venv\Scripts\ruff.exe check app tests scripts sample_project
Format: .\.venv\Scripts\ruff.exe format --check app tests scripts sample_project
Frontend: npm run format:check; npm run check:js

Inspect Git status and app port/listed running jobs first. Preserve any pre-existing .gitattributes edit (it was outside this phase). Read current PROGRESS result; fix only actual failures. Verify UI using isolated fixture data before real provider charges. Update progress and this handoff as work changes.

Do NOT rerun C: workspace apply_bias_governance.py, finish_governance_ui.py, complete_governance_details.py or other patch helpers: they are one-off non-idempotent installation scripts. Edit the actual D: source files. Do not delete production history or the old referenced scenarios.json/legacy tests merely because defaults changed.

Final quality checks: Ruff check/format passed; 19 JavaScript files passed syntax checks; elevated Git Bash syntax check of start.sh passed. Live production setup returned ten categories, nine bias sub-tests and three repeats. No browser console errors in the live setup. Source changes are saved in local Git; inspect git log for the final commit. The pre-existing .gitattributes change remains outside this phase.
