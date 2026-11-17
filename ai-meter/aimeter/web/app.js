"use strict";
// AI-Meter dashboard. All data is rendered with textContent (never innerHTML)
// so chat titles can't inject markup.

const TOKEN = document.querySelector('meta[name="aimeter-token"]').content;
const BUILTIN = {
  claude_web: "Claude (browser)", claude_code: "Claude Code (this PC)",
  chatgpt_web: "ChatGPT (browser)", codex: "Codex CLI (this PC)", minimax: "MiniMax Code",
};
const COVERS = {
  claude: "Covers claude.ai (chats + Claude Code in the browser) and Claude Code on this PC",
  chatgpt: "Covers chatgpt.com and Codex",
  minimax: "Covers the MiniMax Code desktop app",
};
const TOOL_COLORS = { claude: "var(--t-claude)", chatgpt: "var(--t-chatgpt)", minimax: "var(--t-minimax)" };
const EXTRA_COLORS = ["var(--t-c1)", "var(--t-c2)", "var(--t-c3)"];
let report = null, state = null, config = null;
const open = new Set();

function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "text") el.textContent = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false)
    el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  return el;
}
const $ = (id) => document.getElementById(id);

async function api(path, body) {
  const opts = { headers: { "X-AIMeter-Token": TOKEN } };
  if (body !== undefined) {
    opts.method = "POST";
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json();
}

function money(v, cur) {
  try { return new Intl.NumberFormat(undefined, { style: "currency", currency: cur || "USD", maximumFractionDigits: 2 }).format(v || 0); }
  catch { return `${(v || 0).toFixed(2)} ${cur || ""}`; }
}
function dur(sec) {
  sec = Math.round(sec || 0);
  if (sec < 60) return sec ? "<1m" : "0m";
  const hrs = Math.floor(sec / 3600), m = Math.round((sec % 3600) / 60);
  return hrs ? `${hrs}h ${String(m).padStart(2, "0")}m` : `${m}m`;
}
function until(ts) {
  if (!ts) return "reset time unknown";
  const s = ts - Date.now() / 1000;
  if (s <= 0) return "resetting now";
  const d = Math.floor(s / 86400), hr = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60);
  return "resets in " + (d ? `${d}d ${hr}h` : hr ? `${hr}h ${String(m).padStart(2, "0")}m` : `${m}m`);
}
function bar(pct, cls) {
  const fill = h("span");
  fill.style.width = `${Math.max(0, Math.min(100, pct || 0)).toFixed(1)}%`;
  return h("div", { class: `bar ${cls || ""}`, role: "img", "aria-label": `${(pct || 0).toFixed(0)} percent` }, fill);
}
function ago(ts) {
  if (!ts) return "never";
  const s = Date.now() / 1000 - ts;
  return s < 90 ? "just now" : s < 3600 ? `${Math.round(s / 60)}m ago` : s < 86400 ? `${Math.round(s / 3600)}h ago` : `${Math.round(s / 86400)}d ago`;
}
function colorFor(subId) {
  if (TOOL_COLORS[subId]) return TOOL_COLORS[subId];
  const ids = report.subscriptions.map((s) => s.id).filter((id) => !TOOL_COLORS[id]);
  return EXTRA_COLORS[Math.max(0, ids.indexOf(subId)) % EXTRA_COLORS.length];
}

// ---------------------------------------------------------------- tools (overview)
function renderOverview() {
  const cur = report.currency;
  $("k-paid").textContent = money(report.total_cost, cur);
  $("k-time").textContent = dur(report.total_seconds);
  $("k-rate").textContent = report.total_seconds >= 60 && report.total_cost
    ? money(report.total_cost / (report.total_seconds / 3600), cur) : "–";
  $("k-unassigned").textContent = `${report.unassigned_pct.toFixed(0)}% of time`;

  const box = $("plans");
  box.replaceChildren();
  for (const s of state.subscriptions) {
    const rep = report.subscriptions.find((x) => x.id === s.id) || { projects: [] };
    const card = h("div", { class: "card tool", tabindex: 0, role: "button", "aria-expanded": String(open.has(s.id)) });
    card.style.setProperty("--tc", colorFor(s.id));
    const toggle = () => { open.has(s.id) ? open.delete(s.id) : open.add(s.id); renderOverview(); };
    card.addEventListener("click", (e) => { if (!e.target.closest("a,button,input")) toggle(); });
    card.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } });

    card.append(h("div", { class: "head" }, h("h3", { text: s.name }), h("span", { class: "money", text: `${money(s.monthly_cost, cur)}/mo` })));
    if (!s.windows.length) card.append(h("div", { class: "nolimit", text: s.no_plan_hint }));
    for (const w of s.windows) {
      const left = w.left_pct ?? 0;
      card.append(h("div", { class: "win" },
        h("div", { class: "row" },
          h("span", {}, h("span", { class: `left ${left <= 10 ? "low" : left <= 30 ? "mid" : ""}`, text: `${left.toFixed(0)}% left` }),
            ` · ${w.label}`),
          h("span", { class: "hint", text: until(w.resets_at) })),
        bar(w.used_pct, w.used_pct >= 90 ? "bad" : w.used_pct >= 70 ? "warn" : ""),
        h("div", { class: "status", text: `${(w.used_pct ?? 0).toFixed(0)}% used · from ${w.source} · updated ${ago(w.observed_at)}` +
          (w.month_peak != null ? ` · peak this month ${w.month_peak.toFixed(0)}%` : "") })));
    }
    card.append(h("div", { class: "stats" },
      h("div", {}, h("b", { text: dur(s.today_seconds) }), h("span", { text: "today" })),
      h("div", {}, h("b", { text: dur(rep.seconds) }), h("span", { text: "this month" })),
      h("div", {}, h("b", { text: rep.cost_per_hour ? money(rep.cost_per_hour, cur) : "–" }), h("span", { text: "per hour" }))));
    if (s.credits_remaining != null) card.append(h("div", { class: "status", text: `Credits remaining: ${Number(s.credits_remaining).toLocaleString()}` }));

    if (open.has(s.id)) {
      const rows = rep.projects.length ? rep.projects.map((p) => h("tr", {},
        h("td", { text: p.project }), h("td", { class: "num", text: dur(p.seconds) }),
        h("td", { class: "num", text: money(p.cost, cur) }), h("td", { class: "num", text: `${p.pct_cost.toFixed(0)}%` })))
        : [h("tr", {}, h("td", { colspan: 4, class: "muted", text: "No activity this month yet." }))];
      card.append(h("table", { class: "mini" },
        h("thead", {}, h("tr", {}, h("th", { text: "Project" }), h("th", { class: "num", text: "Time" }), h("th", { class: "num", text: "Cost" }), h("th", { class: "num", text: "Share" }))),
        h("tbody", {}, rows)));
      for (const t of s.tools) {
        const known = t.ok !== undefined;
        card.append(h("div", { class: "status" }, h("span", { class: known ? (t.ok ? "ok" : "bad") : "", text: known && t.ok ? "● " : "○ " }),
          `${t.name}: ${t.message || (t.id.endsWith("_web") ? "waiting for the browser extension" : "not checked yet")}`));
      }
      card.append(h("div", { class: "expand-hint", text: "Click to close" }));
    } else {
      const n = rep.projects.filter((p) => p.project !== "Unused subscription").length;
      card.append(h("div", { class: "expand-hint", text: n ? `Show ${n} project${n === 1 ? "" : "s"} →` : "No projects this month yet" }));
    }
    box.append(card);
  }

  const banner = $("banner");
  const msgs = [];
  if (state.setup_needed) msgs.push("Enter what you pay per month under Settings → Tools and prices to see cost per project.");
  if (!state.extension || !state.extension.ok) msgs.push("Browser extension not connected yet: Claude and ChatGPT limits and browser time appear once it is paired (Settings → Browser extension pairing).");
  banner.hidden = !msgs.length;
  banner.replaceChildren(...msgs.map((m) => h("div", { text: m })));
}

// ---------------------------------------------------------------- projects
function renderProjects() {
  const cur = report.currency;
  const subs = report.subscriptions.filter((s) => s.tools.length);
  $("legend").replaceChildren(...subs.map((s) => {
    const sw = h("i"); sw.style.background = colorFor(s.id);
    return h("span", {}, sw, s.name);
  }));
  const tb = $("projects").querySelector("tbody");
  tb.replaceChildren();
  const rows = report.projects;
  if (!rows.length) tb.append(h("tr", {}, h("td", { colspan: 6, class: "empty", text: "No activity recorded for this month yet." })));
  const names = report.projects.map((p) => p.project).filter((n) => n !== "Unassigned" && n !== "Unused subscription");
  for (const p of rows) {
    const stack = h("div", { class: "stack", role: "img",
      "aria-label": Object.entries(p.by_sub).map(([sid, v]) => `${sid} ${dur(v.seconds)}`).join(", ") });
    const tip = [];
    for (const s of subs) {
      const v = p.by_sub[s.id];
      if (!v || !v.seconds) continue;
      const seg = h("span");
      seg.style.width = `${(100 * v.seconds / Math.max(1, p.seconds)).toFixed(2)}%`;
      seg.style.background = colorFor(s.id);
      stack.append(seg);
      tip.push(`${s.name}: ${dur(v.seconds)} · ${money(v.cost, cur)}`);
    }
    stack.title = tip.join("\n");
    let merge = h("span", { class: "muted", text: "–" });
    if (p.project !== "Unassigned" && p.project !== "Unused subscription") {
      merge = h("select", { "aria-label": `Merge ${p.project} into another project` },
        h("option", { value: "", text: "—" }),
        names.filter((n) => n !== p.project).map((n) => h("option", { value: n, text: n })));
      merge.addEventListener("change", async () => {
        if (!merge.value) return;
        const aliases = { ...(config.project_aliases || {}) };
        aliases[p.project] = merge.value;
        config = await api("/api/config", { project_aliases: aliases });
        await load(false);
      });
    }
    tb.append(h("tr", {},
      h("td", { text: p.project }),
      h("td", { title: tip.join("\n") }, stack, h("div", { class: "status", text: tip.join(" · ") })),
      h("td", { class: "num", text: dur(p.seconds) }),
      h("td", { class: "num", text: money(p.cost, cur) }),
      h("td", { class: "num", text: `${p.pct_cost.toFixed(1)}%` }),
      h("td", {}, merge)));
  }
}

// ---------------------------------------------------------------- chats
function renderChats() {
  const cur = report.currency;
  const q = $("search").value.trim().toLowerCase();
  const only = $("only-unassigned").checked;
  $("joblist").replaceChildren(...report.known_jobs.map((j) => h("option", { value: j })));
  const tb = $("chats").querySelector("tbody");
  tb.replaceChildren();
  const rows = report.chats.filter((c) => (!only || c.job === "Unassigned") &&
    (!q || `${c.title} ${c.project} ${c.job} ${c.tool_name}`.toLowerCase().includes(q)));
  if (!rows.length) tb.append(h("tr", {}, h("td", { colspan: 6, class: "empty", text: "Nothing to show." })));
  for (const c of rows.slice(0, 500)) {
    const input = h("input", { class: "job", list: "joblist", value: c.job === "Unassigned" ? "" : c.job,
      placeholder: "Unassigned", "aria-label": `Project for ${c.title || c.chat_id}`, maxlength: 80,
      title: c.job_source === "manual" ? "Set by you" : c.job_source === "rule" ? "Set by a rule" : c.job_source === "folder" ? "Detected automatically" : "" });
    input.addEventListener("change", async () => {
      await api("/api/assign", { tool: c.tool, chat_id: c.chat_id, job: input.value.trim() });
      await load(false);
    });
    tb.append(h("tr", {},
      h("td", { text: c.tool_name }),
      h("td", { class: "title", title: c.title || c.chat_id, text: c.title || c.chat_id }),
      h("td", { class: "title muted", title: c.project, text: c.project }),
      h("td", { class: "num", text: dur(c.seconds) }),
      h("td", { class: "num", text: c.sub ? money(c.cost, cur) : "–" }),
      h("td", {}, input)));
  }
}

// ---------------------------------------------------------------- settings
function field(label, input) { return h("label", {}, label, input); }
function removeBtn(fn) { return h("button", { type: "button", class: "link", onclick: fn, text: "Remove" }); }
function price(obj) {
  return h("input", { type: "number", min: 0, step: "0.01", value: obj.monthly_cost,
    oninput: (e) => (obj.monthly_cost = Number(e.target.value) || 0) });
}

function renderSettings() {
  const subs = $("subs"); subs.replaceChildren();
  for (const s of config.subscriptions) {
    if (s.id.startsWith("custom_")) continue;
    subs.append(h("div", { class: "editrow" },
      field("Name", h("input", { value: s.name, maxlength: 80, oninput: (e) => (s.name = e.target.value) })),
      field("Monthly price", price(s)),
      field("Split cost by", h("select", { onchange: (e) => (s.basis = e.target.value) },
        h("option", { value: "time", text: "time spent", selected: s.basis === "time" }),
        h("option", { value: "tokens", text: "tokens used (this-PC tools only)", selected: s.basis === "tokens" }))),
      h("span", { class: "covers", text: COVERS[s.id] || "" })));
  }

  const customs = $("customs"); customs.replaceChildren();
  config.custom_tools.forEach((t, i) => {
    customs.append(h("div", { class: "editrow" },
      field("Name", h("input", { value: t.name, maxlength: 80, oninput: (e) => (t.name = e.target.value) })),
      field("Monthly price", price(t)),
      field("Websites (comma separated)", h("input", { value: t.sites.join(", "), placeholder: "perplexity.ai", oninput: (e) => (t.sites = e.target.value.split(",").map((x) => x.trim()).filter(Boolean)) })),
      field("Desktop apps (Windows)", h("input", { value: t.apps.join(", "), placeholder: "cursor.exe", oninput: (e) => (t.apps = e.target.value.split(",").map((x) => x.trim()).filter(Boolean)) })),
      removeBtn(() => { config.custom_tools.splice(i, 1); renderSettings(); })));
  });

  const tools = { ...BUILTIN };
  for (const t of config.custom_tools) if (t.id) tools[t.id] = t.name;
  const rules = $("rules"); rules.replaceChildren();
  config.rules.forEach((r, i) => {
    rules.append(h("div", { class: "editrow" },
      field("If", h("select", { onchange: (e) => (r.field = e.target.value) },
        ["any", "title", "project"].map((f) => h("option", { value: f, text: f === "any" ? "title or project" : f, selected: r.field === f })))),
      field("contains", h("input", { value: r.contains, maxlength: 120, oninput: (e) => (r.contains = e.target.value) })),
      field("in tool", h("select", { onchange: (e) => (r.tool = e.target.value) },
        h("option", { value: "", text: "any tool", selected: !r.tool }),
        Object.entries(tools).map(([id, label]) => h("option", { value: id, text: label, selected: r.tool === id })))),
      field("→ project", h("input", { value: r.job, maxlength: 80, list: "joblist", oninput: (e) => (r.job = e.target.value) })),
      removeBtn(() => { config.rules.splice(i, 1); renderSettings(); })));
  });

  $("idle").value = config.idle_cap_minutes;
  $("currency").value = config.currency;
  $("homeun").checked = config.home_folder_is_unassigned;
  $("port").value = config.port;
  $("token").value = TOKEN;
}

async function saveSettings() {
  config.idle_cap_minutes = Number($("idle").value) || 5;
  config.currency = $("currency").value.trim().toUpperCase() || "USD";
  config.home_folder_is_unassigned = $("homeun").checked;
  try {
    config = await api("/api/config", config);
    $("saved").textContent = "Saved.";
    await api("/api/refresh", {});
    await load(false);
  } catch (e) { $("saved").textContent = `Could not save: ${e.message}`; }
  setTimeout(() => ($("saved").textContent = ""), 4000);
}

// ---------------------------------------------------------------- wiring
function months() {
  const sel = $("month");
  const now = new Date();
  for (let i = 0; i < 13; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const v = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    sel.append(h("option", { value: v, text: d.toLocaleDateString(undefined, { month: "long", year: "numeric" }) }));
  }
}

async function load(withConfig = true) {
  const m = $("month").value;
  [report, state] = await Promise.all([api(`/api/report?month=${encodeURIComponent(m)}`), api("/api/state")]);
  if (withConfig || !config) { config = await api("/api/config"); renderSettings(); }
  renderOverview();
  renderProjects();
  renderChats();
}

async function exportCsv(e) {
  e.preventDefault();
  const r = await fetch(`/api/export.csv?month=${encodeURIComponent($("month").value)}`, { headers: { "X-AIMeter-Token": TOKEN } });
  const blob = await r.blob();
  const a = h("a", { href: URL.createObjectURL(blob), download: `ai-meter-${$("month").value}.csv` });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

document.addEventListener("DOMContentLoaded", () => {
  months();
  for (const b of document.querySelectorAll(".tabs button")) {
    b.addEventListener("click", () => {
      for (const o of document.querySelectorAll(".tabs button")) o.setAttribute("aria-selected", String(o === b));
      for (const s of document.querySelectorAll(".tab")) s.hidden = s.id !== `tab-${b.dataset.tab}`;
    });
  }
  $("month").addEventListener("change", () => load(false));
  $("refresh").addEventListener("click", async () => { await api("/api/refresh", {}); setTimeout(() => load(false), 1500); });
  $("export").addEventListener("click", exportCsv);
  $("search").addEventListener("input", renderChats);
  $("only-unassigned").addEventListener("change", renderChats);
  $("add-custom").addEventListener("click", () => { config.custom_tools.push({ name: "New tool", monthly_cost: 0, sites: [], apps: [] }); renderSettings(); });
  $("add-rule").addEventListener("click", () => { config.rules.push({ field: "any", contains: "", tool: "", job: "" }); renderSettings(); });
  $("save").addEventListener("click", saveSettings);
  $("load-diag").addEventListener("click", async () => {
    const d = await api("/api/diagnostics");
    $("diag").textContent = JSON.stringify(d, null, 2);
    $("diag").hidden = false;
  });
  $("copy-token").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(TOKEN); $("copy-token").textContent = "Copied"; }
    catch { $("token").type = "text"; $("token").select(); }
    setTimeout(() => ($("copy-token").textContent = "Copy"), 2000);
  });
  load().catch((e) => { $("banner").hidden = false; $("banner").textContent = `Could not load data: ${e.message}`; });
  setInterval(() => {
    const busy = ["INPUT", "SELECT"].includes(document.activeElement?.tagName);
    if (document.visibilityState === "visible" && !busy) load(false).catch(() => {});
  }, 60000);
});
