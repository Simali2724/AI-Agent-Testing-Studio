/* Ten-case screen. Credentials remain in password fields and request bodies only. */
const $ = (id) => document.getElementById(id);
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
  );
let pollBusy = false;
let hydrateRequested = !!new URLSearchParams(location.search).get("run");
let settings,
  runId = new URLSearchParams(location.search).get("run"),
  botCount = 0,
  nextBot = 0,
  current;
const tell = (message) => {
  $("notice").className = "notice";
  $("notice").textContent = message;
};
async function api(url, body, method = "POST") {
  const response = await fetch(
    url,
    body === undefined
      ? {}
      : {
          method,
          headers: { "Content-Type": "application/json", "X-Studio-Request": "1" },
          body: JSON.stringify(body),
        },
  );
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail || response.status),
    );
  }
  return response.json();
}
function addBot() {
  if (botCount >= 4) return;
  const i = nextBot++;
  botCount++;
  $("bots").insertAdjacentHTML(
    "beforeend",
    `<article class="bot" data-bot="${i}"><h3>Chatbot ${i + 1}</h3><div class="grid"><label>Name<input data-field="name" value="Chatbot ${i + 1}"></label><label>Chat page or full API link<input data-field="url" placeholder="https://your-bot.example/chat"></label></div><label>Or upload a ZIP<input data-field="zip" type="file" accept=".zip"></label><details><summary>Connection help (only if automatic detection needs help)</summary><div class="grid"><label>Type<select data-field="kind"><option value="auto">Detect automatically</option><option value="rest">REST API</option><option value="openai">OpenAI compatible</option><option value="web">Web chat widget</option></select></label><label>API key<input data-field="token" type="password" autocomplete="off"></label><label>Bot model / cost alias<input data-field="model"></label><label>Request message field<input data-field="message_field" value="message"></label><label>Response field<input data-field="response_field" placeholder="Detect common fields"></label><label>History field<input data-field="history_field"></label><label>Conversation ID field<input data-field="session_field" value="conversation_id"></label><label>Extra request JSON<textarea data-field="defaults">{}</textarea></label><label>Chat input selector<input data-field="input_selector"></label><label>Bot reply selector<input data-field="answer_selector"></label><label>Send button selector<input data-field="send_selector"></label></div></details><button class="remove-bot">Remove this bot</button></article>`,
  );
  const card = $("bots").lastElementChild;
  card.querySelector(".remove-bot").onclick = () => {
    card.remove();
    botCount--;
    planned();
  };
  card.querySelector("[data-field=zip]").onchange = async (e) => {
    try {
      const data = new FormData();
      data.append("file", e.target.files[0]);
      const r = await fetch("/api/blackbox/upload", {
        method: "POST",
        headers: { "X-Studio-Request": "1" },
        body: data,
      });
      const result = await r.json();
      if (!r.ok) throw new Error(result.detail);
      card.dataset.archive = result.id || result.archive_id;
      tell(
        "ZIP stored. Start this trusted bot in your own environment and paste its running link; no isolated ZIP runner is configured.",
      );
    } catch (error) {
      tell(error.message);
    }
  };
  planned();
}
function planned() {
  $("add-bot").disabled = botCount >= 4;
  if (!settings) return;
  const repeats = [...document.querySelectorAll("[data-repeat]")].reduce(
    (n, e) => n + Number(e.value) * (settings.scenario_sets?.[e.dataset.repeat]?.length || 1),
    0,
  );
  $("planned").textContent =
    `${settings.cases.length} categories × distinct cases × chosen repeats = ${repeats} case executions per bot; ${repeats * botCount} planned bot case executions. Multi-turn and paired cases contain several messages.`;
}
function judges() {
  return [...document.querySelectorAll(".judge")]
    .filter((e) => e.querySelector("[data-enabled]").checked)
    .map((e) => ({
      model: e.querySelector("[data-model]").value.trim(),
      url: e.dataset.url,
      token: e.querySelector("[data-key]").value || null,
      local: e.dataset.local === "true",
      fallback: e.querySelector("[data-fallback]").checked,
    }));
}
function configuration() {
  const targets = [...document.querySelectorAll(".bot")].map((e) => {
    const val = (k) => e.querySelector(`[data-field=${k}]`).value.trim();
    return {
      name: val("name"),
      url: val("url"),
      kind: e.dataset.archive && !val("url") ? "zip" : val("kind"),
      archive_id: e.dataset.archive || "",
      token: val("token") || null,
      model: val("model"),
      model_alias: val("model"),
      message_field: val("message_field"),
      response_field: val("response_field"),
      history_field: val("history_field"),
      session_field: val("session_field"),
      request_defaults: JSON.parse(val("defaults") || "{}"),
      input_selector: val("input_selector"),
      answer_selector: val("answer_selector"),
      send_selector: val("send_selector"),
    };
  });
  return {
    targets,
    judges: judges(),
    consent: $("consent").checked,
    judge_consent: $("consent").checked,
    simple_mode: true,
    repeat_counts: Object.fromEntries(
      [...document.querySelectorAll("[data-repeat]")].map((e) => [
        e.dataset.repeat,
        Number(e.value),
      ]),
    ),
    references: JSON.parse($("references").value || "[]"),
    policy: $("policy").value,
    scope: $("scope").value,
    timeout: 60,
    max_minutes: 180,
    case_concurrency: 2,
    target_concurrency: 2,
    judge_concurrency: 1,
  };
}
const money = (n) => (n == null ? "Unknown" : "$" + (n / 1000000).toFixed(6));
function table(head, rows) {
  return `<div class="scroll"><table><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}
function bar(value, max) {
  return `<div class="bar-track"><div class="bar" style="width:${Math.min(100, Math.max(0, (Number(value) / Math.max(1, max)) * 100))}%"></div></div>`;
}
function render(run) {
  current = run;
  if (hydrateRequested && run.config.simple_mode) {
    $("bots").innerHTML = "";
    botCount = 0;
    nextBot = 0;
    run.targets.forEach((target) => {
      addBot();
      const card = $("bots").lastElementChild;
      card.dataset.archive = target.archive_id || "";
      for (const [key, value] of Object.entries(target)) {
        const field = card.querySelector(`[data-field="${key}"]`);
        if (field && key !== "token") field.value = typeof value === "string" ? value : "";
      }
      if (target.kind === "zip") card.querySelector("[data-field=kind]").value = "auto";
      card.querySelector("[data-field=defaults]").value = JSON.stringify(
        target.request_defaults || {},
      );
    });
    document
      .querySelectorAll("[data-repeat]")
      .forEach(
        (e) => (e.value = run.config.repeat_counts[e.dataset.repeat] || settings.default_repeats),
      );
    $("policy").value = run.config.policy;
    $("scope").value = run.config.scope;
    $("references").value = JSON.stringify(run.config.references || []);
    hydrateRequested = false;
    planned();
  }
  document.querySelectorAll(".judge").forEach((e) => {
    const model = e.querySelector("[data-model]").value;
    const event = [...(run.audit || [])]
      .reverse()
      .find(
        (a) =>
          a.model === model && ["judge_verdict", "judge_unavailable", "fallback"].includes(a.event),
      );
    const badge = e.querySelector("[data-status]");
    if (badge)
      badge.textContent = event
        ? event.event === "judge_unavailable"
          ? "Unavailable: " + event.reason
          : "Working: " + model
        : "Not checked yet";
  });
  const active = ["running", "queued"].includes(run.status);
  $("stop").disabled = !active;
  $("apply-judges").disabled = !active;
  $("resume").disabled =
    active || !run.cases.some((c) => c.results.some((r) => r.status === "not_tested"));
  const done = run.cases.filter((c) => c.completed).length;
  $("stage").textContent =
    `${run.status}: ${run.stage} • ${done}/${run.cases.length} cases processed. Scored coverage is shown below.`;
  $("progress").value = run.progress;
  const studio = run.studio;
  const resultCases =
    run.protocol_snapshot?.cases ||
    settings.cases.filter((c) => run.categories.includes(c.category));
  const caseName = (item) =>
    settings.cases.find((c) => c.category === item.category)?.name || item.name;
  if (!studio) {
    ["scores", "relevance-charts", "costs", "case-results", "audit", "downloads"].forEach(
      (id) => ($(id).innerHTML = ""),
    );
    $("resume").disabled = true;
    $("verdict").innerHTML =
      `<p>This is an older protocol. <a href="/index.html?run=${esc(run.id)}#results">Open its complete historical results</a>.</p>`;
    return;
  }
  $("verdict").innerHTML =
    `<h3>${studio.winner == null ? esc(studio.confidence_note) : "Winner: " + esc(run.targets[studio.winner].name)}</h3><p>${esc(studio.confidence_note)}</p><p>${esc(studio.formula)}</p><p>${studio.warnings.map(esc).join(" ")}</p>`;
  if (resultCases.length < settings.cases.length) {
    $("verdict").innerHTML +=
      `<p>This saved run contains ${resultCases.length} checks. ${settings.cases.length - resultCases.length} new checks are available above; start a new evaluation to score them. Historical scores are unchanged.</p>`;
  }
  $("scores").innerHTML =
    `<div class="grid">${studio.bots
      .map(
        (b) =>
          `<article class="metric"><h3>${esc(b.name)}</h3><p>Configured evaluation index</p><div class="score">${b.score}%</div><p>${b.tested}/${b.planned} conversations scored</p><p>Strongest measured check: ${esc([...b.categories].filter((c) => c.tested).sort((a, z) => z.quality - a.quality)[0]?.name || "Not established")}<br>Check first: ${esc(
            [...b.categories]
              .sort((a, z) => a.score - z.score)
              .slice(0, 3)
              .map((c) => c.name)
              .join(", "),
          )}</p>${bar(b.score, 100)}</article>`,
      )
      .join("")}</div>` +
    table(
      ["Check", ...studio.bots.map((b) => b.name), "Category result"],
      resultCases.map((item) => {
        const groups = studio.bots.map((b) => b.categories.find((c) => c.id === item.category));
        const complete = groups.every((g) => g.tested === g.planned);
        const high = Math.max(...groups.map((g) => g.score));
        const win = groups
          .map((g, i) => (high - g.score <= settings.tie_margin ? studio.bots[i].name : null))
          .filter(Boolean);
        return [
          esc(caseName(item)),
          ...groups.map(
            (g) =>
              `${g.score}% ${bar(g.score, 100)}<small>${g.tested}/${g.planned} scored; measured quality: ${g.quality == null ? "Not measured" : g.quality + "%"}; largest within-case repeat spread: ${g.repeat_spread ?? g.spread ?? "Unknown"} points</small>`,
          ),
          esc(!complete ? "Incomplete evidence" : win.length > 1 ? "Tie" : win[0]),
        ];
      }),
    );
  const relevanceKeys = ["hallucination_relevant", "hallucination_irrelevant"];
  $("relevance-charts").innerHTML =
    '<h3>Relevance and irrelevance — separate scores</h3><div class="grid">' +
    relevanceKeys
      .map((key) => {
        const label = settings.cases.find((c) => c.category === key)?.name || key;
        return `<article class="metric"><h4>${esc(label)}</h4>${studio.bots
          .map((bot) => {
            const group = bot.categories.find((c) => c.id === key);
            return group
              ? `<p><strong>${esc(bot.name)}: ${group.tested ? group.quality + "% measured quality" : "Not tested yet"}</strong></p>${bar(group.quality ?? 0, 100)}<small>${group.tested}/${group.planned} scored; configured index: ${group.score}%. Missing evidence contributes zero to the index.</small>`
              : `<p>${esc(bot.name)}: Not tested in this saved run</p>`;
          })
          .join("")}</article>`;
      })
      .join("") +
    "</div>";
  const costs = run.costs;
  if (costs?.available) {
    const rows = [
      ...(costs.bots || []).map((b) => ({ ...b, label: "Bot: " + b.name })),
      ...(costs.breakdowns?.model_alias || [])
        .filter((b) => b.evaluation?.calls)
        .map((b) => ({ ...b.evaluation, label: "Judge: " + b.name })),
    ];
    const max = Math.max(1, ...rows.map((r) => r.input_tokens + r.output_tokens));
    const maxCost = Math.max(1, ...rows.map((r) => r.cost_micro_usd || 0));
    $("costs").innerHTML =
      "<h3>Tokens and dollar cost</h3>" +
      table(
        [
          "Bot / judge",
          "Input",
          "Output",
          "Reasoning (included in output)",
          "Tokens chart",
          "USD cost",
          "Cost chart",
        ],
        rows.map((r) => [
          esc(r.label),
          r.input_tokens,
          r.output_tokens,
          r.reasoning_tokens || 0,
          bar(r.input_tokens + r.output_tokens, max),
          money(r.cost_micro_usd),
          r.cost_micro_usd == null ? "Unknown" : bar(r.cost_micro_usd, maxCost),
        ]),
      ) +
      `<p>Bot total: ${money(costs.bot?.cost_micro_usd)}. Evaluation total: ${money(costs.evaluation?.cost_micro_usd)}. Hidden bot calls require its own telemetry. Token totals can include estimates for failed or opaque calls; JSON records each source.</p>`;
  }
  const openIds = new Set(
    [...document.querySelectorAll("#case-results details[open]")].map((e) => e.dataset.case),
  );
  $("case-results").innerHTML =
    `<h3>${resultCases.length} recorded checks: summaries and transcripts</h3>` +
    resultCases
      .map(
        (item) =>
          `<details data-case="${esc(item.category)}" ${openIds.has(item.category) ? "open" : ""}><summary>${esc(caseName(item))}</summary>${run.cases
            .filter((c) => c.category === item.category)
            .map(
              (c) =>
                `<h4>${esc(c.name)} — case ${c.scenario_index || 1}, repeat ${c.repeat}</h4><div class="grid">${c.results.map((r, i) => `<article><strong>${esc(run.targets[i].name)} — ${esc(r.status.replaceAll("_", " "))}</strong><p>Score: ${r.score ?? "Not tested (index contribution 0)"}${r.score == null ? "" : "%"}</p><p>${esc(r.reason)}</p>${(r.judges || []).map((j) => `<p>Judge: ${esc(j.model)} — ${j.score}%<br>Evidence: ${j.evidence.map(esc).join(" | ")}</p>`).join("")}${r.transcript.map((t) => `<div class="transcript"><strong>User:</strong> ${esc(t.input)}\n<strong>Bot:</strong> ${esc(t.output || t.error || "No response")}\nTime: ${t.seconds ?? "Unknown"} seconds</div>`).join("")}${!active ? `<button data-review="${esc(c.id)}" data-slot="${i}">Add human review</button>` : ""}</article>`).join("")}</div>`,
            )
            .join("")}</details>`,
      )
      .join("");
  document.querySelectorAll("[data-review]").forEach(
    (e) =>
      (e.onclick = async () => {
        const score = prompt("Human-reviewed score (0–100)");
        if (score === null) return;
        const note = prompt("Explain your review (at least 10 characters)");
        if (!note) return;
        try {
          await api(`/api/studio/runs/${runId}/override`, {
            case_id: e.dataset.review,
            bot: Number(e.dataset.slot),
            score: Number(score),
            note,
          });
          await poll();
        } catch (error) {
          tell(error.message);
        }
      }),
  );
  $("audit").innerHTML =
    `<p>Run ID: ${esc(run.id)}. Agreement measured on ${studio.agreement_cases || 0} conversations with distinct valid judge models. Agreement: ${studio.agreement_percent ?? "Not measured"}%. ${esc(studio.agreement_definition || "")}</p><pre>${esc(JSON.stringify(run.audit || [], null, 2))}</pre>`;
  $("downloads").innerHTML =
    `<a href="/api/blackbox/runs/${run.id}/download?format=json">Download JSON</a><a href="/api/blackbox/runs/${run.id}/download?format=pdf">Download PDF</a>`;
}
async function poll() {
  if (!runId || pollBusy) return;
  pollBusy = true;
  try {
    render(await api(`/api/blackbox/runs/${runId}`));
  } catch (error) {
    tell(error.message);
  } finally {
    pollBusy = false;
  }
}
async function loadHistory() {
  const runs = await api("/api/blackbox/runs");
  $("history").innerHTML = runs
    .map(
      (r) =>
        `<button data-run="${esc(r.id)}">${esc(r.targets?.map((b) => b.name).join(" vs ") || r.id)} — ${esc(r.status)}</button>`,
    )
    .join(" ");
  document.querySelectorAll("[data-run]").forEach(
    (e) =>
      (e.onclick = () => {
        runId = e.dataset.run;
        hydrateRequested = true;
        window.history.replaceState(null, "", `?run=${runId}#results`);
        poll();
      }),
  );
}
async function boot() {
  settings = await api("/api/studio/settings");
  $("suite-intro").textContent =
    `${settings.cases.length} categories with ${settings.scenario_sets ? 10 : 1} distinct cases each. Choose repeats per case. Repeats measure consistency, not additional independent coverage.`;
  addBot();
  $("checks").innerHTML = settings.cases
    .map(
      (c) =>
        `<label class="check">${esc(c.name)}<br><small>${esc(settings.descriptions?.[c.category] || "")}</small><br><small>${settings.scenario_sets?.[c.category]?.length || 1} distinct cases × repeats per case</small><br>Repeats <input type="number" min="1" max="20" value="${settings.default_repeats}" data-repeat="${c.category}"></label>`,
    )
    .join("");
  document.querySelectorAll("[data-repeat]").forEach((e) => (e.oninput = planned));
  if (!runId) {
    ["stop", "apply-judges", "resume"].forEach((id) => ($(id).disabled = true));
  }
  const saved = settings.saved_judge;
  let list = settings.judges;
  if (saved.configured)
    list = [
      {
        label: "Saved backend judge",
        model: saved.model,
        url: saved.endpoint,
        local: !saved.external,
      },
      ...list,
    ];
  $("judges").innerHTML = list
    .map(
      (j, i) =>
        `<article class="judge" data-url="${esc(j.url)}" data-local="${j.local}"><label><input data-enabled type="checkbox" ${(j.local && j.model) || (i === 0 && saved.configured && !settings.preferred_local_model) ? "checked" : ""}>${esc(j.label)}</label><span data-status class="pill">Not checked yet</span><details ${(j.local && j.model) || (i === 0 && saved.configured && !settings.preferred_local_model) ? "open" : ""}><summary>Model and key</summary><div class="grid"><label>Model ID<input data-model list="models-${i}" value="${esc(j.model)}" placeholder="Enter a model available to your account"></label><label>API key (leave empty for saved or local)<input data-key type="password" autocomplete="off"></label></div><label><input data-fallback type="checkbox" ${j.local ? "" : "disabled"}>Use as automatic local fallback only</label><button data-discover type="button">Show available models</button><datalist id="models-${i}">${j.local ? settings.ollama_models.map((m) => `<option value="${esc(m)}">`).join("") : ""}</datalist></details></article>`,
    )
    .join("");
  document.querySelectorAll(".judge").forEach((e) => {
    e.querySelector("[data-enabled]").onchange = () => {
      e.querySelector("details").open = e.querySelector("[data-enabled]").checked;
    };
    e.querySelector("[data-discover]").onclick = async () => {
      try {
        const result = await api("/api/studio/models", {
          model: "discovery",
          url: e.dataset.url,
          token: e.querySelector("[data-key]").value || null,
          local: e.dataset.local === "true",
        });
        e.querySelector("datalist").innerHTML = result.models
          .map((m) => `<option value="${esc(m)}">`)
          .join("");
        e.querySelector("[data-status]").textContent =
          result.models.length + " available models. Open the Model ID dropdown.";
      } catch (error) {
        e.querySelector("[data-status]").textContent = error.message;
      }
    };
  });
  $("local-models").innerHTML = settings.ollama_models
    .map((m) => `<option value="${esc(m)}">`)
    .join("");
  $("local-status").textContent = settings.ollama_models.length
    ? "Installed Ollama models: " + settings.ollama_models.join(", ")
    : "Ollama is unavailable or has no installed models. No automatic local fallback can run yet.";
  planned();
  await loadHistory();
  await poll();
}
$("add-bot").onclick = addBot;
$("start").onclick = async () => {
  try {
    const cfg = configuration();
    if (!cfg.judges.length) throw new Error("Choose a judge model first.");
    const result = await api("/api/studio/runs", cfg);
    runId = result.id;
    window.history.replaceState(null, "", `?run=${runId}#results`);
    tell("Evaluation started. Each completed conversation is saved.");
    await poll();
    await loadHistory();
  } catch (error) {
    tell(error.message);
  }
};
$("apply-judges").onclick = async () => {
  try {
    await api(
      `/api/studio/runs/${runId}/judges`,
      { judges: judges(), consent: $("consent").checked },
      "PUT",
    );
    tell("Future cases use the updated judges; in-flight calls keep their original judge.");
  } catch (error) {
    tell(error.message);
  }
};
$("resume").onclick = async () => {
  try {
    await api(`/api/studio/runs/${runId}/resume`, {
      judges: judges(),
      consent: $("consent").checked,
      target_tokens: [...document.querySelectorAll(".bot")].map(
        (e) => e.querySelector("[data-field=token]").value || null,
      ),
    });
    tell("Resuming missing cases. Completed scores and costs remain recorded.");
    await poll();
  } catch (error) {
    tell(error.message);
  }
};
$("stop").onclick = async () => {
  try {
    await api(`/api/blackbox/runs/${runId}/stop`, {});
    await poll();
  } catch (error) {
    tell(error.message);
  }
};
$("references-file").onchange = async (e) => {
  try {
    $("references").value = await e.target.files[0].text();
    JSON.parse($("references").value);
  } catch (error) {
    tell("Invalid reference JSON: " + error.message);
  }
};
boot().catch((error) => tell(error.message));
setInterval(() => {
  if (current && ["queued", "running"].includes(current.status)) poll();
}, 2500);
