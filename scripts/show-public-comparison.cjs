const { chromium } = require("../runtime/ui-check/node_modules/playwright");
(async () => {
  const b = await chromium.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: true,
  });
  try {
    const p = await b.newPage({ viewport: { width: 1450, height: 1000 } });
    const errors = [];
    p.on("pageerror", (e) => errors.push(e.message));
    await p.goto("http://127.0.0.1:2708/?comparison=ed476a39-1fe0-4fa7-b572-e9ae935ea1bb");
    await p.waitForFunction(() =>
      document.querySelector("#comparisonResults")?.textContent.includes("SupportFlow"),
    );
    console.log("MESSAGE", await p.locator("#comparisonMessage").innerText());
    console.log("SUMMARY", (await p.locator("#comparisonResults").innerText()).slice(0, 1700));
    console.log("JS ERRORS", JSON.stringify(errors));
    await p.locator("#comparisonResults").scrollIntoViewIfNeeded();
    await p.screenshot({ path: "runtime/reports/public-comparison-screen.png" });
  } finally {
    await b.close();
  }
})().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
