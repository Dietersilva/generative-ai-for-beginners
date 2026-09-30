'use strict';

// Episode Radar: new-series, new-season and new-episode alerts for the streaming
// services you pay for. Data comes from the public TVmaze API. Everything the
// user saves stays in this browser's localStorage. The page never uses innerHTML:
// every string from the API is rendered as text, and every link or image URL is
// checked before it reaches the DOM.
(() => {
  const API = 'https://api.tvmaze.com';
  const STORE_KEY = 'episodeRadar.v1';
  const CACHE_KEY = 'episodeRadar.cache.v1';
  const MINUTE = 60e3;
  const HOUR = 60 * MINUTE;
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

  // ---------- small helpers ----------

  const $ = (sel) => document.querySelector(sel);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const str = (v, max) => (typeof v === 'string' ? v.slice(0, max) : '');
  const posInt = (v) => (Number.isInteger(v) && v > 0 && v < 1e9 ? v : null);
  const isIso = (v) => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v);

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

  // TVmaze summaries are HTML. DOMParser builds an inert document (no scripts,
  // no image loads), so reading textContent from it is safe.
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

  function fmtDate(iso) {
    if (!isIso(iso)) return 'date not announced';
    const d = new Date(iso + 'T12:00:00');
    const opts = { weekday: 'short', month: 'short', day: 'numeric' };
    if (d.getFullYear() !== new Date().getFullYear()) opts.year = 'numeric';
    return d.toLocaleDateString(undefined, opts);
  }

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
      services: DEFAULT_SERVICES.slice(),
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

  // Validates anything read from storage or a restored backup, field by field.
  function normalizeState(raw) {
    const s = defaults();
    if (!raw || typeof raw !== 'object') return s;
    if (Array.isArray(raw.services)) s.services = raw.services.filter((id) => SERVICES.some((x) => x.id === id));
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
    const cutoff = Date.now() - 3 * 24 * HOUR;
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
        genres: Array.isArray(show.genres) ? show.genres.filter((g) => typeof g === 'string').slice(0, 3) : [],
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

    for (const p of model.premieres) {
      const svc = serviceFor(p.channel);
      if (!svc || !selected.has(svc.id) || p.airdate < from) continue;
      push({ key: `prem:${p.id}:s${p.season}`, kind: p.season === 1 ? 'series' : 'season', show: p, svc, season: p.season, number: null, airdate: p.airdate });
    }

    // Tracked shows alert on any service, including ones not selected above.
    for (const [id, d] of Object.entries(model.details)) {
      const svc = serviceFor(d.channel);
      const last = d.past[d.past.length - 1];
      if (last && last.airdate >= from) {
        // Episode 1 alone, or a drop that starts at episode 1, is a premiere.
        if (last.number === d.lastBatch) {
          push({ key: `prem:${id}:s${last.season}`, kind: last.season === 1 ? 'series' : 'season', show: d, svc, season: last.season, number: null, airdate: last.airdate });
        } else {
          push({ key: `ep:${last.id}`, kind: 'episode', show: d, svc, season: last.season, number: last.number, title: last.name, count: d.lastBatch, airdate: last.airdate });
        }
      }
      const next = d.future[0];
      if (next && next.number === 1 && next.airdate <= until) {
        push({ key: `prem:${id}:s${next.season}`, kind: next.season === 1 ? 'series' : 'season', show: d, svc, season: next.season, number: null, airdate: next.airdate });
      }
    }

    return alerts.filter((a) => !state.dismissed[a.key]);
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
      setBanner(`Tracking ${ref.name}. Its episode dates will load on the next refresh.`);
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

  function buildICS(details) {
    const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
    const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Episode Radar//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'X-WR-CALNAME:Episode Radar'];
    let count = 0;
    for (const d of Object.values(details)) {
      for (const e of d.future.slice(0, 26)) {
        const start = e.airdate.replace(/-/g, '');
        const end = isoDate(addDays(new Date(e.airdate + 'T12:00:00'), 1)).replace(/-/g, '');
        const summary = `${d.name} ${epCode(e.season, e.number)}` + (e.name ? ` · ${e.name}` : '');
        const where = d.channel ? `Streaming on ${d.channel}.` : 'Check your streaming service.';
        lines.push(
          'BEGIN:VEVENT',
          `UID:tvmaze-episode-${e.id}@episode-radar`,
          `DTSTAMP:${stamp}`,
          `DTSTART;VALUE=DATE:${start}`,
          `DTEND;VALUE=DATE:${end}`,
          `SUMMARY:${icsEscape(summary)}`,
          `DESCRIPTION:${icsEscape(where + ' Data from TVmaze.')}`,
          'TRANSP:TRANSPARENT',
          'BEGIN:VALARM',
          'ACTION:DISPLAY',
          `DESCRIPTION:${icsEscape(summary)}`,
          'TRIGGER;RELATED=START:PT9H',
          'END:VALARM',
          'END:VEVENT',
        );
        count++;
      }
    }
    lines.push('END:VCALENDAR');
    return { text: lines.map(icsFold).join('\r\n') + '\r\n', count };
  }

  // ---------- refresh ----------

  let busy = false;
  let lastAlerts = [];

  async function refresh(force) {
    if (busy) return;
    busy = true;
    $('#refresh').disabled = true;
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
        await premieresFor(d, d < t ? 24 * HOUR : futureTtl);
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
        : "Couldn't reach TVmaze. Showing the results saved from your last check. Try Refresh again in a few minutes.");
    } else if (failed) {
      setBanner(`${failed} of ${total} checks failed, so some alerts may be missing. Try Refresh again later.`);
    }
    busy = false;
    $('#refresh').disabled = false;
    renderAll();
    maybeNotify(lastAlerts);
  }

  // ---------- notifications ----------

  const canNotify = () => 'Notification' in window && window.isSecureContext;

  function maybeNotify(alerts) {
    if (!state.notify || !canNotify() || Notification.permission !== 'granted') return;
    const t = today();
    const fresh = alerts.filter((a) => !state.notified[a.key] && (a.kind !== 'episode' || a.airdate <= t));
    if (!fresh.length) return;
    for (const a of fresh) state.notified[a.key] = true;
    save();
    const names = fresh.slice(0, 3).map((a) => a.show.name).join(', ');
    try {
      new Notification('Episode Radar', {
        body: `${fresh.length} new: ${names}${fresh.length > 3 ? ' and more' : ''}`,
        tag: 'episode-radar',
      });
    } catch {
      // Some mobile browsers only allow notifications from a service worker.
    }
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

  function poster(show) {
    const src = safeImg(show.image);
    if (!src) return h('div', { class: 'poster-blank', 'aria-hidden': 'true' }, (show.name || '?').charAt(0).toUpperCase());
    const img = h('img', { class: 'poster', src, alt: '', loading: 'lazy', decoding: 'async', referrerpolicy: 'no-referrer' });
    img.addEventListener('error', () => img.replaceWith(h('div', { class: 'poster-blank', 'aria-hidden': 'true' }, (show.name || '?').charAt(0).toUpperCase())), { once: true });
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
    }, on ? 'Tracking' : 'Track');
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
    const root = $('#alerts');
    const t = today();
    const shown = alerts.filter((a) => filter === 'all' || a.kind === filter);
    const outNow = shown.filter((a) => a.airdate <= t).sort((x, y) => y.airdate.localeCompare(x.airdate));
    const soon = shown.filter((a) => a.airdate > t).sort((x, y) => x.airdate.localeCompare(y.airdate));
    const kids = [];
    if (!state.services.length && !Object.keys(state.tracked).length) {
      kids.push(empty('Choose your services', 'Pick the services you subscribe to in Settings, and new series and seasons will show up here.'));
    } else if (!shown.length) {
      kids.push(state.lastRefresh
        ? empty('Nothing new right now', `No ${filter === 'all' ? 'premieres or new episodes' : 'alerts of this type'} in the last ${state.lookBackDays} days or the next ${state.lookAheadDays}. Tap Refresh to check again.`)
        : empty('Checking for premieres', 'Episode Radar is reading the streaming schedule from TVmaze. This takes about 20 seconds the first time.'));
    }
    if (outNow.length) kids.push(h('h3', { class: 'section-title' }, 'Out now'), h('div', { class: 'list' }, outNow.map(alertCard)));
    if (soon.length) kids.push(h('h3', { class: 'section-title' }, 'Coming up'), h('div', { class: 'list' }, soon.map(alertCard)));
    root.replaceChildren(...kids);
  }

  function epLine(e) {
    return e ? `${epCode(e.season, e.number)} · ${fmtDate(e.airdate)}` : null;
  }

  function trackedCard(ref, d) {
    const show = d || ref;
    const svc = serviceFor(show.channel);
    const last = d && d.past[d.past.length - 1];
    const next = d && d.future[0];
    const rows = d
      ? [
          ['Latest', epLine(last) || 'No episodes yet'],
          ['Next', epLine(next) || (d.status === 'Ended' ? 'Series ended' : 'Not announced')],
        ]
      : [['Episodes', 'Load on next refresh']];
    return h('article', { class: 'card' },
      poster(show),
      h('div', { class: 'card-body' },
        h('div', { class: 'card-top' }, serviceChip(show, svc), d && d.status ? h('span', { class: 'meta' }, d.status) : null),
        h('h3', null, show.name),
        h('dl', { class: 'ep-grid' }, rows.map(([k, v]) => h('div', null, h('dt', null, k), h('dd', null, v)))),
        h('div', { class: 'actions' },
          last ? downloadButton({ show, season: last.season, number: last.number, title: last.name, airdate: last.airdate }) : null,
          openLink(show, svc),
          h('button', { class: 'btn btn-quiet', type: 'button', onclick: () => untrack(show.id) }, 'Stop tracking'),
        ),
      ),
    );
  }

  function renderTracking(model) {
    const refs = Object.values(state.tracked);
    const key = (r) => {
      const d = model.details[r.id];
      return (d && d.future[0] && d.future[0].airdate) || '9999';
    };
    refs.sort((a, b) => key(a).localeCompare(key(b)) || a.name.localeCompare(b.name));
    const kids = refs.length
      ? [h('div', { class: 'list' }, refs.map((r) => trackedCard(r, model.details[r.id])))]
      : [empty('No tracked shows yet', 'Search for a show above, or tap Track on any alert. Tracked shows alert you about new episodes on any service.')];
    $('#tracking').replaceChildren(...kids);

    const sr = $('#search-results');
    if (!searchResults) {
      sr.replaceChildren();
      return;
    }
    const head = h('div', { class: 'panel-head' },
      h('h3', { class: 'section-title' }, `Search results (${searchResults.length})`),
      h('button', { class: 'btn btn-quiet', type: 'button', onclick: () => { searchResults = null; renderAll(); } }, 'Clear'));
    const list = searchResults.length
      ? h('div', { class: 'list' }, searchResults.map((s) => {
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
        }))
      : empty('No matches', 'Check the spelling, or try fewer words.');
    sr.replaceChildren(head, list);
  }

  function renderDownloads() {
    const items = state.downloads.slice().sort((a, b) => Number(a.done) - Number(b.done) || b.addedAt - a.addedAt);
    if (!items.length) {
      $('#downloads').replaceChildren(empty('Nothing to download', 'Tap "Add to downloads" on an alert or a tracked show to build your list.'));
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

  function renderSettings() {
    const boxes = SERVICES.map((s) => {
      const box = h('input', { type: 'checkbox', id: `svc-${s.id}` });
      box.checked = state.services.includes(s.id);
      box.addEventListener('change', () => {
        state.services = SERVICES.filter((x) => (x.id === s.id ? box.checked : state.services.includes(x.id))).map((x) => x.id);
        save();
        renderAll();
      });
      return h('label', { for: `svc-${s.id}` }, box, s.label);
    });
    $('#services').replaceChildren(...boxes);
    $('#look-back').value = String(state.lookBackDays);
    $('#look-ahead').value = String(state.lookAheadDays);
    const notify = $('#notify');
    notify.checked = state.notify && canNotify() && Notification.permission === 'granted';
    notify.disabled = !canNotify();
    if (!canNotify()) {
      $('#notify-hint').textContent = 'Notifications need the page served over https. For reminders when the page is closed, use "Add upcoming to calendar" on the Tracking tab.';
    }
  }

  function setCount(id, n) {
    $(id).textContent = n ? String(n) : '';
  }

  function renderAll() {
    const model = collect();
    lastAlerts = buildAlerts(model);
    renderAlerts(lastAlerts);
    renderTracking(model);
    renderDownloads();
    renderSettings();
    setCount('#count-alerts', lastAlerts.length);
    setCount('#count-tracking', Object.keys(state.tracked).length);
    setCount('#count-downloads', state.downloads.filter((d) => !d.done).length);
    document.title = lastAlerts.length ? `(${lastAlerts.length}) Episode Radar` : 'Episode Radar';
    if (!busy) setStatus(statusText());
  }

  // ---------- tabs ----------

  const TABS = ['alerts', 'tracking', 'downloads', 'settings'];
  function showTab(name, focus) {
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
      // file:// pages can refuse history changes; the tab still switches.
    }
  }

  // ---------- wiring ----------

  function wire() {
    for (const t of TABS) $(`#tab-${t}`).addEventListener('click', () => showTab(t));
    $('.tabs').addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      const cur = TABS.findIndex((t) => $(`#tab-${t}`).getAttribute('aria-selected') === 'true');
      const next = (cur + (e.key === 'ArrowRight' ? 1 : TABS.length - 1)) % TABS.length;
      showTab(TABS[next], true);
    });

    $('#refresh').addEventListener('click', () => refresh(true));

    for (const chip of document.querySelectorAll('[data-filter]')) {
      chip.addEventListener('click', () => {
        filter = chip.dataset.filter;
        for (const c of document.querySelectorAll('[data-filter]')) c.setAttribute('aria-pressed', c === chip ? 'true' : 'false');
        renderAll();
      });
    }

    $('#search-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const q = $('#search-q').value.trim().slice(0, 100);
      if (!q) return;
      setStatus(`Searching for "${q}"…`);
      try {
        const data = await api(`/search/shows?q=${encodeURIComponent(q)}`);
        searchResults = (Array.isArray(data) ? data : [])
          .map((r) => r && r.show)
          .filter((s) => s && posInt(s.id))
          .slice(0, 10)
          .map((s) => ({ ...showRef(s), premiered: isIso(s.premiered) ? s.premiered : '', status: str(s.status, 40), summary: plain(s.summary, 200) }));
        setBanner('');
      } catch {
        setBanner("Search couldn't reach TVmaze. Check your connection and try again.");
      }
      renderAll();
    });

    $('#export-ics').addEventListener('click', () => {
      const { text, count } = buildICS(collect().details);
      if (!count) {
        setBanner('None of your tracked shows has an announced upcoming episode yet, so there is nothing to add to your calendar.');
        return;
      }
      setBanner('');
      saveFile('episode-radar.ics', text, 'text/calendar;charset=utf-8');
      setStatus(`Saved ${count} upcoming episode${count === 1 ? '' : 's'} to episode-radar.ics. Open it to add them to your calendar.`);
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
      let perm = Notification.permission;
      if (perm === 'default') {
        try {
          perm = await Notification.requestPermission();
        } catch {
          perm = 'denied';
        }
      }
      state.notify = perm === 'granted';
      if (state.notify) {
        // Start from now: don't fire a notification for alerts already on screen.
        for (const a of lastAlerts) state.notified[a.key] = true;
      } else {
        setBanner('Notifications are blocked for this site. Allow them in your browser settings, then turn this on again.');
      }
      save();
      renderSettings();
    });

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
        save();
        setBanner('');
        setStatus('Backup restored.');
        renderAll();
        refresh(false);
      } catch {
        setBanner("That file isn't an Episode Radar backup. Choose the .json file saved from Save backup.");
      }
    });

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
      refresh(false);
    });

    // Re-check while the page stays open, and when it comes back to the foreground.
    const checkStale = () => {
      if (!document.hidden && Date.now() - state.lastRefresh > STALE_AFTER) refresh(false);
    };
    setInterval(checkStale, 15 * MINUTE);
    document.addEventListener('visibilitychange', checkStale);
    window.addEventListener('hashchange', () => showTab(location.hash.slice(1)));
  }

  wire();
  showTab(location.hash.slice(1));
  renderAll();
  if (Date.now() - state.lastRefresh > STALE_AFTER) refresh(false);
  else maybeNotify(lastAlerts);
})();
