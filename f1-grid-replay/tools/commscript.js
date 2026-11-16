// usage: node commscript.js <hash> [out.json]   prints / writes the commentary script for one session
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto((process.env.BASE || 'http://localhost:8767/index.html') + process.argv[2]);
  await p.waitForFunction(() => window.__gridReplay && window.__gridReplay.st.R && window.__gridReplay.st.R.comm, null, {timeout: 90000});
  const L = await p.evaluate(() => window.__gridReplay.st.R.comm);
  if (process.argv[3]) require('fs').writeFileSync(process.argv[3], JSON.stringify(L)); else L.forEach(x => console.log(String(Math.round(x.t)).padStart(5), x.pri, x.who, x.e, x.radio ? 'R' : ' ', x.text));
  if (errs.length) console.error('ERRORS', errs); await b.close(); })();
