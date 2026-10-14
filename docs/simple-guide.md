# AI Agent Studio — simple guide

Judge one bot, or compare up to four bots using the same ten conversations. Set repeats (default three), choose judge models, and read scores, transcripts, tokens and costs on one screen.

## Start

Windows: open PowerShell in this folder and run `powershell -ExecutionPolicy Bypass -File .\run.ps1`.

macOS/Linux: install Python 3.12+, then run `./start.sh`. If the downloaded file has no executable permission, run `chmod +x start.sh` once. It creates a virtual environment, installs dependencies and Chromium, checks for Ollama and opens the Studio. Internet is needed during installation. Native macOS/Linux startup has not been verified on this Windows host.

Open **http://127.0.0.1:2708/**. Your chatbot must already be running. Paste its chat page or complete API URL. If automatic detection fails, open Connection help and specify message/response fields or browser selectors. The Studio cannot connect to every proprietary interface automatically.

Choose one or more judges. Enter a model your account supports and its key in the password box. Keys are never saved in browser storage or reports. A saved backend judge can reuse local environment configuration. Claude uses LiteLLM's Anthropic transport; the API connection must be checked with your account before a benchmark.

For local judging: install Ollama, run `ollama serve`, and install a suitable model yourself (`ollama pull <model>`). Reload Studio; installed model names are listed. Tick a local model and **Use as automatic local fallback only**. Studio never downloads models automatically. Local compute time is not free electricity or hardware; its API token charge can be zero.

Allow test messages and judge access, then click **Start evaluation**. During testing use **Change judges for active run** if your provider fails. Existing calls keep the previous judge; subsequent cases use your selection. After a stop or crash, **Resume missing cases** keeps prior scores, transcripts and cost events. Target API keys may need re-entry after restart; credentials are not stored in the database.

## Understanding results

Ten base scenarios cover accuracy, injection, jailbreak, guardrails, bias, memory, language, personal data, unnecessary refusal and uncertainty. Repeated answers measure consistency, not broad independent coverage. Upload verified reference facts for factual accuracy; without them the accuracy scenario only checks an unsupported premise.

The configured overall index is a weighted mean of scenario scores across planned repeats. **Not tested contributes zero**, with its reason and tested quality/coverage separately disclosed. Zero for missing evidence does not prove the bot answered unsafely. A comparison winner is withheld when evidence is incomplete or the scenario-cluster confidence interval includes a tie. Ten scenarios provide limited confidence and do not certify production safety.

Expand any check to read the prompts, actual answers, judge explanation and exact evidence. Evidence quotes still undergo the existing validation. Human reviews require an explanation, preserve the previous verdict and appear in the audit log. Audit records judge models, prompt, configuration, price snapshot, provider errors, fallback and manual changes. Temperature is zero, but providers may still be nondeterministic; a model alias does not prove a fixed provider revision.

Tokens and dollar costs are shown separately for bots and judges, as bars and a table. Missing telemetry/prices are **Unknown**, not $0. Internal bot tools, embeddings and hidden retries need that bot's own instrumentation. Prices are snapshots in `app/pricing/seed.json` and may need refresh.

## Configuration and development

- `app/studio/settings.json`: ten scenarios, repeats, weights, tie margin and judge options.
- `app/blackbox/studio_engine.py`: repeat building, multi-judge fallback, summary and governance.
- `app/blackbox/studio_routes.py`: simple workflow, live judge changes and human review.
- `app/blackbox_static/simple.*`: accessible offline UI and charts.
- Existing backend connectors, metering, retries, storage and reports remain in `app/blackbox/`.
- Legacy interface and datasets remain at `/index.html` for old runs.
- Run `python -m pytest tests/test_simple_studio.py tests/test_recovery_controls.py tests/test_costs.py` and `ruff check app tests` / `ruff format --check app tests`.

The evaluator attempts every scheduled case with timeouts and bounded retries. It can finish processing with Not tested entries when a bot/judge is unavailable. It cannot guarantee 100% valid judgments during provider outages. User stops and run deadlines intentionally remain effective.

ZIPs are validated and stored, never executed on the host. This release has no isolated ZIP application runner. Optional Docker hosts the Studio only and does not provide a ZIP sandbox. Run trusted projects separately; an untrusted-code sandbox is a separate implementation task.

Optional Docker: copy `.env.example` to `.env`, configure your own keys, then `docker compose up --build`. Results persist in a named volume. Bot links must be accessible inside the container; use `host.docker.internal` for host services. Change local judge URL in settings for Docker. This is a local single-user tool; do not expose it publicly.

Promptfoo was not added: existing LiteLLM adapters and black-box connector/runner reuse already cover this protocol, so a second runner would duplicate metering and governance.
