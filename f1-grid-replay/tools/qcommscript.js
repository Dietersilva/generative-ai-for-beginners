// usage: node qcommscript.js list.json   list = [[hash, session_key, out.json|"-"], ...]; qualifying commentary scripts
const { chromium } = require('playwright'); const fs = require('fs');
(async () => { const list = JSON.parse(fs.readFileSync(process.argv[2])); const b = await chromium.launch(); const p = await b.newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(process.env.BASE || 'http://localhost:8767/index.html'); await p.waitForFunction(() => window.__gridReplay && window.__gridReplay.st.R, null, {timeout: 90000});
  let ok = 0;
  for (const [hash, sk, out] of list) {
    await p.evaluate(h => { location.hash = h; }, hash);
    try { await p.waitForFunction(sk => { const s = window.__gridReplay.st; return s.Q && s.Q.commKey === sk && s.Q.comm; }, sk, {timeout: 90000});
      const L = await p.evaluate(() => ({T: window.__gridReplay.st.Q.T, L: window.__gridReplay.st.Q.comm}));
      if (out === '-') { console.log('==', hash, 'lap clock', L.T.toFixed(1)); L.L.forEach(x => console.log(String(x.t).padStart(6), x.pri, x.who, x.text)); } else fs.writeFileSync(out, JSON.stringify(L.L));
      ok++; } catch (e) { console.log(sk, 'FAILED', e.message.slice(0, 80)); } }
  console.log('done', ok, '/', list.length, errs.length ? 'ERRORS ' + errs.slice(0, 3) : ''); await b.close(); })();
