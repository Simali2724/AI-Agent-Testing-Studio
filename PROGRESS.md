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
