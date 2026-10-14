# HANDOFF — Continue the existing AI Agent Studio

You are continuing an existing implementation. Do not rebuild it or rerun the one-off installer scripts. Work in small, verified edits; keep API keys out of code, chat, Git and reports.

## Exact project and environment

- Product repo: D:\AI-Agent-Testing-Studio
- Workspace/artifacts: C:\Users\Moinuddeen hussain\Documents\ChatGPT\Moinuddeen_airm
- Windows PowerShell; Python 3.12 virtual environment at D:\AI-Agent-Testing-Studio\.venv\Scripts\python.exe.
- Studio: http://127.0.0.1:2708/. Backend entry point app.main:app.
- Reliance bot: D:\reliance-project\backend, already running at http://127.0.0.1:8000/chat/stream.
- Ollama is now running at http://127.0.0.1:11434. Installed models: llama3.2:3b and nomic-embed-text:latest. The latter is an embedding model, not a rubric judge.
- A local Git repository was initialized in the product folder. Restore point is 6b041bd. No remote was configured or GitHub push performed in this phase.
- D: is outside this chat's writable workspace; use the normal escalation/approval mechanism for mutations there. Never touch unrelated D: files.
- Secrets used for the running services have been held in process environments/password fields. Do not assume a restart has valid cloud keys in .env. Never print .env, child environments or supplied keys.

## Latest real result (not a fixture)

Run 3ed8185c-669e-43cc-b77d-fc62942584bf:
http://127.0.0.1:2708/?run=3ed8185c-669e-43cc-b77d-fc62942584bf#results

Reliance answered through its actual API using gemini-2.5-flash. Local llama3.2:3b judged the answers. All ten scenarios scored, ONE repeat each; future UI default is THREE repeats.

- Configured evaluation index: 90%.
- Accuracy, injection, jailbreak, guardrails, memory, language/tone, PII protection and uncertainty: 100% each.
- Fairness/bias and helpfulness/over-refusal: 50% each. These are subjective local-judge estimates, not proof of discrimination or a universally correct quality rating. Inspect transcripts and reasons before changing the bot.
- Bot: 15 recorded requests; 14,679 input tokens; 2,974 output tokens INCLUDING 1,752 reasoning tokens. Total 17,653. Do NOT add reasoning again.
- Bot price-snapshot estimate: $0.0118387, displayed rounded as $0.011839. This is not an invoice, and hidden bot embeddings/tools/internal calls are outside the telemetry.
- Judge: 14 local requests including evidence-recovery attempts; 9,083 input and 1,813 output tokens. Local API fee $0; electricity/hardware excluded.
- One Hindi answer originally could not be judged because the small model translated its evidence quote. The same bot transcript was retained and rejudged; no additional bot request was made. Exact excerpt IDs fixed the mechanical evidence problem, without forcing a passing verdict (the final case scored 50).
- JSON artifact: C:\Users\Moinuddeen hussain\Documents\ChatGPT\Moinuddeen_airm\comparison-reports\reliance-ten-checks.json. Re-export after any later metadata correction.

Older native Gemma run 12023828-9c6e-4c50-ae0a-a45c760d55c7 scored only 2/320 due Google HTTP 500 and the old circuit breaker. Preserve it as partial evidence. It is not the latest successful benchmark.

## Implemented architecture

- app/studio/settings.json: exactly ten authored base cases, default repeats, category weights, tie margin and editable judge catalogue.
- app/blackbox/studio_engine.py: repetition builder, multi-model judge panel, explicit local fallback, audit events, worst-case index, weighted comparisons and scenario-cluster bootstrap against every opponent.
- app/blackbox/studio_routes.py: /api/studio/settings, /models, /runs, /runs/{id}/judges, /resume and /override. Configured backend credentials are reused server-side only when model/endpoint match.
- app/blackbox/evidence_ids.py: deterministic ID-to-original-excerpt binding. Invalid/made-up IDs are rejected; existing quote validation still runs. No translations become fabricated evidence.
- app/blackbox_static/simple.html, simple.css, simple.js: new default single screen. 1–4 bot cards, references/safety rules hidden unless needed, selectable judges, account model discovery, repeat counts, progress, score/cost bars and tables, transcripts, audit and exports.
- /index.html: retained legacy interface and datasets for old runs. Its quality-only scoring is a historical/advanced companion to the new worst-case index; do not accidentally display it as the new overall index.
- Existing connectors.py, metering.py, pricing.py, cost_summary.py, runner.py, scheduling.py and reports.py were reused with targeted integration changes.
- runner.py checkpoints, retains successful results and complete observations for judge-only resume. It attempts each simple-mode case with bounded retries instead of permanent circuit-breaker skipping. User stops/deadlines remain effective.
- app lifecycle auto-resumes interrupted simple runs when credentials remain available. Authenticated targets/missing keys require UI re-entry; secrets are not stored in SQLite.
- scheduling.py dynamically registers judge hosts, so fallback/mid-run endpoint changes use real limits rather than failing on missing gates.
- Settings.\_used_secrets keeps all password-field keys used during a run in memory for redaction after rotation. It is private and never serialized.
- Human override requires a note and an actual bot reply; original verdict and audit record remain.
- start.sh, scripts/open_browser.py and updated run.ps1 provide startup/browser opening. Optional Dockerfile, compose.yaml and .dockerignore host the Studio as a non-root user, with localhost port publishing.
- Docker-only host.docker.internal access requires an explicit environment switch; direct private IPs and metadata/link-local endpoints remain blocked. Tests cover this boundary.
- CI now has Windows/Ubuntu/macOS matrix; Ruff and Prettier remain the tools. Promptfoo was deliberately not added because it would duplicate the existing runner, metering and LiteLLM adapters.

## Scoring and governance contracts

Use run.studio as the primary new UI/report contract. Legacy run.summary and run.comparison fields retain older measured-quality meanings where applicable. New index: weighted mean of ten category means over ALL planned repeats, with Not tested contributing 0. Case score stays null when untested; index_contribution is explicitly 0. Tested quality and coverage are separate.

A winner requires complete evidence and a positive weighted scenario-cluster interval against every opponent. Close scores tie; uncertain intervals say too close to call. Mismatched actual judge panels across bots withhold a winner. Repeats are not independent coverage.

Actual model identifiers, exact judge request messages, protocol/config and price snapshots, temperature, fallback/manual changes and runtime versions are recorded. Upstream aliases do not guarantee an immutable model revision. Audit details are deep-copied so retry reminders cannot alter earlier prompt records. Older events created before this correction may be incomplete/reconstructed; do not claim every historical prompt is immutable.

Token output totals in cost_summary already include reasoning. UI bars now count input + output, and the reasoning column is explicitly labelled as included in output. Unknown prices/usage remain Unknown. Local API zero is a configured local-host declaration, not proof that electricity or a hidden proxy service is free.

## Cleanup actually performed

Five verified unreferenced tracked retired experiments removed with git rm:

- scripts/check-whitebox.cjs
- scripts/improve-readability.cjs
- scripts/show-public-comparison.cjs
- scripts/inspect-public-bots.cjs
- scripts/check-team-preflight.cjs

Unreferenced untracked verification/coverage-ui.cjs removed with a recoverable copy at C:\Users\Moinuddeen hussain\Documents\ChatGPT\Moinuddeen_airm\coverage-ui-cleanup-backup.cjs. Git cannot remove untracked files. Every deletion is listed in PROGRESS.md.

Keep runtime history, .env, installed dependencies and referenced legacy scripts/data. Do not delete a file merely because it looks old. Runtime paths are dynamic references. Git ignores .venv, node_modules, runtime, .env, caches and ZIPs. No prior run was deleted.

## Verification completed

- Full suite: 152 passed, 1 skipped, one existing Starlette/httpx deprecation warning (before final evidence-ID and audit/rotation additions).
- Later relevant evidence/Gemma/protocol/API checks: 34 then 40 passed. Final rotation/audit checks are recorded in PROGRESS.md after completion.
- Ruff lint/format and JavaScript syntax passed. Git Bash syntax check of start.sh passed.
- Browser verified four-bot setup, exactly ten controls, planned counts, live real 90% result and token/cost table. A global async function named history had overwritten window.history; renamed to loadHistory and actual history-button navigation verified in a fresh tab.
- Details preserve open state during polling. Switching to a legacy run clears stale new-run charts and links to its precise legacy URL.
- Neither cloud Claude/OpenAI/Gemma integration nor native macOS/Linux/Docker startup is established by these unit tests. Record them as tasks, not successes.

## Remaining work, in priority order

1. Implement a genuine isolated ZIP application runner. CURRENTLY NOT IMPLEMENTED. ZIP intake stores/validates archives, and ZIP-only runs record Not tested; no host code execution is allowed. Docker setup currently hosts only the Studio. Add resource/time/network limits, read-only upload mounting, clean environment without host/judge keys, explicit dependency/install consent, process/container teardown and safe black-box endpoint access. Unknown startup commands must not run on the host.
2. Execute Mac/Linux startup and Docker on actual environments. Minimal Linux may need Playwright OS libraries. Verify the CI matrix remotely only when a repository push is explicitly in scope.
3. Test real 2–4-bot comparison and provider failover with usable accounts. Do not invent a second bot/winner. Google Gemma previously returned HTTP 500. Local llama3.2:3b works; its judgment quality is limited. A stronger second family and expert review are useful.
4. Validate editable protocol JSON (exactly ten unique supported categories, finite positive weights, valid repeats and tie margin) with friendly configuration errors. Current file is valid, but arbitrary owner edits can break it.
5. Improve generic connection detection for API base URLs/authenticated web widgets. Current UI asks for a chat page or COMPLETE REST/OpenAI endpoint; arbitrary protocols, GraphQL schemas, CLI agents and unknown auth schemes need adapters. Do not advertise universal automatic connection.
6. The ten-case mode uses only the first uploaded factual scenario; additional cases belong to the legacy/advanced mode. Make larger reference coverage an explicit future protocol rather than silently counting it.
7. Secret redaction for arbitrary extra request JSON/body-auth schemes needs a structured design. Current configured password fields are protected; do not put keys in references/default JSON. Existing save redaction is a serialized-string replacement, which should become value-aware for short/escaped secrets before production.
8. Resume duration currently describes the last execution segment; old request statistics can duplicate a reused transcript in previous_attempts. Metered request/cost events are authoritative. Add cumulative active duration and metrics derived from real request IDs/events.
9. Avoid duplicate default/selected judge entries when a saved local judge matches an installed local preset. Distinct actual models, not repeated calls to one model, determine agreement. Query Ollama capabilities/digests instead of relying only on names that do not contain embed.
10. Improve PDF font handling for Hindi on Linux/macOS, capture actual local model digests/upstream revisions where available, and label all legacy companion metrics clearly in JSON consumers.
11. Reassess old verification scripts that remain referenced by docs; some expect the old / UI. The CI comparison script was redirected to /index.html. Do not delete referenced tools without updating their users.

## Commands

From D:\AI-Agent-Testing-Studio:

Windows startup: powershell -ExecutionPolicy Bypass -File .\run.ps1
macOS/Linux startup: ./start.sh (chmod +x once if needed)
Ollama: ollama serve; select an installed TEXT model. Do not download large models without considering hardware/disk.

Tests: .\.venv\Scripts\python.exe -m pytest -q
Focused: .\.venv\Scripts\python.exe -m pytest tests/test_simple_studio.py tests/test_studio_api.py tests/test_gemma.py tests/test_curated_and_evidence.py -q
Lint: .\.venv\Scripts\ruff.exe check app tests scripts sample_project
Format check: .\.venv\Scripts\ruff.exe format --check app tests scripts sample_project
JS: node scripts/check-js-syntax.cjs
Formatting: npm run format:check

All scripts/tests that use relative paths must run from the PRODUCT folder, not the C: artifact workspace.

Before restarting, query /api/blackbox/runs and check for queued/running evaluations. Do not kill an active job. Verify the port-owning process is the Studio before stopping it. Source changes require a reload; frontend static files reload with the page.

Do not rerun C: workspace install_simple_studio.py, finish_simple_integration.py or other one-off patch installers: they are non-idempotent and may overwrite later changes. Edit the actual D: files directly, run relevant tests, update PROGRESS.md and DECISIONS.md, and preserve this handoff when continuing.

## Latest run checkpoint — 2026-10-14

User authorized the safest restart/resume so all cases continue. Run `1dbd9014-5ecb-49c0-888d-4fd300c6973b` has 800 planned cases (16 categories, 10 cases x 5 repeats), preserving the separately started expanded suite. Stopped cleanly at 83 scored cases, restarted only Studio, and resumed the same run through `/api/studio/runs/{id}/resume`: 717 pending cases. Verified status running, 84 scored, stage Warranty help after resume. Original cloud Gemma primary and local llama3.2:3b fallback retained. Credentials loaded from existing local environment files into process memory, never printed or added to Git. Do not claim this 800-case benchmark is complete; check live status before any restart. Completed ten-case report remains run `3ed8185c-669e-43cc-b77d-fc62942584bf`, score 90, bot API cost estimate $0.0118387, local judge API cost $0.
