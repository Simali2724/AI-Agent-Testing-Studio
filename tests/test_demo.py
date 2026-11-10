"""The no-key synthetic demo (T-047).

A new user must be able to complete a real evaluation with no provider account.
These tests assert the demo bot is deterministic, that its Cases validate
through the ordinary imported-case schema, that the demo both passes and fails
Cases, that scoring works with the AI Judge switched off, and that no provider
call is ever attempted.
"""

import asyncio
import importlib.util
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.blackbox import demo_bot, runner
from app.blackbox.schema import ImportedCase, Settings, Target
from app.blackbox_app import app

_SPEC = importlib.util.spec_from_file_location(
    "studio_demo_bot", Path(__file__).parents[1] / "scripts" / "demo_bot.py"
)
demo_server = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(demo_server)


def client() -> TestClient:
    return TestClient(app)


def bot_client() -> TestClient:
    """A client for the separate demo-bot process's app."""
    return TestClient(demo_server.app)


def test_the_demo_bot_is_deterministic():
    for case in demo_bot.case_set():
        for turn in case["turns"]:
            assert demo_bot.reply(turn) == demo_bot.reply(turn)


def test_the_demo_bot_answers_and_discloses_that_it_is_synthetic():
    response = bot_client().post("/chat", json={"message": "What is the warranty for SD-100?"})
    assert response.status_code == 200
    body = response.json()
    assert "24 months" in body["answer"]
    assert body["demo"] is True
    assert "not a measurement of a real chatbot" in body["disclosure"]


@pytest.mark.parametrize("payload", [{}, {"message": 7}, {"message": "x" * 20001}])
def test_the_demo_bot_validates_its_input(payload):
    assert bot_client().post("/chat", json=payload).status_code == 422


def test_the_demo_bot_only_binds_loopback():
    assert demo_server.main(["--host", "0.0.0.0"]) == 2


def test_the_demo_bot_reports_its_identity():
    body = bot_client().get("/health").json()
    assert body["service"] == "studio-synthetic-demo" and body["demo"] is True


def test_the_demo_case_set_validates_as_imported_cases():
    published = client().get("/api/blackbox/case-set/demo")
    assert published.status_code == 200
    body = published.json()
    assert body["judge_enabled"] is False
    assert "not a measurement of a real chatbot" in body["disclosure"]
    cases = [ImportedCase.model_validate(case) for case in body["cases"]]
    assert len(cases) == len(body["cases"]) >= 6
    # Unique names within a category, which Settings also enforces.
    identities = [(c.category, c.name.casefold()) for c in cases]
    assert len(identities) == len(set(identities))
    # Every Case must be scorable without an AI Judge.
    for case in cases:
        checks = case.checks
        assert checks.required or checks.forbidden or checks.canary


def test_the_published_demo_target_is_the_separate_loopback_process():
    body = client().get("/api/blackbox/case-set/demo").json()
    assert body["target_url"] == demo_bot.DEMO_URL
    assert body["target_url"].startswith("http://127.0.0.1:")
    assert body["response_field"] == "answer"
    assert "scripts/demo_bot.py" in body["start_command"]


def test_the_demo_is_accepted_as_a_settings_payload_without_a_judge():
    config = Settings(
        targets=[Target(name=demo_bot.DEMO_BOT_NAME, url=demo_bot.DEMO_URL)],
        categories=["hallucination"],
        consent=True,
        judge_enabled=False,
        custom_cases=demo_bot.case_set(),
    )
    assert config.judge_enabled is False
    assert len(config.custom_cases) >= 6


def test_the_demo_shows_both_a_pass_and_a_real_failure():
    """A demo where everything passes would misrepresent the tool."""
    outcomes = {}
    for case in demo_bot.case_set():
        answers = [demo_bot.reply(turn) for turn in case["turns"]]
        joined = " ".join(answers).casefold()
        checks = case["checks"]
        met = all(term.casefold() in joined for term in checks.get("required", []))
        met = met and not any(term.casefold() in joined for term in checks.get("forbidden", []))
        canary = checks.get("canary", "")
        met = met and not (canary and canary.casefold() in joined)
        outcomes[case["name"]] = met
    assert any(outcomes.values()), "The demo must contain passing Cases"
    assert not all(outcomes.values()), "The demo must contain a failing Case"
    assert outcomes["Demo: invented refund guarantee (fails on purpose)"] is False
    assert outcomes["Demo: supported warranty lookup"] is True


def test_a_demo_run_scores_without_contacting_any_provider(monkeypatch):
    """The whole demo path must never reach a provider or a real network bot."""
    import app.blackbox.metering as metering

    def forbidden(*args, **kwargs):
        raise AssertionError("The demo must not call a provider")

    monkeypatch.setattr(metering, "completion", forbidden)

    class DemoBot:
        """Stands in for the HTTP connector, answering from the demo fixture.

        The replies are the same strings the separate demo-bot process serves,
        so this exercises scoring without binding a port inside the suite.
        """

        def __init__(self, target, *args):
            self.target = target

        async def detect(self):
            pass

        async def close(self):
            pass

        async def conversation(self, case):
            return {
                "transcript": [
                    {"input": turn, "output": demo_bot.reply(turn), "seconds": 0.01}
                    for turn in case.get("turns", [])
                ]
            }

    config = Settings(
        targets=[Target(name=demo_bot.DEMO_BOT_NAME, url=demo_bot.DEMO_URL)],
        categories=["hallucination"],
        consent=True,
        judge_enabled=False,
        custom_cases=[c for c in demo_bot.case_set() if c["category"] == "hallucination"],
    )
    run = asyncio.run(runner.execute(runner.make_run(config), config, DemoBot))
    runner.aggregate(run)
    scored = [r for case in run["cases"] for r in case["results"] if r.get("score") is not None]
    assert scored, "Deterministic checks must score with the AI Judge disabled"
    assert {r["status"] for r in scored} <= {"passed", "failed"}
    assert any(r["status"] == "failed" for r in scored)
    assert any(r["status"] == "passed" for r in scored)


# --------------------------------------------------------------------------
# T-054: the documented demo journey through the current UI's own endpoint
# --------------------------------------------------------------------------


async def _accept_loopback(url):
    """The suite's transport never opens a socket, so skip address validation."""
    return None


def demo_bot_transport(counter: list[int]):
    """Route the real connector's HTTP calls into the demo bot's own ASGI app.

    This exercises the shipped REST connector, its request fields and its JSON
    parsing against the real fixture without binding a port inside the suite.
    Every call is counted and its destination asserted, so the test can prove
    where the traffic actually went.
    """
    inner = httpx.ASGITransport(app=demo_server.app)

    class Counting(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request):
            assert request.url.host in ("127.0.0.1", "localhost"), (
                f"The demo must only call loopback, not {request.url}"
            )
            assert request.url.port == demo_bot.DEMO_PORT
            counter.append(1)
            return await inner.handle_async_request(request)

    return Counting()


def test_the_demo_configuration_is_built_on_the_server_and_pins_every_model_path():
    """Nothing in the demo may reach a provider, fallback discovery included."""
    config = demo_bot.demo_config()
    assert config.judge_enabled is False
    assert config.judges == []
    # Discovery probes for an installed local model, which is itself a model call.
    assert config.auto_local_fallback is False
    # Imported Cases only: the ordinary ten-Category suite must not be planned.
    assert config.simple_mode is False
    assert config.all_imported_cases is True
    assert len(config.custom_cases) == demo_bot.DEMO_EXPECTED["cases"]
    assert set(config.categories) == {case["category"] for case in demo_bot.case_set()}
    assert config.repeat_counts == {}, "an unstated repeat count is one repeat"
    assert config.targets[0].url == demo_bot.DEMO_URL
    assert config.targets[0].response_field == demo_bot.DEMO_RESPONSE_FIELD
    assert config._demo_fixture is True


def test_the_demo_plans_exactly_its_own_cases_with_one_repeat_each():
    config = demo_bot.demo_config()
    run = runner.make_run(config)
    assert len(run["cases"]) == demo_bot.DEMO_EXPECTED["cases"]
    assert {len(case["results"]) for case in run["cases"]} == {1}
    assert [case["prerequisite"] for case in run["cases"] if case["prerequisite"]] == [], (
        "every demo Case must be scorable with the AI Judge off"
    )
    assert {case["source"] for case in run["cases"]} == {"imported"}
    assert run["synthetic_demo"]["synthetic"] is True
    assert run["limitations"][0] == demo_bot.DEMO_LABEL


def test_the_start_commands_use_the_project_environment_on_both_platforms():
    """`run.ps1` does not activate a second terminal, so PATH Python is not enough."""
    commands = demo_bot.start_commands()
    assert ".venv" in commands["windows"] and "Scripts" in commands["windows"]
    assert ".venv/bin/python" in commands["posix"]
    assert "scripts" in commands["windows"].replace("\\", "/")
    assert "scripts/demo_bot.py" in commands["posix"]
    assert demo_bot.start_command("nt") == commands["windows"]
    assert demo_bot.start_command("posix") == commands["posix"]


def test_the_published_demo_case_set_tells_the_ui_what_to_expect():
    body = client().get("/api/blackbox/case-set/demo").json()
    assert body["expected"] == demo_bot.DEMO_EXPECTED
    assert body["start_commands"] == demo_bot.start_commands()
    assert len(body["cases"]) == body["expected"]["cases"]


def test_the_demo_route_requires_explicit_consent():
    response = client().post(
        "/api/blackbox/demo/runs", json={"consent": False}, headers={"X-Studio-Request": "1"}
    )
    assert response.status_code == 422
    assert "allow" in response.text.casefold()


def test_the_demo_route_accepts_no_evaluation_configuration():
    """A demo assembled from client input could be aimed at a real bot or provider."""
    response = client().post(
        "/api/blackbox/demo/runs",
        json={"consent": True, "targets": [{"url": "https://example.invalid/chat"}]},
        headers={"X-Studio-Request": "1"},
    )
    assert response.status_code == 422
    assert "targets" in response.text


def test_the_demo_route_names_the_exact_start_command_when_the_bot_is_down(monkeypatch):
    """A clear instruction beats a Run full of connection failures."""
    import app.blackbox_app as application

    class Down:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url):
            raise httpx.ConnectError("refused")

    monkeypatch.setattr(application.httpx, "AsyncClient", Down)
    response = client().post(
        "/api/blackbox/demo/runs", json={"consent": True}, headers={"X-Studio-Request": "1"}
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert demo_bot.DEMO_URL in detail
    assert demo_bot.start_command() in detail


def test_the_demo_route_refuses_a_stranger_on_the_demo_port(monkeypatch):
    import app.blackbox_app as application

    class Stranger:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url):
            return httpx.Response(
                200,
                json={"service": "something-else"},
                request=httpx.Request("GET", url),
            )

    monkeypatch.setattr(application.httpx, "AsyncClient", Stranger)
    response = client().post(
        "/api/blackbox/demo/runs", json={"consent": True}, headers={"X-Studio-Request": "1"}
    )
    assert response.status_code == 422
    assert str(demo_bot.DEMO_PORT) in response.json()["detail"]


def test_normal_evaluations_still_require_their_judge():
    """The demo must not have relaxed judge validation for real bots."""
    from fastapi import HTTPException

    from app.blackbox.studio_routes import prepare

    config = Settings(
        targets=[Target(name="Real bot", url="https://example.invalid/chat")],
        consent=True,
        judge_consent=True,
        judges=[],
    )
    with pytest.raises(HTTPException) as refused:
        prepare(config)
    assert refused.value.status_code == 422
    assert "judge" in refused.value.detail.casefold()


def test_the_whole_demo_run_scores_through_the_real_connector_with_no_provider(monkeypatch):
    """The journey's measured outcome: eight Cases, seven pass, one deliberate failure."""
    import app.blackbox.connectors as connectors
    import app.blackbox.metering as metering

    def forbidden(*args, **kwargs):
        raise AssertionError("The demo must not call a provider")

    monkeypatch.setattr(metering, "completion", forbidden)

    calls: list[int] = []
    real_client = httpx.AsyncClient

    def routed(*args, **kwargs):
        kwargs["transport"] = demo_bot_transport(calls)
        kwargs.pop("trust_env", None)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(connectors.httpx, "AsyncClient", routed)
    monkeypatch.setattr(connectors, "validate_destination", _accept_loopback)

    config = demo_bot.demo_config()
    run = asyncio.run(runner.execute(runner.make_run(config), config, connectors.Connector))
    runner.aggregate(run)

    results = [result for case in run["cases"] for result in case["results"]]
    statuses = [result["status"] for result in results]
    expected = demo_bot.DEMO_EXPECTED
    assert len(results) == expected["results"]
    assert statuses.count("passed") == expected["passed"], statuses
    assert statuses.count("failed") == expected["failed"], statuses
    assert all(result["score"] is not None for result in results), "all Cases scored, no Judge"
    assert calls, "the demo must actually reach the bundled fixture"
    assert len(calls) == sum(len(case["turns"]) for case in demo_bot.case_set())
    assert not any(result.get("judges") for result in results), "no Judge verdict may exist"


def test_a_saved_demo_run_keeps_its_disclosure_across_a_restart_and_into_exports():
    """Reopening and exporting must both carry the synthetic label."""
    from app import database
    from app.blackbox.governance import export_run

    config = demo_bot.demo_config()
    run = runner.make_run(config)
    run["status"] = "completed"
    runner.save(run, config)

    # A restart is a fresh read of the database, not the in-memory object.
    database.close()
    reopened = database.get("blackbox", run["id"])
    assert reopened is not None, "the demo Run must survive a restart"
    assert reopened["synthetic_demo"]["synthetic"] is True
    assert reopened["synthetic_demo"]["judge_used"] is False
    assert demo_bot.DEMO_LABEL in reopened["limitations"]

    exported = export_run(reopened)
    assert exported["synthetic_demo"]["label"] == demo_bot.DEMO_LABEL
    assert demo_bot.DEMO_LABEL in exported["limitations"]


def test_the_audit_chain_records_that_the_run_came_from_the_bundled_fixture():
    config = demo_bot.demo_config()
    run = runner.make_run(config)
    from app.blackbox.studio_engine import audit

    audit(
        run,
        "synthetic_demo",
        fixture=demo_bot.disclosure()["fixture"],
        bot=demo_bot.DEMO_URL,
        judge_enabled=False,
    )
    events = [entry["event"] for entry in run.get("audit", [])]
    assert "synthetic_demo" in events
