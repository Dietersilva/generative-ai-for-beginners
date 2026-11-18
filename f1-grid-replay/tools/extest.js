const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({viewport:{width:1440,height:900}});
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  const SK = process.env.SK || '11253', S = process.argv[2], Y = process.env.YEAR || '';
  await p.goto('http://localhost:8767/index.html' + (Y ? '#' + Y : '')); await p.waitForFunction(() => window.__gridReplay && window.__gridReplay.st.idx, null, {timeout: 60000});
  await p.waitForTimeout(1500);
  await p.evaluate(() => { window.__prevR = window.__gridReplay.st.R; }); await p.selectOption('#raceSel', SK); await p.waitForFunction(sk => { const s = window.__gridReplay.st; return s.R && s.R !== window.__prevR && s.meta.session_key == sk && document.querySelector('#loading').hidden; }, +SK, {timeout: 60000}); await p.waitForTimeout(800);
  const info = await p.evaluate(() => { const g = window.__gridReplay, R = g.st.R;
    return {name: g.st.meta.name, src: R.ovSrc || 'detected', raw: R.ovRaw, ov: R.overtakes.length, sec: !!R.sec, champ: !!(R.h.ext && R.h.ext.cd && R.h.ext.cd.length),
      first: R.overtakes.slice(0, 6).map(o => `${o.a.code}>${o.b.code} P${o.pos} t${Math.round(o.t - R.lightsOut)}`).join(', ')}; });
  await p.evaluate(() => { const R = window.__gridReplay.st.R; window.__gridReplay.setTime(R.lightsOut + (R.chq - R.lightsOut) * 0.5); });
  await p.waitForTimeout(700);
  const ms = await p.evaluate(() => document.querySelectorAll('.row .ms i.p, .row .ms i.g, .row .ms i.y').length);
  await p.screenshot({path: S + '/tower.png'});
  await p.evaluate(() => { const R = window.__gridReplay.st.R; const D = R.drivers.find(d => d.res && d.res.position === 1) || R.drivers[0]; window.__gridReplay.selectDriver(D.num, true); });
  await p.waitForTimeout(900); await p.screenshot({path: S + '/driver.png'});
  await p.click('#anaBtn'); await p.waitForTimeout(400);
  for (const t of ['inc', 'trap', 'champ']) { await p.click(`[data-ana="${t}"]`); await p.waitForTimeout(600); await p.screenshot({path: `${S}/ana_${t}.png`}); }
  const champTop = await p.evaluate(() => [...document.querySelectorAll('#anaInfo table.stbl')].map(t => t.querySelector('tbody tr') && t.querySelector('tbody tr').innerText.replace(/\s+/g, ' ')));
  console.log(JSON.stringify(info), '| tower sector bars lit:', ms, '| champ leaders:', JSON.stringify(champTop), '| errors:', errs.length ? errs : 'none'); await b.close(); })();
