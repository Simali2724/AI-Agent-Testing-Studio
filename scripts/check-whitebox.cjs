const { chromium } = require("../runtime/ui-check/node_modules/playwright");
const assert = require("node:assert/strict");
(async () => {
  const browser = await chromium.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: true,
  });
  try {
    const p = await browser.newPage();
    const errors = [];
    p.on("pageerror", (e) => errors.push(e.message));
    await p.goto("http://127.0.0.1:2708/");
    await p.locator('nav button[data-view="configuration"]').click();
    await p.locator("#whiteBoxPreset").click();
    assert.deepEqual(
      await p.locator("#testChoices input:checked").evaluateAll((es) => es.map((e) => e.value)),
      ["static", "security"],
    );
    assert.match(await p.locator("#testChoices").innerText(), /White-box testing/);
    await p.locator("#allTestsPreset").click();
    assert.equal(await p.locator("#testChoices input:checked").count(), 12);
    assert.equal(await p.locator("[name=execution_consent]").isChecked(), false);
    await p.locator('nav button[data-view="results"]').click();
    await p.waitForFunction(() => document.querySelector("#resultRows").children.length > 0);
    const runs = await (await p.request.get("http://127.0.0.1:2708/api/runs")).json();
    const saved = runs.find((r) => r.results.some((x) => x.category === "static"));
    assert(saved, "Saved white-box source result exists");
    await p.locator("#runSelect").selectOption(saved.id);
    await p.waitForFunction(() =>
      document.querySelector("#resultRows").textContent.includes("White-box testing"),
    );
    assert.deepEqual(errors, []);
    console.log(
      "PASS: white-box label, presets, all 12 category selections, separate consent and actual result visible; no browser errors.",
    );
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
