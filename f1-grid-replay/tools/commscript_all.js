// usage: node commscript_all.js list.json   list = [[hash, session_key, out.json], ...]; writes each session's commentary script
const { chromium } = require('playwright'); const fs = require('fs');
(async () => { const list = JSON.parse(fs.readFileSync(process.argv[2])); const b = await chromium.launch(); const p = await b.newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(process.env.BASE || 'http://localhost:8767/index.html'); await p.waitForFunction(() => window.__gridReplay && window.__gridReplay.st.R, null, {timeout: 90000});
  let ok = 0;
  for (const [hash, sk, out] of list) {
    await p.evaluate(h => { location.hash = h; }, hash);
    try { await p.waitForFunction(sk => { const s = window.__gridReplay.st; return s.R && s.R.h.session_key === sk && s.R.comm; }, sk, {timeout: 90000});
      const L = await p.evaluate(() => window.__gridReplay.st.R.comm); fs.writeFileSync(out, JSON.stringify(L)); ok++; console.log(sk, L.length); }
    catch (e) { console.log(sk, 'FAILED', e.message.slice(0, 80)); } }
  console.log('done', ok, '/', list.length, errs.length ? 'ERRORS ' + errs.slice(0, 3) : ''); await b.close(); })();
