'use strict';

// Episode Radar: new-series, new-season and new-episode alerts for the streaming
// services you pay for, plus a planner that shows which services you can pause.
// Data comes from the public TVmaze API. Everything the user saves stays in this
// device's localStorage. The page never uses innerHTML: every string from the API
// is rendered as text, and every link or image URL is checked before it reaches
// the DOM.
(() => {
  const API = 'https://api.tvmaze.com';
  const STORE_KEY = 'episodeRadar.v1';
  const CACHE_KEY = 'episodeRadar.cache.v1';
  const MINUTE = 60e3;
  const HOUR = 60 * MINUTE;
  const DAY = 24 * HOUR;
  const STALE_AFTER = 6 * HOUR;
  // TVmaze allows roughly 20 requests per 10 seconds per IP; stay well under it.
  const REQUEST_GAP_MS = 550;

  // `names` are TVmaze web channel names, lower-cased. `hosts` decide whether a
  // show's official site is a direct link into that service.
  const SERVICES = [
    { id: 'netflix', label: 'Netflix', names: ['netflix'], hosts: ['netflix.com'], home: 'https://www.netflix.com/' },
    { id: 'hulu', label: 'Hulu', names: ['hulu'], hosts: ['hulu.com'], home: 'https://www.hulu.com/' },
    { id: 'prime', label: 'Prime Video', names: ['prime video', 'amazon prime video', 'amazon prime', 'amazon video'], hosts: ['primevideo.com', 'amazon.com'], home: 'https://www.primevideo.com/' },
    { id: 'hbomax', label: 'HBO Max', names: ['hbo max', 'max'], hosts: ['hbomax.com', 'max.com'], home: 'https://www.hbomax.com/' },
    { id: 'disney', label: 'Disney+', names: ['disney+'], hosts: ['disneyplus.com'], home: 'https://www.disneyplus.com/' },
    { id: 'appletv', label: 'Apple TV+', names: ['apple tv+', 'apple tv'], hosts: ['tv.apple.com'], home: 'https://tv.apple.com/' },
    { id: 'paramount', label: 'Paramount+', names: ['paramount+', 'cbs all access'], hosts: ['paramountplus.com'], home: 'https://www.paramountplus.com/' },
    { id: 'peacock', label: 'Peacock', names: ['peacock', 'peacock premium'], hosts: ['peacocktv.com'], home: 'https://www.peacocktv.com/' },
  ];
  const DEFAULT_SERVICES = ['netflix', 'hulu', 'prime'];
  const TABS = ['alerts', 'shows', 'downloads', 'savings', 'settings'];

  // ---------- small helpers ----------

  const $ = (sel) => document.querySelector(sel);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const str = (v, max) => (typeof v === 'string' ? v.slice(0, max) : '');
  const posInt = (v) => (Number.isInteger(v) && v > 0 && v < 1e9 ? v : null);
  const isIso = (v) => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v);
  const svcById = (id) => SERVICES.find((s) => s.id === id) || null;

  function safeUrl(v) {
    if (typeof v !== 'string') return null;
    try {
      const u = new URL(v);
      return u.protocol === 'https:' ? u.href : null;
    } catch {
      return null;
    }
  }

  function safeImg(v) {
    const u = safeUrl(v);
    return u && new URL(u).hostname === 'static.tvmaze.com' ? u : null;
  }

  function hostMatches(url, hosts) {
    const safe = safeUrl(url);
    if (!safe) return false;
    const host = new URL(safe).hostname;
    return hosts.some((h) => host === h || host.endsWith('.' + h));
  }

  // TVmaze summaries are HTML. DOMParser builds an inert document (no scripts
  // run, no images load); script and style contents are dropped before reading text.
  function plain(html, max = 280) {
    if (typeof html !== 'string' || !html) return '';
    const body = new DOMParser().parseFromString(html, 'text/html').body;
    for (const el of body.querySelectorAll('script, style, noscript, template')) el.remove();
    const text = (body.textContent || '').replace(/\s+/g, ' ').trim();
    return text.length > max ? text.slice(0, max - 1).trimEnd() + '…' : text;
  }

  function isoDate(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }
  function addDays(d, n) {
    const x = new Date(d);
    x.setDate(x.getDate() + n);
    return x;
  }
  const today = () => isoDate(new Date());
  const noon = (iso) => new Date(iso + 'T12:00:00');
  const daysBetween = (a, b) => Math.round((noon(b) - noon(a)) / DAY);

  function fmtDate(iso) {
    if (!isIso(iso)) return 'date not announced';
    const d = noon(iso);
    const opts = { weekday: 'short', month: 'short', day: 'numeric' };
    if (d.getFullYear() !== new Date().getFullYear()) opts.year = 'numeric';
    return d.toLocaleDateString(undefined, opts);
  }

  function listJoin(items) {
    try {
      return new Intl.ListFormat(undefined, { style: 'long', type: 'conjunction' }).format(items);
    } catch {
      return items.join(', ');
    }
  }

  const money = (cents) => (cents / 100).toLocaleString(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: cents % 100 ? 2 : 0 });
  const epCode = (season, number) => (number ? `S${season} E${number}` : `Season ${season}`);

  // Builds DOM nodes. Strings always become text nodes; href and src go through
  // the URL checks above and are dropped when they fail.
  function h(tag, props, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(props || {})) {
      if (v == null || v === false) continue;
      if (k === 'class') el.className = v;
      else if (k === 'text') el.textContent = v;
      else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
      else if (k === 'href') {
        const u = safeUrl(v);
        if (u) {
          el.href = u;
          el.target = '_blank';
          el.rel = 'noopener noreferrer';
        }
      } else if (k === 'src') {
        const u = safeImg(v);
        if (u) el.src = u;
      } else el.setAttribute(k, v === true ? '' : String(v));
    }
    for (const c of kids.flat()) {
      if (c == null || c === false) continue;
      el.append(c instanceof Node ? c : String(c));
    }
    return el;
  }

  // ---------- storage ----------

  function readJSON(key) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }
  function writeJSON(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch {
      return false;
    }
  }

  function defaults() {
    return {
      version: 1,
      onboarded: false,
      services: DEFAULT_SERVICES.slice(),
      prices: {},
      lookBackDays: 7,
      lookAheadDays: 21,
      tracked: {},
      downloads: [],
      dismissed: {},
      notified: {},
      notify: false,
      lastRefresh: 0,
    };
  }

  function cleanShowRef(v) {
    if (!v || typeof v !== 'object' || !posInt(v.id)) return null;
    return {
      id: v.id,
      name: str(v.name, 200) || 'Untitled',
      channel: str(v.channel, 100),
      image: safeImg(v.image),
      site: safeUrl(v.site),
    };
  }

  function cleanDownload(v) {
    if (!v || typeof v !== 'object') return null;
    if (typeof v.key !== 'string' || !/^dl:\d+:s\d+(e\d+)?$/.test(v.key)) return null;
    if (!posInt(v.showId) || !posInt(v.season)) return null;
    return {
      key: v.key,
      showId: v.showId,
      showName: str(v.showName, 200) || 'Untitled',
      channel: str(v.channel, 100),
      season: v.season,
      number: posInt(v.number),
      title: str(v.title, 200),
      airdate: isIso(v.airdate) ? v.airdate : '',
      site: safeUrl(v.site),
      done: v.done === true,
      addedAt: Number.isFinite(v.addedAt) ? v.addedAt : Date.now(),
    };
  }

  const cleanCents = (v) => (Number.isInteger(v) && v >= 0 && v <= 100000 ? v : null);

  // Validates anything read from storage or a restored backup, field by field.
  function normalizeState(raw) {
    const s = defaults();
    if (!raw || typeof raw !== 'object') return s;
    if (Array.isArray(raw.services)) s.services = SERVICES.map((x) => x.id).filter((id) => raw.services.includes(id));
    if (raw.prices && typeof raw.prices === 'object') {
      for (const x of SERVICES) {
        const c = cleanCents(raw.prices[x.id]);
        if (c) s.prices[x.id] = c;
      }
    }
    if ([3, 7, 14].includes(raw.lookBackDays)) s.lookBackDays = raw.lookBackDays;
    if ([7, 14, 21, 30].includes(raw.lookAheadDays)) s.lookAheadDays = raw.lookAheadDays;
    if (raw.tracked && typeof raw.tracked === 'object') {
      for (const [k, v] of Object.entries(raw.tracked).slice(0, 500)) {
        const t = cleanShowRef(v);
        if (t && String(t.id) === k) s.tracked[k] = t;
      }
    }
    if (Array.isArray(raw.downloads)) s.downloads = raw.downloads.map(cleanDownload).filter(Boolean).slice(0, 500);
    for (const field of ['dismissed', 'notified']) {
      if (raw[field] && typeof raw[field] === 'object') {
        for (const k of Object.keys(raw[field]).slice(0, 5000)) {
          if (/^(prem|ep):[\w:]{1,40}$/.test(k)) s[field][k] = true;
        }
      }
    }
    s.notify = raw.notify === true;
    s.lastRefresh = Number.isFinite(raw.lastRefresh) ? raw.lastRefresh : 0;
    // People upgrading from the first version already set things up.
    s.onboarded = raw.onboarded === true || s.lastRefresh > 0 || Object.keys(s.tracked).length > 0;
    return s;
  }

  let state = normalizeState(readJSON(STORE_KEY));
  const save = () => writeJSON(STORE_KEY, state);

  // Cache of trimmed API results, keyed "sched:YYYY-MM-DD" and "show:ID".
  let cache = readJSON(CACHE_KEY);
  if (!cache || typeof cache !== 'object' || Array.isArray(cache)) cache = {};
  const cacheAny = (key) => (cache[key] ? cache[key].v : undefined);
  function cacheFresh(key, ttl) {
    const e = cache[key];
    return e && Number.isFinite(e.t) && Date.now() - e.t < ttl ? e.v : undefined;
  }
  const cacheSet = (key, v) => { cache[key] = { t: Date.now(), v }; };
  function saveCache() {
    const cutoff = Date.now() - 3 * DAY;
    for (const k of Object.keys(cache)) {
      if (!cache[k] || !Number.isFinite(cache[k].t) || cache[k].t < cutoff) delete cache[k];
    }
    if (!writeJSON(CACHE_KEY, cache)) {
      // Storage full: drop the cache rather than the user's lists.
      cache = {};
      writeJSON(CACHE_KEY, cache);
    }
  }

  // ---------- TVmaze API ----------

  let queue = Promise.resolve();
  function api(path) {
    const run = queue.then(() => fetchJSON(path, 0));
    queue = run.catch(() => {}).then(() => sleep(REQUEST_GAP_MS));
    return run;
  }

  async function fetchJSON(path, attempt) {
    const res = await fetch(API + path, {
      headers: { Accept: 'application/json' },
      credentials: 'omit',
      referrerPolicy: 'no-referrer',
    });
    if (res.status === 429 && attempt < 3) {
      await sleep(2500 * (attempt + 1));
      return fetchJSON(path, attempt + 1);
    }
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`TVmaze returned ${res.status}`);
    return res.json();
  }

  function serviceFor(channel) {
    const n = str(channel, 100).trim().toLowerCase();
    return n ? SERVICES.find((s) => s.names.includes(n)) || null : null;
  }

  function showRef(show) {
    return {
      id: show.id,
      name: str(show.name, 200) || 'Untitled',
      channel: str((show.webChannel && show.webChannel.name) || (show.network && show.network.name), 100),
      image: safeImg(show.image && show.image.medium),
      site: safeUrl(show.officialSite),
    };
  }

  // Episode 1 of any season on a streaming service's schedule for one date.
  async function premieresFor(date, ttl) {
    const key = 'sched:' + date;
    const hit = cacheFresh(key, ttl);
    if (hit) return hit;
    const data = await api(`/schedule/web?date=${date}`);
    const out = [];
    for (const ep of Array.isArray(data) ? data : []) {
      const show = ep && ((ep._embedded && ep._embedded.show) || ep.show);
      if (!show || !posInt(show.id) || ep.number !== 1 || !posInt(ep.season)) continue;
      if (ep.type && ep.type !== 'regular') continue;
      out.push({
        ...showRef(show),
        season: ep.season,
        airdate: isIso(ep.airdate) ? ep.airdate : date,
        summary: plain(show.summary),
      });
    }
    cacheSet(key, out);
    return out;
  }

  async function showDetail(id, ttl) {
    const key = 'show:' + id;
    const hit = cacheFresh(key, ttl);
    if (hit) return hit;
    const data = await api(`/shows/${encodeURIComponent(id)}?embed=episodes`);
    if (!data || !posInt(data.id)) return null;
    const t = today();
    const eps = ((data._embedded && data._embedded.episodes) || [])
      .filter((e) => e && posInt(e.id) && posInt(e.season) && posInt(e.number) && isIso(e.airdate) && (!e.type || e.type === 'regular'))
      .map((e) => ({ id: e.id, season: e.season, number: e.number, name: str(e.name, 200), airdate: e.airdate }))
      .sort((a, b) => a.airdate.localeCompare(b.airdate) || a.season - b.season || a.number - b.number);
    const past = eps.filter((e) => e.airdate <= t);
    const future = eps.filter((e) => e.airdate > t);
    const last = past[past.length - 1];
    const v = {
      ...showRef(data),
      status: str(data.status, 40),
      summary: plain(data.summary),
      past: past.slice(-3),
      future: future.slice(0, 60),
      // Streaming seasons often drop all at once; count the episodes in the latest drop.
      lastBatch: last ? past.filter((e) => e.airdate === last.airdate && e.season === last.season).length : 0,
    };
    cacheSet(key, v);
    return v;
  }

  async function searchShows(q) {
    const data = await api(`/search/shows?q=${encodeURIComponent(q)}`);
    return (Array.isArray(data) ? data : [])
      .map((r) => r && r.show)
      .filter((s) => s && posInt(s.id))
      .slice(0, 10)
      .map((s) => ({ ...showRef(s), premiered: isIso(s.premiered) ? s.premiered : '', status: str(s.status, 40), summary: plain(s.summary, 200) }));
  }

  // ---------- model ----------

  function windowDates() {
    const base = new Date();
    const dates = [];
    for (let i = -state.lookBackDays; i <= state.lookAheadDays; i++) dates.push(isoDate(addDays(base, i)));
    return dates;
  }

  function collect() {
    const seen = new Map();
    for (const d of windowDates()) {
      const list = cacheAny('sched:' + d);
      if (!Array.isArray(list)) continue;
      for (const p of list) {
        const k = `${p.id}:${p.season}`;
        const prev = seen.get(k);
        if (!prev || p.airdate < prev.airdate) seen.set(k, p);
      }
    }
    const details = {};
    for (const id of Object.keys(state.tracked)) {
      const d = cacheAny('show:' + id);
      if (d) details[id] = d;
    }
    return { premieres: [...seen.values()], details };
  }

  function buildAlerts(model) {
    const from = isoDate(addDays(new Date(), -state.lookBackDays));
    const until = isoDate(addDays(new Date(), state.lookAheadDays));
    const selected = new Set(state.services);
    const alerts = [];
    const keys = new Set();
    const push = (a) => {
      if (!keys.has(a.key)) {
        keys.add(a.key);
        alerts.push(a);
      }
    };
    const premiere = (id, show, svc, season, airdate) =>
      push({ key: `prem:${id}:s${season}`, kind: season === 1 ? 'series' : 'season', show, svc, season, number: null, airdate });

    for (const p of model.premieres) {
      const svc = serviceFor(p.channel);
      if (!svc || !selected.has(svc.id) || p.airdate < from) continue;
      premiere(p.id, p, svc, p.season, p.airdate);
    }

    // Followed shows alert on any service, including ones not selected above.
    for (const [id, d] of Object.entries(model.details)) {
      const svc = serviceFor(d.channel);
      const last = d.past[d.past.length - 1];
      if (last && last.airdate >= from) {
        // Episode 1 alone, or a drop that starts at episode 1, is a premiere.
        if (last.number === d.lastBatch) premiere(id, d, svc, last.season, last.airdate);
        else push({ key: `ep:${last.id}`, kind: 'episode', show: d, svc, season: last.season, number: last.number, title: last.name, count: d.lastBatch, airdate: last.airdate });
      }
      const next = d.future[0];
      if (next && next.number === 1 && next.airdate <= until) premiere(id, d, svc, next.season, next.airdate);
    }

    return alerts.filter((a) => !state.dismissed[a.key]);
  }

  // Keep a service while a followed show is mid-season (an episode in the last
  // 14 days or the next 30). Otherwise suggest pausing until the next return.
  function buildPlan(model) {
    const t = today();
    const recent = isoDate(addDays(new Date(), -14));
    const soon = isoDate(addDays(new Date(), 30));
    return state.services.map((id) => {
      const svc = svcById(id);
      const price = state.prices[id] || 0;
      const shows = Object.values(model.details).filter((d) => {
        const s = serviceFor(d.channel);
        return s && s.id === id;
      });
      const premieresSoon = model.premieres.filter((p) => {
        const s = serviceFor(p.channel);
        return s && s.id === id && p.airdate >= t;
      }).length;
      const nexts = shows
        .filter((d) => d.future[0])
        .map((d) => ({ show: d, ep: d.future[0] }))
        .sort((a, b) => a.ep.airdate.localeCompare(b.ep.airdate));
      const next = nexts[0] || null;
      const active = shows.filter((d) => {
        const last = d.past[d.past.length - 1];
        return (last && last.airdate >= recent) || (d.future[0] && d.future[0].airdate <= soon);
      });

      if (!shows.length) return { svc, price, shows, premieresSoon, kind: 'idle', save: price };
      if (active.length) return { svc, price, shows, premieresSoon, kind: 'keep', next, active, save: 0 };
      const days = next ? daysBetween(t, next.ep.airdate) : null;
      const months = days == null ? null : Math.max(1, Math.floor(days / 30));
      return { svc, price, shows, premieresSoon, kind: 'pause', next, days, months, save: price };
    });
  }

  // ---------- actions ----------

  function linkFor(show, svc) {
    if (svc && hostMatches(show.site, svc.hosts)) return show.site;
    if (svc) return svc.home;
    return safeUrl(show.site) || `https://www.tvmaze.com/shows/${show.id}`;
  }

  const isTracked = (id) => Object.prototype.hasOwnProperty.call(state.tracked, String(id));

  async function track(show) {
    const ref = cleanShowRef(show);
    if (!ref) return;
    state.tracked[String(ref.id)] = ref;
    save();
    renderAll();
    try {
      await showDetail(ref.id, 0);
      saveCache();
    } catch {
      setBanner(`Following ${ref.name}. Its episode dates will load on the next check.`);
    }
    renderAll();
  }

  function untrack(id) {
    delete state.tracked[String(id)];
    save();
    renderAll();
  }

  function downloadKey(showId, season, number) {
    return `dl:${showId}:s${season}` + (number ? `e${number}` : '');
  }
  const inDownloads = (key) => state.downloads.some((d) => d.key === key);

  function addDownload({ show, season, number, title, airdate }) {
    const item = cleanDownload({
      key: downloadKey(show.id, season, number),
      showId: show.id,
      showName: show.name,
      channel: show.channel,
      season,
      number,
      title,
      airdate,
      site: linkFor(show, serviceFor(show.channel)),
      addedAt: Date.now(),
    });
    if (!item || inDownloads(item.key)) return;
    state.downloads.push(item);
    save();
    renderAll();
  }

  function dismiss(key) {
    state.dismissed[key] = true;
    save();
    renderAll();
  }

  // Blob downloads work on a normal web host; the browser shows its usual save flow.
  function saveFile(filename, text, type) {
    const url = URL.createObjectURL(new Blob([text], { type }));
    const a = h('a', { download: filename });
    a.href = url;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10e3);
  }

  // ---------- calendar export ----------

  function icsEscape(s) {
    return String(s).replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n');
  }

  // RFC 5545 lines are limited to 75 octets; continuation lines start with a space.
  function icsFold(line) {
    const enc = new TextEncoder();
    const out = [];
    let cur = '';
    let bytes = 0;
    for (const ch of line) {
      const n = enc.encode(ch).length;
      if (bytes + n > (out.length ? 74 : 75)) {
        out.push(cur);
        cur = '';
        bytes = 0;
      }
      cur += ch;
      bytes += n;
    }
    out.push(cur);
    return out.join('\r\n ');
  }

  function icsEvent(lines, stamp, uid, iso, summary, description) {
    const start = iso.replace(/-/g, '');
    const end = isoDate(addDays(noon(iso), 1)).replace(/-/g, '');
    lines.push(
      'BEGIN:VEVENT',
      `UID:${uid}@episode-radar`,
      `DTSTAMP:${stamp}`,
      `DTSTART;VALUE=DATE:${start}`,
      `DTEND;VALUE=DATE:${end}`,
      `SUMMARY:${icsEscape(summary)}`,
      `DESCRIPTION:${icsEscape(description)}`,
      'TRANSP:TRANSPARENT',
      'BEGIN:VALARM',
      'ACTION:DISPLAY',
      `DESCRIPTION:${icsEscape(summary)}`,
      'TRIGGER;RELATED=START:PT9H',
      'END:VALARM',
      'END:VEVENT',
    );
  }

  function buildICS(model) {
    const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
    const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Episode Radar//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'X-WR-CALNAME:Episode Radar'];
    let episodes = 0;
    let reminders = 0;
    for (const d of Object.values(model.details)) {
      for (const e of d.future.slice(0, 26)) {
        const summary = `${d.name} ${epCode(e.season, e.number)}` + (e.name ? ` · ${e.name}` : '');
        const where = d.channel ? `Streaming on ${d.channel}.` : 'Check your streaming service.';
        icsEvent(lines, stamp, `tvmaze-episode-${e.id}`, e.airdate, summary, `${where} Data from TVmaze.`);
        episodes++;
      }
    }
    // A reminder to resubscribe 3 days before a paused service's show returns.
    const t = today();
    for (const p of buildPlan(model)) {
      if (p.kind !== 'pause' || !p.next) continue;
      const when = isoDate(addDays(noon(p.next.ep.airdate), -3));
      if (when <= t) continue;
      icsEvent(lines, stamp, `resubscribe-${p.svc.id}-${p.next.ep.id}`, when,
        `Resubscribe to ${p.svc.label}`,
        `${p.next.show.name} returns ${fmtDate(p.next.ep.airdate)}. Reminder from Episode Radar.`);
      reminders++;
    }
    lines.push('END:VCALENDAR');
    return { text: lines.map(icsFold).join('\r\n') + '\r\n', episodes, reminders };
  }

  // ---------- refresh ----------

  let busy = false;
  let lastAlerts = [];

  async function refresh(force) {
    if (busy) return;
    busy = true;
    const btn = $('#refresh');
    btn.disabled = true;
    btn.setAttribute('aria-busy', 'true');
    setBanner('');
    const t = today();
    const futureTtl = force ? 30 * MINUTE : STALE_AFTER;
    const dates = windowDates();
    const ids = Object.keys(state.tracked);
    const total = dates.length + ids.length;
    let done = 0;
    let failed = 0;
    const tick = () => setStatus(`Checking TVmaze… ${++done} of ${total}`);

    for (const d of dates) {
      try {
        await premieresFor(d, d < t ? DAY : futureTtl);
      } catch {
        failed++;
      }
      tick();
    }
    renderAll();
    for (const id of ids) {
      try {
        await showDetail(id, futureTtl);
      } catch {
        failed++;
      }
      tick();
    }
    saveCache();

    if (failed < total) {
      state.lastRefresh = Date.now();
      save();
    }
    if (failed === total) {
      setBanner(navigator.onLine === false
        ? "You're offline. Showing the results saved from your last check."
        : "Couldn't reach TVmaze. Showing the results saved from your last check. Try again in a few minutes.");
    } else if (failed) {
      setBanner(`${failed} of ${total} checks failed, so some alerts may be missing. Try again later.`);
    }
    busy = false;
    btn.disabled = false;
    btn.removeAttribute('aria-busy');
    renderAll();
    maybeNotify(lastAlerts);
  }

  // ---------- notifications and install ----------

  const canNotify = () => 'Notification' in window && window.isSecureContext;
  const isIOS = () => /iphone|ipad|ipod/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  const isStandalone = () => (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone === true;
  let swReg = null;
  let installPrompt = null;

  // Phones only allow notifications from a service worker; desktops accept either.
  async function showNotification(title, body) {
    try {
      if (swReg) {
        await swReg.showNotification(title, { body, tag: 'episode-radar', icon: 'icons/icon-192.png' });
        return;
      }
      new Notification(title, { body, tag: 'episode-radar' });
    } catch {
      // Refused by the browser; the in-app alerts still show.
    }
  }

  function maybeNotify(alerts) {
    if (!state.notify || !canNotify() || Notification.permission !== 'granted') return;
    const t = today();
    const fresh = alerts.filter((a) => !state.notified[a.key] && (a.kind !== 'episode' || a.airdate <= t));
    if (!fresh.length) return;
    for (const a of fresh) state.notified[a.key] = true;
    save();
    const names = fresh.slice(0, 3).map((a) => a.show.name).join(', ');
    showNotification('Episode Radar', `${fresh.length} new: ${names}${fresh.length > 3 ? ' and more' : ''}`);
  }

  // Returns true when notifications end up allowed.
  async function enableNotifications() {
    if (!canNotify()) return false;
    let perm = Notification.permission;
    if (perm === 'default') {
      try {
        perm = await Notification.requestPermission();
      } catch {
        perm = 'denied';
      }
    }
    state.notify = perm === 'granted';
    // Start from now: don't notify about alerts already on screen.
    if (state.notify) for (const a of lastAlerts) state.notified[a.key] = true;
    save();
    return state.notify;
  }

  function notifyHelp() {
    if (canNotify()) return null;
    if (isIOS() && !isStandalone()) return 'On iPhone and iPad, notifications work after you add Episode Radar to your Home Screen: tap Share, then Add to Home Screen, and open it from there.';
    if (!window.isSecureContext) return 'Notifications need the app served over https.';
    return "This browser doesn't support notifications. Use Add to calendar on My shows instead.";
  }

  function installHelp() {
    if (isStandalone()) return null;
    if (installPrompt) return 'Install Episode Radar to open it from your home screen, full screen, even offline.';
    if (isIOS()) return 'To install: tap Share, then Add to Home Screen.';
    return null;
  }

  async function promptInstall() {
    if (!installPrompt) return;
    const p = installPrompt;
    installPrompt = null;
    try {
      await p.prompt();
      await p.userChoice;
    } catch {
      // Dismissed or unsupported.
    }
    renderSettings();
    renderOnboardingStep3();
  }

  // ---------- rendering ----------

  let filter = 'all';
  let searchResults = null;

  function setStatus(text) {
    $('#status').textContent = text;
  }
  function setBanner(text) {
    const b = $('#banner');
    b.textContent = text;
    b.hidden = !text;
  }

  function statusText() {
    if (!state.lastRefresh) return 'Not checked yet';
    const d = new Date(state.lastRefresh);
    const sameDay = isoDate(d) === today();
    const time = d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
    return `Updated ${sameDay ? 'today' : d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} at ${time}`;
  }

  function blankPoster(show) {
    return h('div', { class: 'poster-blank', 'aria-hidden': 'true' }, (show.name || '?').charAt(0).toUpperCase());
  }
  function poster(show) {
    const src = safeImg(show.image);
    if (!src) return blankPoster(show);
    const img = h('img', { class: 'poster', src, alt: '', loading: 'lazy', decoding: 'async', referrerpolicy: 'no-referrer' });
    img.addEventListener('error', () => img.replaceWith(blankPoster(show)), { once: true });
    return img;
  }

  function serviceChip(show, svc) {
    if (svc) return h('span', { class: 'svc' }, svc.label);
    return show.channel ? h('span', { class: 'meta' }, show.channel) : null;
  }

  function trackButton(show) {
    const on = isTracked(show.id);
    return h('button', {
      class: 'btn' + (on ? ' btn-on' : ''),
      type: 'button',
      'aria-pressed': on ? 'true' : 'false',
      onclick: () => (on ? untrack(show.id) : track(show)),
    }, on ? 'Following' : 'Follow');
  }

  function downloadButton(args) {
    const key = downloadKey(args.show.id, args.season, args.number);
    const on = inDownloads(key);
    return h('button', {
      class: 'btn' + (on ? ' btn-on' : ''),
      type: 'button',
      disabled: on,
      onclick: () => addDownload(args),
    }, on ? 'In downloads' : 'Add to downloads');
  }

  function openLink(show, svc) {
    return h('a', { class: 'btn', href: linkFor(show, svc) }, svc ? `Open ${svc.label}` : 'Show details');
  }

  function alertCard(a) {
    const out = a.airdate <= today();
    let badge;
    let when;
    if (a.kind === 'series') {
      badge = h('span', { class: 'badge badge-new' }, 'New series');
      when = out ? `Premiered ${fmtDate(a.airdate)}` : `Premieres ${fmtDate(a.airdate)}`;
    } else if (a.kind === 'season') {
      badge = h('span', { class: 'badge badge-season' }, `Season ${a.season}`);
      when = out ? `Returned ${fmtDate(a.airdate)}` : `Returns ${fmtDate(a.airdate)}`;
    } else {
      badge = h('span', { class: 'badge badge-episode' }, a.count > 1 ? `${a.count} new episodes` : 'New episode');
      when = `${epCode(a.season, a.number)}${a.title ? ` · ${a.title}` : ''} · ${fmtDate(a.airdate)}`;
    }
    const show = a.show;
    return h('article', { class: 'card' },
      poster(show),
      h('div', { class: 'card-body' },
        h('div', { class: 'card-top' }, badge, serviceChip(show, a.svc)),
        h('h3', null, show.name),
        h('div', { class: 'meta' }, when),
        show.summary ? h('p', { class: 'summary' }, show.summary) : null,
        h('div', { class: 'actions' },
          trackButton(show),
          downloadButton({ show, season: a.season, number: a.number, title: a.title || '', airdate: a.airdate }),
          openLink(show, a.svc),
          h('button', { class: 'btn btn-quiet', type: 'button', onclick: () => dismiss(a.key), 'aria-label': `Dismiss alert for ${show.name}` }, 'Dismiss'),
        ),
      ),
    );
  }

  function empty(title, body) {
    return h('div', { class: 'empty' }, h('strong', null, title), body);
  }

  function renderAlerts(alerts) {
    const t = today();
    const shown = alerts.filter((a) => filter === 'all' || a.kind === filter);
    const outNow = shown.filter((a) => a.airdate <= t).sort((x, y) => y.airdate.localeCompare(x.airdate));
    const soon = shown.filter((a) => a.airdate > t).sort((x, y) => x.airdate.localeCompare(y.airdate));
    const kids = [];
    if (!state.services.length && !Object.keys(state.tracked).length) {
      kids.push(empty('Choose your services', 'Pick the services you pay for in Settings, and new series and seasons will show up here.'));
    } else if (!shown.length) {
      kids.push(state.lastRefresh
        ? empty('Nothing new right now', `No ${filter === 'all' ? 'premieres or new episodes' : 'alerts of this type'} in the last ${state.lookBackDays} days or the next ${state.lookAheadDays}. Episode Radar checks again automatically.`)
        : empty('Checking for premieres', 'Reading the streaming schedule from TVmaze. The first check takes about 20 seconds.'));
    }
    if (outNow.length) kids.push(h('h3', { class: 'section-title' }, 'Out now'), h('div', { class: 'list' }, outNow.map(alertCard)));
    if (soon.length) kids.push(h('h3', { class: 'section-title' }, 'Coming up'), h('div', { class: 'list' }, soon.map(alertCard)));
    $('#alerts').replaceChildren(...kids);
  }

  const epLine = (e) => (e ? `${epCode(e.season, e.number)} · ${fmtDate(e.airdate)}` : null);

  function showCard(ref, d) {
    const show = d || ref;
    const svc = serviceFor(show.channel);
    const last = d && d.past[d.past.length - 1];
    const next = d && d.future[0];
    const rows = d
      ? [
          ['Latest', epLine(last) || 'No episodes yet'],
          ['Next', epLine(next) || (d.status === 'Ended' ? 'Series ended' : 'Not announced')],
        ]
      : [['Episodes', 'Load on the next check']];
    return h('article', { class: 'card' },
      poster(show),
      h('div', { class: 'card-body' },
        h('div', { class: 'card-top' }, serviceChip(show, svc), d && d.status ? h('span', { class: 'meta' }, d.status) : null),
        h('h3', null, show.name),
        h('dl', { class: 'ep-grid' }, rows.map(([k, v]) => h('div', null, h('dt', null, k), h('dd', null, v)))),
        h('div', { class: 'actions' },
          last ? downloadButton({ show, season: last.season, number: last.number, title: last.name, airdate: last.airdate }) : null,
          openLink(show, svc),
          h('button', { class: 'btn btn-quiet', type: 'button', onclick: () => untrack(show.id) }, 'Unfollow'),
        ),
      ),
    );
  }

  function searchCard(s) {
    const svc = serviceFor(s.channel);
    const year = isIso(s.premiered) ? s.premiered.slice(0, 4) : '';
    return h('article', { class: 'card' },
      poster(s),
      h('div', { class: 'card-body' },
        h('div', { class: 'card-top' }, serviceChip(s, svc), year ? h('span', { class: 'meta' }, year) : null, s.status ? h('span', { class: 'meta' }, s.status) : null),
        h('h3', null, s.name),
        s.summary ? h('p', { class: 'summary' }, s.summary) : null,
        h('div', { class: 'actions' }, trackButton(s), openLink(s, svc)),
      ),
    );
  }

  function renderSearch(target, results, onClear) {
    if (!results) {
      target.replaceChildren();
      return;
    }
    const head = h('div', { class: 'panel-head' },
      h('h3', { class: 'section-title' }, `Search results (${results.length})`),
      h('button', { class: 'btn btn-quiet', type: 'button', onclick: onClear }, 'Clear'));
    const list = results.length
      ? h('div', { class: 'list' }, results.map(searchCard))
      : empty('No matches', 'Check the spelling, or try fewer words.');
    target.replaceChildren(head, list);
  }

  function renderShows(model) {
    const refs = Object.values(state.tracked);
    const key = (r) => {
      const d = model.details[r.id];
      return (d && d.future[0] && d.future[0].airdate) || '9999';
    };
    refs.sort((a, b) => key(a).localeCompare(key(b)) || a.name.localeCompare(b.name));
    $('#shows').replaceChildren(refs.length
      ? h('div', { class: 'list' }, refs.map((r) => showCard(r, model.details[r.id])))
      : empty('No shows yet', 'Search above, or tap Follow on any alert. You get an alert for every new episode of a show you follow, on any service.'));
    renderSearch($('#search-results'), searchResults, () => { searchResults = null; renderAll(); });
  }

  function renderDownloads() {
    const items = state.downloads.slice().sort((a, b) => Number(a.done) - Number(b.done) || b.addedAt - a.addedAt);
    if (!items.length) {
      $('#downloads').replaceChildren(empty('Nothing to download', 'Tap "Add to downloads" on an alert or a show to build your list.'));
      return;
    }
    const t = today();
    const cards = items.map((d) => {
      const svc = serviceFor(d.channel);
      const what = d.number ? `${epCode(d.season, d.number)}${d.title ? ` · ${d.title}` : ''}` : `Season ${d.season}`;
      const avail = d.airdate ? (d.airdate > t ? `Available ${fmtDate(d.airdate)}` : `Out since ${fmtDate(d.airdate)}`) : '';
      const id = `dl-${d.key.replace(/[^\w]/g, '-')}`;
      const box = h('input', { type: 'checkbox', id, 'aria-label': `Downloaded ${d.showName} ${what}` });
      box.checked = d.done;
      box.addEventListener('change', () => {
        d.done = box.checked;
        save();
        renderAll();
      });
      return h('article', { class: 'card no-poster' },
        h('div', { class: 'dl' + (d.done ? ' done' : '') },
          box,
          h('div', { class: 'card-body' },
            h('div', { class: 'card-top' }, serviceChip({ channel: d.channel }, svc)),
            h('label', { class: 'dl-title', for: id }, h('strong', null, d.showName), ` · ${what}`),
            avail ? h('div', { class: 'meta' }, avail) : null,
          ),
          h('div', { class: 'actions' },
            h('a', { class: 'btn', href: d.site || (svc && svc.home) }, svc ? `Open ${svc.label}` : 'Open'),
            h('button', {
              class: 'btn btn-quiet',
              type: 'button',
              onclick: () => {
                state.downloads = state.downloads.filter((x) => x.key !== d.key);
                save();
                renderAll();
              },
            }, 'Remove'),
          ),
        ),
      );
    });
    $('#downloads').replaceChildren(h('div', { class: 'list' }, cards));
  }

  function renderSavings(model) {
    const root = $('#savings');
    if (!state.services.length) {
      root.replaceChildren(empty('No services yet', 'Tick the services you pay for in Settings to see which ones you could pause.'));
      return;
    }
    const plan = buildPlan(model);
    const pausable = plan.filter((p) => p.kind !== 'keep');
    const monthly = pausable.reduce((sum, p) => sum + p.save, 0);
    const missingPrices = plan.filter((p) => !p.price).map((p) => p.svc.label);
    const summary = h('div', { class: 'save-summary' },
      pausable.length
        ? [
            h('span', { class: 'meta' }, 'You could pause'),
            h('span', { class: 'save-amount' }, monthly ? `${money(monthly)} a month` : `${pausable.length} service${pausable.length === 1 ? '' : 's'}`),
            h('span', { class: 'meta' }, `Nothing you follow airs on ${listJoin(pausable.map((p) => p.svc.label))} in the next 30 days.`),
          ]
        : [
            h('span', { class: 'save-amount' }, 'Keep them all'),
            h('span', { class: 'meta' }, 'Every service you pay for has a show you follow airing now or within 30 days.'),
          ],
      missingPrices.length ? h('span', { class: 'hint' }, `Add a monthly price for ${listJoin(missingPrices)} in Settings to include ${missingPrices.length === 1 ? 'it' : 'them'} in the total.`) : null,
    );

    const cards = plan.map((p) => {
      let pill;
      let line;
      if (p.kind === 'keep') {
        pill = h('span', { class: 'verdict verdict-keep' }, 'Keep');
        const lead = p.next || null;
        line = lead && lead.ep.airdate <= isoDate(addDays(new Date(), 30))
          ? `${lead.show.name}: ${epCode(lead.ep.season, lead.ep.number)} on ${fmtDate(lead.ep.airdate)}.`
          : `${p.active[0].name} is mid-season.`;
      } else if (p.kind === 'pause') {
        pill = h('span', { class: 'verdict verdict-pause' }, p.next ? `Pause, rejoin ${fmtDate(isoDate(addDays(noon(p.next.ep.airdate), -3)))}` : 'Pause');
        line = p.next
          ? `${p.next.show.name} returns ${fmtDate(p.next.ep.airdate)}, about ${p.months} month${p.months === 1 ? '' : 's'} away.${p.price ? ` Pausing saves about ${money(p.price * p.months)}.` : ''}`
          : 'No new episodes announced for the shows you follow here.';
      } else {
        pill = h('span', { class: 'verdict verdict-idle' }, 'Not following anything');
        line = p.premieresSoon
          ? `You don't follow any shows here. ${p.premieresSoon} premiere${p.premieresSoon === 1 ? '' : 's'} coming up; see Alerts.`
          : "You don't follow any shows here.";
      }
      return h('article', { class: 'save-card' },
        h('div', { class: 'save-top' },
          h('h3', null, p.svc.label, p.price ? h('span', { class: 'meta' }, ` · ${money(p.price)}/mo`) : null),
          pill),
        h('div', { class: 'meta' }, line),
        p.shows.length ? h('ul', { class: 'save-shows' }, p.shows.map((d) => h('li', null, d.name))) : null,
      );
    });

    const reminder = pausable.some((p) => p.kind === 'pause' && p.next)
      ? h('p', { class: 'hint' }, 'Add to calendar on My shows includes a reminder to resubscribe 3 days before each show returns.')
      : null;
    root.replaceChildren(summary, h('div', { class: 'list' }, cards), reminder);
  }

  // Service checkboxes with monthly prices, shared by Settings and setup.
  function renderServiceRows(target, prefix) {
    const rows = SERVICES.map((s) => {
      const on = state.services.includes(s.id);
      const box = h('input', { type: 'checkbox', id: `${prefix}-svc-${s.id}` });
      box.checked = on;
      const price = h('input', {
        type: 'number', id: `${prefix}-price-${s.id}`, inputmode: 'decimal', min: '0', max: '1000', step: '0.01',
        placeholder: '0.00', 'aria-label': `${s.label} monthly price in US dollars`,
      });
      if (state.prices[s.id]) price.value = (state.prices[s.id] / 100).toFixed(2);
      price.disabled = !on;
      box.addEventListener('change', () => {
        state.services = SERVICES.filter((x) => (x.id === s.id ? box.checked : state.services.includes(x.id))).map((x) => x.id);
        save();
        renderAll();
      });
      price.addEventListener('change', () => {
        const n = Number(price.value);
        const cents = Number.isFinite(n) && n > 0 ? Math.round(n * 100) : 0;
        if (cleanCents(cents) && cents > 0) state.prices[s.id] = cents;
        else delete state.prices[s.id];
        save();
        renderAll();
      });
      return h('div', { class: 'svc-row' + (on ? ' on' : '') },
        h('label', { for: `${prefix}-svc-${s.id}` }, box, s.label),
        h('span', { class: 'price' }, '$', price, '/mo'));
    });
    // Keep focus on the field being edited when this re-renders.
    const active = document.activeElement && document.activeElement.id;
    target.replaceChildren(...rows);
    if (active && active.startsWith(prefix + '-')) {
      const el = document.getElementById(active);
      if (el) el.focus();
    }
  }

  function renderSettings() {
    renderServiceRows($('#services'), 'set');
    $('#look-back').value = String(state.lookBackDays);
    $('#look-ahead').value = String(state.lookAheadDays);
    const notify = $('#notify');
    notify.checked = state.notify && canNotify() && Notification.permission === 'granted';
    notify.disabled = !canNotify();
    const help = notifyHelp();
    if (help) $('#notify-hint').textContent = help;
    const ih = installHelp();
    $('#install-box').hidden = !ih;
    $('#install').hidden = !installPrompt;
    $('#install-hint').textContent = ih || '';
  }

  function setCount(id, n) {
    $(id).textContent = n ? String(n) : '';
  }

  function renderAll() {
    const model = collect();
    lastAlerts = buildAlerts(model);
    renderAlerts(lastAlerts);
    renderShows(model);
    renderDownloads();
    renderSavings(model);
    renderSettings();
    if (!$('#onboarding').hidden) renderOnboarding(model);
    setCount('#count-alerts', lastAlerts.length);
    setCount('#count-shows', Object.keys(state.tracked).length);
    setCount('#count-downloads', state.downloads.filter((d) => !d.done).length);
    document.title = lastAlerts.length ? `(${lastAlerts.length}) Episode Radar` : 'Episode Radar';
    if (!busy) setStatus(statusText());
  }

  // ---------- setup ----------

  let obStep = 1;
  let obResults = null;

  function openOnboarding() {
    obStep = 1;
    obResults = null;
    $('#onboarding').hidden = false;
    for (const id of ['.top', '#tabs', '#main']) $(id).setAttribute('inert', '');
    renderOnboarding(collect());
    $('#ob-title-1').setAttribute('tabindex', '-1');
    $('#ob-title-1').focus();
  }

  function closeOnboarding() {
    state.onboarded = true;
    save();
    $('#onboarding').hidden = true;
    for (const id of ['.top', '#tabs', '#main']) $(id).removeAttribute('inert');
    showTab('alerts');
    renderAll();
    if (Date.now() - state.lastRefresh > STALE_AFTER) refresh(false);
  }

  function goStep(n) {
    obStep = n;
    renderOnboarding(collect());
    const title = $(`#ob-title-${n}`);
    title.setAttribute('tabindex', '-1');
    title.focus();
    $('#onboarding').scrollTop = 0;
  }

  function renderOnboardingStep3() {
    const help = notifyHelp();
    const btn = $('#ob-notify');
    const granted = canNotify() && Notification.permission === 'granted' && state.notify;
    btn.hidden = !canNotify();
    btn.textContent = granted ? 'On' : 'Turn on';
    btn.className = 'btn' + (granted ? ' btn-on' : '');
    btn.disabled = granted;
    $('#ob-notify-hint').textContent = help || 'Get a notification when something new shows up.';
    const ih = installHelp();
    $('#ob-install-row').hidden = !ih;
    $('#ob-install').hidden = !installPrompt;
    $('#ob-install-hint').textContent = ih || '';
  }

  function renderOnboarding(model) {
    $('#ob-step').textContent = `Step ${obStep} of 3`;
    for (const dot of document.querySelectorAll('.ob-dot')) dot.classList.toggle('on', Number(dot.dataset.dot) <= obStep);
    for (const pane of document.querySelectorAll('.ob-pane')) pane.hidden = Number(pane.dataset.step) !== obStep;
    $('#onboarding').setAttribute('aria-labelledby', `ob-title-${obStep}`);
    if (obStep === 1) renderServiceRows($('#ob-services'), 'ob');
    if (obStep === 2) {
      renderSearch($('#ob-results'), obResults, () => { obResults = null; renderOnboarding(collect()); });
      const t = today();
      const selected = new Set(state.services);
      const soon = model.premieres
        .filter((p) => {
          const s = serviceFor(p.channel);
          return s && selected.has(s.id) && p.airdate >= isoDate(addDays(new Date(), -state.lookBackDays));
        })
        .sort((a, b) => Math.abs(daysBetween(t, a.airdate)) - Math.abs(daysBetween(t, b.airdate)))
        .slice(0, 8);
      $('#ob-premieres').replaceChildren(soon.length
        ? h('div', { class: 'list' }, soon.map((p) => h('div', { class: 'mini' },
            h('div', null,
              h('strong', null, p.name),
              h('span', { class: 'meta' }, `${serviceFor(p.channel).label} · ${p.season === 1 ? 'New series' : `Season ${p.season}`} · ${fmtDate(p.airdate)}`)),
            trackButton(p))))
        : empty(busy ? 'Loading premieres…' : 'No premieres found yet', busy ? 'Reading the schedule from TVmaze. This takes about 20 seconds.' : 'Search for a show above instead.'));
    }
    if (obStep === 3) renderOnboardingStep3();
  }

  // ---------- tabs ----------

  function showTab(name, focus) {
    if (name === 'tracking') name = 'shows';
    if (!TABS.includes(name)) name = 'alerts';
    for (const t of TABS) {
      const tab = $(`#tab-${t}`);
      const on = t === name;
      tab.setAttribute('aria-selected', on ? 'true' : 'false');
      tab.tabIndex = on ? 0 : -1;
      $(`#panel-${t}`).hidden = !on;
      if (on && focus) tab.focus();
    }
    try {
      history.replaceState(null, '', '#' + name);
    } catch {
      // Some contexts refuse history changes; the tab still switches.
    }
  }

  // ---------- wiring ----------

  async function doSearch(q, assign) {
    q = q.trim().slice(0, 100);
    if (!q) return;
    setStatus(`Searching for "${q}"…`);
    try {
      assign(await searchShows(q));
      setBanner('');
    } catch {
      setBanner("Search couldn't reach TVmaze. Check your connection and try again.");
    }
    renderAll();
  }

  function wire() {
    for (const t of TABS) $(`#tab-${t}`).addEventListener('click', () => showTab(t));
    $('#tabs').addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      const cur = TABS.findIndex((t) => $(`#tab-${t}`).getAttribute('aria-selected') === 'true');
      const next = (cur + (e.key === 'ArrowRight' ? 1 : TABS.length - 1)) % TABS.length;
      showTab(TABS.at(next), true);
    });

    $('#refresh').addEventListener('click', () => refresh(true));

    for (const chip of document.querySelectorAll('[data-filter]')) {
      chip.addEventListener('click', () => {
        filter = chip.dataset.filter;
        for (const c of document.querySelectorAll('[data-filter]')) c.setAttribute('aria-pressed', c === chip ? 'true' : 'false');
        renderAll();
      });
    }

    $('#search-form').addEventListener('submit', (e) => {
      e.preventDefault();
      doSearch($('#search-q').value, (r) => { searchResults = r; });
    });

    $('#export-ics').addEventListener('click', () => {
      const { text, episodes, reminders } = buildICS(collect());
      if (!episodes && !reminders) {
        setBanner('None of your shows has an announced upcoming episode yet, so there is nothing to add to your calendar.');
        return;
      }
      setBanner('');
      saveFile('episode-radar.ics', text, 'text/calendar;charset=utf-8');
      const parts = [`${episodes} episode${episodes === 1 ? '' : 's'}`];
      if (reminders) parts.push(`${reminders} resubscribe reminder${reminders === 1 ? '' : 's'}`);
      setStatus(`Saved ${parts.join(' and ')}. Open episode-radar.ics to add them to your calendar.`);
    });

    $('#look-back').addEventListener('change', (e) => {
      state.lookBackDays = Number(e.target.value);
      state = normalizeState(state);
      save();
      refresh(false);
    });
    $('#look-ahead').addEventListener('change', (e) => {
      state.lookAheadDays = Number(e.target.value);
      state = normalizeState(state);
      save();
      refresh(false);
    });

    $('#notify').addEventListener('change', async (e) => {
      if (!e.target.checked) {
        state.notify = false;
        save();
        return;
      }
      const ok = await enableNotifications();
      if (!ok) setBanner('Notifications are blocked for this app. Allow them in your browser or phone settings, then turn this on again.');
      renderSettings();
    });

    $('#install').addEventListener('click', promptInstall);

    $('#export-json').addEventListener('click', () => {
      saveFile('episode-radar-backup.json', JSON.stringify(state, null, 2), 'application/json');
    });

    $('#import-json').addEventListener('change', async (e) => {
      const file = e.target.files && e.target.files[0];
      e.target.value = '';
      if (!file) return;
      if (file.size > 1024 * 1024) {
        setBanner('That file is too large to be an Episode Radar backup.');
        return;
      }
      try {
        const raw = JSON.parse(await file.text());
        if (!raw || raw.version !== 1) throw new Error('not a backup');
        state = normalizeState(raw);
        state.onboarded = true;
        save();
        setBanner('');
        setStatus('Backup restored.');
        renderAll();
        refresh(false);
      } catch {
        setBanner("That file isn't an Episode Radar backup. Choose the .json file saved from Save backup.");
      }
    });

    $('#rerun-setup').addEventListener('click', openOnboarding);
    $('#reset').addEventListener('click', () => { $('#reset-confirm').hidden = false; });
    $('#reset-no').addEventListener('click', () => { $('#reset-confirm').hidden = true; });
    $('#reset-yes').addEventListener('click', () => {
      state = defaults();
      cache = {};
      save();
      saveCache();
      searchResults = null;
      $('#reset-confirm').hidden = true;
      renderAll();
      openOnboarding();
    });

    // Setup
    $('#ob-skip').addEventListener('click', closeOnboarding);
    $('#ob-next-1').addEventListener('click', () => {
      goStep(2);
      // Load premieres for the chosen services while the person picks shows.
      refresh(false);
    });
    $('#ob-back-2').addEventListener('click', () => goStep(1));
    $('#ob-next-2').addEventListener('click', () => goStep(3));
    $('#ob-back-3').addEventListener('click', () => goStep(2));
    $('#ob-done').addEventListener('click', closeOnboarding);
    $('#ob-search').addEventListener('submit', (e) => {
      e.preventDefault();
      doSearch($('#ob-q').value, (r) => { obResults = r; });
    });
    $('#ob-notify').addEventListener('click', async () => {
      await enableNotifications();
      renderOnboardingStep3();
    });
    $('#ob-install').addEventListener('click', promptInstall);

    // Install and offline support.
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      installPrompt = e;
      renderSettings();
      if (!$('#onboarding').hidden) renderOnboardingStep3();
    });
    window.addEventListener('appinstalled', () => {
      installPrompt = null;
      renderSettings();
    });
    if ('serviceWorker' in navigator && window.isSecureContext) {
      navigator.serviceWorker.register('sw.js').then((reg) => { swReg = reg; }).catch(() => {});
    }

    // Re-check while the app stays open, and when it comes back to the foreground.
    const checkStale = () => {
      if (!document.hidden && state.onboarded && Date.now() - state.lastRefresh > STALE_AFTER) refresh(false);
    };
    setInterval(checkStale, 15 * MINUTE);
    document.addEventListener('visibilitychange', checkStale);
    window.addEventListener('hashchange', () => showTab(location.hash.slice(1)));
  }

  wire();
  showTab(location.hash.slice(1));
  renderAll();
  if (!state.onboarded) openOnboarding();
  else if (Date.now() - state.lastRefresh > STALE_AFTER) refresh(false);
  else maybeNotify(lastAlerts);
})();
