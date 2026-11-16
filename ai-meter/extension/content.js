"use strict";
// Runs inside claude.ai / chatgpt.com (and sites you allow for custom tools).
// 1. Counts active seconds per chat: tab visible + focused + you've used the
//    keyboard/mouse recently. Nothing about the chat content is read.
// 2. On claude.ai only: reads your plan usage % from the same endpoint the
//    claude.ai Settings > Usage page uses. Your login never leaves the
//    browser; only the percentages are passed to the AI-Meter app.

(() => {
  if (window.__aimeterLoaded) return;
  window.__aimeterLoaded = true;

  const TICK_MS = 5000;
  const FLUSH_MS = 15000;
  const PLAN_EVERY_MS = 5 * 60 * 1000;
  let idleMs = 5 * 60 * 1000;
  let tool = null;
  let lastInput = Date.now();
  let pending = 0;
  let current = null;

  const mark = () => { lastInput = Date.now(); };
  for (const ev of ["keydown", "mousedown", "wheel", "touchstart", "scroll"]) addEventListener(ev, mark, { passive: true, capture: true });
  let lastMove = 0;
  addEventListener("mousemove", () => { const n = Date.now(); if (n - lastMove > 2000) { lastMove = n; mark(); } }, { passive: true });

  function send(msg) {
    try { return chrome.runtime.sendMessage(msg); } catch { return Promise.resolve(null); }
  }

  function cleanTitle(t) {
    t = (t || "").replace(/\s+/g, " ").trim();
    t = t.replace(/\s+[-|–—]\s+(Claude|ChatGPT)$/i, "").replace(/^(ChatGPT|Claude)\s*[-|–—]\s*/i, "");
    if (/^(claude|chatgpt|new chat)$/i.test(t)) return "";
    return t.slice(0, 200);
  }

  function where() {
    const p = location.pathname;
    let chatId = "home", project = "", m;
    if (location.hostname === "claude.ai") {
      if ((m = p.match(/^\/chat\/([0-9a-f-]{8,})/i))) chatId = `chat:${m[1]}`;
      else if ((m = p.match(/^\/code\/([^/?#]+)/))) chatId = `code:${m[1]}`;
      else if ((m = p.match(/^\/project\/([0-9a-f-]{8,})/i))) { chatId = `project:${m[1]}`; project = m[1]; }
      else if (p.startsWith("/code")) chatId = "code:home";
    } else if (location.hostname.endsWith("chatgpt.com")) {
      if ((m = p.match(/\/c\/([0-9a-z-]{8,})/i))) chatId = `c:${m[1]}`;
      if ((m = p.match(/^\/g\/(g-p-[0-9a-z]+)/i))) project = m[1];
      else if ((m = p.match(/^\/g\/(g-[0-9a-z]+)/i))) project = `GPT ${m[1]}`;
      if (chatId === "home" && project) chatId = `project:${project}`;
    } else {
      chatId = `page:${location.hostname}${p.split("/").slice(0, 3).join("/")}`.slice(0, 200);
    }
    const title = cleanTitle(document.title) || (chatId === "home" ? "(home / new chat)" : "");
    return { chatId, title, project };
  }

  function today() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  function flush() {
    if (!tool || !current || pending <= 0) return;
    const seconds = pending; pending = 0;
    send({ type: "time", tool, chatId: current.chatId, title: current.title, project: current.project, seconds, day: today() });
  }

  function tick() {
    const here = where();
    if (current && here.chatId !== current.chatId) flush();
    current = here;
    const active = document.visibilityState === "visible" && document.hasFocus() && Date.now() - lastInput < idleMs;
    if (active) pending += TICK_MS / 1000;
  }

  // ---- Claude plan usage -------------------------------------------------------
  const LABELS = {
    five_hour: "5-hour window", seven_day: "Weekly", seven_day_opus: "Weekly (Opus)",
    seven_day_sonnet: "Weekly (Sonnet)", seven_day_oauth_apps: "Weekly (apps)", extra_usage: "Extra usage",
  };
  let orgId = null;

  async function getJson(url) {
    const r = await fetch(url, { credentials: "include", headers: { Accept: "application/json" } });
    if (!r.ok) throw new Error(String(r.status));
    return r.json();
  }

  function parseUsage(data) {
    const windows = [];
    if (!data || typeof data !== "object") return windows;
    for (const [key, v] of Object.entries(data)) {
      if (!v || typeof v !== "object" || typeof v.utilization !== "number") continue;
      if (v.is_enabled === false) continue;
      windows.push({
        key: key.toLowerCase().replace(/[^a-z0-9_]/g, "").slice(0, 40),
        label: LABELS[key] || key.replace(/_/g, " "),
        used_pct: Math.max(0, Math.min(100, v.utilization)),
        resets_at: v.resets_at || null,
      });
    }
    return windows;
  }

  async function claudePlan() {
    try {
      if (!orgId) {
        const orgs = await getJson("/api/organizations");
        for (const o of Array.isArray(orgs) ? orgs : []) {
          if (!o || typeof o.uuid !== "string" || !/^[0-9a-f-]{20,}$/i.test(o.uuid)) continue;
          try {
            const w = parseUsage(await getJson(`/api/organizations/${o.uuid}/usage`));
            if (w.length) { orgId = o.uuid; send({ type: "plan", provider: "claude", windows: w }); return; }
          } catch { /* try next org */ }
        }
        return;
      }
      const w = parseUsage(await getJson(`/api/organizations/${orgId}/usage`));
      if (w.length) send({ type: "plan", provider: "claude", windows: w });
    } catch { orgId = null; }
  }

  async function start() {
    const info = await send({ type: "hello" });
    if (!info || !info.tool) return; // not a tracked site
    tool = info.tool;
    if (info.idleMs) idleMs = info.idleMs;
    current = where();
    setInterval(tick, TICK_MS);
    setInterval(flush, FLUSH_MS);
    addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") flush(); });
    addEventListener("pagehide", flush);
    if (location.hostname === "claude.ai") {
      claudePlan();
      setInterval(() => { if (document.visibilityState === "visible") claudePlan(); }, PLAN_EVERY_MS);
    }
  }
  start();
})();
