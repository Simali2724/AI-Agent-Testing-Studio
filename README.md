# AI Agent Studio

Test one chatbot or compare up to four using the same **10 checks**. Each check runs **3 times** by default; change the repeat number on screen.

## Start

**Windows:** open PowerShell in this folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

**macOS / Linux:** install Python 3.12+, then:

```sh
chmod +x start.sh
./start.sh
```

Open **http://127.0.0.1:2708/**.

1. Start your chatbot, then paste its chat page or complete API link.
2. Choose one or more judges. Use **Show available models**, select a model and enter its API key. Saved backend settings can be reused.
3. Set repeats, allow test messages/judge access, then click **Start evaluation**.
4. Read scores, comparison, transcripts, token/cost charts and tables. Download PDF or JSON.

For automatic local fallback, install a model in Ollama, run `ollama serve`, and select that model as a fallback on screen. Judge fallback cannot repair an unavailable chatbot API.

**Not tested contributes 0 to the configured evaluation index.** Its reason and measured coverage are shown separately. An incomplete comparison has no winner. Repeats measure consistency and do not prove broad safety or fairness.

Unknown usage/prices show **Unknown**, not $0. Hidden bot calls require that bot's own telemetry. Keys entered in password fields stay out of Git and reports. Never put credentials in reference facts or extra request JSON.

ZIP uploads are stored safely. **An isolated ZIP execution runner is still a separate task**; start trusted bots yourself and paste their running link. Never run untrusted uploads on the host.

Read [the detailed simple guide](docs/simple-guide.md) for configuration, recovery and optional Docker. [Previous documentation](docs/legacy-guide.md) and the older interface at `/index.html` remain available for historical runs.

[PROGRESS.md](PROGRESS.md) records changes and verification. [HANDOFF.md](HANDOFF.md) describes remaining work.
