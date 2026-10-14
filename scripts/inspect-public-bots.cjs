const { chromium } = require("../runtime/ui-check/node_modules/playwright");
(async () => {
  const b = await chromium.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: true,
  });
  try {
    for (const url of [
      "https://ai-customer-support-chatbot-orcin.vercel.app/",
      "https://voltkart-chatbot.onrender.com/",
    ]) {
      const p = await b.newPage();
      p.on("request", (r) => {
        if (["fetch", "xhr"].includes(r.resourceType())) console.log("API", r.method(), r.url());
      });
      try {
        await p.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
        console.log("PAGE", url, await p.locator("body").innerText({ timeout: 10000 }));
        console.log(
          "CONTROLS",
          await p.locator("input,textarea,button").evaluateAll((es) =>
            es
              .map((e) => ({
                tag: e.tagName,
                type: e.type,
                placeholder: e.placeholder,
                text: e.innerText,
              }))
              .slice(0, 30),
          ),
        );
      } catch (e) {
        console.log("PAGE ERROR", url, e.message);
      }
      await p.close();
    }
  } finally {
    await b.close();
  }
})();
