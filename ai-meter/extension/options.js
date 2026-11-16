"use strict";
const $ = (id) => document.getElementById(id);

function el(tag, text, cls) { const e = document.createElement(tag); if (text) e.textContent = text; if (cls) e.className = cls; return e; }

async function load() {
  const s = await chrome.storage.local.get(["port", "token", "lastSync", "lastError", "appConfig"]);
  $("port").value = s.port || 47821;
  $("token").value = s.token || "";
  const st = $("status");
  if (s.lastError) { st.textContent = `Problem: ${s.lastError}`; st.className = "bad"; }
  else if (s.lastSync) { st.textContent = `Connected. Last sent ${new Date(s.lastSync).toLocaleTimeString()}.`; st.className = "ok"; }
  else st.textContent = "Not connected yet.";
  renderSites(s.appConfig);
}

function renderSites(cfg) {
  const ul = $("sites");
  ul.replaceChildren();
  const tools = (cfg?.custom_tools || []).filter((t) => (t.sites || []).length);
  if (!tools.length) { ul.append(el("li", "None yet. Add websites under Settings → Custom tools in the dashboard.", "hint")); return; }
  for (const t of tools) {
    for (const d of t.sites) {
      const li = el("li", `${t.name}: ${d} `);
      const origins = [`https://${d}/*`, `https://*.${d}/*`];
      chrome.permissions.contains({ origins }).then((ok) => {
        if (ok) { li.append(el("span", "✓ allowed", "ok")); return; }
        const b = el("button", "Allow");
        b.type = "button";
        b.addEventListener("click", async () => {
          const granted = await chrome.permissions.request({ origins });
          if (granted) { await chrome.runtime.sendMessage({ type: "registerSites" }); load(); }
        });
        li.append(b);
      });
      ul.append(li);
    }
  }
}

$("save").addEventListener("click", async () => {
  const port = Number($("port").value) || 47821;
  const token = $("token").value.trim();
  await chrome.storage.local.set({ port, token, lastConfigAt: 0 });
  const out = $("result");
  try {
    const r = await fetch(`http://127.0.0.1:${port}/api/ping`, { headers: { "X-AIMeter-Token": token }, cache: "no-store" });
    if (r.status === 401) throw new Error("wrong token");
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    out.textContent = "Connected ✓"; out.className = "ok";
    await chrome.runtime.sendMessage({ type: "syncNow" });
  } catch (e) {
    out.textContent = `Couldn't connect (${e.message}). Is AI-Meter running?`; out.className = "bad";
  }
  load();
});
$("sync").addEventListener("click", async () => { await chrome.runtime.sendMessage({ type: "syncNow" }); load(); });
load();
