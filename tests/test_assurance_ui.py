"""Isolated browser smoke: synthetic target, no real bot/provider conversations."""

import os
import socket
import threading
import time

import pytest
import uvicorn

from app.blackbox_app import app


def test_white_only_setup_and_combined_results():
    playwright = pytest.importorskip("playwright.sync_api")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", lifespan="off")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.05)
        assert server.started
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"http://127.0.0.1:{port}/")
            page.locator("#start").wait_for(state="visible")
            page.wait_for_function("!document.getElementById('start').disabled")
            page.locator('[data-field="name"]').fill("OFFLINE UI TEST — no bot called")
            page.locator('[data-field="url"]').fill("http://localhost:9999/fixture")
            page.locator('[data-mode="black"]').uncheck()
            page.locator('[data-mode="white"]').check()
            page.locator("#ownership").check()
            page.locator("#start").click()
            page.wait_for_function(
                "document.getElementById('assurance-status').textContent.includes('completed')",
                timeout=20000,
            )
            assert page.locator('[data-assurance-tab="black"]').is_disabled()
            page.locator('[data-assurance-tab="white"]').click()
            assert "Upload a source ZIP" in page.locator("#assurance-content").text_content()
            assert "Unknown" in page.locator("#assurance-content").text_content()
            page.locator('nav [data-view="governance"]').click()
            assert page.locator("#assurance-governance").is_visible()
            assert "Assessment" in page.locator("#assurance-governance").text_content()
            if os.getenv("STUDIO_UI_SCREENSHOT"):
                page.screenshot(path=os.environ["STUDIO_UI_SCREENSHOT"], full_page=True)
            assert not errors
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=10)
