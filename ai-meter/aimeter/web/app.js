"use strict";
// AI-Meter dashboard. All data is rendered with textContent (never innerHTML)
// so chat titles can't inject markup.

const TOKEN = document.querySelector('meta[name="aimeter-token"]').content;
const BUILTIN = {
  claude_web: "Claude (browser)", claude_code: "Claude Code (this PC)",
  chatgpt_web: "ChatGPT (browser)", codex: "Codex CLI (this PC)", minimax: "MiniMax Code",
};
let report = null, state = null, config = null;

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
  if (!ts) return "";
  const s = ts - Date.now() / 1000;
  if (s <= 0) return "reset due";
  const d = Math.floor(s / 86400), hr = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60);
  return "resets in " + (d ? `${d}d ${hr}h` : hr ? `${hr}h ${m}m` : `${m}m`);
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

// ---------------------------------------------------------------- overview
function renderOverview() {
  const cur = report.currency;
  $("k-paid").textContent = money(report.total_cost, cur);
  $("k-time").textContent = dur(report.total_seconds);
  $("k-rate").textContent = report.total_seconds >= 60 && report.total_cost
    ? money(report.total_cost / (report.total_seconds / 3600), cur) : "–";
  $("k-unassigned").textContent = `${report.unassigned_pct.toFixed(0)}% of time`;

  const subName = Object.fromEntries(report.subscriptions.map((s) => [s.id, s.name]));
  const tb = $("jobs").querySelector("tbody");
  tb.replaceChildren();
  if (!report.jobs.length) tb.append(h("tr", {}, h("td", { colspan: 6, class: "empty", text: "No activity recorded for this month yet." })));
  for (const j of report.jobs) {
    tb.append(h("tr", {},
      h("td", { text: j.job }),
      h("td", {}, bar(j.pct_cost)),
      h("td", { class: "num", text: `${j.pct_cost.toFixed(1)}%` }),
      h("td", { class: "num", text: dur(j.seconds) }),
      h("td", { class: "num", text: money(j.cost, cur) }),
      h("td", {}, Object.entries(j.by_sub).map(([sid, v]) => h("span", { class: "chip", text: `${subName[sid] || sid} ${money(v.cost, cur)}` })))));
  }

  const box = $("plans");
  box.replaceChildren();
  for (const s of state.subscriptions) {
    const rep = report.subscriptions.find((x) => x.id === s.id) || {};
    const card = h("div", { class: "card" },
      h("h3", { text: s.name }),
      h("div", { class: "sub", text: `${money(s.monthly_cost, cur)}/month · today ${dur(s.today_seconds)} · this month ${dur(rep.seconds)}` +
        (rep.cost_per_hour ? ` · ${money(rep.cost_per_hour, cur)}/hour` : "") }));
    if (!s.windows.length) card.append(h("div", { class: "hint", text: "No plan % available for this subscription (see status below)." }));
    for (const w of s.windows) {
      const pct = w.used_pct ?? 0;
      card.append(h("div", { class: "win" },
        h("div", { class: "row" }, h("span", { text: `${w.label} · ${until(w.resets_at)}` }), h("strong", { text: `${pct.toFixed(0)}% used` })),
        bar(pct, pct >= 90 ? "bad" : pct >= 70 ? "warn" : ""),
        h("div", { class: "status", text: `from ${w.source} · updated ${ago(w.observed_at)}` + (w.month_peak != null ? ` · peak this month ${w.month_peak.toFixed(0)}%` : "") })));
    }
    if (s.credits_remaining != null) card.append(h("div", { class: "status", text: `Credits remaining: ${Number(s.credits_remaining).toLocaleString()}` }));
    for (const t of s.tools) {
      const known = t.ok !== undefined;
      card.append(h("div", { class: "status" }, h("span", { class: known ? (t.ok ? "ok" : "bad") : "", text: known ? (t.ok ? "● " : "○ ") : "○ " }),
        `${t.name}: ${t.message || (t.id.endsWith("_web") ? "waiting for the browser extension" : "not checked yet")}`));
    }
    box.append(card);
  }

  const banner = $("banner");
  const msgs = [];
  if (state.setup_needed) msgs.push("Enter what you pay per month under Settings → Subscriptions to see cost per job.");
  if (!state.extension || !state.extension.ok) msgs.push("Browser extension not connected yet: Claude/ChatGPT browser time and Claude plan % will appear once it is paired.");
  banner.hidden = !msgs.length;
  banner.replaceChildren(...msgs.map((m) => h("div", { text: m })));
}

// ---------------------------------------------------------------- chats
function renderChats() {
  const cur = report.currency;
  const q = $("search").value.trim().toLowerCase();
  const only = $("only-unassigned").checked;
  const dl = $("joblist");
  dl.replaceChildren(...report.known_jobs.map((j) => h("option", { value: j })));
  const tb = $("chats").querySelector("tbody");
  tb.replaceChildren();
  const rows = report.chats.filter((c) => (!only || c.job === "Unassigned") &&
    (!q || `${c.title} ${c.project} ${c.job} ${c.tool_name}`.toLowerCase().includes(q)));
  if (!rows.length) tb.append(h("tr", {}, h("td", { colspan: 6, class: "empty", text: "Nothing to show." })));
  for (const c of rows.slice(0, 500)) {
    const input = h("input", { class: "job", list: "joblist", value: c.job === "Unassigned" ? "" : c.job,
      placeholder: "Unassigned", "aria-label": `Job for ${c.title || c.chat_id}`, maxlength: 80,
      title: c.job_source === "manual" ? "Set by you" : c.job_source === "rule" ? "Set by a rule" : c.job_source === "folder" ? "From the project folder" : "" });
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
function toolOptions() {
  const out = { ...BUILTIN };
  for (const t of config.custom_tools) out[t.id] = t.name;
  return out;
}
function field(label, input) { return h("label", {}, label, input); }
function removeBtn(fn) { return h("button", { type: "button", class: "link", onclick: fn, "aria-label": "Remove", text: "Remove" }); }

function renderSettings() {
  const subs = $("subs"); subs.replaceChildren();
  const tools = toolOptions();
  config.subscriptions.forEach((s, i) => {
    const name = h("input", { value: s.name, maxlength: 80, oninput: (e) => (s.name = e.target.value) });
    const cost = h("input", { type: "number", min: 0, step: "0.01", value: s.monthly_cost, oninput: (e) => (s.monthly_cost = Number(e.target.value) || 0) });
    const basis = h("select", { onchange: (e) => (s.basis = e.target.value) },
      h("option", { value: "time", text: "time spent", selected: s.basis === "time" }),
      h("option", { value: "tokens", text: "tokens used (this-PC tools only)", selected: s.basis === "tokens" }));
    const boxes = h("div", { class: "tools" }, Object.entries(tools).map(([id, label]) => {
      const cb = h("input", { type: "checkbox", checked: s.tools.includes(id) });
      cb.addEventListener("change", () => {
        if (cb.checked) {
          config.subscriptions.forEach((o) => (o.tools = o.tools.filter((t) => t !== id)));
          s.tools.push(id);
        } else s.tools = s.tools.filter((t) => t !== id);
        renderSettings();
      });
      return h("label", { class: "check" }, cb, label);
    }));
    subs.append(h("div", { class: "editrow" }, field("Name", name), field("Monthly cost", cost), field("Split by", basis),
      field("Tools covered", boxes), removeBtn(() => { config.subscriptions.splice(i, 1); renderSettings(); })));
  });

  const customs = $("customs"); customs.replaceChildren();
  config.custom_tools.forEach((t, i) => {
    customs.append(h("div", { class: "editrow" },
      field("Name", h("input", { value: t.name, maxlength: 80, oninput: (e) => (t.name = e.target.value) })),
      field("Websites (comma separated)", h("input", { value: t.sites.join(", "), placeholder: "perplexity.ai", oninput: (e) => (t.sites = e.target.value.split(",").map((x) => x.trim()).filter(Boolean)) })),
      field("Desktop apps (Windows, comma separated)", h("input", { value: t.apps.join(", "), placeholder: "cursor.exe", oninput: (e) => (t.apps = e.target.value.split(",").map((x) => x.trim()).filter(Boolean)) })),
      removeBtn(() => { config.custom_tools.splice(i, 1); renderSettings(); })));
  });

  const rules = $("rules"); rules.replaceChildren();
  config.rules.forEach((r, i) => {
    rules.append(h("div", { class: "editrow" },
      field("If", h("select", { onchange: (e) => (r.field = e.target.value) },
        ["any", "title", "project"].map((f) => h("option", { value: f, text: f === "any" ? "title or project" : f, selected: r.field === f })))),
      field("contains", h("input", { value: r.contains, maxlength: 120, oninput: (e) => (r.contains = e.target.value) })),
      field("in tool", h("select", { onchange: (e) => (r.tool = e.target.value) },
        h("option", { value: "", text: "any tool", selected: !r.tool }),
        Object.entries(tools).map(([id, label]) => h("option", { value: id, text: label, selected: r.tool === id })))),
      field("→ job", h("input", { value: r.job, maxlength: 80, list: "joblist", oninput: (e) => (r.job = e.target.value) })),
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
  config.custom_tools.forEach((t) => { if (!t.id) t.id = ""; });
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
  $("add-sub").addEventListener("click", () => { config.subscriptions.push({ name: "New subscription", monthly_cost: 0, tools: [], basis: "time" }); renderSettings(); });
  $("add-custom").addEventListener("click", () => { config.custom_tools.push({ name: "New tool", sites: [], apps: [] }); renderSettings(); });
  $("add-rule").addEventListener("click", () => { config.rules.push({ field: "any", contains: "", tool: "", job: "" }); renderSettings(); });
  $("save").addEventListener("click", saveSettings);
  $("copy-token").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(TOKEN); $("copy-token").textContent = "Copied"; }
    catch { $("token").type = "text"; $("token").select(); }
    setTimeout(() => ($("copy-token").textContent = "Copy"), 2000);
  });
  load().catch((e) => { $("banner").hidden = false; $("banner").textContent = `Could not load data: ${e.message}`; });
  setInterval(() => { if (document.visibilityState === "visible" && document.activeElement?.tagName !== "INPUT") load(false).catch(() => {}); }, 60000);
});
