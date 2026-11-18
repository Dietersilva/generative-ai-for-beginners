// load every race and sprint in the page and record the on-track overtakes it shows (official feed after filtering)
// usage: node ovcollect.js out.json   (needs the test server on :8767)
const { chromium } = require('playwright'); const fs = require('fs');
(async () => { const b = await chromium.launch(); const p = await b.newPage({viewport: {width: 1280, height: 800}}); const out = {}; const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  for (const y of [2026, 2025, 2024, 2023]) {
    await p.goto('http://localhost:8767/index.html#' + y); await p.waitForFunction(y => window.__gridReplay && window.__gridReplay.st.idx && window.__gridReplay.st.year == y && window.__gridReplay.st.R, y, {timeout: 90000});
    const list = await p.evaluate(() => { const i = window.__gridReplay.st.idx; return i.races.map(r => [r.session_key, 'gp', r.name]).concat((i.sprints || []).map(r => [r.session_key, 'sprint', r.name])); });
    for (const [sk, kind, name] of list) {
      await p.evaluate(() => { window.__prevR = window.__gridReplay.st.R; });
      await p.selectOption('#raceSel', String(sk));
      await p.waitForFunction(sk => { const s = window.__gridReplay.st; return s.R && s.R !== window.__prevR && s.meta.session_key == sk && document.querySelector('#loading').hidden; }, sk, {timeout: 90000});
      const r = await p.evaluate(() => { const R = window.__gridReplay.st.R, c = {}; for (const o of R.overtakes) { (c[o.a.code] = c[o.a.code] || [0, 0])[0]++; (c[o.b.code] = c[o.b.code] || [0, 0])[1]++; } return {src: R.ovSrc || 'detected', raw: R.ovRaw || 0, n: R.overtakes.length, c}; });
      out[`${y}|${kind}|${name}`] = r; console.log(y, kind, name, r.src, r.raw, '->', r.n);
    }
  }
  fs.writeFileSync(process.argv[2], JSON.stringify(out)); console.log('DONE', Object.keys(out).length, 'errors:', errs.length ? errs.slice(0, 5) : 'none'); await b.close(); })();
