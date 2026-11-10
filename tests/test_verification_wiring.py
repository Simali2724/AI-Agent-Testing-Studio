"""The verification scripts CI actually runs (Phase D of the 2026-10-23 review).

The review found that CI's only real browser check drove the retained legacy `index.html`, while
eleven `scripts/check-*.cjs` files could not run from a clean checkout at all. Configuration
silently drifting away from the current UI is the failure mode these tests guard.
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github/workflows/quality.yml"

#: Removed on 2026-10-23: they required Playwright from the gitignored runtime directory,
#: hardcoded one machine's chrome.exe path and deleted run identifiers, and asserted retired
#: selectors. PROGRESS.md records the per-file reasons.
REMOVED = (
    "check-blackbox.cjs",
    "check-category-labels.cjs",
    "check-comparison.cjs",
    "check-easy-setup.cjs",
    "check-import-selection.cjs",
    "check-judge-experience.cjs",
    "check-judge-providers.cjs",
    "check-large-upload.cjs",
    "check-readability.cjs",
    "check-scoring.cjs",
    "check-simple-ui.cjs",
)


def steps() -> list[dict]:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return workflow["jobs"]["quality"]["steps"]


def commands() -> str:
    return "\n".join(str(step.get("run", "")) for step in steps())


def test_ci_runs_the_current_shell_browser_check():
    assert "scripts/check-studio-ui.py" in commands(), (
        "CI must run the browser check for the current shell, not only the legacy interface"
    )


def test_ci_still_runs_the_retained_legacy_browser_check():
    """The legacy interface stays served, so its coverage must not be dropped silently."""
    assert "scripts/check-exact-compare.py" in commands()


def test_ci_installs_linux_browser_system_dependencies():
    """Chromium needs its shared libraries on the Ubuntu runner."""
    text = commands()
    assert "--with-deps chromium" in text, "Linux browser system dependencies are not installed"
    assert "$IsLinux" in text, "the --with-deps install must be conditional on Linux"


def test_ci_keeps_browser_failure_artifacts():
    upload = [s for s in steps() if "upload-artifact" in str(s.get("uses", ""))]
    assert upload, "CI must keep a trace or screenshot when a browser check fails"
    assert any(step.get("if") == "failure()" for step in upload), (
        "artifacts should be uploaded on failure, not on every run"
    )


def test_ci_covers_every_supported_platform():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    matrix = workflow["jobs"]["quality"]["strategy"]["matrix"]["os"]
    assert set(matrix) == {"windows-latest", "ubuntu-latest", "macos-latest"}


def test_the_current_browser_check_is_self_contained():
    """It must bring its own server and fixtures, so CI needs no running Studio."""
    text = (ROOT / "scripts/check-studio-ui.py").read_text(encoding="utf-8")
    assert "tempfile.TemporaryDirectory" in text, "it must use a temporary runtime directory"
    assert "STUDIO_RUNTIME" in text, "it must not touch the owner's saved history"
    assert "uvicorn" in text, "it must start its own server"
    assert "127.0.0.1" in text, "the server must stay on loopback"
    assert "runtime/ui-check" not in text, "it must not load Playwright from the runtime directory"
    assert "Program Files" not in text, "it must not hardcode a browser path"
    assert "data-view=" in text and "data-panel=" in text, "it must drive the shell navigation"
    for view in ("evaluate", "results", "governance"):
        assert view in text, f"the {view} view is not exercised"
    assert "#calibration-panel" in text, "Judge calibration is not exercised"
    assert "#gov-human" in text, "Governance human alignment is not exercised"
    assert "#evaluator-provenance" in text, "evaluator provenance is not exercised"


def test_removed_browser_checks_are_gone_and_not_invoked():
    """No runnable entry point may invoke them. Documents may record that they were removed."""
    for name in REMOVED:
        assert not (ROOT / "scripts" / name).exists(), f"{name} came back"
    invokers = [
        ROOT / "package.json",
        *(ROOT / ".github/workflows").glob("*.yml"),
        *(ROOT / "scripts").iterdir(),
        *(ROOT / "app").rglob("*.py"),
    ]
    for path in invokers:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in REMOVED:
            assert name not in text, f"{path.name} still invokes the removed {name}"


def test_no_tracked_script_loads_playwright_from_the_runtime_directory():
    """`runtime/` is gitignored, so anything requiring it cannot run from a clean checkout."""
    offenders = []
    for path in (ROOT / "scripts").iterdir():
        if path.is_file() and path.suffix in {".py", ".cjs", ".js"}:
            if re.search(r"runtime/ui-check", path.read_text(encoding="utf-8", errors="ignore")):
                offenders.append(path.name)
    assert not offenders, f"these load Playwright from the gitignored runtime: {offenders}"


def test_ci_runs_the_advertised_demo_journey_in_a_browser():
    """The README's no-key journey is a release claim, so CI must execute it (T-054).

    The defect this guards was a working API demo with no way to reach it from the
    shipped UI. API tests passed throughout, so only a browser check catches it.
    """
    assert "scripts/check-demo-journey.py" in commands(), (
        "CI must run the demo journey browser check, not only API-level demo tests"
    )


def test_the_demo_journey_check_is_self_contained_and_proves_no_provider_was_called():
    text = (ROOT / "scripts/check-demo-journey.py").read_text(encoding="utf-8")
    assert "tempfile.TemporaryDirectory" in text, "it must use a temporary runtime directory"
    assert "STUDIO_RUNTIME" in text, "it must not touch the owner's saved history"
    assert "uvicorn" in text, "it must start its own Studio"
    assert "scripts/demo_bot.py" in text, "it must start the bundled demo bot itself"
    assert "127.0.0.1" in text, "both servers must stay on loopback"
    assert "runtime/ui-check" not in text, "it must not load Playwright from the runtime directory"
    assert "Program Files" not in text, "it must not hardcode a browser path"
    # The journey itself, driven through the shipped shell.
    assert "#demo-start" in text and "#demo-consent" in text, "it must drive the demo controls"
    assert "#case-results" in text, "it must read the Results panel"
    assert "#synthetic-badge" in text, "it must check the persistent synthetic disclosure"
    # The boundaries that make the demo free.
    assert "offsite" in text, "it must fail on any request outside the two loopback ports"
    assert "judge_calls" in text, "it must assert zero judge calls"
    assert "format=pdf" in text and "format=json" in text, "both exports must be checked"
    assert "restart_studio" in text, "the saved Run must be reopened after a restart"
