# Progress

## Phase 1 — restore point and cleanup

- Restore point: 6b041bd (local Git initialized; no remote configured).
- Credential-pattern scan of staged source found no recognizable keys. .env/runtime/venv ignored.
- Reference scan (source, tests, configs and docs, excluding candidate itself) found no references to these retired standalone experiments. Deleted with git rm:
  - scripts/check-whitebox.cjs
  - scripts/improve-readability.cjs
  - scripts/show-public-comparison.cjs
  - scripts/inspect-public-bots.cjs
  - scripts/check-team-preflight.cjs
- Retained runtime history, uploaded datasets, dependencies and .env. Runtime records are accessed dynamically; deleting them is not justified by import scans.
- Existing large suites remain referenced by legacy endpoints/tests, so retained for backward compatibility.

## Phase 2 — simple studio

In progress: exactly ten base scenarios with configurable repetitions, multi-judge fallback, audit trail, simple comparison screen.

## Phase 2 — implemented and verified in local tests

- Default / screen: 1–4 targets; links, REST/OpenAI APIs, web-chat connector settings and safe ZIP intake.
- Exactly ten authored base scenarios, default three repeats, per-scenario repeat controls; legacy suites retained only for old interface/API compatibility.
- Editable protocol, weights, tie margin and provider catalogue: app/studio/settings.json.
- Multi-judge panel, explicitly selected local fallback, live judge/key changes, account model discovery and status indicators.
- Missing evidence contributes zero to the configured index while measured quality/coverage remain separate. Incomplete panels retain partial verdicts and remain Not tested.
- Weighted comparison with ties and category-cluster bootstrap intervals against every opponent; incomplete comparisons have no winner.
- Case details preserve open panels during progress refresh. Token/cost bars and tables separate bot versus evaluation cost; unknown costs remain Unknown.
- Audit stores exact judge request messages, model identifiers, runtime versions, configuration/price snapshots, switches and human-review notes. Original human-overridden verdict is preserved.

## Phase 3 — recovery and portable setup

- No permanent circuit-breaker skipping in the ten-case protocol. Bounded target/judge retries and per-call timeouts remain; stop/deadline controls remain effective.
- Checkpoints and automatic restart recovery for simple runs whose credentials remain available. Authenticated targets or missing judge keys require UI re-entry; no keys are stored in the database.
- start.sh installs dependencies and Chromium, checks Ollama and opens the browser after health succeeds. Windows run.ps1 gains hidden browser helper and first-time Chromium installation.
- Optional non-root Docker hosting added. This hosts the Studio, NOT arbitrary uploaded projects. Docker-only explicit host-gateway access preserves metadata/private-IP blocking by default.
- CI matrix configured for Windows, macOS and Ubuntu. Native macOS/Linux/Docker execution is a task awaiting those environments, not a verified result.

## Verification

- Full regression suite before the final small governance changes: 149 passed, 1 skipped, one existing Starlette/httpx deprecation warning.
- Following recovery/eligibility changes: 20 focused tests passed, including crash recovery and distinct-model agreement.
- Latest complete suite result recorded below after completion.
- Ruff lint/format and JavaScript syntax checks passed. Bash syntax check passed using installed Git Bash. Browser verified 1–4 target cards, 10 repeat controls, 6 judge choices and planned counts; a missing route slash was found and corrected.
- Live provider limitation: native Google Gemma returned HTTP 500. Earlier native 320-case Reliance run 12023828-9c6e-4c50-ae0a-a45c760d55c7 scored only 2 cases; it is partial evidence, not an overall quality verdict. No new full live benchmark or API cost total is claimed.

## Remaining tasks

- Implement and verify an actual isolated ZIP application runner; never replace this with host execution.
- Run real cloud/local model integration checks and a complete live ten-case benchmark when a working provider/local model is available.
- Execute Mac/Linux startup, Docker and the new CI matrix on those systems.
- Broader cleanup: referenced scripts/datasets/docs and dynamic runtime history remain. Only the five proven unreferenced tracked experiments were removed.

- Cleanup addendum: removed unreferenced, untracked verification/coverage-ui.cjs after a reference scan. Git cannot remove untracked files; a recoverable copy is outside this repo at C:/Users/Moinuddeen hussain/Documents/ChatGPT/Moinuddeen_airm/coverage-ui-cleanup-backup.cjs. No runtime results were removed.

## 2026-10-14 — factuality and demographic bias extension

- Renamed Answer accuracy to Hallucination and Fairness to Bias: accessibility.
- Added relevant/on-topic factuality, irrelevant/off-topic claim handling, religion, caste, sex/gender and skin-colour pairs.
- New simple protocol has 16 scenarios; repeats, scores, transcripts and weighting are config-driven.
- Preserved old protocol snapshots in result rendering, manual resume and crash recovery.
- Verified 25 focused category, API, recovery and reference-free tests; live UI verification follows.

## 2026-10-14: ten cases per category, five repeats

- Added 160 authored scenarios across the 16 visible categories; no wording padding.
- Default five repeats produces 800 case executions per bot. Each stores a unique base-case
  ID, scenario number and repeat number, with within-case consistency summaries.
- Added independent relevant-answer and irrelevant-request score bars. Older runs explicitly
  show these as not tested, without rewriting their scores or transcripts.
- Kept existing judge, token/cost metering, checkpoints and provider controls.
- Verification: 24 targeted tests passed; Ruff and JavaScript syntax checks passed. Browser confirmed all 16 controls and independent relevance/irrelevance bars.
- Live evaluation `1dbd9014-5ecb-49c0-888d-4fd300c6973b` started with 800 cases and ten bot-declared mock catalogue references. Gemini/Gemma routing and judge fallbacks are audited.
- Reliance backend went offline during execution. Restarted the existing backend without changing credentials or source; retained 19 valid scores and resumed 781 pending/missing cases with bounded concurrency.
- No full-score or completion claim until final coverage is established; provider failures stay Not tested with their reasons.

## Final live verification and corrections

- Real Reliance run 3ed8185c-669e-43cc-b77d-fc62942584bf completed with 10/10 scored scenarios, one repeat each, using local llama3.2:3b as judge and Gemini 2.5 Flash as bot. Index 90%; fairness/helpfulness 50%, remaining checks 100%. These are AI estimates on a small suite.
- 15 bot requests: 14,679 input + 2,974 output tokens (reasoning 1,752 is already included). Snapshot estimate $0.011839. Judge: 14 local requests, 9,083 input + 1,813 output, zero API fee; hardware cost excluded.
- Exact evidence-ID binding solved Hindi quote-translation failure without accepting fabricated excerpts or re-requesting the bot answer. Original source excerpts still pass the quote validator.
- Fixed global history function shadowing the browser History object; renamed to loadHistory and verified actual saved-run navigation. Fixed stale charts when switching to legacy runs and double-counted reasoning in token bars.
- Audit details now freeze request messages before retry mutation. Previous password-field keys remain redacted after rotation. ZIP-only intake creates explicit Not tested records; automatic ZIP execution remains a task.
- Latest complete regression suite: 152 passed, 1 skipped. Subsequent focused checks cover evidence IDs, immutable audit messages and rotation; results appended after completion.
- HANDOFF.md is the self-contained continuation prompt and lists concrete remaining tasks. No claim of universal bot support, production certification or verified cross-OS execution is made.

- Final focused regression after evidence IDs, immutable audit and key rotation: 41 passed. Browser history navigation and real completed dashboard verified with no JavaScript errors in a fresh tab. Screenshot saved outside the source repo.

## Latest run checkpoint — 2026-10-14

User authorized the safest restart/resume so all cases continue. Run `1dbd9014-5ecb-49c0-888d-4fd300c6973b` has 800 planned cases (16 categories, 10 cases x 5 repeats), preserving the separately started expanded suite. Stopped cleanly at 83 scored cases, restarted only Studio, and resumed the same run through `/api/studio/runs/{id}/resume`: 717 pending cases. Verified status running, 84 scored, stage Warranty help after resume. Original cloud Gemma primary and local llama3.2:3b fallback retained. Credentials loaded from existing local environment files into process memory, never printed or added to Git. Do not claim this 800-case benchmark is complete; check live status before any restart. Completed ten-case report remains run `3ed8185c-669e-43cc-b77d-fc62942584bf`, score 90, bot API cost estimate $0.0118387, local judge API cost $0.

## 2026-10-15 — Bias and governance phase

- New defaults restore ten categories and three repeats. Bias has eight neutral paired probes plus a derived algorithmic disparity index; prior sixteen-category run snapshots remain unchanged.
- Added editable app/studio/bias-v1.json, pair-order randomization and descriptive pre-judge signals. Algorithmic aggregate does not double-weight Bias.
- Added SQLite-anchored hash chain, Governance page, reproduction, overrides badge, redacted export, retention and delete cleanup. Tests and live verification follow; no new quality scores claimed.

## 2026-10-15 — execution and verification phase

- Added run-scoped durable bot cache (separate repeat keys) and validated judge cache keyed by canonical request and transcript hashes. Swapped A/B orders remain independent. Cached resumes do not issue another bot request.
- Independent judge selections now run concurrently behind existing global/provider gates. Strict JSON micro-batching rejects missing/duplicate IDs and falls back to individual requests; shared batch cost is counted once, not assigned to the first bot.
- Added exact-canary short-circuit, descriptive PII/refusal/length signals and optional offline HHEM/Qwen adapters. Local models are not downloaded or claimed installed; bounded subprocess inference terminates on timeout.
- Added SSE per-bot/category progress, cumulative active duration and report timing data. A pinned simulated runner benchmark enforces a 20% regression budget.
- Verification milestones: 56 focused scoring/evidence/cost tests passed; 47 bias/governance/recovery/cache/concurrency tests passed (overlap exists). Browser verified all nine bias subtype rows, paired evidence and an intact governance panel against an isolated synthetic fixture; JSON/PDF export worked. No live bot/provider calls were issued for these checks.
- Restored old sixteen-category/eight-hundred-case compatibility tests using an explicit historical protocol fixture. No production history, keys or old results were deleted.

## 2026-10-15 — final corrections and handoff

- Full regression isolated three compatibility defects (credential mask spelling and minimal disabled-classifier fixtures), then fixed them; 23 targeted privacy/fallback/governance checks passed.
- Partial API conversations now checkpoint each successful turn and resume its session/history without repeating those answers. Stateful web partial sessions fail visibly if they cannot be restored without replay; paired web requests remain independent.
- A full run produced 189 passed, 1 skipped and one timing failure (1.234 s vs fixed 1.2 s). Added unmeasured warm-up, explicit GC isolation and median-of-five steady-state measurement; the SAME threshold passes. No tolerance/baseline increase was made to hide a regression. Final full-suite verification follows.
- Updated HANDOFF.md as a self-contained continuation prompt, with exact paths, implemented contracts and remaining real integration limitations. No new paid benchmark or new chatbot score claimed.

## Final verified checkpoint — 2026-10-15

- Final COMPLETE regression suite: **190 passed, 1 skipped**, one existing Starlette/httpx deprecation warning; 70.56 seconds. Fixed 20% benchmark gate also passed under full-suite load.
- Ruff check/format passed; 19 JavaScript syntax checks passed; Git Bash start.sh syntax check passed with normal escalation after the restricted IPC error.
- Live setup http://127.0.0.1:2708 returned ten categories, nine bias sub-tests and default three repeats. Browser showed the correct derived-record count and no console errors. Screenshot: comparison-reports/studio-bias-governance-live.jpg outside the product repo.
- Upgraded Studio is running with historical auto-resume disabled for this launch; no new paid evaluation or new chatbot quality result was produced during feature verification. Historical data is preserved.
- Local-classifier weights, real cloud-provider integration and actual macOS/Linux/Docker execution remain explicit integration tasks. Partial stateful web sessions preserve evidence and become Not tested if safe restoration is impossible.

## 2026-10-15 — one simple Studio interface

- Replaced the separate Evaluate/Governance/Advanced entry points with one app shell: **Evaluate, Results, Governance**. “Test and compare chatbots” replaces the old question heading. Advanced setup is optional and collapsed inside Evaluate; legacy protocols remain available there.
- Added a shared saved-evaluation selector, accessible active navigation, hash/deep-link and Back/Forward support. Old governance bookmarks retain their run ID and redirect into the unified screen. Browsing history preserves a new draft; saved settings load only on explicit request. Stop/resume remain reachable from results.
- Results prioritize overall score, scored coverage, category bars, evidence and separate bot/judge cost totals. Fully scored and partial coverage are visible. Formula, detailed timings and raw audit data are expandable. Conversation evidence is inserted on demand; expanded case and bias evidence survives refresh.
- Governance loads within the same screen, with integrity cards and collapsed model cards, audit, privacy/retention and framework details. Reproduce, written overrides, redacted exports and protected deletion keep their existing API contracts. Added stale-request/stream guards when changing saved runs.
- Focused verification: **25 API/governance Python tests passed**, **9 navigation tests passed** (including two Back-button regressions). Node navigation tests were added to the existing Windows/Linux/macOS CI matrix. Browser checked old governance bookmark redirect, run switching, draft preservation, existing 10-case scores/costs, lazy injection evidence and refresh keeping it open. No new paid run, no user history deletion and no score changes.

- Final UI checks: all 22 JavaScript files parsed; Prettier, Ruff lint and changed Python formatting passed. Browser console had no errors. Saved visual proof under the C: workspace `comparison-reports/studio-unified-results.png` and `studio-unified-governance.png`. No backend restart was required.
- Final visual correction: direct view anchors reserve space for the sticky header, keeping the page title visible after reload or bookmark navigation.

## 2026-10-15 — Phase 0: black-box recovery and honest display

- Restore commit d5c08bf; unrelated .gitattributes change preserved.
- Installed-only local judge discovery is lazy after failure. Run-scoped quota/auth cooldown avoids repeatedly billing a broken provider; key changes create a new identity. Local model timeout is configurable. Private runtime locks are not deep-copied into judge configurations.
- Retained bot answers can be judged even when target discovery is offline; timed-out conversations retain successful prefixes. SDK/tokenizer imports/counting run off the event loop. Automatic restart can use local fallback when a cloud credential is absent.
- Empty billing evidence stays Unknown; tiny positive costs display <$0.0001 and local-only zero API costs are labeled. Categories below half scored coverage get Low confidence.
- Historical local benchmark d55be5cf-d8e0-4a31-a00f-d6f3467abc05 last verified 8/34 live outcomes scored, 36 records including two derived rows. Listeners were subsequently absent. No completed score is claimed.

## 2026-10-15 — Phases 1/2: optional assurance plug-ins and shared UI

- Added app/assurance contracts, planner, Black adapter, Gray checks and read-only White scanner adapters. Only selected engines run; missing tools/inputs have explicit findings. Plans and findings are sealed into the existing anchored audit chain.
- Added mode tabs and Combined classification, four-part evidence explanations, severity/review queue, original-preserving false-positive review, private-input cloud opt-in, input hashes, retention/delete, JSON/PDF and same-config reproduction.
- Gray extracts each explicit policy rule into its own check. Editable templates: app/studio/gray-v1.json. Correlated synthetic canary logs can be attached after the chat; old run IDs cannot score a new run. HHEM is a separate optional metric, never faked by a rubric score.
- White never imports/builds/executes uploaded code. ZIP intake limits paths, expansion, files and time. Docker scanner execution is read-only/networkless/resource bounded with pinned tools, runtime version checks, inspected image IDs, bounded output and cleanup on timeout. No Docker/tool/database means Not tested. Gitleaks findings show only credential tails, never secret-containing lines.
- Ownership is required on both new and legacy public start/resume paths. Existing history and old protocols remain intact.

## Verification for this upgrade (latest details in HANDOFF)

- Earlier focused black-box/cost/recovery selection: 35 passed.
- New engine/combiner/privacy/sandbox tests initially: 31 passed. Later API/UI/recovery selection: 49 passed, including isolated headless White-only UI without any real bot/provider calls. Further tests added for rule expansion, fresh-canary correlation, finding tampering and offline-target cached rejudging; final result to be appended.
- Timing gate was NOT relaxed: staged isolated median 2.281 s versus fixed 1.2 s. The restore-point code also failed, median 1.984 s, on this host. This is an open performance verification issue, not a passing check. Classifier weights, real scanner containers/databases and native macOS/Linux execution remain integration tasks.

## Final focused source verification

- 112 tests passed (128.14 s), one existing Starlette/httpx deprecation warning. Includes all mode combinations, masking/limits, local-only defaults, canary correlation, state tampering, cached offline-target rejudging, ownership/capacity, costs, audit/recovery and isolated Chromium UI/Governance. No paid evaluation was started by these tests.
- Ruff check/format passed for app/tests (74 files); new JavaScript syntax and changed frontend/doc formatting passed. Timing gate remains open as recorded above; no claim of full-suite green or production certification.

## Installed/runtime checkpoint after verification

- All 45 reviewed files installed into D:/AI-Agent-Testing-Studio with content-hash verification. Existing .gitattributes edit left untouched. Installed Ruff lint/format passed; 9 Node navigation tests passed. A final assurance/UI subset passed 38 tests after the informational capability route slash correction. Counts overlap the 112-test focused run.
- Studio PID15324/session55277, Ollama PID7988 and Reliance backend PID13692 were healthy at launch. STUDIO_AUTO_RESUME=0. Existing local llama3.2:3b warmed with an empty prompt; no new quality case/provider bill was introduced by warming.
- SAME run d55be5cf-d8e0-4a31-a00f-d6f3467abc05 resumed with ownership_confirmed=true. Eight scored cases preserved, 28 pending records at resume (including two derived). Latest verified progress: RUNNING, 9/34 live outcomes scored, stage Age, 36 total records. Bot ledger $0 API; judge total temporarily Unknown while a request is in flight. No complete benchmark, final quality score or winner is claimed.
- Do not restart the running benchmark for the final informational /api/assurance/capabilities route correction. Source is corrected; that optional endpoint becomes available on the next SAFE backend restart. Main UI does not depend on it.
- Remaining assurance work includes actual scanner/database/classifier integrations; broader semantic/control-flow coverage; cross-run model-version baselines; and freezing/checking scanner config/rules across reproduction (current reproduction freezes protocol/private input hashes, not an immutable scanner image/rules snapshot). Preserve these limits in product claims. Legacy old-run settings can omit newly added runtime defaults (notably local judge timeout 240); do not claim bit-identical reproduction of pre-upgrade execution.
- Source changes are prepared for a scoped local implementation commit; inspect git log for its SHA. No GitHub push was performed.

## 2026-10-15 — Real White-box source audit completed

- User requested every prior chatbot evaluation stopped and only digital-multi-agent-ai-main.zip scanned. Stopped d55be5cf-d8e0-4a31-a00f-d6f3467abc05 with an anchored user_stop event, retaining all scores/transcripts. Historical auto-resume remains disabled for this launch. No new Black/Gray conversations or LLM judge calls.
- Installed Docker Engine 29.1.3 in existing Ubuntu WSL and provisioned all pinned scanner images plus official public npm/PyPI OSV and Trivy databases separately from source scanning. Actual source scans remained networkless, read-only and unprivileged; submitted programs/tests/install scripts were never executed.
- Corrected OSV 1.9.2 command flags, WSL bind paths, cold-start timeouts and Trivy's BoltDB writable-copy requirement. Original DB/source remain read-only; only the disposable public DB copy is writable and cleaned after scanning. Linux/macOS source-child/cache permissions corrected without exposing private parent directories.
- Full OSV database exceeded its memory cap. Used official OSV inventory (never a vulnerability verdict) to scope public advisories to 804 packages, retaining every matching advisory independent of version/severity. Final OSV report package coverage and filtered DB hashes are verified before accepting a finding. Snapshot records original/filtered hashes. New projects with uncovered packages are rejected rather than given false clean results.
- Added per-tool durable progress and an explicit White execution count. Static no-match controls stay Not tested with scanner_completed metadata, not passes. Bandit keeps its actual Low/Medium/High severity.
- SAME assessment 0941855a-1d8a-4571-95b7-bd15b4e5bc4e completed in 232.501 seconds after repair: 6/6 tools, 14/14 checks processed, 3 pass / 3 fail / 2 declarations / 6 insufficient-evidence Not tested. Source SHA-256 6753386792629121cbbdef878983f8e8c294c0ef014e212118895f3d1536d177. Audit valid. Original private upload deleted immediately after run.
- Findings: one Low Bandit assert finding at backend/main.py:88; 137 OSV package/advisory matches; 11 Trivy findings. Scanner counts can overlap and are not a deduplicated vulnerability total. No container image was built/scanned: Trivy scanned filesystem dependencies; this archive contains no Dockerfile. Three clean checks are limited to selected Gitleaks/Semgrep rules, not proof of universal safety.
- Verification: 52 focused scanner/assurance/API/UI tests passed; Ruff passed. Reports exported outside repo as comparison-reports/digital-white-audit.html, .pdf, .json. One public CVE identifier was over-redacted by the existing phone masker; the other advisory evidence remains linked, and redaction fidelity needs follow-up. No claim of a behavioral quality score, native cross-OS integration, or complete security coverage.

## 2026-10-15 — Repair GitHub Actions formatting failure

- Applied the pinned Prettier formatter to docs/assurance-guide.md, DECISIONS.md, HANDOFF.md and PROGRESS.md. The initial personal-repository CI failed on these Markdown files.
- Disabled matrix fail-fast so a failure on one OS does not cancel the other Windows/Linux/macOS jobs. Kept all lint, formatting, UI and regression checks enabled. Application behavior, scores, local history and credentials are unchanged.
- Verify with the exact npm run format:check command and the next GitHub Actions run; source changes remain limited to documentation formatting and this matrix setting.

## 2026-10-15 — Cross-platform CI regression fixes

- Fixed the macOS comparison smoke test by using Windows process flags only where supported. The fixture now confirms ownership, stores its screenshot in its temporary workspace, and closes database handles before cleanup.
- Corrected the overlapping-run concurrency test to keep both leases active during the measurement. Added a separate event-driven test proving that releasing a stricter run restores the wider run's allowed concurrency.
- Reuse idle SQLite connections per database path and thread. Nested/concurrent transactions get separate leases; FULL synchronous WAL commits, rollback, and evidence persistence are retained. Shutdown closes idle handles and lets active transactions finish before closing them.
- Added six database regression tests for independent transactions, rollback, concurrent writes, reuse, durable reopen and shutdown. The existing performance baseline and 20% threshold are unchanged.
- Local verification: 249 passed, 1 existing symlink-permission skip, 85.28 seconds. Ruff format/lint, Prettier, 24-file JavaScript syntax, nine navigation tests and the isolated four-bot comparison smoke test pass. No chatbot/provider calls were made. Native GitHub matrix verification follows the commit.

### Native CI follow-up

- Run 38770550500, commit 663d90d: macOS and Ubuntu passed every check, including the full regression suite and comparison UI.
- Windows failed before tests: the hosted runner's preinstalled pipx requires filelock>=4.0.9, conflicting with the project dependency version. Create a clean .venv and add its platform-specific executable directory to GITHUB_PATH before installation. Keep pip check enabled inside the isolated environment; do not uninstall runner tools or weaken dependency validation.

## 2026-10-15 — Local generated-file cleanup and API guide

Removed 103 untracked generated/cache files (2835072 bytes), plus their cache folders and the empty verification directory. Source, tests, sample data, dependencies, local credentials, saved reports, audit history, scanner databases and recovery backups are preserved. No tracked file was deleted; git rm is not applicable to ignored caches.

Added docs/api-keys.md explaining Studio judge keys, chatbot authentication and the separate Reliance backend .env. Current CI verification: b5888be, run 38771088235, Windows/Ubuntu/macOS all successful.

Deleted files:

- `.pytest_cache/.gitignore`
- `.pytest_cache/CACHEDIR.TAG`
- `.pytest_cache/README.md`
- `.pytest_cache/v/cache/lastfailed`
- `.pytest_cache/v/cache/nodeids`
- `.ruff_cache/.gitignore`
- `.ruff_cache/0.14.1/15167142090786329581`
- `.ruff_cache/0.14.1/195581709312814720`
- `.ruff_cache/0.14.1/3553882810115875040`
- `.ruff_cache/0.14.1/4323519583363054123`
- `.ruff_cache/0.14.1/7054680015494741488`
- `.ruff_cache/CACHEDIR.TAG`
- `app/__pycache__/__init__.cpython-312.pyc`
- `app/__pycache__/blackbox_app.cpython-312.pyc`
- `app/__pycache__/config.cpython-312.pyc`
- `app/__pycache__/database.cpython-312.pyc`
- `app/__pycache__/main.cpython-312.pyc`
- `app/__pycache__/models.cpython-312.pyc`
- `app/assurance/__pycache__/__init__.cpython-312.pyc`
- `app/assurance/__pycache__/black.cpython-312.pyc`
- `app/assurance/__pycache__/combine.cpython-312.pyc`
- `app/assurance/__pycache__/gray.cpython-312.pyc`
- `app/assurance/__pycache__/intake.cpython-312.pyc`
- `app/assurance/__pycache__/models.cpython-312.pyc`
- `app/assurance/__pycache__/privacy.cpython-312.pyc`
- `app/assurance/__pycache__/routes.cpython-312.pyc`
- `app/assurance/__pycache__/sandbox.cpython-312.pyc`
- `app/assurance/__pycache__/service.cpython-312.pyc`
- `app/assurance/__pycache__/white.cpython-312.pyc`
- `app/blackbox/__pycache__/__init__.cpython-312.pyc`
- `app/blackbox/__pycache__/baselines.cpython-312.pyc`
- `app/blackbox/__pycache__/bias.cpython-312.pyc`
- `app/blackbox/__pycache__/catalog.cpython-312.pyc`
- `app/blackbox/__pycache__/classifier_runtime.cpython-312.pyc`
- `app/blackbox/__pycache__/comparisons.cpython-312.pyc`
- `app/blackbox/__pycache__/connectors.cpython-312.pyc`
- `app/blackbox/__pycache__/cost_adapters.cpython-312.pyc`
- `app/blackbox/__pycache__/cost_summary.cpython-312.pyc`
- `app/blackbox/__pycache__/deterministic.cpython-312.pyc`
- `app/blackbox/__pycache__/easy_setup.cpython-312.pyc`
- `app/blackbox/__pycache__/evidence_ids.cpython-312.pyc`
- `app/blackbox/__pycache__/evidence.cpython-312.pyc`
- `app/blackbox/__pycache__/execution_cache.cpython-312.pyc`
- `app/blackbox/__pycache__/gemma_native.cpython-312.pyc`
- `app/blackbox/__pycache__/governance_routes.cpython-312.pyc`
- `app/blackbox/__pycache__/governance.cpython-312.pyc`
- `app/blackbox/__pycache__/judge_batch.cpython-312.pyc`
- `app/blackbox/__pycache__/judge_prompts.cpython-312.pyc`
- `app/blackbox/__pycache__/judge_recovery.cpython-312.pyc`
- `app/blackbox/__pycache__/judge.cpython-312.pyc`
- `app/blackbox/__pycache__/local_metrics.cpython-312.pyc`
- `app/blackbox/__pycache__/metering.cpython-312.pyc`
- `app/blackbox/__pycache__/pricing.cpython-312.pyc`
- `app/blackbox/__pycache__/quota.cpython-312.pyc`
- `app/blackbox/__pycache__/readiness.cpython-312.pyc`
- `app/blackbox/__pycache__/reports.cpython-312.pyc`
- `app/blackbox/__pycache__/runner.cpython-312.pyc`
- `app/blackbox/__pycache__/scheduling.cpython-312.pyc`
- `app/blackbox/__pycache__/schema.cpython-312.pyc`
- `app/blackbox/__pycache__/studio_engine.cpython-312.pyc`
- `app/blackbox/__pycache__/studio_routes.cpython-312.pyc`
- `runtime/judge-detail.png`
- `runtime/judge-readiness.png`
- `runtime/readability-desktop.png`
- `runtime/readability-mobile.png`
- `runtime/scoring-summary.png`
- `sample_project/__pycache__/chatbot.cpython-312.pyc`
- `sample-chatbot.zip`
- `scripts/__pycache__/package_release.cpython-312.pyc`
- `tests/__pycache__/conftest.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/legacy_protocol.cpython-312.pyc`
- `tests/__pycache__/test_assurance_ui.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_assurance.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_bias_governance.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_blackbox_upgrade.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_comparison.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_concurrency.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_costs.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_coverage_scoring.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_curated_and_evidence.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_database.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_easy_setup.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_entrypoint.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_exact_multijudge_compare.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_expanded_scenarios.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_extended_categories.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_gemma.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_governance_recovery.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_http_turn_cache.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_judge_providers.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_judge_readiness.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_package_release.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_platform.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_provider_quota.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_recovery_controls.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_reference_free.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_remote_bots.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_scanner_runtime.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_scoring.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_simple_studio.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_speed_cache.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_studio_api.cpython-312-pytest-9.1.1.pyc`
- `tests/__pycache__/test_zip_handler.cpython-312-pytest-9.1.1.pyc`

## 2026-10-16 — Repair intermittent Windows comparison cleanup

- A fresh attempt of run 38771088235 confirmed the pipx/filelock dependency fix and regression suite still pass, but exposed an intermittent WinError 32 at the comparison smoke test's temporary SQLite cleanup. The older dependency error and this new cleanup failure have different causes.
- The isolated server now shuts down its owned process tree. On Windows, terminate the virtual-environment launcher and its server descendants together using taskkill with the exact spawned PID; on POSIX, start a separate session and stop its process group. Wait for exit before releasing parent database handles and removing the workspace. Existing UI assertions remain enabled.
- Added a real parent/child regression fixture: the descendant holds a SQLite file and a listening socket, and cleanup must release both. Cleanup is idempotent. Seven targeted database/process tests passed. The comparison smoke test passed three consecutive local runs, including temporary directory removal, with zero provider calls. Remote matrix results must be verified after pushing.

## 2026-10-16 — Run checks against the latest branch

- The user's pasted pipx/filelock log belongs to historical run #3, commit 663d90d, re-run as attempt 2 after newer fixes existed. Re-running old jobs executes their original workflow, so it still lacks the isolated environment. Remote master ea40d8d and run #5 passed all platforms.
- Added workflow_dispatch so users can choose Run workflow, select master, and test the current code. Added an explicit virtual-environment assertion before dependency installation; pip check remains mandatory.
- Added a README status badge and instructions distinguishing a new branch run from replaying an old job. Included the already prepared API-key guide so the README's configuration-help link resolves in the repository.
- Validate YAML/events, PowerShell syntax and formatting, then verify the new remote matrix. No historical run is deleted or relabeled.

## 2026-10-16 — Standalone judge provider configuration

- Removed this machine's STUDIO_JUDGE_ENV_FILE dependency on Reliance. Preserved the existing judge credential in Studio's ignored .env without printing it or changing the chatbot's own file. Changing the target bot no longer involves its configuration for judge credentials.
- Added config-driven provider/model/key environment bindings in app/studio/settings.json and a provider-scoped resolver in app/blackbox/judge_credentials.py. Default provider selection uses STUDIO_JUDGE_PROVIDER; OpenAI, Claude, Gemini, hosted Gemma and Ollama use their own model variables. Explicit custom overrides remain supported.
- Simple setup, model discovery, multi-judge selection and live judge changes reuse the corresponding Studio provider key. Explicit UI keys take priority. Built-in provider credentials are not forwarded to arbitrary endpoints; public settings expose only whether a key is configured.
- Updated .env.example, README and API/setup guides. An explicitly configured external credentials file remains a legacy opt-in; there is no default target-bot path. Thirty initial credential/setup/API tests passed without external provider requests. Final regression/format results follow.

### Standalone judge verification

- Full local regression suite: 258 passed, one existing Windows symlink-permission skip, 176.80 seconds. Eight provider/credential tests cover independent accounts, explicit overrides, legacy opt-in, hostile endpoint variants, several judges with arbitrary targets and model discovery. No provider requests were made by these tests.
- Ruff format/lint passed (88 Python files), 24-file JavaScript syntax passed, nine navigation tests passed, and the full Prettier check passed. Fresh-process checks confirm the saved Gemini key/model come from Studio's own .env, no external bot env is required, and public defaults do not expose the key.

Native Linux follow-up: run 38849599247 exposed a pre-existing immediate socket-rebind race in tests/test_process_cleanup.py; judge credential tests passed. Parent wait() can return slightly before a descendant's kernel handles are released. The regression now waits at most five seconds for socket/file release, retrying only EADDRINUSE or PermissionError; a persistent orphan still fails. No check is skipped and the speed benchmark threshold is unchanged. Verify on both Windows and native Linux before repushing.

Cleanup follow-up verification: nine focused Windows tests passed (process release plus all credential tests). The process-release regression then passed 20 consecutive native Linux runs in existing Ubuntu WSL, using only Python standard-library fixture processes. No bot/provider request or performance-threshold change was introduced.
