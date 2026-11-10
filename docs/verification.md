# Ticket 89 verification record

Date: 2026-10-13. Scope: maintained source, development checks and documentation.
All evaluation tests use local/synthetic fixtures; no chatbot quality benchmark
or paid provider request is claimed.

## Checks

| Check                      | Result                                                                                                                                                    |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dependency consistency     | `pip check`: no broken requirements                                                                                                                       |
| Python format and lint     | Ruff format/check passed for maintained Python files                                                                                                      |
| Frontend/docs formatting   | Prettier check passed                                                                                                                                     |
| JavaScript syntax          | 21 files parsed successfully without executing helper scripts                                                                                             |
| Startup script             | PowerShell parser accepted `run.ps1`                                                                                                                      |
| Case-builder compatibility | Generated case payloads identical to the pre-refactor app in eight configurations spanning judge on/off, references and legacy-variation settings         |
| Literal wrapping           | Python AST compared before/after wrapping to preserve literal values                                                                                      |
| Isolated browser           | Four-target setup, exact preview, matrix, evidence details, baseline saving, concurrency controls and starting another run passed; zero JavaScript errors |

Final regression suite: **123 passed, 1 skipped, 1 dependency deprecation warning**
in 101.66 seconds. Python format/lint checks cover 41 maintained files. The
initial 121-test pass preceded the additional packaging and entry-point checks.

## Corrections found during verification

- Ruff's unused-import cleanup removed the public `app.main` export. Browser
  startup caught this before deployment. The export is now explicit (`app as app`),
  with a production-entry-point regression test.
- The browser check now fails explicitly if its isolated server exits or never
  becomes healthy, rather than continuing with an unavailable URL. Its working
  directory is explicit.
- A session/pacing fixture hit its unrelated two-second timeout under simultaneous
  browser/test load. Its timeout allowance is now 30 seconds; the actual pacing
  and latency assertions remain, with additional assertions requiring all four
  turns to complete without errors. Production timeouts were not changed.
- Release packaging now includes reviewed CI/dev/doc files while rejecting other
  GitHub metadata. A regression test covers both inclusion and exclusion.

## Dependency audit

The installed core environment reported FastAPI 0.142.2, Uvicorn 0.54.0, HTTPX
0.28.1, pytest 9.1.1, Playwright 1.63.0, ReportLab 5.0.1, LiteLLM 1.105.0 and Ruff
0.14.1. These are observed local versions, not a new runtime lockfile.

DeepEval, DeepTeam, Garak and Transformers were absent. Torch 2.14.1 was present;
this alone establishes neither HHEM nor QwenGuard availability. Their real engine
integration is tracked in MAINT-02. No historical install log is used as current
proof of successful installation.

## Limits of this verification

- Local fixtures verify interface behavior, not universal connector compatibility.
- One Windows symlink test needs permission to create symlinks and is skipped
  when that permission is unavailable.
- The installed FastAPI/Starlette test client emits an HTTPX deprecation warning;
  it is not a failed application check.
- The GitHub Actions workflow is configured, but its hosted run requires publishing
  the change. No commit, push or remote CI success is claimed by this record.
- Historical source, reports and old notes are preserved; optional capabilities
  remain explicitly tracked in `BACKLOG.md` rather than advertised as complete.

## Deployment

Applied reviewed files to the live Studio and existing `hussain-code` checkout.
The idle server on port 2708 restarted successfully. Health returned OK; the live
setup page returned HTTP 200 with zero JavaScript errors. Source backups were
kept outside the project; local credentials and existing runtime data were not
copied or replaced. Git whitespace checks passed. Git attributes now retain LF
for formatter-managed files on Windows and in CI; editor defaults document the
same indentation rules.

## Recovery and visible controls — 14 October 2026

- Before quota-pause additions: 131 platform tests passed, 1 skipped. Ruff
  check and formatting passed; 22 JavaScript files passed syntax checks.
- Browser checks: all 509 imported cases retained, all 16 categories selected,
  Kimi endpoint selection correct, key input remains a password field, slow
  mode sets 30-second gaps and a 720-minute ceiling. No console errors observed.
- Live provider diagnostics are blockers, not quality failures: both Gemini
  keys hit the same daily limit; Kimi returned insufficient balance. Full
  chatbot coverage is not claimed. Known recorded subtotal is $0.018593, but
  final cost is unknown because failed attempts have incomplete billing data.

## 2026-10-24 — Verification categories recorded separately (T-032)

These five categories are deliberately kept apart. Passing one is not evidence for another: a Linux container or a WSL shell does not qualify native macOS, and a committed CI configuration file is not evidence that a remote job ran.

| Category                             | What it covers                                                                                                | Exercised on                                                   | Result                                                                            | Not exercised                                                                     |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **Unit and integration tests**       | `python -m pytest` with synthetic fixtures and mocked providers                                               | Windows 11, Python 3.12.3, project `.venv`                     | See the dated run in PROGRESS.md                                                  | Native Linux and macOS runs                                                       |
| **Dependency locks**                 | Clean hash-verified install from `requirements-dev.lock`, then `pip check` and the full suite                 | Windows 11, a fresh virtual environment outside the repository | 78 packages, no broken requirements, suite passed                                 | Native Linux and macOS installs; the optional evaluation lock was never installed |
| **Browser tests**                    | `scripts/check-studio-ui.py` (current shell) and `scripts/check-exact-compare.py` (retained legacy interface) | Headless Chromium on Windows 11                                | Both passed locally                                                               | Firefox and WebKit; any browser on Linux or macOS                                 |
| **Launcher verification**            | `start.sh`, `run.ps1`, `Dockerfile`, `compose.yaml` creating an environment and serving Studio                | `run.ps1` on Windows 11 only                                   | Windows launcher used throughout this work                                        | `start.sh` on native Linux or macOS; a container build and run                    |
| **Native scanner qualification**     | Docker or WSL scanner images, offline databases, read-only mounts, no-network sandbox                         | Not exercised in this task                                     | No scan was run                                                                   | Every target OS; image and database provisioning                                  |
| **Local and cloud model validation** | A real local Judge (Ollama) or an authorised cloud provider answering real requests                           | Not exercised in this task                                     | No provider call was made; every test used mocked providers or synthetic fixtures | All providers; no paid call was authorised or made                                |

Two further boundaries, so a reader does not over-read the table:

- **Human-label calibration** is implemented and tested with synthetic fixtures, but no representative human labels exist, so every Judge reports **uncalibrated**. See [judge-validation.md](judge-validation.md).
- **CI** is configured for Windows, Ubuntu and macOS, installs Linux browser system dependencies and keeps failure traces. That configuration has not been executed on a remote runner as part of this work, so CI behaviour on Linux and macOS is configured but not observed.

## 2026-11-09 — Open-source release candidate 0.1.0-rc.1 (T-046 to T-052)

Environment: Windows 11 Home Single Language 10.0.26300, Python 3.12.3, Node 24.18.0,
pip 24.0. Repository `AI-Agent-Testing-Studio`, branch `codex/open-source-release`,
based on commit `cfbe8de`. Every check below used synthetic fixtures and mocked
providers. **No provider credential was used and no paid or cloud call was made.**

A note on provenance: the project lives on `D:`, and that volume **disconnected
mid-session**. Windows logged NTFS `Delayed Write Failed` errors against `D:\$Mft` and
`D:\AI-Agent-Testing-Studio\.venv\...` at 22:08:40, after which the volume was absent and
`Get-Disk` showed only the internal NVMe. Every command issued against it had been read-only.

Work continued on a clone of the published `master` on `C:`, whose source inventory matched
the absent tree at **184 of 184** files. The volume later came back **intact**, and the
release work was transferred onto it as a 34-file patch that applied cleanly. The surviving
`D:` tree kept its working `.venv`, `node_modules`, `.env` and `runtime/studio.db`, so **no
saved evaluation was lost**. The modules Windows had failed to write
(`litellm/integrations`, `litellm/harness`) import correctly and `pip check` is clean, so the
environment was not damaged. The results below were produced on `D:`.

### Regression suite

Run on `D:\AI-Agent-Testing-Studio`, serially, with the machine otherwise idle.

| Check                    | Command                                                          | Result                                |
| ------------------------ | ---------------------------------------------------------------- | ------------------------------------- |
| Dependency consistency   | `python -m pip check`                                            | No broken requirements                |
| Full suite               | `python -m pytest -q`                                            | **817 passed, 1 skipped** in 222.83 s |
| Python format            | `python -m ruff format --check app tests scripts sample_project` | 135 files already formatted           |
| Python lint              | `python -m ruff check app tests scripts sample_project`          | All checks passed                     |
| Frontend and docs format | `npm run format:check`                                           | All matched files use Prettier style  |
| JavaScript syntax        | `npm run check:js`                                               | 16 files checked                      |
| Interface unit tests     | `npm run test:ui`                                                | 23 passed, 0 failed                   |
| Documents                | `python scripts/check_docs.py`                                   | Passed across 32 Markdown documents   |
| Whitespace               | `git diff --check`                                               | Clean                                 |

The 1 skip is `test_symlink_escape_is_skipped`, which skips on a Windows account that cannot
create symlinks. It is not a disabled failure.

#### The real-time benchmark, and a failure I caused

`test_standard_suite_runtime_regression_budget` measures wall-clock time and is only valid
**serially on an otherwise idle machine**. An earlier full-suite run, during which this session
was also running `npm`, Prettier and document writes, **failed** it:

```text
benchmark median 1.297s, budget 1.200s, runs [0.968, 1.703, 1.297, 1.063, 1.375]
```

The 0.968 s to 1.703 s spread is contention, not a code regression. Re-run alone on an idle
machine, three consecutive times:

```text
run 1: median 0.984s, budget 1.200s, runs [0.828, 0.922, 1.687, 1.235, 0.984]  passed
run 2: median 0.859s, budget 1.200s, runs [0.859, 0.875, 0.969, 0.828, 0.844]  passed
run 3: median 0.813s, budget 1.200s, runs [0.859, 0.859, 0.813, 0.797, 0.813]  passed
```

It then also passed inside the full serial suite above. **The 1.200 s threshold was not changed
and no workload was reduced.** The recorded failure is kept here deliberately: the lesson is
that this benchmark must not share a machine, not that the budget is too tight.

### Browser and interface checks

| Check                            | Result                                                                                                                                                                                                                                     |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `scripts/check-studio-ui.py`     | navigation, saved report, escaped model output, calibration panel (17 eligible conversations), governance alignment, provenance, full analysis sections, custom and unscored history, mobile layout — all **passed**, `browser_errors: []` |
| `scripts/check-exact-compare.py` | four-target setup, exact-only preview, matrix and case details, baseline save, concurrency controls, start another run — all **passed**; **0 provider calls**, 0 judge requests                                                            |
| `scripts/check_contrast.py`      | WCAG 2.2 AA: **44 measured, 0 failing, 0 skipped**                                                                                                                                                                                         |

Artifacts were written to `runtime/ui-artifacts` from synthetic fixtures only.

### Release candidate packaging

Measured on the final artifact, built after every document change in this candidate. Its
SHA-256 and content digest are recorded in the manifest written beside it by
`scripts/release_manifest.py`; the hash is deliberately **not** copied into this document,
because a document inside the archive cannot state its own archive's hash.

| Step                               | Result                                                                                                                                                                           |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Archive build                      | `scripts/package_release.py` produced a verified ZIP of **232 files**; its exact size and hash are in the manifest beside it                                                     |
| Required setup files present       | All three lockfiles, `run.ps1`, `start.sh`, `Dockerfile`, `Dockerfile.scanners`, `compose.yaml`, `.dockerignore`, `LICENSE`, `CHANGELOG.md` and the reviewed `.github` templates |
| Archive boundary                   | No `runtime/` entry, no `.env`, and `PROGRESS.md` and `HANDOFF.md` are excluded by design                                                                                        |
| Fresh extraction                   | Extracted to a directory **whose path contains spaces**, outside the repository                                                                                                  |
| Locked install from the archive    | `pip install --require-hashes -r requirements.lock` exit 0 in **260 s**; **77 packages**; `pip check` reported no broken requirements                                            |
| Resolved versions                  | fastapi 0.142.2, uvicorn 0.54.0, httpx 0.28.1, litellm 1.105.0, reportlab 5.0.1, playwright 1.63.0, PyYAML 6.0.3                                                                 |
| Start with the documented launcher | `powershell -ExecutionPolicy Bypass -File .\run.ps1 -Port 2813` served **HTTP 200**, 20941 bytes, in **4.1 s to 9.7 s** across runs                                              |
| Demo reachable from the archive    | `GET /api/blackbox/case-set/demo` returned HTTP 200 with **8 Cases**                                                                                                             |
| `.env` bootstrap                   | The launcher copied `.env.example` to `.env` in the fresh directory                                                                                                              |
| `LICENSE` in the extract           | Present                                                                                                                                                                          |
| Occupied port                      | Refused with `[Errno 10048] error while attempting to bind`, then shut down cleanly. It did not hang                                                                             |

The environment was created from this artifact's own `requirements.lock`. An earlier
intermediate build was install-tested the same way and gave the same result; the counts above
are from the final artifact.

**Not exercised in the fresh install:** the first-run `playwright install chromium` download
was skipped, because the environment already existed when the launcher ran. The web-chat
browser connector is therefore **unverified** in the extracted archive, and a genuine first
run additionally downloads Chromium, which makes a true first install slower than the 260 s
above. The `start.sh` path was not executed at all; see the platform limits below.

### Synthetic no-key demo

Two real processes, driven over HTTP, with no provider credential:

| Step                        | Result                                                                                   |
| --------------------------- | ---------------------------------------------------------------------------------------- |
| Demo bot startup            | Ready in **1.1 s** on `127.0.0.1:2809`                                                   |
| Studio startup              | Ready in **0.5 s**                                                                       |
| Demo bot answered over HTTP | `POST /chat` returned the catalogue warranty answer                                      |
| Demo Cases fetched          | **8 Cases**, published with `judge_enabled=false`                                        |
| Run                         | Completed through the ordinary API connector and runner                                  |
| Scoring without any Judge   | **8 of 8 results scored — 7 passed, 1 failed**                                           |
| JSON export                 | HTTP 200, and its `id` matched the selected Run                                          |
| PDF export                  | Rendered, **59760 bytes**, valid `%PDF` header                                           |
| Restart durability          | After restarting Studio only, the Run was still listed and reopened with the same status |

The single failing Case is deliberate: the demo bot answers a refund question with an
invented unconditional guarantee and the Case forbids that phrase. A demo in which
everything passed would misrepresent the tool.

**What this does not establish:** the demo measures hand-written strings in
`app/blackbox/demo_bot.py`. It is not a measurement of any real chatbot, and it says
nothing about Judge accuracy because no Judge ran.

### Prerequisite and failure behaviour

On this machine **Docker is not installed** and **Ollama is installed**, which made the
missing-prerequisite path testable rather than assumed.

- White-box readiness with no source supplied reported **`ready: 0`** across all 14
  checks, each with the reason "No source ZIP or repository was supplied", under the
  notice "Ready means the check can be attempted. It is not a pass."
- **Not verified:** the Docker-absent path with a source ZIP actually supplied, any
  scanner execution, the scanner image and database provisioning, and the optional
  HHEM/Qwen classifiers, which remain disabled and unverified.

### Private material review

- No `.env`, key, certificate or credential file was added in **any reachable commit**.
- No provider-key-shaped string appears in any reachable commit. Patterns covered
  Google, Anthropic, OpenAI-style, GitHub, Slack and AWS keys, and PEM private-key headers.
- Credential-shaped literals in `tests/test_export_redaction.py` and
  `tests/test_judge_calibration.py` are synthetic fixtures whose purpose is to be
  redacted; they sit beside a fictional phone number, `example.com` and documentation UUIDs.
- The 509-Case and 20-per-Category packs contain **authored synthetic prompts** using
  synthetic identifiers, not customer transcripts or personal data.
- **Disclosure limit:** this is pattern scanning over reachable commits. It is evidence
  that nothing was found, not proof that nothing exists. Unreachable objects and any
  other remote are out of scope.
- **Owner decision outstanding:** a named third-party company still appears in shipped UI
  labels, auto-detection logic, API route names and case-pack filenames. Recorded in
  [open-source-readiness.md](open-source-readiness.md).

### Platform limits as of rc.1 — partly superseded

This table records what was true on **2026-11-09**, for rc.1. Two rows changed on 2026-11-10
when the branch was pushed and remote CI ran green on all three platforms. Read the current
table in [the 2026-11-10 section](#the-branch-was-pushed-and-remote-ci-ran-green--2026-11-10)
instead; this one is kept as the historical record, not corrected in place.

| Platform                | Status on 2026-11-09                                                                                        |
| ----------------------- | ----------------------------------------------------------------------------------------------------------- |
| Windows 11, Python 3.12 | Qualified: locked install, launcher start, demo, suite, packaging                                           |
| Linux (native)          | **Not qualified.** `start.sh` was not executed — _suite and browser checks since green in CI_               |
| macOS (native)          | **Not qualified.** `start.sh` was not executed — _suite and browser checks since green in CI_               |
| Docker container        | **Not qualified.** No image was built; Docker is absent on this machine                                     |
| Remote CI               | **Not observed** at that date. No remote run was triggered — _since observed, success on all three runners_ |

Python support is claimed for **3.12 only**, which is the one version tested. Node 24.18.0
was used for contributor checks; Studio does not require Node at runtime.

### Pacing and the real-time benchmark

The bounded parallel pacing harness, the clock seam and the fake-clock pacing tests exist
only in a **separate local working tree** and are **not present in this repository**, so
this candidate reports pacing stress as **Not tested** rather than citing the other tree's
recorded 50 of 50 result. `tests/test_concurrency.py` and the real-time benchmark in
`tests/test_speed_cache.py` do pass here, which is a narrower claim. The benchmark
threshold was not changed and no workload was reduced.

## 2026-11-10 — Release-candidate defect repair (T-054)

Environment: Windows 11 Home Single Language 10.0.26300, Python 3.12.3, Node 24.18.0,
project `.venv`. Repository checkout on the `D:` volume, branch `codex/open-source-release`,
based on commit `4db73b8`. Every check below used synthetic fixtures, temporary runtimes and
loopback servers. **No provider credential was used and no paid or cloud call was made.**

A note on which checkout this record qualifies: the 2026-11-10 offline audit ran against a
second checkout on the `C:` volume, HEAD `cfbe8de` plus 34 staged changes, because its `D:`
Git access was denied. Those 34 changes are committed here
as `178b8c7`, with three later commits on top. The repair was applied **here**, to the newer
tree, and the numbers below are from this tree. The audit's own numbers remain historical and
describe the older checkout.

### Defects reproduced before the repair

Confirmed present in this checkout, not taken on the audit's word:

| Audit ticket     | Reproduced here                                                                                                                            |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 1 — demo UI      | Yes. `configuration()` carries no `custom_cases` field and the shell has no Judge-off or import control                                    |
| 2 — overwrite    | Yes. `--artifact` and `--output` on one path exited 0 and left the ZIP as Markdown                                                         |
| 3 — provenance   | Yes. Unavailable Git produced `Working tree \| clean` and `commit unavailable (clean working tree)`                                        |
| 4 — digest       | Yes. `{"a": b"bc"}` and `{"ab": b"c"}` returned one content digest; artifact SHA-256 values differed, as the audit stated                  |
| 5 — archive docs | Yes. The extracted archive reported four broken links in `docs/Rules.md`; the checkout checker passed                                      |
| 6 — formatting   | **No.** `npm run format:check` already exited 0 here. The four files were formatted by `178b8c7`–`4db73b8`, which the audit could not read |

### Verification gate after the repair

Run serially on an otherwise idle machine. The real-time benchmark ran inside the full suite
with no browser or stress work alongside it.

| Check                      | Command                                                                 | Result                                                                                                   |
| -------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Dependency consistency     | `python -m pip check`                                                   | No broken requirements                                                                                   |
| Python lint                | `python -m ruff check app tests scripts sample_project`                 | Passed                                                                                                   |
| Python format              | `python -m ruff format --check app tests scripts sample_project`        | **139 files** already formatted                                                                          |
| Frontend/docs formatting   | `npm run format:check`                                                  | **Exit 0.** All matched files use Prettier style                                                         |
| JavaScript syntax          | `npm run check:js`                                                      | 16 files parsed                                                                                          |
| Shell navigation/state     | `npm run test:ui`                                                       | **23 passed, 0 failed**                                                                                  |
| Documentation checker      | `python scripts/check_docs.py`                                          | Passed across **34** maintained documents                                                                |
| Full regression suite      | `python -m pytest -q`                                                   | **897 passed, 1 skipped**, 1 warning. Twice: **157.45 s**, then **217.08 s** on the final committed tree |
| Current shell in a browser | `python scripts/check-studio-ui.py --artifacts runtime/ui-artifacts`    | All sections passed, 17 eligible conversations, `browser_errors: []`                                     |
| Demo journey in a browser  | `python scripts/check-demo-journey.py --artifacts runtime/ui-artifacts` | Passed, **0 judge calls**, 9 loopback bot calls, `offsite_requests: []`                                  |
| Legacy comparison UI       | `python scripts/check-exact-compare.py`                                 | All sections passed, **0 provider calls**                                                                |
| Colour contrast            | `python scripts/check_contrast.py`                                      | WCAG 2.2 AA: **45 measured, 0 failing, 0 skipped**                                                       |
| Whitespace                 | `git diff --check`                                                      | Clean                                                                                                    |

The suite grew from **817 passed, 1 skipped** to **897 passed, 1 skipped**: 80 new tests. The
Windows symlink-capability skip and the single Starlette `TestClient` deprecation warning are
unchanged and are disclosed rather than counted as passes. The audit's earlier
`socket.socketpair` stall did not recur here; no production event-loop behaviour was changed
and no test was skipped to avoid it.

The suite was run twice: once when the source fixes were complete, at **157.45 s**, and once
again on the **final committed tree**, at **217.08 s**. Same 897 passed and 1 skipped both
times. Only Markdown changed between them, so the difference is wall-clock variance on this
machine rather than a code change, and it is recorded rather than averaged away. The real-time
benchmark passed inside both runs against its **unchanged** 1.200 s budget. The second run is
the one that qualifies the committed tree; the first is not claimed to.

Contrast went from 44 to 45 measured because this task added one colour: the synthetic-demo
badge, measured at **7.17:1** on its own background against the 4.5:1 requirement for normal
text. It is amber rather than the interface's purple, so a demonstration Run is not mistaken at
a glance for a measurement of a real chatbot.

### The advertised demo journey, in a real browser

`scripts/check-demo-journey.py` drives two real loopback processes — Studio and the bundled
demo bot — through the journey the README documents, in Chromium, in a temporary runtime.

| Step                              | Result                                                                                |
| --------------------------------- | ------------------------------------------------------------------------------------- |
| Per-platform start commands shown | `.venv\Scripts\python.exe` and `.venv/bin/python`, both asserted in the page          |
| Consent enforced                  | Clicking **Run the demo** unticked refuses and starts nothing                         |
| Demo started from the shell       | `POST /api/blackbox/demo/runs` with a consent boolean and no evaluation configuration |
| Cases planned                     | **8**, one repeat each, across six Categories; the ten-Category suite was not planned |
| Scored with no Judge              | **8 of 8 scored — 7 passed, 1 failed**; `0 Not tested` in every Category              |
| Bot calls                         | **9** — the exact turn count — all to `127.0.0.1:2709`                                |
| Judge calls                       | **0.** `judge_enabled=false`, `judges=[]`, `auto_local_fallback=false`                |
| Requests outside the two ports    | **None.** `offsite_requests: []`                                                      |
| Synthetic disclosure              | Badge visible on Evaluate, Results **and** Governance, from the saved Run             |
| JSON export                       | Carries `synthetic_demo` and the label in `limitations`                               |
| PDF export                        | Rendered, **59793 bytes**, valid `%PDF` header                                        |
| Reopened after a Studio restart   | Same Run, same eight results, badge still present                                     |
| Browser errors                    | **None**                                                                              |

Provider absence is enforced twice: this check fails on any request leaving the two loopback
ports, and `tests/test_demo.py` runs the whole demo through the shipped REST connector against
the demo bot's own ASGI app with `metering.completion` replaced by a stub that raises.

Fixed while building this check: a Black-box-only Run's results were invisible in the current
shell, because `assurance.js` hides them unless its own tab is active and the non-notifying
`selectRun` never re-ran that logic. The demo now selects its Run the notifying way.

### Manifest, provenance and digest

`tests/test_release_manifest.py`: **33 passed**. Each case below is asserted there, and the
audit's probes were rewritten as assertions of corrected behaviour.

| Case                                                             | Result                                                             |
| ---------------------------------------------------------------- | ------------------------------------------------------------------ |
| `--output` equal to `--artifact`                                 | Exit 1; input bytes unchanged; still a valid ZIP                   |
| Hard-link alias of the artifact with a `.md` name                | Exit 1; input bytes unchanged                                      |
| Relative and absolute spellings of one path                      | Refused                                                            |
| Existing unrelated destination                                   | Preserved; exit 1                                                  |
| Destination created mid-generation (race)                        | Preserved; no manifest written                                     |
| `--replace`                                                      | Replaces deliberately, and only then                               |
| Fresh manifest                                                   | Exit 0; records the artifact's actual unchanged SHA-256            |
| Missing artifact, non-ZIP file                                   | Exit 1, no traceback, no output file                               |
| Missing Git, failed `git status`, no commit, non-repository      | **Unknown** provenance with a stated reason; never clean           |
| Known clean vs dirty                                             | Distinguishable, with commit and tree recorded                     |
| Older ZIP against another build's record                         | Exit 1, "different artifact"; no attribution                       |
| Verified clean build record                                      | Attributes the commit, labelled "clean working tree at build time" |
| `{"a": b"bc"}` vs `{"ab": b"c"}`                                 | **Different** content digests; artifact hashes differ as before    |
| Renames, changed bytes, empty files, Unicode names, path vs name | All distinguished                                                  |
| Differing ZIP timestamps, member order and compression           | **Equal** content digests, per the documented policy               |
| Duplicate member names                                           | Refused explicitly; exit 1                                         |

The content-digest algorithm is now versioned as `studio-release-content-v2` and printed in the
manifest. It length-frames every member name and content and uses a per-member SHA-256. Values
from the earlier unframed algorithm are **not comparable** with it; the manifest says so. No
previously published content digest exists to invalidate. Full artifact SHA-256 behaviour is
unchanged.

### Documentation inside the shipped artifact

| Step                                                           | Result                                                                             |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Build the real archive, extract to a fresh temporary directory | Done from the tracked tree via `git ls-files`                                      |
| Run the **archive's own** `scripts/check_docs.py` on it        | **Exit 0**, in an isolated interpreter (`python -I`)                               |
| Coverage inside the archive                                    | Every shipped Markdown document, not only the README                               |
| Local history, secrets, runtime records                        | `PROGRESS.md`, `HANDOFF.md`, `NEXT_AI_PROMPT.md`, `.env` and `runtime/` all absent |
| Checkout checker catches the same class of defect              | Yes: a shipped document linking an excluded file now fails                         |

Verified by reintroducing the original `docs/Rules.md` link: the checkout checker exited 1 and
both archive tests failed. Restored, all three pass. `docs/Rules.md` now names the working
history without linking it and points a reader of a released copy at the tasks and the release
checklist. **The local `PROGRESS.md` and `HANDOFF.md` were not moved, trimmed or published.**

### What this repair still does not establish

Unchanged by this task, and not closed by it:

- Native Linux, macOS and Docker qualification (**T-032**, **T-052**). Only Windows was
  exercised. A committed workflow file is not evidence that a remote job ran.
- Bounded parallel pacing stress (**T-052**). Still **Not tested** here; the harness lives in a
  separate working tree and its results are not this candidate's.
- Human Judge calibration (**T-053**'s outstanding half). No real human labels exist, so no
  Judge in this release is calibrated. The demo says nothing about Judge accuracy: no Judge ran.
- Owner approvals gating publication (**T-051**): written distribution rights, the third-party
  company reference decision, and a monitored security reporting route.

None of these four is a defect the 2026-11-10 audit demonstrated, and none may be marked Done
from an offline repair.

### The branch was pushed, and remote CI ran green — 2026-11-10

Originally this task pushed nothing. The owner then **explicitly instructed a push**, so the
`codex/open-source-release` branch was pushed to the already-public `origin`
(`Simali2724/AI-Agent-Testing-Studio`) as a new branch at commit `9893785`. Eight commits went
up, four from this task and four from the 2026-11-09 candidate that had never been pushed.

Before pushing: the whole range was scanned for credential-shaped strings (Google, OpenAI-style,
GitHub, Slack, AWS and PEM headers) with **no hits**; no `.env`, archive, database or `runtime/`
path was in the range; and the third-party company name that T-051 still gates was confirmed
**already public on `origin/master`** in three files, so the push did not newly expose it.

| Field          | Value                                                     |
| -------------- | --------------------------------------------------------- |
| Remote ref     | `refs/heads/codex/open-source-release` at `9893785`       |
| Verified       | Remote ref equals local HEAD                              |
| Commits pushed | 8 (54 files)                                              |
| Tag or Release | **None.** No tag, GitHub Release or package was published |

**This is the first remote CI run ever observed for this project.** Every earlier record
correctly said a committed workflow file was not evidence that a job had run. One has now run:
run [42759604031](https://github.com/Simali2724/AI-Agent-Testing-Studio/actions/runs/42759604031), attempt 1, on commit `9893785`, triggered by the push, **conclusion success on all three platforms**.

| Runner         | Result      | Duration |
| -------------- | ----------- | -------- |
| ubuntu-latest  | **success** | 3.3 min  |
| macos-latest   | **success** | 4.2 min  |
| windows-latest | **success** | 4.4 min  |

Every step succeeded on every platform: Ruff format and lint, Prettier, JavaScript syntax,
Studio navigation, the **full pytest suite**, the current-shell browser check, the **new demo
journey browser check** and the legacy comparison browser check. The only skipped step is
`Keep browser failure traces`, which is `if: failure()` and correctly did not run.

A second run, [42762344909](https://github.com/Simali2724/AI-Agent-Testing-Studio/actions/runs/42762344909),
was triggered by the follow-up commit `167edf3` and also reported **success on all three
runners**. It covers a documentation-only change, so it confirms the workflow is repeatable
rather than adding platform evidence.

**What this CI run qualifies:** the regression suite and all three browser checks now pass on
**native Linux and native macOS**, not only on this Windows workstation. The demo journey added
by T-054 passes on all three.

**What it does not qualify, so T-032 and T-052 stay Blocked:** CI builds its own environment
from the lockfiles and **never runs `start.sh`**. Fresh-machine startup from an extracted
archive, browser system-dependency provisioning on a clean machine, local Judge discovery, a
container build, the White scanners and any real provider call remain unexercised. Bounded
parallel pacing stress remains **Not tested**. No Judge is calibrated. These are narrower gaps
than before, not closed ones.

| Platform         | Status after this run                                                                                   |
| ---------------- | ------------------------------------------------------------------------------------------------------- |
| Windows 11       | Qualified locally: locked install, launcher start, demo, suite, packaging. Also green in CI             |
| Linux (native)   | **Suite and browser checks qualified in CI.** `start.sh`, scanners and container still **not executed** |
| macOS (native)   | **Suite and browser checks qualified in CI.** `start.sh` and scanners still **not executed**            |
| Docker container | **Not qualified.** No image was built                                                                   |
| Remote CI        | **Observed, green.** Success on all three runners, attempt 1                                            |
