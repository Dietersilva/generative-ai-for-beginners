"use strict";
// Runs inside claude.ai / chatgpt.com (and sites you allow for custom tools).
// 1. Counts active seconds per chat: tab visible + focused + you've used the
//    keyboard/mouse recently. Nothing about the chat content is read.
// 2. Reads your plan limits (% used, reset time) on claude.ai and chatgpt.com
//    from the same endpoints their own usage pages use. Your login never
//    leaves the browser; only the percentages go to the AI-Meter app.

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

  function linkText(sel) {
    const a = document.querySelector(sel);
    const t = a && (a.getAttribute("aria-label") || a.textContent || "").replace(/\s+/g, " ").trim();
    return t && t.length <= 80 ? t : "";
  }

  function where() {
    const p = location.pathname;
    let chatId = "home", project = "", m;
    if (location.hostname === "claude.ai") {
      if ((m = p.match(/^\/chat\/([0-9a-f-]{8,})/i))) {
        chatId = `chat:${m[1]}`;
        // A chat inside a Claude Project shows a link back to the project.
        project = linkText('main a[href^="/project/"]');
      } else if ((m = p.match(/^\/code\/([^/?#]+)/))) chatId = `code:${m[1]}`;
      else if ((m = p.match(/^\/project\/([0-9a-f-]{8,})/i))) {
        chatId = `project:${m[1]}`;
        project = cleanTitle(document.title);
      } else if (p.startsWith("/code")) chatId = "code:home";
    } else if (location.hostname.endsWith("chatgpt.com")) {
      if ((m = p.match(/\/c\/([0-9a-z-]{8,})/i))) chatId = `c:${m[1]}`;
      if ((m = p.match(/^\/g\/(g-p-[0-9a-f]+)(?:-([a-z0-9-]+))?/i))) {
        // ChatGPT project: prefer the name shown in the sidebar, else the URL slug.
        project = linkText(`nav a[href^="/g/${m[1]}"]`) || (m[2] ? m[2].replace(/-/g, " ") : m[1]);
      } else if ((m = p.match(/^\/g\/(g-[0-9a-z]+)/i))) project = `GPT ${m[1]}`;
      if (chatId === "home" && project) chatId = `project:${project}`;
    } else {
      chatId = `page:${location.hostname}${p.split("/").slice(0, 3).join("/")}`.slice(0, 200);
    }
    const title = cleanTitle(document.title) || (chatId === "home" ? "(home / new chat)" : "");
    return { chatId, title, project: project.slice(0, 120) };
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

  // ---- ChatGPT plan limits (the numbers on ChatGPT's Codex usage page) --------
  // The session token is used only for this one same-site request and is never
  // stored or sent anywhere else.
  function windowFrom(w, now) {
    if (!w || typeof w !== "object" || typeof w.used_percent !== "number") return null;
    const secs = Number(w.limit_window_seconds) || 0;
    const key = secs === 18000 ? "five_hour" : secs === 604800 ? "weekly" : secs ? `w${Math.round(secs / 60)}` : "";
    if (!key) return null;
    const label = key === "five_hour" ? "5-hour window" : key === "weekly" ? "Weekly"
      : secs < 172800 ? `${Math.round(secs / 3600)}-hour window` : `${Math.round(secs / 86400)}-day window`;
    let resets = Number(w.reset_at) || null;
    if (!resets && Number(w.reset_after_seconds)) resets = now + Number(w.reset_after_seconds);
    return { key, label, used_pct: Math.max(0, Math.min(100, w.used_percent)), resets_at: resets };
  }

  async function chatgptPlan() {
    try {
      const s = await getJson("/api/auth/session");
      const token = s && typeof s.accessToken === "string" ? s.accessToken : "";
      if (!token) return;
      const headers = { Accept: "application/json", Authorization: `Bearer ${token}` };
      const acct = s.account && typeof s.account.id === "string" ? s.account.id : "";
      if (acct) headers["ChatGPT-Account-Id"] = acct;
      const r = await fetch("/backend-api/wham/usage", { credentials: "include", headers });
      if (!r.ok) return;
      const data = await r.json();
      const rl = (data && data.rate_limit) || {};
      const now = Date.now() / 1000;
      const windows = [windowFrom(rl.primary_window, now), windowFrom(rl.secondary_window, now)].filter(Boolean);
      if (windows.length) send({ type: "plan", provider: "chatgpt", windows });
    } catch { /* not available for this account */ }
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
    const plan = location.hostname === "claude.ai" ? claudePlan
      : location.hostname.endsWith("chatgpt.com") ? chatgptPlan : null;
    if (plan) {
      plan();
      setInterval(() => { if (document.visibilityState === "visible") plan(); }, PLAN_EVERY_MS);
    }
  }
  start();
})();
