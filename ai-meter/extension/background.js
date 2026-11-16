"use strict";
// Collects totals from the content scripts and sends them to the AI-Meter app
// on 127.0.0.1 (this PC only), authenticated with the pairing token.

const DEFAULT_PORT = 47821;
const KEEP_DAYS = 45;
const BUILTIN_SITES = { "claude.ai": "claude_web", "chatgpt.com": "chatgpt_web" };

// Serialize all storage read-modify-write work so updates are never lost.
let chain = Promise.resolve();
const locked = (fn) => (chain = chain.then(fn, fn));

async function get(keys) { return chrome.storage.local.get(keys); }

async function settings() {
  const s = await get(["port", "token", "sourceId", "appConfig"]);
  if (!s.sourceId) {
    s.sourceId = crypto.randomUUID().replace(/-/g, "").slice(0, 24);
    await chrome.storage.local.set({ sourceId: s.sourceId });
  }
  return { port: Number(s.port) || DEFAULT_PORT, token: s.token || "", sourceId: s.sourceId, appConfig: s.appConfig || null };
}

function toolForHost(host, appConfig) {
  for (const [domain, id] of Object.entries(BUILTIN_SITES)) if (host === domain || host.endsWith(`.${domain}`)) return id;
  for (const t of appConfig?.custom_tools || []) {
    for (const d of t.sites || []) if (host === d || host.endsWith(`.${d}`)) return t.id;
  }
  return null;
}

async function call(path, body) {
  const { port, token } = await settings();
  if (!token) throw new Error("Not paired yet: paste the token from the AI-Meter dashboard.");
  const opts = { headers: { "X-AIMeter-Token": token }, cache: "no-store" };
  if (body !== undefined) { opts.method = "POST"; opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
  const r = await fetch(`http://127.0.0.1:${port}${path}`, opts);
  if (r.status === 401) throw new Error("Wrong pairing token.");
  if (!r.ok) throw new Error(`AI-Meter answered HTTP ${r.status}`);
  return r.json();
}

chrome.runtime.onMessage.addListener((msg, sender, reply) => {
  // Only accept messages from our own content scripts / pages.
  if (sender.id !== chrome.runtime.id || !msg || typeof msg.type !== "string") return false;
  if (msg.type === "hello") {
    settings().then(({ appConfig }) => {
      let host = "";
      try { host = new URL(sender.tab?.url || sender.url || "").hostname; } catch { /* ignore */ }
      const idle = Number(appConfig?.idle_cap_minutes) || 5;
      reply({ tool: toolForHost(host, appConfig), idleMs: idle * 60000 });
    });
    return true;
  }
  if (msg.type === "time" && sender.tab) {
    const secs = Number(msg.seconds);
    if (!(secs > 0) || secs > 120 || !/^\d{4}-\d{2}-\d{2}$/.test(msg.day || "")) return false;
    locked(async () => {
      const { totals = {}, dirty = {} } = await get(["totals", "dirty"]);
      const key = `${msg.day}|${msg.tool}|${String(msg.chatId).slice(0, 200)}`;
      const t = totals[key] || { day: msg.day, tool: String(msg.tool).slice(0, 64), chat_id: String(msg.chatId).slice(0, 200), seconds: 0 };
      t.seconds = Math.min(86400, t.seconds + secs);
      if (msg.title) t.title = String(msg.title).slice(0, 200);
      if (msg.project) t.project = String(msg.project).slice(0, 200);
      totals[key] = t;
      dirty[key] = 1;
      await chrome.storage.local.set({ totals, dirty });
    });
    return false;
  }
  if (msg.type === "plan" && sender.tab && msg.provider === "claude" && Array.isArray(msg.windows)) {
    locked(() => chrome.storage.local.set({ pendingPlan: { provider: "claude", windows: msg.windows.slice(0, 12) } }));
    return false;
  }
  if (msg.type === "syncNow") { sync().then(() => reply(true), () => reply(false)); return true; }
  if (msg.type === "registerSites") { registerCustomSites().then(() => reply(true)); return true; }
  return false;
});

async function sync() {
  return locked(async () => {
    try {
      const { sourceId } = await settings();
      const { totals = {}, dirty = {}, pendingPlan = null, lastConfigAt = 0 } =
        await get(["totals", "dirty", "pendingPlan", "lastConfigAt"]);
      const keys = Object.keys(dirty).filter((k) => totals[k]);
      if (keys.length || pendingPlan) {
        await call("/api/ingest", { source: sourceId, time: keys.map((k) => totals[k]), plans: pendingPlan ? [pendingPlan] : [] });
      }
      // prune old days
      const cutoff = new Date(Date.now() - KEEP_DAYS * 86400000).toISOString().slice(0, 10);
      for (const k of Object.keys(totals)) if (totals[k].day < cutoff) delete totals[k];
      const set = { totals, dirty: {}, pendingPlan: null, lastSync: Date.now(), lastError: "" };
      if (Date.now() - lastConfigAt > 10 * 60000) {
        set.appConfig = await call("/api/config");
        set.lastConfigAt = Date.now();
      }
      await chrome.storage.local.set(set);
      if (set.appConfig) await registerCustomSites();
    } catch (e) {
      await chrome.storage.local.set({ lastError: String(e.message || e).slice(0, 200) });
    }
  });
}

// Custom tools: inject the timer only on sites the user granted.
async function registerCustomSites() {
  const { appConfig } = await settings();
  const origins = [];
  for (const t of appConfig?.custom_tools || []) {
    for (const d of t.sites || []) {
      if (!/^[a-z0-9.-]+$/.test(d) || BUILTIN_SITES[d]) continue;
      for (const o of [`https://${d}/*`, `https://*.${d}/*`]) {
        if (await chrome.permissions.contains({ origins: [o] })) origins.push(o);
      }
    }
  }
  try { await chrome.scripting.unregisterContentScripts({ ids: ["aimeter-custom"] }); } catch { /* none yet */ }
  if (origins.length) {
    await chrome.scripting.registerContentScripts([{ id: "aimeter-custom", matches: origins, js: ["content.js"], runAt: "document_idle", persistAcrossSessions: true }]);
  }
}

chrome.alarms.create("sync", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener((a) => { if (a.name === "sync") sync(); });
chrome.action.onClicked.addListener(() => chrome.runtime.openOptionsPage());
chrome.runtime.onInstalled.addListener((d) => { if (d.reason === "install") chrome.runtime.openOptionsPage(); });
