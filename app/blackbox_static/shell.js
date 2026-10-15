/* One application, three views. Navigation never submits a test or resets form input. */
(() => {
  const panels = [...document.querySelectorAll("[data-panel]")];
  const links = [...document.querySelectorAll("nav [data-view]")];
  const selector = document.getElementById("selected-run");
  const titles = { evaluate: "Evaluate", results: "Results", governance: "Governance" };
  let runs = [];
  let selected = new URLSearchParams(location.search).get("run");
  let view;
  const emit = (name, detail) => window.dispatchEvent(new CustomEvent(name, { detail }));
  function readView() {
    const hash = location.hash.slice(1);
    if (!hash) return selected ? "results" : "evaluate";
    if (["setup", "checks"].includes(hash)) return "evaluate";
    if (["scores", "costs", "case-results", "usage-section", "bias-panel"].includes(hash))
      return "results";
    return titles[hash] ? hash : view || (selected ? "results" : "evaluate");
  }
  function urlFor(next) {
    const url = new URL(location.href);
    if (selected) url.searchParams.set("run", selected);
    else url.searchParams.delete("run");
    url.hash = next;
    return url;
  }
  function selectRun(id, { notify = true, replace = false } = {}) {
    selected = id || null;
    selector.value = selected || "";
    document.getElementById("run-label").textContent = selected ? "Loading…" : "No run selected";
    window.history[replace ? "replaceState" : "pushState"](null, "", urlFor(view));
    if (notify) emit("studio:run-selected", { id: selected });
    show(view);
  }
  function show(next, focus = false) {
    view = next;
    panels.forEach((panel) => (panel.hidden = panel.dataset.panel !== view));
    links.forEach((link) => {
      if (link.dataset.view === view) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    document.title = `${titles[view]} — AI Agent Studio`;
    document.getElementById("run-toolbar").hidden = view === "evaluate" && !selected;
    if (view !== "evaluate" && !selected && runs[0]) {
      selectRun(runs[0].id, { replace: true });
      return;
    }
    emit("studio:view", { view, id: selected });
    if (focus) {
      document.querySelector(`[data-panel="${view}"] h1`).focus({ preventScroll: true });
      window.scrollTo({ top: 0, behavior: "instant" });
    }
  }
  function navigate(next) {
    window.history.pushState(null, "", urlFor(next));
    show(next, true);
  }
  function restore() {
    const id = new URLSearchParams(location.search).get("run");
    if (id !== selected) {
      selected = id;
      selector.value = id || "";
      emit("studio:run-selected", { id });
    }
    show(readView());
  }
  document.addEventListener("click", (event) => {
    const link = event.target.closest("a[data-view]");
    if (
      !link ||
      event.ctrlKey ||
      event.metaKey ||
      event.shiftKey ||
      event.altKey ||
      event.button !== 0
    )
      return;
    event.preventDefault();
    navigate(link.dataset.view);
  });
  selector.addEventListener("change", () => selectRun(selector.value));
  document.getElementById("refresh-run").onclick = () => emit("studio:refresh", { id: selected });
  window.history.scrollRestoration = "manual";
  window.addEventListener("load", () => {
    if (["", "#evaluate", "#results", "#governance", "#setup"].includes(location.hash)) {
      window.scrollTo({ top: 0, behavior: "instant" });
    }
  });
  window.addEventListener("hashchange", restore);
  window.addEventListener("popstate", restore);
  window.StudioUI = {
    navigate,
    selectRun,
    get view() {
      return view;
    },
    get runId() {
      return selected;
    },
    setRuns(items) {
      runs = items;
      selector.replaceChildren(new Option("Choose a saved run", ""));
      items.forEach((run) => {
        const label = `${run.targets?.map((b) => b.name).join(" vs ") || "Evaluation"} · ${run.status} · ${run.id.slice(0, 8)}`;
        selector.add(new Option(label, run.id));
      });
      if (selected && !items.some((run) => run.id === selected))
        selector.add(new Option(`Run ${selected.slice(0, 8)}`, selected));
      selector.value = selected || "";
      show(view);
    },
    updateRun(run) {
      if (run.id !== selected) return;
      document.getElementById("run-label").textContent = run.status.replaceAll("_", " ");
    },
  };
  show(readView());
})();
