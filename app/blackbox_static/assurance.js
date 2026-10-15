/* Evidence-mode controller. Keys remain in password fields and requests only. */
(() => {
  let id = new URLSearchParams(location.search).get("assessment"),
    current,
    busy = false,
    tab = "combined";
  const root = $("assurance-results"),
    cards = new Map();
  const kinds = {
    system_prompt: "System prompt (.txt)",
    config: "Configuration (.json/.yaml)",
    tools: "Tools (.json)",
    knowledge: "Knowledge (.txt/.md)",
    logs: "Logs / OTel (.json/.jsonl)",
    code: "Source (.zip)",
  };
  const active = (run) => ["running", "queued"].includes(run?.status);
  function select(value) {
    id = value || null;
    const url = new URL(location.href);
    if (id) url.searchParams.set("assessment", id);
    else url.searchParams.delete("assessment");
    window.history.replaceState(null, "", url);
  }
  function addInputs() {
    for (const card of document.querySelectorAll(".bot")) {
      if (cards.has(card)) continue;
      cards.set(card, {});
      card.insertAdjacentHTML(
        "beforeend",
        `<details><summary>Optional Gray / White inputs</summary><p>Private inputs use a local judge by default. Code is read, never executed.</p>${Object.entries(
          kinds,
        )
          .map(
            ([kind, label]) =>
              `<label>${esc(label)}<input type="file" data-private="${kind}"></label><small data-ready="${kind}"></small>`,
          )
          .join(
            "",
          )}<label>Public GitHub source repository<input data-repository placeholder="https://github.com/owner/repo/tree/main"></label><button type="button" data-source>Import source</button><button type="button" data-canary>Attach updated canary logs</button></details>`,
      );
      card.querySelectorAll("[data-private]").forEach(
        (input) =>
          (input.onchange = async () => {
            try {
              if (!input.files.length) return;
              const body = new FormData();
              body.append("file", input.files[0]);
              const response = await fetch(`/api/assurance/inputs/${input.dataset.private}`, {
                method: "POST",
                headers: { "X-Studio-Request": "1" },
                body,
              });
              const result = await response.json();
              if (!response.ok)
                throw new Error(
                  typeof result.detail === "string" ? result.detail : "Upload failed",
                );
              cards.get(card)[input.dataset.private] = result.id;
              card.querySelector(`[data-ready=${input.dataset.private}]`).textContent =
                `Input ready for ${result.unlocks} checks; tools checked during run. Hash ${result.sha256.slice(0, 8)}`;
            } catch (error) {
              tell(error.message);
            }
          }),
      );
      card.querySelector("[data-source]").onclick = async () => {
        try {
          const result = await api("/api/assurance/repository", {
            url: card.querySelector("[data-repository]").value.trim(),
            ownership_confirmed: $("ownership").checked,
          });
          cards.get(card).code = result.id;
          card.querySelector("[data-ready=code]").textContent =
            `${result.unlocks} source checks have their input.`;
        } catch (error) {
          tell(error.message);
        }
      };
      card.querySelector("[data-canary]").onclick = async () => {
        try {
          if (!id || !cards.get(card).logs)
            throw new Error("Select the saved assessment and upload its new logs first.");
          await api(`/api/assurance/runs/${id}/canary-logs`, {
            bot: [...document.querySelectorAll(".bot")].indexOf(card),
            logs: cards.get(card).logs,
          });
          await refresh();
        } catch (error) {
          tell(error.message);
        }
      };
    }
  }
  function request() {
    const modes = [...document.querySelectorAll("[data-mode]:checked")].map((e) => e.dataset.mode);
    if (!modes.length) throw new Error("Select at least one test mode.");
    const cfg = configuration(),
      inputs = [...document.querySelectorAll(".bot")].map((card) => cards.get(card) || {});
    cfg.targets.forEach((target, index) => {
      if (!target.url && inputs[index].code) {
        target.kind = "zip";
        target.archive_id = inputs[index].code;
      }
    });
    return {
      settings: cfg,
      modes,
      inputs,
      ownership_confirmed: $("ownership").checked,
      private_cloud_opt_in: $("private-cloud").checked,
      upload_retention_days: Number($("upload-retention").value),
    };
  }
  function show(next) {
    tab = current && next !== "combined" && !current.modes.includes(next) ? "combined" : next;
    root
      .querySelectorAll("[data-assurance-tab]")
      .forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.assuranceTab === tab)));
    [...$("results").children].forEach((e) => {
      if (e !== root && !e.classList.contains("page-heading")) e.hidden = tab !== "black";
    });
    $("assurance-content").hidden = tab === "black";
    if (current && tab !== "black") render();
  }
  function render() {
    const run = current,
      c = run.combined,
      costs = run.assurance_costs;
    const headings = $("assurance-hinglish").checked
      ? ["Kya check kiya", "Kya mila", "Kyun zaroori hai", "Kaise theek karein"]
      : ["What we checked", "What we found", "Why it matters", "How to fix it"];
    const opened = new Set(
      [...root.querySelectorAll("details[open][data-finding]")].map((e) => e.dataset.finding),
    );
    const rows = run.findings
      .filter((f) => tab === "combined" || f.mode === tab)
      .sort(
        (a, b) =>
          ["Critical", "High", "Medium", "Low", "Pass"].indexOf(a.severity) -
          ["Critical", "High", "Medium", "Low", "Pass"].indexOf(b.severity),
      );
    const matrix = table(
      ["Bot", "Category", ...run.modes, "Classification", "Confidence"],
      c.categories.map((r) => [
        String(r.bot + 1),
        esc(r.category),
        ...run.modes.map((m) => esc(r.cells[m])),
        `<span title="${esc(r.reason)}">${esc(r.label)}</span>`,
        r.confidence,
      ]),
    );
    const sourceChecks = run.findings.filter((f) => f.mode === "white");
    const sourceSummary = sourceChecks.length
      ? `<p><strong>White-box execution: ${sourceChecks.filter((f) => f.details?.scanner_completed).length}/${sourceChecks.length} checks completed by scanners.</strong> ${sourceChecks.filter((f) => f.verdict === "not_tested" && f.details?.scanner_completed).length} completed checks have insufficient control evidence and remain Not tested. Exists means a declaration was found; it does not prove the control works.</p>`
      : "";
    $("assurance-content").innerHTML =
      `<p><strong>${esc(c.assurance)} evidence modes · ${esc(c.verdict)}</strong></p><p>${esc(c.reason)} ${esc(c.assurance_note)}</p><p>${esc(run.status)} · ${esc(
        Object.entries(run.engine_status)
          .map(([mode, state]) => `${mode}: ${state}`)
          .join("; "),
      )} · ${run.duration_seconds ?? "Running"} seconds</p><p>${c.integrity.accounted}/${c.integrity.planned} checks recorded; ${c.integrity.not_tested} Not tested. Audit: ${run.audit_integrity?.valid ? "Intact" : "Needs review"}. ${c.review_queue.length} findings need human review.</p>${costs ? `<p>Bot calls ${costMoney(costs.bot)} · Judge calls ${costMoney(costs.evaluation)}. Bot tokens ${costs.bot.input_tokens + costs.bot.output_tokens}; judge tokens ${costs.evaluation.input_tokens + costs.evaluation.output_tokens}. Historical uploaded telemetry is separate.</p>` : ""}<p><abbr title="Chat behavior only">Black</abbr> · <abbr title="Declarations, knowledge and traces">Gray</abbr> · <abbr title="Read-only source scans">White</abbr> · <abbr title="A control declaration does not prove effectiveness">Exists</abbr></p>${tab === "combined" ? matrix : ""}${rows
        .map((f) => {
          const key = `${f.bot}:${f.mode}:${f.test_id}`;
          return `<details data-finding="${esc(key)}" ${opened.has(key) ? "open" : ""}><summary>Bot ${f.bot + 1} · ${esc(f.test_id)} · ${esc(f.verdict)} · ${f.severity} · ${f.confidence} confidence ${f.overridden ? '<span class="pill">Overridden</span>' : ""}</summary>${[f.checked, f.explanation, f.consequence, f.fix].map((text, i) => `<p><strong>${headings[i]}:</strong> ${esc(text)}</p>`).join("")}${$("assurance-hinglish").checked ? "<p>Original judge reason aur evidence ki language preserve ki gayi hai.</p>" : ""}${f.evidence.length ? f.evidence.map((e) => `<p>${esc(e.file || e.source_id || e.kind)}${e.line ? ":" + e.line : ""}</p><blockquote>${esc(e.excerpt)}</blockquote>`).join("") : "<p>No supporting evidence was obtained.</p>"}${f.tool ? `<p>${esc(f.tool)} ${esc(f.tool_version)}</p>` : ""}${f.review && !active(run) ? `<button type="button" data-review="${esc(key)}">Review / false positive</button>` : ""}</details>`;
        })
        .join(
          "",
        )}<details><summary>Governance and informational mapping</summary><p>Private cloud opt-in: ${run.private_cloud_opt_in ? "On" : "Off: local only"}. Uploads: ${run.uploads_deleted ? "Deleted" : "Retained per setting; shared inputs may remain for another assessment"}.</p><pre>${esc(JSON.stringify({ cards: run.model_cards, inputs: run.input_hashes, mapping: c.mapping, audit: run.audit }, null, 2))}</pre></details>`;
    if (sourceSummary) $("assurance-content").insertAdjacentHTML("afterbegin", sourceSummary);
    root.querySelectorAll("[data-review]").forEach(
      (button) =>
        (button.onclick = async () => {
          const reason = prompt(
            "Write why this is a false positive, or why you accept the finding:",
          );
          if (!reason) return;
          const false_positive = confirm(
              "Mark as false positive? Cancel keeps its score and records the review.",
            ),
            [bot, mode, ...test] = button.dataset.review.split(":");
          try {
            await api(`/api/assurance/runs/${id}/review`, {
              bot: Number(bot),
              mode,
              test_id: test.join(":"),
              false_positive,
              reason,
            });
            await refresh();
          } catch (error) {
            tell(error.message);
          }
        }),
    );
  }
  async function refresh() {
    if (!id || busy) return;
    const selected = id;
    busy = true;
    try {
      const run = await api(`/api/assurance/runs/${selected}`);
      if (id !== selected) return;
      current = run;
      root.hidden = false;
      root
        .querySelectorAll("[data-assurance-tab]")
        .forEach(
          (b) =>
            (b.disabled =
              b.dataset.assuranceTab !== "combined" && !run.modes.includes(b.dataset.assuranceTab)),
        );
      if (run.blackbox_run_id && runId !== run.blackbox_run_id) {
        runId = run.blackbox_run_id;
        window.StudioUI.selectRun(runId, { notify: false, replace: true });
        await poll();
      }
      $("assurance-status").textContent = `Assessment ${run.id.slice(0, 8)} · ${run.status}`;
      if (active(run)) {
        $("apply-judges").disabled = false;
        $("apply-judges").hidden = false;
      }
      if (tab !== "black") render();
      window.dispatchEvent(new CustomEvent("assurance:updated"));
    } catch (error) {
      tell(error.message);
    } finally {
      busy = false;
    }
  }
  async function historyList() {
    const runs = await api("/api/assurance/runs");
    $("assurance-saved").innerHTML =
      '<option value="">Select assessment</option>' +
      runs
        .map(
          (r) =>
            `<option value="${esc(r.id)}" ${r.id === id ? "selected" : ""}>${esc(r.modes.join(" + "))} · ${esc(r.status)} · ${r.id.slice(0, 8)}</option>`,
        )
        .join("");
  }
  $("start").addEventListener(
    "click",
    async (event) => {
      event.preventDefault();
      event.stopImmediatePropagation();
      try {
        $("start").disabled = true;
        const run = await api("/api/assurance/runs", request());
        select(run.id);
        window.StudioUI.navigate("results");
        await refresh();
        show("combined");
        tell("Assessment started. Missing inputs/tools are Not tested.");
        await historyList();
      } catch (error) {
        tell(error.message);
      } finally {
        $("start").disabled = false;
      }
    },
    true,
  );
  $("apply-judges").addEventListener(
    "click",
    async (event) => {
      if (!id) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      try {
        await api(
          `/api/assurance/runs/${id}/judges`,
          { judges: judges(), consent: $("consent").checked },
          "PUT",
        );
        tell("Future cases use updated judges; private cloud consent stays unchanged.");
      } catch (error) {
        tell(error.message);
      }
    },
    true,
  );
  $("assurance-stop").onclick = async () => {
    try {
      if (id) {
        await api(`/api/assurance/runs/${id}/stop`, {});
        await refresh();
      }
    } catch (error) {
      tell(error.message);
    }
  };
  $("assurance-resume").onclick = async () => {
    try {
      await api(`/api/assurance/runs/${id}/resume`, request());
      tell("Resuming saved evidence; re-upload deleted inputs if requested.");
      await refresh();
    } catch (error) {
      tell(error.message);
    }
  };
  $("assurance-reproduce").onclick = async () => {
    try {
      if (!current) return;
      const data = request(),
        draft = data.settings;
      data.settings = { ...current.config, judges: draft.judges };
      data.settings.targets = current.config.targets.map((t, i) => ({
        ...t,
        token: draft.targets[i]?.url === t.url ? draft.targets[i].token : null,
      }));
      const result = await api(`/api/assurance/runs/${id}/reproduce`, data);
      select(result.id);
      await refresh();
      await historyList();
    } catch (error) {
      tell(error.message);
    }
  };
  $("assurance-delete").onclick = async () => {
    if (
      !id ||
      !confirm(
        "Delete this assessment/private inputs? Linked Black history stays separately deletable.",
      )
    )
      return;
    try {
      await api(`/api/assurance/runs/${id}`, {}, "DELETE");
      select(null);
      current = null;
      root.hidden = true;
      window.dispatchEvent(new CustomEvent("assurance:updated"));
      await historyList();
    } catch (error) {
      tell(error.message);
    }
  };
  for (const format of ["json", "pdf"])
    $("assurance-" + format).onclick = () => {
      if (id) location.href = `/api/assurance/runs/${id}/download?format=${format}`;
    };
  root
    .querySelectorAll("[data-assurance-tab]")
    .forEach((b) => (b.onclick = () => show(b.dataset.assuranceTab)));
  $("assurance-hinglish").onchange = () => current && render();
  $("assurance-saved").onchange = async () => {
    select($("assurance-saved").value);
    await refresh();
    show("combined");
  };
  new MutationObserver(addInputs).observe($("bots"), { childList: true });
  addInputs();
  window.addEventListener("studio:run-selected", (event) => {
    if (current && event.detail.id !== current.blackbox_run_id) {
      select(null);
      current = null;
      root.hidden = true;
      show("black");
      window.dispatchEvent(new CustomEvent("assurance:updated"));
    }
  });
  window.addEventListener("studio:view", () => id && refresh());
  setInterval(() => active(current) && refresh(), 3000);
  window.AssuranceUI = {
    get current() {
      return current;
    },
    get id() {
      return id;
    },
    refresh,
  };
  historyList()
    .then(refresh)
    .then(() => id && show("combined"))
    .catch((error) => tell(error.message));
})();
