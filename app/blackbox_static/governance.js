/* No API keys are persisted by this page. Reproduce reuses saved server credentials. */
const $ = (id) => document.getElementById(id);
const esc = (x) =>
  String(x ?? "").replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
  );
let storedJudges = [];
let selected = new URLSearchParams(location.search).get("run");
async function request(url, method = "GET", data) {
  const r = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json", "X-Studio-Request": "1" },
    body: data === undefined ? undefined : JSON.stringify(data),
  });
  const result = await r.json();
  if (!r.ok) throw Error(result.detail || "Request failed");
  return result;
}
async function load() {
  if (!selected) return;
  const [g, run] = await Promise.all([
    request(`/api/studio/runs/${selected}/governance`),
    request(`/api/blackbox/runs/${selected}`),
  ]);
  storedJudges = run.config.judges || [];
  const integrity = g.run_integrity;
  $("integrity").innerHTML =
    `<h2>Run integrity</h2><p>Audit chain: <strong>${g.audit_integrity.valid === null ? "Legacy / unavailable" : g.audit_integrity.valid ? "Intact" : "TAMPERING DETECTED"}</strong> — ${esc(g.audit_integrity.reason)}</p><p>${integrity.accounted_for}/${integrity.planned} outcomes accounted for. ${integrity.scored} scored; ${integrity.not_tested} not tested with reason; ${integrity.pending} pending. ${integrity.overrides} overrides.</p><p>Judge agreement: ${integrity.agreement_percent == null ? "Not measured" : integrity.agreement_percent + "%"}. Human review flags: ${esc(integrity.low_agreement_cases.join(", ") || "None")}</p><p>Suite ${esc(g.suite_version)}<br>Config hash ${esc(g.config_hash)}</p><p>${esc(g.reproduction_note)}</p>`;
  $("cards").innerHTML = [
    ...g.bot_cards.map(
      (b) =>
        `<article><h3>Bot: ${esc(b.name)}</h3><p>${esc(b.declared_model)}<br>${esc(b.url)}<br>${esc(b.connection)}</p></article>`,
    ),
    ...g.judge_cards.map(
      (j) =>
        `<article><h3>Judge: ${esc(j.model)}</h3><p>Revision: ${esc(j.revision)}<br>${j.local ? "Local" : "Cloud"}${j.fallback ? " fallback" : " primary"}<br>${esc(j.endpoint)}</p></article>`,
    ),
  ].join("");
  $("warnings").innerHTML = g.warnings.map((w) => `<p>${esc(w)}</p>`).join("");
  $("audit").textContent = JSON.stringify(run.audit || [], null, 2);
  $("mapping").innerHTML =
    `<p>${esc(g.mapping.disclaimer)}</p>` +
    Object.entries(g.mapping.categories)
      .map(
        ([c, m]) =>
          `<details><summary>${esc(c)}</summary><pre>${esc(JSON.stringify(m, null, 2))}</pre></details>`,
      )
      .join("");
  $("credentials").innerHTML =
    g.judge_cards
      .map((j, i) =>
        !j.local
          ? `<label>${esc(j.model)} API key (only if needed)<input type="password" autocomplete="off" data-judge-key="${i}"></label>`
          : "",
      )
      .join("") +
    g.bot_cards
      .map(
        (b, i) =>
          `<label>${esc(b.name)} token (only if originally required)<input type="password" autocomplete="off" data-bot-key="${i}"></label>`,
      )
      .join("");
  $("days").value = g.retention_days;
  $("results").href = `/?run=${selected}#results`;
  $("export").href = `/api/blackbox/runs/${selected}/download?format=json`;
  history.replaceState(null, "", `?run=${selected}`);
}
function act(action) {
  return async () => {
    try {
      await action();
    } catch (e) {
      $("status").textContent = e.message;
    }
  };
}
$("runs").onchange = act(async () => {
  selected = $("runs").value;
  await load();
});
$("reproduce").onclick = act(async () => {
  const run = await request(`/api/studio/runs/${selected}/reproduce`, "POST", {
    judges: storedJudges.map((j, i) => ({
      ...j,
      token: document.querySelector(`[data-judge-key="${i}"]`)?.value || null,
    })),
    target_tokens: [...document.querySelectorAll("[data-bot-key]")].map((e) => e.value || null),
  });
  location.href = `/?run=${run.id}#results`;
});
$("save-retention").onclick = act(async () => {
  await request(`/api/studio/runs/${selected}/retention`, "PUT", { days: Number($("days").value) });
  $("status").textContent = "Retention saved";
  await load();
});
$("delete").onclick = act(async () => {
  if (
    !confirm(
      "Delete this run, usage and cached evidence permanently? Downloaded copies are unchanged.",
    )
  )
    return;
  await request(`/api/blackbox/runs/${selected}`, "DELETE");
  location.href = "/governance.html";
});
act(async () => {
  const runs = await request("/api/blackbox/runs");
  $("runs").innerHTML = runs
    .map(
      (r) =>
        `<option value="${esc(r.id)}">${esc(r.targets.map((b) => b.name).join(" vs "))} — ${esc(r.id)}</option>`,
    )
    .join("");
  selected = selected || runs[0]?.id;
  if (selected) {
    $("runs").value = selected;
    await load();
  } else {
    $("status").textContent = "Start an evaluation first.";
    $("reproduce").disabled = true;
    $("delete").disabled = true;
  }
})();
