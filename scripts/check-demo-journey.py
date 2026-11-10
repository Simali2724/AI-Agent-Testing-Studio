"""Browser check for the advertised no-key demo journey (T-054).

This drives the journey the README documents, in a real browser, through the
CURRENT shell (`simple.html`): open `/`, allow the demo messages, click
**Run the demo**, and watch eight synthetic Cases complete with seven passes and
one deliberate failure. It then exports the Run, restarts Studio and reopens it,
so the saved disclosure is checked after a restart rather than only in memory.

Why a browser check and not only API tests: the defect this guards was precisely
that the API demo worked while the UI had no way to reach it. `tests/test_demo.py`
covers the server side; only this check proves a person can complete the journey.

Everything is synthetic and local:

* Two real processes on loopback — Studio, and the bundled demo bot from
  `scripts/demo_bot.py`. Both in a temporary runtime directory.
* Zero provider calls. The demo configuration is built on the server with the
  AI Judge off, no Judge selected and local fallback discovery disabled; this
  check asserts the saved Run records no Judge verdict and no Judge cost, and
  fails if the browser requests any host other than the two loopback ports.
* No saved history outside the temporary runtime is read or written.

    python scripts/check-demo-journey.py
    python scripts/check-demo-journey.py --artifacts runtime/ui-artifacts --port 2713
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from contextlib import ExitStack
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def wait_for(url: str, process: subprocess.Popen, what: str, attempts: int = 150):
    """Poll one loopback health endpoint until the process answers it."""
    for _ in range(attempts):
        if process.poll() is not None:
            raise RuntimeError(f"{what} exited with code {process.returncode}.")
        try:
            with urllib.request.urlopen(url, timeout=1):
                return process
        except Exception:  # noqa: BLE001 - it is simply not listening yet
            time.sleep(0.2)
    process.kill()
    raise RuntimeError(f"{what} did not become healthy at {url}.")


def spawn(arguments: list[str]) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, *arguments],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        start_new_session=os.name != "nt",
        cwd=REPO,
    )


def serve_studio(port: int) -> subprocess.Popen:
    process = spawn(["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)])
    return wait_for(f"http://127.0.0.1:{port}/api/health", process, "Studio")


def serve_demo_bot(port: int) -> subprocess.Popen:
    process = spawn(["scripts/demo_bot.py", "--port", str(port)])
    return wait_for(f"http://127.0.0.1:{port}/health", process, "The demo bot")


def demo_case_names() -> list[str]:
    from app.blackbox import demo_bot

    return [case["name"] for case in demo_bot.case_set()]


def demo_categories() -> list[str]:
    from app.blackbox import demo_bot

    return list(dict.fromkeys(case["category"] for case in demo_bot.case_set()))


def fetch(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def run_the_demo(page, base: str, expected: dict) -> str:
    """Complete the documented journey and return the new Run's identifier."""
    page.goto(base + "/", wait_until="networkidle")
    page.wait_for_selector("#demo-section")

    # The setup instructions must name the project environment, not bare `python`.
    page.locator("#demo-setup > summary").click()
    windows = page.locator("#demo-command-windows").inner_text()
    posix = page.locator("#demo-command-posix").inner_text()
    assert ".venv\\Scripts\\python.exe" in windows, (
        f"Windows command is not venv-qualified: {windows!r}"
    )
    assert ".venv/bin/python" in posix, f"POSIX command is not venv-qualified: {posix!r}"

    page.wait_for_function(
        "() => document.querySelector('#demo-expected').textContent.includes('Cases')"
    )
    summary = page.locator("#demo-expected").inner_text()
    assert f"{expected['cases']} Cases" in summary, summary
    assert "Judge calls: 0" in summary, summary

    # Consent is required, and refusing it must not start anything.
    page.locator("#demo-start").click()
    page.wait_for_function(
        "() => document.querySelector('#demo-status').textContent.includes('Tick the box')"
    )

    page.locator("#demo-consent").check()
    page.locator("#demo-start").click()
    page.wait_for_function(
        "() => document.querySelector('#demo-status').textContent.includes('Demo started')",
        timeout=60000,
    )
    page.wait_for_function(
        "() => !document.querySelector('[data-panel=results]').hidden", timeout=60000
    )
    page.wait_for_function(
        "() => /completed/.test(document.querySelector('#run-label').textContent)",
        timeout=180000,
    )
    label = page.locator("#run-label").inner_text()
    assert f"{expected['results']}/{expected['results']} scored" in label, label
    identifier = page.evaluate("() => new URLSearchParams(location.search).get('run')")
    assert identifier, "the demo Run was not selected in the address bar"
    return identifier


def check_disclosure(page) -> None:
    """The synthetic badge must be visible on every view, not just Results."""
    badge = page.locator("#synthetic-badge")
    badge.wait_for(state="visible")
    text = badge.inner_text()
    assert "Synthetic demonstration data" in text, text
    for view in ("governance", "evaluate", "results"):
        page.locator(f"nav a[data-view={view}]").click()
        page.wait_for_function(
            "name => !document.querySelector(`[data-panel=${name}]`).hidden", arg=view
        )
        assert badge.is_visible(), f"the synthetic badge disappeared on {view}"


def check_results(page, expected: dict, categories: list[str]) -> None:
    """All eight Cases must be reachable, with the deliberate failure's evidence shown.

    `#case-results` groups by Category and loads each group's transcripts only when
    it is opened, so the check expands every group rather than assuming the Cases
    are already in the document.
    """
    page.wait_for_selector("#case-results details[data-case]", state="visible")
    groups = page.locator("#case-results details[data-case]")
    assert groups.count() == len(categories), (
        f"{groups.count()} Category groups rendered, expected {len(categories)}"
    )
    for index in range(groups.count()):
        group = groups.nth(index)
        group.locator(":scope > summary").click()
        group.locator("[data-case-body] article").first.wait_for(state="visible")

    body = page.locator("#case-results").inner_text()
    for case in demo_case_names():
        assert case in body, f"Case missing from Results: {case}"
    assert "fails on purpose" in body, "the deliberately failing Case is not listed"
    assert "guaranteed lifetime refund" in body, "the failing Case's evidence is not shown"

    # Counted inside the per-Case evidence only. Each group's summary line also
    # carries the words "Not tested", with a zero in front of them.
    verdicts = page.evaluate("""() => {
        const bodies = [...document.querySelectorAll('#case-results [data-case-body]')]
          .map(node => node.innerText).join('\\n');
        const summaries = [...document.querySelectorAll('#case-results details[data-case] > summary')]
          .map(node => node.innerText);
        return {
          passed: (bodies.match(/Passed/g) || []).length,
          attention: (bodies.match(/Needs attention/g) || []).length,
          untested: (bodies.match(/Not tested/g) || []).length,
          summaries,
        };
    }""")
    assert verdicts["untested"] == 0, verdicts
    assert verdicts["passed"] == expected["passed"], verdicts
    assert verdicts["attention"] == expected["failed"], verdicts
    processed = sum(
        int(found[1])
        for line in verdicts["summaries"]
        if (found := re.search(r"(\d+) processed", line))
    )
    assert processed == expected["results"], verdicts["summaries"]
    for line in verdicts["summaries"]:
        assert "0 Not tested" in line, f"a Category reports untested Cases: {line!r}"


def saved_run(base: str, identifier: str, expected: dict) -> dict:
    """Read the saved Run through the API and assert no Judge or provider was used."""
    run = fetch(f"{base}/api/blackbox/runs/{identifier}")
    assert run["status"] == "completed", run["status"]
    results = [result for case in run["cases"] for result in case["results"]]
    statuses = [result["status"] for result in results]
    assert len(results) == expected["results"], statuses
    assert statuses.count("passed") == expected["passed"], statuses
    assert statuses.count("failed") == expected["failed"], statuses
    assert all(result.get("score") is not None for result in results), "a Case went unscored"
    assert not any(result.get("judges") for result in results), "a Judge verdict was recorded"
    assert run["config"]["judge_enabled"] is False
    assert run["config"]["judges"] == []
    assert run["config"]["auto_local_fallback"] is False
    assert run["config"]["simple_mode"] is False, "the demo must not run the ten-Category suite"
    assert run["synthetic_demo"]["synthetic"] is True
    assert run["synthetic_demo"]["judge_used"] is False
    events = [entry["event"] for entry in run.get("audit", [])]
    assert "synthetic_demo" in events, events
    return run


def check_exports(base: str, identifier: str, label: str) -> dict:
    """Both exports must carry the synthetic disclosure, not just the screen."""
    exported = fetch(f"{base}/api/blackbox/runs/{identifier}/download?format=json")
    assert exported["synthetic_demo"]["label"] == label
    assert label in exported["limitations"]
    request = urllib.request.Request(f"{base}/api/blackbox/runs/{identifier}/download?format=pdf")
    with urllib.request.urlopen(request, timeout=120) as response:
        pdf = response.read()
    assert pdf.startswith(b"%PDF"), "the PDF export did not render"
    return {"json_export": "passed", "pdf_bytes": len(pdf)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=2713)
    parser.add_argument("--bot-port", type=int, default=2709)
    parser.add_argument(
        "--artifacts",
        default="",
        help="Directory for a failure screenshot and trace. Defaults to the temporary runtime.",
    )
    args = parser.parse_args(argv)
    base = f"http://127.0.0.1:{args.port}"

    with ExitStack() as cleanup:
        runtime = cleanup.enter_context(tempfile.TemporaryDirectory(prefix="studio-demo-ui-"))
        os.environ["STUDIO_RUNTIME"] = runtime
        os.environ.setdefault("STUDIO_AUTO_RESUME", "0")
        sys.path.insert(0, str(REPO))
        from playwright.sync_api import sync_playwright

        from app.blackbox import demo_bot
        from scripts.process_cleanup import stop_process_tree

        if args.bot_port != demo_bot.DEMO_PORT:
            raise SystemExit(
                f"The shell points at port {demo_bot.DEMO_PORT}; serve the demo bot there."
            )
        artifacts = Path(args.artifacts or runtime)
        artifacts.mkdir(parents=True, exist_ok=True)
        expected = dict(demo_bot.DEMO_EXPECTED)
        categories = demo_categories()

        bot = serve_demo_bot(args.bot_port)
        cleanup.callback(stop_process_tree, bot)
        # One callback stops whichever Studio process is current, so the restart
        # below cannot leave an orphan behind on a failure.
        running = [serve_studio(args.port)]
        cleanup.callback(lambda: stop_process_tree(running[-1]))

        def restart_studio():
            """Prove the saved Run survives a process restart, not just a reload."""
            stop_process_tree(running[-1])
            running.append(serve_studio(args.port))

        report: dict = {"artifacts": str(artifacts), "expected": expected}
        allowed = {f"127.0.0.1:{args.port}", f"127.0.0.1:{args.bot_port}"}
        with sync_playwright() as play:
            browser = play.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 1000})
            context.tracing.start(screenshots=True, snapshots=True)
            page = context.new_page()
            errors: list[str] = []
            offsite: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            # Any request leaving the two loopback ports is a finding in itself.
            page.on(
                "request",
                lambda request: None
                if _host_of(request.url) in allowed
                else offsite.append(request.url),
            )
            try:
                identifier = run_the_demo(page, base, expected)
                report["run_id"] = identifier
                check_results(page, expected, categories)
                check_disclosure(page)
                report["demo_journey"] = "passed"

                run = saved_run(base, identifier, expected)
                costs = run.get("costs") or {}
                report["judge_calls"] = (costs.get("evaluation") or {}).get("calls", 0)
                report["bot_calls"] = (costs.get("bot") or costs.get("target") or {}).get(
                    "calls", 0
                )
                assert not report["judge_calls"], report["judge_calls"]
                report["no_provider_calls"] = "passed"
                report |= check_exports(base, identifier, run["synthetic_demo"]["label"])

                restart_studio()
                page.goto(f"{base}/?run={identifier}", wait_until="networkidle")
                check_results(page, expected, categories)
                check_disclosure(page)
                reopened = saved_run(base, identifier, expected)
                assert reopened["id"] == identifier
                report["reopened_after_restart"] = "passed"

                assert not offsite, offsite
                assert not errors, errors
                report["browser_errors"] = errors
                report["offsite_requests"] = offsite
            except Exception:
                page.screenshot(path=str(artifacts / "demo-failure.png"), full_page=True)
                context.tracing.stop(path=str(artifacts / "demo-failure-trace.zip"))
                report["browser_errors"] = errors
                report["offsite_requests"] = offsite
                print(json.dumps(report, indent=2), file=sys.stderr)
                print(f"Saved failure artifacts to {artifacts}", file=sys.stderr)
                raise
            context.tracing.stop()
            browser.close()
        print(json.dumps(report, indent=2))
    return 0


def _host_of(url: str) -> str:
    from urllib.parse import urlsplit

    parsed = urlsplit(url)
    return f"{parsed.hostname}:{parsed.port}" if parsed.port else str(parsed.hostname)


if __name__ == "__main__":
    raise SystemExit(main())
