const { chromium } = require('playwright');
const Y = +(process.env.YEAR || 2025), SHOT = process.env.SHOT || '';
(async () => { const b = await chromium.launch(); const p = await b.newPage({viewport:{width:1440,height:900}});
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto(process.env.URL || 'http://localhost:8767/index.html');
  await p.waitForFunction(() => window.__gridReplay && window.__gridReplay.st.R, null, {timeout: 60000});
  const seasons = await p.$$eval('#seasonSel option', os => os.map(o => o.value)); console.log('seasons', seasons);
  if (seasons.length > 1) await p.selectOption('#seasonSel', String(Y));
  await p.waitForFunction(y => { const s = window.__gridReplay.st; return s.year === y && s.idx && s.idx.season === y && s.R && document.querySelector("#loading").hidden; }, Y, {timeout: 180000});
  console.log('groups:', (await p.$$eval('#raceSel optgroup', g => g.map(x => x.label + ':' + x.children.length))).join(' | '));
  const opts = await p.$$eval('#raceSel option', os => os.filter(o => !o.disabled).map(o => [o.value, o.textContent]));
  let ok = 0, bad = [];
  for (const [v, txt] of opts) { await p.selectOption('#raceSel', v);
    try { await p.waitForFunction(v => { const s = window.__gridReplay.st; return (s.R && s.R.h.session_key === +v) || (s.Q && s.Q.q.session_key === +v); }, v, {timeout: 30000}); ok++; } catch (e) { bad.push(txt); } }
  if (SHOT) { await p.selectOption('#raceSel', SHOT); await p.waitForTimeout(2500); await p.evaluate(() => window.__gridReplay.setTime(2500)); await p.waitForTimeout(1000); await p.screenshot({path: `${process.argv[2]}/y${Y}.png`}); }
  console.log(`${Y}: loaded ${ok}/${opts.length}`, bad.length ? 'FAILED: ' + bad.join('; ') : '', '| errors:', errs.length ? errs.slice(0, 5) : 'none');
  await b.close(); })();
