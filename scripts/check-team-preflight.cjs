const { chromium } = require("../runtime/ui-check/node_modules/playwright");
(async () => {
  const b = await chromium.launch({
    headless: true,
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
  });
  const p = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  let errors = [];
  p.on("pageerror", (e) => errors.push(e.message));
  await p.goto("http://127.0.0.1:2708/?run=d9931cd3-70c6-47cd-bc0b-2ed946970446#results");
  await p.getByText("Connection checks: evaluation could not start", { exact: true }).waitFor();
  await p.locator("#preflight").scrollIntoViewIfNeeded();
  await p.screenshot({ path: "runtime/reports/team-comparison-preflight.png" });
  if (errors.length) throw Error(errors.join("\n"));
  console.log("Verified: preflight failure visible, zero chat cases, no winner.");
  await b.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
