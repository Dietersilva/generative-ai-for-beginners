'use strict';

// Episode Radar: one monthly streaming plan for a household, built from
// everyone's shows, their teams' games and the streaming they already get
// through memberships, phone plans and cards. Also alerts for new series,
// seasons, episodes and games.
//
// TV data comes from the public TVmaze API; sports data from TheSportsDB via
// this site's own /api/sports function (which holds the paid key). Everything
// the user saves stays in this device's localStorage. The page never uses
// innerHTML: every outside string is rendered as text, and every link or image
// URL is checked before it reaches the DOM.
(() => {
  const DATA = window.EPISODE_RADAR_DATA;
  if (!DATA) {
    document.getElementById('status').textContent = 'Episode Radar could not load its data. Reload the page.';
    return;
  }
  const { services: SERVICES, networks: NETWORKS, perks: PERKS } = DATA;

  const API = 'https://api.tvmaze.com';
  const SPORTS_API = 'api/sports';
  const STORE_KEY = 'episodeRadar.v1';
  const CACHE_KEY = 'episodeRadar.cache.v1';
  const MINUTE = 60e3;
  const HOUR = 60 * MINUTE;
  const DAY = 24 * HOUR;
  const STALE_AFTER = 6 * HOUR;
  // TVmaze allows roughly 20 requests per 10 seconds per IP; stay well under it.
  const REQUEST_GAP_MS = 550;
  const DEFAULT_SERVICES = ['netflix', 'hulu', 'prime'];
  const TABS = ['alerts', 'plan', 'shows', 'sports', 'downloads', 'settings'];
  const MAX_MEMBERS = 8;
  const PLAN_PERIODS = 3; // 30-day periods, matching how streaming bills
  const PERIOD_DAYS = 30;
  const TVMAZE_IMG = ['static.tvmaze.com'];
  const SPORTS_IMG = ['www.thesportsdb.com', 'r2.thesportsdb.com'];

  // ---------- small helpers ----------

  const $ = (sel) => document.querySelector(sel);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const str = (v, max) => (typeof v === 'string' ? v.slice(0, max) : '');
  const posInt = (v) => (Number.isInteger(v) && v > 0 && v < 1e12 ? v : null);
  const isIso = (v) => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v);
  const svcById = (id) => SERVICES.find((s) => s.id === id) || null;
  const own = (o, k) => Object.prototype.hasOwnProperty.call(o, k);

  function safeUrl(v) {
    if (typeof v !== 'string') return null;
    try {
      const u = new URL(v);
      return u.protocol === 'https:' ? u.href : null;
    } catch {
      return null;
    }
  }

  function safeImg(v, hosts = TVMAZE_IMG) {
    const u = safeUrl(v);
    return u && hosts.includes(new URL(u).hostname) ? u : null;
  }
  const anyImg = (v) => safeImg(v, TVMAZE_IMG) || safeImg(v, SPORTS_IMG);

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

  const shortDate = (iso) => noon(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

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
        const u = anyImg(v);
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

  const newMemberId = () => 'm' + Math.random().toString(36).slice(2, 8);

  function defaults() {
    return {
      version: 1,
      onboarded: false,
      members: [{ id: 'me', name: 'Me' }],
      services: DEFAULT_SERVICES.slice(),
      prices: {},
      perks: {},
      lookBackDays: 7,
      lookAheadDays: 21,
      tracked: {},
      teams: {},
      downloads: [],
      dismissed: {},
      notified: {},
      notify: false,
      lastRefresh: 0,
    };
  }

  function cleanMembers(list, valid) {
    return Array.isArray(list) ? [...new Set(list.filter((id) => valid.has(id)))] : [];
  }

  function cleanShowRef(v, valid) {
    if (!v || typeof v !== 'object' || !posInt(v.id)) return null;
    return {
      id: v.id,
      name: str(v.name, 200) || 'Untitled',
      channel: str(v.channel, 100),
      image: safeImg(v.image),
      site: safeUrl(v.site),
      members: cleanMembers(v.members, valid),
    };
  }

  function cleanTeamRef(v, valid) {
    if (!v || typeof v !== 'object' || !posInt(v.id)) return null;
    return {
      id: v.id,
      name: str(v.name, 80) || 'Team',
      league: str(v.league, 80),
      sport: str(v.sport, 40),
      badge: safeImg(v.badge, SPORTS_IMG),
      members: cleanMembers(v.members, valid),
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

    if (Array.isArray(raw.members)) {
      const seen = new Set();
      const members = [];
      for (const m of raw.members.slice(0, MAX_MEMBERS)) {
        if (!m || typeof m.id !== 'string' || !/^[a-z0-9]{1,12}$/.test(m.id) || seen.has(m.id)) continue;
        seen.add(m.id);
        members.push({ id: m.id, name: str(m.name, 24).trim() || 'Someone' });
      }
      if (members.length) s.members = members;
    }
    const valid = new Set(s.members.map((m) => m.id));

    if (Array.isArray(raw.services)) s.services = SERVICES.map((x) => x.id).filter((id) => raw.services.includes(id));
    if (raw.prices && typeof raw.prices === 'object') {
      for (const x of SERVICES) {
        const c = cleanCents(raw.prices[x.id]);
        if (c) s.prices[x.id] = c;
      }
    }
    if (raw.perks && typeof raw.perks === 'object') {
      for (const p of PERKS) {
        const v = raw.perks[p.id];
        if (p.options ? p.options.some((o) => o.id === v) : v === true) s.perks[p.id] = v;
      }
    }
    if ([3, 7, 14].includes(raw.lookBackDays)) s.lookBackDays = raw.lookBackDays;
    if ([7, 14, 21, 30].includes(raw.lookAheadDays)) s.lookAheadDays = raw.lookAheadDays;
    for (const [field, clean] of [['tracked', cleanShowRef], ['teams', cleanTeamRef]]) {
      if (raw[field] && typeof raw[field] === 'object') {
        for (const [k, v] of Object.entries(raw[field]).slice(0, 500)) {
          const t = clean(v, valid);
          if (t && String(t.id) === k) s[field][k] = t;
        }
      }
    }
    if (Array.isArray(raw.downloads)) s.downloads = raw.downloads.map(cleanDownload).filter(Boolean).slice(0, 500);
    for (const field of ['dismissed', 'notified']) {
      if (raw[field] && typeof raw[field] === 'object') {
        for (const k of Object.keys(raw[field]).slice(0, 5000)) {
          if (/^(prem|ep|game):[\w:]{1,40}$/.test(k)) s[field][k] = true;
        }
      }
    }
    s.notify = raw.notify === true;
    s.lastRefresh = Number.isFinite(raw.lastRefresh) ? raw.lastRefresh : 0;
    // People upgrading from an earlier version already set things up.
    s.onboarded = raw.onboarded === true || s.lastRefresh > 0 || Object.keys(s.tracked).length > 0;
    return s;
  }

  let state = normalizeState(readJSON(STORE_KEY));
  const save = () => writeJSON(STORE_KEY, state);

  // Cache of trimmed API results: "sched:YYYY-MM-DD", "show:ID", "team:ID".
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
      // Storage full: drop the cache rather than the user's data.
      cache = {};
      writeJSON(CACHE_KEY, cache);
    }
  }

  // ---------- household ----------

  const memberName = (id) => (state.members.find((m) => m.id === id) || {}).name || 'Someone';
  // An empty list means everyone in the household.
  const membersOf = (item) => (item && item.members && item.members.length ? item.members : state.members.map((m) => m.id));
  function whoLabel(item) {
    if (state.members.length < 2) return null;
    const ids = membersOf(item);
    return ids.length === state.members.length ? 'Everyone' : listJoin(ids.map(memberName));
  }

  // ---------- perks and coverage ----------

  function activePerks() {
    const out = [];
    for (const p of PERKS) {
      const v = state.perks[p.id];
      if (!v) continue;
      if (p.options) {
        const o = p.options.find((x) => x.id === v);
        if (o) out.push({ perk: p, grants: o.grants || [], label: `${p.label} (${o.label.replace(/ chosen$/, '')})` });
      } else out.push({ perk: p, grants: p.grants || [], label: p.label });
    }
    return out;
  }

  const normChannel = (name) => str(name, 60).toLowerCase().replace(/\((us|usa)\)/g, '').replace(/\b(usa|us|hd)\b/g, '').replace(/\s+/g, ' ').trim();
  const networkRule = (channel) => {
    const n = normChannel(channel);
    return NETWORKS.find((r) => r.names.includes(n)) || null;
  };

  function tierOk(serviceId, have, need) {
    const svc = svcById(serviceId);
    if (!svc || !svc.tiers || !need || !have) return true;
    return svc.tiers.indexOf(have) >= svc.tiers.indexOf(need);
  }

  function coverageIndex() {
    const active = activePerks();
    const grants = [];
    const nets = new Map();
    const credits = [];
    for (const a of active) {
      for (const g of a.grants) grants.push({ service: g.service, tier: g.tier || null, by: a.label });
      for (const n of a.perk.networks || []) if (!nets.has(n)) nets.set(n, a.label);
      if (a.perk.credit) credits.push({ cents: a.perk.credit.cents, services: a.perk.credit.services, by: a.label });
    }
    return { grants, nets, credits };
  }

  // Returns the label of what already covers this need, or null.
  function coveredBy(cov, need) {
    if (need.channel) {
      const by = cov.nets.get(normChannel(need.channel));
      if (by) return by;
    }
    const svc = svcById(need.service);
    if (svc && svc.free) return `${svc.label} (free)`;
    const g = cov.grants.find((x) => x.service === need.service && tierOk(need.service, x.tier, need.tier));
    return g ? g.by : null;
  }

  // How to watch one game given its US channels and what the household has.
  function gameWatch(cov, game) {
    if (!Array.isArray(game.channels) || !game.channels.length) return { status: 'unlisted' };
    const options = game.channels.map((channel) => ({ channel, rule: networkRule(channel) }));
    for (const o of options) {
      const viaChannel = cov.nets.get(normChannel(o.channel));
      if (viaChannel) return { status: 'covered', by: viaChannel, channel: o.channel, service: null, tier: null };
    }
    for (const o of options) {
      const by = o.rule && coveredBy(cov, { service: o.rule.service, tier: o.rule.tier });
      if (by) return { status: 'covered', by, channel: o.channel, service: o.rule.service, tier: o.rule.tier || null };
    }
    const mapped = options.filter((o) => o.rule);
    const paid = mapped.find((o) => state.services.includes(o.rule.service));
    if (paid) return { status: 'paid', channel: paid.channel, service: paid.rule.service, tier: paid.rule.tier || null, note: paid.rule.note };
    if (mapped.length) {
      const price = (o) => state.prices[o.rule.service] || Infinity;
      const best = mapped.slice().sort((a, b) => price(a) - price(b))[0];
      return { status: 'need', channel: best.channel, service: best.rule.service, tier: best.rule.tier || null, note: best.rule.note };
    }
    return { status: 'unknown', channels: game.channels };
  }

  function tierName(serviceId, tier) {
    const svc = svcById(serviceId);
    if (!svc) return 'a service';
    if (!svc.tiers || !tier) return svc.label;
    const label = svc.tierLabels[tier];
    return label.startsWith(svc.label) ? label : `${svc.label} ${label}`;
  }

  function watchText(w) {
    const svcName = w.service ? tierName(w.service, w.tier) : '';
    const via = svcName.toLowerCase().startsWith(normChannel(w.channel || '')) ? '' : ` (${w.channel})`;
    if (w.status === 'covered') return { cls: 'watch-ok', text: `Free with ${w.by}${w.by.toLowerCase().includes(normChannel(w.channel)) ? '' : ` (${w.channel})`}` };
    if (w.status === 'paid') return { cls: 'watch-ok', text: `On ${svcName}, which you pay for${via}` };
    if (w.status === 'need') return { cls: 'watch-need', text: `Needs ${svcName}${via}` };
    if (w.status === 'unknown') return { cls: 'watch-unknown', text: `On ${listJoin(w.channels)}: needs cable, a live TV service or the league's own package` };
    return { cls: 'watch-unknown', text: 'TV channel not announced yet' };
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
      out.push({ ...showRef(show), season: ep.season, airdate: isIso(ep.airdate) ? ep.airdate : date, summary: plain(show.summary) });
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

  // ---------- sports API (this site's /api/sports) ----------

  let sportsStatus = 'unknown'; // 'ok' | 'not_configured' | 'no_server' | 'error'

  async function sportsApi(params) {
    let res;
    try {
      res = await fetch(`${SPORTS_API}?${new URLSearchParams(params)}`, { headers: { Accept: 'application/json' }, credentials: 'same-origin' });
    } catch {
      const e = new Error('network');
      e.code = 'error';
      throw e;
    }
    let body = null;
    try {
      body = await res.json();
    } catch {
      body = null;
    }
    if (res.ok && body) {
      sportsStatus = 'ok';
      return body;
    }
    const e = new Error('sports unavailable');
    e.code = res.status === 503 && body && body.error === 'not_configured' ? 'not_configured' : res.status === 404 || !body ? 'no_server' : 'error';
    throw e;
  }

  function cleanGame(g) {
    if (!g || !posInt(g.id)) return null;
    const start = typeof g.start === 'string' && !Number.isNaN(Date.parse(g.start)) ? new Date(g.start).toISOString() : null;
    return {
      id: g.id,
      name: str(g.name, 120),
      league: str(g.league, 80),
      home: str(g.home, 80),
      away: str(g.away, 80),
      date: isIso(g.date) ? g.date : '',
      start,
      channels: Array.isArray(g.channels) ? g.channels.filter((c) => typeof c === 'string').map((c) => str(c, 60)).slice(0, 8) : null,
    };
  }

  async function searchTeams(q) {
    const body = await sportsApi({ action: 'teams', q });
    return (Array.isArray(body.teams) ? body.teams : [])
      .map((t) => t && posInt(t.id) && { id: t.id, name: str(t.name, 80) || 'Team', league: str(t.league, 80), sport: str(t.sport, 40), badge: safeImg(t.badge, SPORTS_IMG) })
      .filter(Boolean)
      .slice(0, 10);
  }

  async function teamGames(id, ttl) {
    const key = 'team:' + id;
    const hit = cacheFresh(key, ttl);
    if (hit) return hit;
    const body = await sportsApi({ action: 'games', id: String(id) });
    const games = (Array.isArray(body.games) ? body.games : []).map(cleanGame).filter(Boolean).slice(0, 15);
    cacheSet(key, games);
    return games;
  }

  const gameDate = (g) => (g.start ? isoDate(new Date(g.start)) : g.date);
  const gameTitle = (g) => g.name || (g.away && g.home ? `${g.away} at ${g.home}` : 'Game');
  function gameWhen(g) {
    if (g.start) {
      const d = new Date(g.start);
      return `${d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}, ${d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })}`;
    }
    return fmtDate(g.date);
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
    const games = {};
    for (const id of Object.keys(state.teams)) {
      const g = cacheAny('team:' + id);
      if (Array.isArray(g)) games[id] = g;
    }
    return { premieres: [...seen.values()], details, games, cov: coverageIndex() };
  }

  function buildAlerts(model) {
    const t = today();
    const from = isoDate(addDays(new Date(), -state.lookBackDays));
    const until = isoDate(addDays(new Date(), state.lookAheadDays));
    const soonGames = isoDate(addDays(new Date(), 2));
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

    // Games in the next three days for followed teams.
    for (const [id, games] of Object.entries(model.games)) {
      const team = state.teams[id];
      if (!team) continue;
      for (const g of games) {
        const d = gameDate(g);
        if (!d || d < t || d > soonGames) continue;
        const w = gameWatch(model.cov, g);
        push({ key: `game:${g.id}`, kind: 'game', team, game: g, watch: w, svc: w.service ? svcById(w.service) : null, airdate: d });
      }
    }

    return alerts.filter((a) => !state.dismissed[a.key]);
  }

  // ---------- household plan ----------

  function planPeriods() {
    const base = new Date();
    return Array.from({ length: PLAN_PERIODS }, (_, i) => ({
      start: isoDate(addDays(base, i * PERIOD_DAYS)),
      end: isoDate(addDays(base, (i + 1) * PERIOD_DAYS - 1)),
      first: i === 0,
    }));
  }

  // Everything the household wants to watch in one 30-day period, and what it needs.
  function periodNeeds(period, model) {
    const t = today();
    const inPeriod = (d) => d >= period.start && d <= period.end;
    const needs = [];
    const unknown = [];
    for (const [id, d] of Object.entries(model.details)) {
      const svc = serviceFor(d.channel);
      const ref = state.tracked[id];
      if (!svc || !ref) continue;
      const eps = d.future.filter((e) => inPeriod(e.airdate));
      const last = d.past[d.past.length - 1];
      const midSeason = period.first && last && daysBetween(last.airdate, t) <= 14;
      if (!eps.length && !midSeason) continue;
      const detail = eps.length
        ? `${epCode(eps[0].season, eps[0].number)}, ${fmtDate(eps[0].airdate)}${eps.length > 1 ? ` + ${eps.length - 1} more` : ''}`
        : 'Mid-season now';
      needs.push({ kind: 'show', service: svc.id, tier: null, title: d.name, detail, date: eps.length ? eps[0].airdate : t, item: ref });
    }
    for (const [id, games] of Object.entries(model.games)) {
      const team = state.teams[id];
      if (!team) continue;
      for (const g of games) {
        const d = gameDate(g);
        if (!d || d < t || !inPeriod(d)) continue;
        const w = gameWatch(model.cov, g);
        if (w.status === 'unknown' || w.status === 'unlisted') {
          unknown.push({ title: gameTitle(g), detail: `${fmtDate(d)} · ${watchText(w).text}`, date: d, item: team });
          continue;
        }
        needs.push({ kind: 'game', service: w.service, tier: w.tier, channel: w.channel, title: gameTitle(g), detail: `${fmtDate(d)} on ${w.channel}`, date: d, item: team, by: w.status === 'covered' ? w.by : null });
      }
    }
    return { needs, unknown };
  }

  function buildPlan(model) {
    const perMonth = planPeriods().map((p) => ({ ...p, ...periodNeeds(p, model) }));
    const plans = perMonth.map((pm, i) => {
      const covered = new Map();
      const uncovered = new Map();
      for (const n of pm.needs) {
        const by = n.by || coveredBy(model.cov, n);
        if (by) {
          if (!covered.has(by)) covered.set(by, []);
          covered.get(by).push(n);
        } else if (n.service) {
          if (!uncovered.has(n.service)) uncovered.set(n.service, []);
          uncovered.get(n.service).push(n);
        }
      }
      const rows = [];
      for (const [serviceId, needs] of uncovered) {
        const svc = svcById(serviceId);
        const paying = state.services.includes(serviceId);
        const tiers = needs.map((n) => n.tier).filter(Boolean);
        const tier = svc.tiers && tiers.length ? tiers.sort((a, b) => svc.tiers.indexOf(b) - svc.tiers.indexOf(a))[0] : null;
        const partial = model.cov.grants.find((g) => g.service === serviceId);
        const note = partial && tier ? `${partial.by} includes ${svc.tierLabels[partial.tier] || svc.label}, which doesn't include these games.` : null;
        rows.push({ kind: paying ? 'keep' : 'add', svc, tier, needs, price: state.prices[serviceId] || 0, note, from: needs.map((n) => n.date).sort()[0] });
      }
      for (const serviceId of state.services) {
        if (uncovered.has(serviceId)) continue;
        const svc = svcById(serviceId);
        const grant = model.cov.grants.find((g) => g.service === serviceId);
        if (grant) {
          rows.push({ kind: 'double', svc, by: grant.by, needs: [], price: state.prices[serviceId] || 0 });
          continue;
        }
        let rejoin = null;
        for (const later of perMonth.slice(i + 1)) {
          const n = later.needs.filter((x) => x.service === serviceId && !(x.by || coveredBy(model.cov, x))).sort((a, b) => a.date.localeCompare(b.date))[0];
          if (n) {
            rejoin = n;
            break;
          }
        }
        rows.push({ kind: 'pause', svc, needs: [], price: state.prices[serviceId] || 0, rejoin, first: pm.first });
      }
      for (const [by, needs] of covered) rows.push({ kind: 'covered', by, needs });

      const order = { add: 0, keep: 1, double: 2, pause: 3, covered: 4 };
      rows.sort((a, b) => order[a.kind] - order[b.kind] || (a.svc && b.svc ? a.svc.label.localeCompare(b.svc.label) : 0));

      const payRows = rows.filter((r) => r.kind === 'keep' || r.kind === 'add');
      const cost = payRows.reduce((s, r) => s + r.price, 0);
      let credit = 0;
      const creditNotes = [];
      for (const c of model.cov.credits) {
        const eligible = payRows.filter((r) => c.services.includes(r.svc.id)).reduce((s, r) => s + r.price, 0);
        const used = Math.min(c.cents, eligible);
        if (used > 0) {
          credit += used;
          creditNotes.push(`${c.by} pays back ${money(used)}`);
        }
      }
      const current = state.services.reduce((s, id) => s + (state.prices[id] || 0), 0);
      const net = Math.max(0, cost - credit);
      const missingPrices = [...new Set([...payRows.map((r) => r.svc), ...state.services.map(svcById)].filter((s) => s && !state.prices[s.id]).map((s) => s.label))];
      return { start: pm.start, end: pm.end, first: pm.first, rows, unknown: pm.unknown, cost, credit, creditNotes, net, current, save: current - net, missingPrices };
    });
    return plans;
  }

  // ---------- actions ----------

  function linkFor(show, svc) {
    if (svc && hostMatches(show.site, svc.hosts)) return show.site;
    if (svc) return svc.home;
    return safeUrl(show.site) || `https://www.tvmaze.com/shows/${show.id}`;
  }

  const isTracked = (id) => own(state.tracked, String(id));
  const isTeamFollowed = (id) => own(state.teams, String(id));
  const validMembers = () => new Set(state.members.map((m) => m.id));

  async function track(show) {
    const ref = cleanShowRef({ ...show, members: [] }, validMembers());
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

  async function followTeam(team) {
    const ref = cleanTeamRef({ ...team, members: [] }, validMembers());
    if (!ref) return;
    state.teams[String(ref.id)] = ref;
    save();
    renderAll();
    try {
      await teamGames(ref.id, 0);
      saveCache();
    } catch (e) {
      sportsStatus = e.code || 'error';
      setBanner(`Following ${ref.name}. Its games will load when sports data is available.`);
    }
    renderAll();
  }

  function unfollowTeam(id) {
    delete state.teams[String(id)];
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

  const icsStamp = (d) => d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');

  // `when` is either { date } for an all-day event or { start } for a timed one.
  function icsEvent(lines, stamp, uid, when, summary, description, alarm) {
    lines.push('BEGIN:VEVENT', `UID:${uid}@episode-radar`, `DTSTAMP:${stamp}`);
    if (when.start) {
      const s = new Date(when.start);
      lines.push(`DTSTART:${icsStamp(s)}`, `DTEND:${icsStamp(new Date(s.getTime() + 3 * HOUR))}`);
    } else {
      lines.push(`DTSTART;VALUE=DATE:${when.date.replace(/-/g, '')}`, `DTEND;VALUE=DATE:${isoDate(addDays(noon(when.date), 1)).replace(/-/g, '')}`);
    }
    lines.push(
      `SUMMARY:${icsEscape(summary)}`,
      `DESCRIPTION:${icsEscape(description)}`,
      'TRANSP:TRANSPARENT',
      'BEGIN:VALARM',
      'ACTION:DISPLAY',
      `DESCRIPTION:${icsEscape(summary)}`,
      alarm,
      'END:VALARM',
      'END:VEVENT',
    );
  }

  function buildICS(model) {
    const stamp = icsStamp(new Date());
    const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Episode Radar//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'X-WR-CALNAME:Episode Radar'];
    const counts = { episodes: 0, games: 0, reminders: 0 };
    const t = today();
    for (const d of Object.values(model.details)) {
      for (const e of d.future.slice(0, 26)) {
        const summary = `${d.name} ${epCode(e.season, e.number)}` + (e.name ? ` · ${e.name}` : '');
        const where = d.channel ? `Streaming on ${d.channel}.` : 'Check your streaming service.';
        icsEvent(lines, stamp, `tvmaze-episode-${e.id}`, { date: e.airdate }, summary, `${where} Data from TVmaze.`, 'TRIGGER;RELATED=START:PT9H');
        counts.episodes++;
      }
    }
    for (const [id, games] of Object.entries(model.games)) {
      if (!state.teams[id]) continue;
      for (const g of games) {
        const d = gameDate(g);
        if (!d || d < t) continue;
        const w = watchText(gameWatch(model.cov, g));
        icsEvent(lines, stamp, `tsdb-event-${g.id}`, g.start ? { start: g.start } : { date: d }, gameTitle(g), `${w.text}. Data from TheSportsDB.`, g.start ? 'TRIGGER:-PT30M' : 'TRIGGER;RELATED=START:PT9H');
        counts.games++;
      }
    }
    // Resubscribe reminders 3 days before a paused service is needed again.
    const plans = buildPlan(model);
    const reminded = new Set();
    for (const row of plans[0].rows) {
      if (row.kind !== 'pause' || !row.rejoin || reminded.has(row.svc.id)) continue;
      const when = isoDate(addDays(noon(row.rejoin.date), -3));
      if (when <= t) continue;
      reminded.add(row.svc.id);
      icsEvent(lines, stamp, `resubscribe-${row.svc.id}-${row.rejoin.date}`, { date: when }, `Resubscribe to ${row.svc.label}`,
        `${row.rejoin.title} (${row.rejoin.detail}). Reminder from Episode Radar.`, 'TRIGGER;RELATED=START:PT9H');
      counts.reminders++;
    }
    for (const plan of plans.slice(1)) {
      for (const row of plan.rows) {
        if (row.kind !== 'add' || reminded.has(row.svc.id)) continue;
        const when = isoDate(addDays(noon(row.from), -3));
        if (when <= t) continue;
        reminded.add(row.svc.id);
        icsEvent(lines, stamp, `subscribe-${row.svc.id}-${row.from}`, { date: when }, `Subscribe to ${tierName(row.svc.id, row.tier)}`,
          `${row.needs[0].title} (${row.needs[0].detail}). Reminder from Episode Radar.`, 'TRIGGER;RELATED=START:PT9H');
        counts.reminders++;
      }
    }
    lines.push('END:VCALENDAR');
    return { text: lines.map(icsFold).join('\r\n') + '\r\n', ...counts };
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
    const teamIds = Object.keys(state.teams);
    const total = dates.length + ids.length + teamIds.length;
    let done = 0;
    let failed = 0;
    const tick = () => setStatus(`Checking for news… ${++done} of ${total}`);

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
    let sportsProblem = false;
    for (const id of teamIds) {
      if (sportsProblem) {
        tick();
        continue;
      }
      try {
        await teamGames(id, futureTtl);
      } catch (e) {
        sportsStatus = e.code || 'error';
        // Sports isn't set up (or the server is missing): skip the rest quietly.
        sportsProblem = sportsStatus !== 'error';
        if (!sportsProblem) failed++;
      }
      tick();
    }
    saveCache();

    if (failed < total) {
      state.lastRefresh = Date.now();
      save();
    }
    if (total && failed === total) {
      setBanner(navigator.onLine === false
        ? "You're offline. Showing the results saved from your last check."
        : "Couldn't reach the TV listings. Showing the results saved from your last check. Try again in a few minutes.");
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

  const alertName = (a) => (a.kind === 'game' ? gameTitle(a.game) : a.show.name);

  function maybeNotify(alerts) {
    if (!state.notify || !canNotify() || Notification.permission !== 'granted') return;
    const t = today();
    const fresh = alerts.filter((a) => !state.notified[a.key] && (a.kind !== 'episode' || a.airdate <= t));
    if (!fresh.length) return;
    for (const a of fresh) state.notified[a.key] = true;
    save();
    const names = fresh.slice(0, 3).map(alertName).join(', ');
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
    return "This browser doesn't support notifications. Use Add to calendar instead.";
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
    renderOnboardingStep4();
  }

  // ---------- rendering: shared pieces ----------

  let filter = 'all';
  let searchResults = null;
  let teamResults = null;
  let planMonth = 0;

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

  function blankPoster(name) {
    return h('div', { class: 'poster-blank', 'aria-hidden': 'true' }, (name || '?').charAt(0).toUpperCase());
  }
  function poster(show) {
    const src = safeImg(show.image);
    if (!src) return blankPoster(show.name);
    const img = h('img', { class: 'poster', src, alt: '', loading: 'lazy', decoding: 'async', referrerpolicy: 'no-referrer' });
    img.addEventListener('error', () => img.replaceWith(blankPoster(show.name)), { once: true });
    return img;
  }
  function teamBadge(team) {
    const src = safeImg(team.badge, SPORTS_IMG);
    if (!src) return blankPoster(team.name);
    const img = h('img', { class: 'badge-img', src, alt: '', loading: 'lazy', decoding: 'async', referrerpolicy: 'no-referrer' });
    img.addEventListener('error', () => img.replaceWith(blankPoster(team.name)), { once: true });
    return img;
  }

  function serviceChip(show, svc) {
    if (svc) return h('span', { class: 'svc' }, svc.label);
    return show.channel ? h('span', { class: 'meta' }, show.channel) : null;
  }

  // Who in the household a show or team is for. Hidden for one-person households.
  function whoChips(item, onChange) {
    if (state.members.length < 2) return null;
    const ids = new Set(membersOf(item));
    return h('div', { class: 'who' },
      h('span', { class: 'meta' }, 'For'),
      state.members.map((m) => h('button', {
        class: 'chip',
        type: 'button',
        'aria-pressed': ids.has(m.id) ? 'true' : 'false',
        onclick: () => {
          const next = new Set(ids);
          if (next.has(m.id)) {
            if (next.size === 1) return; // Someone must watch it.
            next.delete(m.id);
          } else next.add(m.id);
          item.members = next.size === state.members.length ? [] : [...next];
          save();
          onChange();
        },
      }, m.name)));
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

  function teamButton(team) {
    const on = isTeamFollowed(team.id);
    return h('button', {
      class: 'btn' + (on ? ' btn-on' : ''),
      type: 'button',
      'aria-pressed': on ? 'true' : 'false',
      onclick: () => (on ? unfollowTeam(team.id) : followTeam(team)),
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

  function empty(title, body) {
    return h('div', { class: 'empty' }, h('strong', null, title), body);
  }

  // ---------- rendering: alerts ----------

  function gameAlertCard(a) {
    const g = a.game;
    const w = watchText(a.watch);
    const d = gameDate(g);
    const label = d === today() ? 'Game today' : d === isoDate(addDays(new Date(), 1)) ? 'Game tomorrow' : 'Game soon';
    return h('article', { class: 'card team' },
      teamBadge(a.team),
      h('div', { class: 'card-body' },
        h('div', { class: 'card-top' }, h('span', { class: 'badge badge-game' }, label), h('span', { class: 'meta' }, a.team.league)),
        h('h3', null, gameTitle(g)),
        h('div', { class: 'meta' }, gameWhen(g)),
        h('div', { class: w.cls }, w.text),
        h('div', { class: 'actions' },
          a.svc ? h('a', { class: 'btn', href: a.svc.home }, `Open ${a.svc.label}`) : null,
          h('button', { class: 'btn btn-quiet', type: 'button', onclick: () => dismiss(a.key), 'aria-label': `Dismiss alert for ${gameTitle(g)}` }, 'Dismiss'),
        ),
      ),
    );
  }

  function alertCard(a) {
    if (a.kind === 'game') return gameAlertCard(a);
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

  function renderAlerts(alerts) {
    const t = today();
    const shown = alerts.filter((a) => filter === 'all' || a.kind === filter);
    const games = shown.filter((a) => a.kind === 'game').sort((x, y) => (x.game.start || x.airdate).localeCompare(y.game.start || y.airdate));
    const rest = shown.filter((a) => a.kind !== 'game');
    const outNow = rest.filter((a) => a.airdate <= t).sort((x, y) => y.airdate.localeCompare(x.airdate));
    const soon = rest.filter((a) => a.airdate > t).sort((x, y) => x.airdate.localeCompare(y.airdate));
    const kids = [];
    if (!state.services.length && !Object.keys(state.tracked).length && !Object.keys(state.teams).length) {
      kids.push(empty('Choose your services', 'Pick the services you pay for in Settings, and new series and seasons will show up here.'));
    } else if (!shown.length) {
      kids.push(state.lastRefresh
        ? empty('Nothing new right now', `No alerts of this type in the last ${state.lookBackDays} days or the next ${state.lookAheadDays}. Episode Radar checks again automatically.`)
        : empty('Checking for news', 'Reading the TV schedule. The first check takes about 20 seconds.'));
    }
    if (games.length) kids.push(h('h3', { class: 'section-title' }, 'Game days'), h('div', { class: 'list' }, games.map(alertCard)));
    if (outNow.length) kids.push(h('h3', { class: 'section-title' }, 'Out now'), h('div', { class: 'list' }, outNow.map(alertCard)));
    if (soon.length) kids.push(h('h3', { class: 'section-title' }, 'Coming up'), h('div', { class: 'list' }, soon.map(alertCard)));
    $('#alerts').replaceChildren(...kids);
  }

  // ---------- rendering: plan ----------

  function reasonList(needs) {
    return h('ul', { class: 'reasons' }, needs.slice(0, 6).map((n) => {
      const who = whoLabel(n.item);
      return h('li', null, who ? h('span', { class: 'who-tag' }, who) : null, h('span', null, `${n.title}: ${n.detail}`));
    }), needs.length > 6 ? h('li', null, `+ ${needs.length - 6} more`) : null);
  }

  function planRow(row) {
    const priceTag = row.price ? h('span', { class: 'meta' }, `${money(row.price)}/mo`) : null;
    let title;
    let pill;
    let line = null;
    if (row.kind === 'add' || row.kind === 'keep') {
      title = h('h3', null, tierName(row.svc.id, row.tier), priceTag);
      pill = row.kind === 'add'
        ? h('span', { class: 'verdict verdict-add' }, row.from > today() ? `Subscribe by ${fmtDate(row.from)}` : 'Subscribe')
        : h('span', { class: 'verdict verdict-keep' }, 'Keep');
      line = row.note;
    } else if (row.kind === 'pause') {
      title = h('h3', null, row.svc.label, priceTag);
      pill = h('span', { class: 'verdict verdict-pause' }, row.rejoin ? `Pause, rejoin ${fmtDate(isoDate(addDays(noon(row.rejoin.date), -3)))}` : 'Pause');
      line = row.rejoin
        ? `Nothing your household follows is on ${row.svc.label} until ${row.rejoin.title} (${fmtDate(row.rejoin.date)}).`
        : `Nothing your household follows is on ${row.svc.label} ${row.first ? `in the next ${PLAN_PERIODS * PERIOD_DAYS} days` : `for the rest of this ${PLAN_PERIODS * PERIOD_DAYS}-day plan`}.`;
    } else if (row.kind === 'double') {
      title = h('h3', null, row.svc.label, priceTag);
      pill = h('span', { class: 'verdict verdict-double' }, 'Paying twice?');
      line = `You pay for ${row.svc.label}, but ${row.by} already includes it. Check whether you can cancel the separate subscription.`;
    } else {
      title = h('h3', null, row.by);
      pill = h('span', { class: 'verdict verdict-covered' }, 'Already covered');
    }
    return h('article', { class: 'plan-row' },
      h('div', { class: 'plan-top' }, title, pill),
      line ? h('div', { class: 'meta' }, line) : null,
      row.needs.length ? reasonList(row.needs) : null);
  }

  function renderPlan(model) {
    const plans = buildPlan(model);
    planMonth = Math.min(planMonth, plans.length - 1);
    $('#month-chips').replaceChildren(...plans.map((p, i) => h('button', {
      class: 'chip', type: 'button', 'aria-pressed': i === planMonth ? 'true' : 'false',
      onclick: () => { planMonth = i; renderAll(); },
    }, p.first ? 'Next 30 days' : `From ${shortDate(p.start)}`)));

    const p = plans[planMonth];
    const root = $('#plan');
    const nothing = !Object.keys(state.tracked).length && !Object.keys(state.teams).length;
    if (nothing && !state.services.length) {
      root.replaceChildren(empty('Start your plan', 'Follow shows and teams, and tick the services you pay for in Settings. The plan then shows what to keep, pause or add each month.'));
      return plans;
    }
    const doubles = p.rows.filter((r) => r.kind === 'double');
    const summary = h('div', { class: 'plan-summary' },
      h('div', { class: 'stat' }, h('span', { class: 'stat-label' }, p.first ? 'Next 30 days' : `${shortDate(p.start)} to ${shortDate(p.end)}`), h('span', { class: 'stat-value' }, money(p.net))),
      h('div', { class: 'stat' }, h('span', { class: 'stat-label' }, 'You pay now'), h('span', { class: 'stat-value' }, money(p.current))),
      h('div', { class: 'stat' }, h('span', { class: 'stat-label' }, p.save >= 0 ? 'You save' : 'Extra this period'), h('span', { class: 'stat-value' + (p.save > 0 ? ' good' : '') }, money(Math.abs(p.save)))),
    );
    const notes = [];
    if (p.creditNotes.length) notes.push(h('p', { class: 'hint' }, `${p.creditNotes.join('; ')} (included above).`));
    if (p.missingPrices.length) notes.push(h('p', { class: 'hint' }, `Add a monthly price for ${listJoin(p.missingPrices)} in Settings for exact totals.`));
    const callout = doubles.length
      ? h('div', { class: 'callout' }, h('strong', null, 'You may be paying twice'),
          h('ul', { class: 'reasons' }, doubles.map((d) => h('li', null, h('span', { class: 'who-tag' }, d.svc.label), h('span', null, `also included with ${d.by}`)))))
      : null;
    const rows = p.rows.length
      ? h('div', { class: 'list' }, p.rows.map(planRow))
      : empty('Nothing needed in this period', 'None of the shows or teams your household follows has anything scheduled in these 30 days.');
    const unknown = p.unknown.length
      ? [h('h3', { class: 'section-title' }, 'Check how to watch'), h('div', { class: 'plan-row' }, reasonList(p.unknown))]
      : [];
    root.replaceChildren(summary, ...notes, callout || '', rows, ...unknown);
    return plans;
  }

  // ---------- rendering: shows, sports, downloads ----------

  const epLine = (e) => (e ? `${epCode(e.season, e.number)} · ${fmtDate(e.airdate)}` : null);

  function showCard(ref, d) {
    const show = d || ref;
    const svc = serviceFor(show.channel);
    const last = d && d.past[d.past.length - 1];
    const next = d && d.future[0];
    const rows = d
      ? [['Latest', epLine(last) || 'No episodes yet'], ['Next', epLine(next) || (d.status === 'Ended' ? 'Series ended' : 'Not announced')]]
      : [['Episodes', 'Load on the next check']];
    return h('article', { class: 'card' },
      poster(show),
      h('div', { class: 'card-body' },
        h('div', { class: 'card-top' }, serviceChip(show, svc), d && d.status ? h('span', { class: 'meta' }, d.status) : null),
        h('h3', null, show.name),
        h('dl', { class: 'ep-grid' }, rows.map(([k, v]) => h('div', null, h('dt', null, k), h('dd', null, v)))),
        whoChips(ref, renderAll),
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

  function teamSearchCard(tm) {
    return h('article', { class: 'card team' },
      teamBadge(tm),
      h('div', { class: 'card-body' },
        h('div', { class: 'card-top' }, h('span', { class: 'meta' }, [tm.league, tm.sport].filter(Boolean).join(' · '))),
        h('h3', null, tm.name),
        h('div', { class: 'actions' }, teamButton(tm)),
      ),
    );
  }

  function renderResults(target, results, cardFn, onClear) {
    if (!results) {
      target.replaceChildren();
      return;
    }
    const head = h('div', { class: 'panel-head' },
      h('h3', { class: 'section-title' }, `Search results (${results.length})`),
      h('button', { class: 'btn btn-quiet', type: 'button', onclick: onClear }, 'Clear'));
    const list = results.length
      ? h('div', { class: 'list' }, results.map(cardFn))
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
    renderResults($('#search-results'), searchResults, searchCard, () => { searchResults = null; renderAll(); });
  }

  function sportsNotice() {
    if (sportsStatus === 'not_configured') return empty('Sports is not switched on yet', 'This copy of Episode Radar needs a TheSportsDB key on its server. The README explains the one-time setup.');
    if (sportsStatus === 'no_server') return empty('Sports needs the Episode Radar server', 'Game listings come through this site\'s own server, which runs on Vercel or with "node dev-server.js". A plain file server can\'t provide them.');
    if (sportsStatus === 'error') return empty("Couldn't load games right now", 'Your teams are saved. Try Refresh again in a few minutes.');
    return null;
  }

  function teamCard(team, games, cov) {
    const t = today();
    const upcoming = (games || []).filter((g) => (gameDate(g) || '9999') >= t).slice(0, 5);
    const list = upcoming.length
      ? h('ul', { class: 'games' }, upcoming.map((g) => {
          const w = watchText(gameWatch(cov, g));
          return h('li', { class: 'game' },
            h('span', { class: 'game-name' }, gameTitle(g)),
            h('span', { class: 'game-when' }, gameWhen(g)),
            h('div', { class: 'game-watch' },
              (g.channels || []).map((c) => h('span', { class: 'tv' }, c)),
              h('span', { class: w.cls }, w.text)));
        }))
      : h('p', { class: 'meta' }, games ? 'No upcoming games listed yet.' : 'Games load on the next check.');
    const who = whoChips(team, renderAll);
    if (who) who.classList.add('span');
    list.classList.add('span');
    return h('article', { class: 'card team' },
      teamBadge(team),
      h('div', { class: 'card-body' },
        h('div', { class: 'card-top' }, h('span', { class: 'meta' }, [team.league, team.sport].filter(Boolean).join(' · '))),
        h('h3', null, team.name),
      ),
      list,
      who,
      h('div', { class: 'actions span' }, h('button', { class: 'btn btn-quiet', type: 'button', onclick: () => unfollowTeam(team.id) }, 'Unfollow')),
    );
  }

  function renderSports(model) {
    const teams = Object.values(state.teams).sort((a, b) => a.name.localeCompare(b.name));
    const notice = sportsNotice();
    const kids = [];
    if (notice) kids.push(notice);
    kids.push(teams.length
      ? h('div', { class: 'list' }, teams.map((tm) => teamCard(tm, model.games[tm.id], model.cov)))
      : empty('No teams yet', 'Search for a team above. Episode Radar lists its games, which channel carries each one, and whether something you already have covers it.'));
    $('#teams').replaceChildren(...kids);
    renderResults($('#team-results'), teamResults, teamSearchCard, () => { teamResults = null; renderAll(); });
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

  // ---------- rendering: settings editors ----------

  // Re-rendering replaces inputs; put focus back on the field being edited.
  function keepFocus(target, prefix, build) {
    const active = document.activeElement && document.activeElement.id;
    target.replaceChildren(...build());
    if (active && active.startsWith(prefix)) {
      const el = document.getElementById(active);
      if (el) el.focus();
    }
  }

  function renderMembers(target, prefix) {
    keepFocus(target, prefix, () => {
      const pills = state.members.map((m) => {
        const input = h('input', { id: `${prefix}-member-${m.id}`, type: 'text', maxlength: '24', autocomplete: 'off', 'aria-label': 'Name' });
        input.value = m.name;
        input.addEventListener('change', () => {
          m.name = input.value.trim().slice(0, 24) || 'Someone';
          save();
          renderAll();
        });
        const remove = state.members.length > 1
          ? h('button', {
              type: 'button', 'aria-label': `Remove ${m.name}`,
              onclick: () => {
                state.members = state.members.filter((x) => x.id !== m.id);
                for (const item of [...Object.values(state.tracked), ...Object.values(state.teams)]) {
                  item.members = (item.members || []).filter((x) => x !== m.id);
                }
                save();
                renderAll();
              },
            }, '×')
          : null;
        return h('span', { class: 'member' }, input, remove);
      });
      const add = state.members.length < MAX_MEMBERS
        ? h('button', {
            class: 'btn', type: 'button', id: `${prefix}-add-member`,
            onclick: () => {
              const id = newMemberId();
              state.members.push({ id, name: `Person ${state.members.length + 1}` });
              save();
              renderAll();
              const el = document.getElementById(`${prefix}-member-${id}`);
              if (el) {
                el.focus();
                el.select();
              }
            },
          }, 'Add person')
        : null;
      return [...pills, add].filter(Boolean);
    });
  }

  // Service checkboxes with monthly prices, shared by Settings and setup.
  function renderServiceRows(target, prefix) {
    keepFocus(target, prefix, () => SERVICES.filter((s) => !s.free).map((s) => {
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
    }));
  }

  function renderPerks(target, prefix) {
    keepFocus(target, prefix, () => PERKS.map((p) => {
      const v = state.perks[p.id];
      let control;
      if (p.options) {
        const sel = h('select', { id: `${prefix}-perk-${p.id}`, 'aria-label': `${p.label} streaming choice` },
          h('option', { value: '' }, "Don't have it"),
          p.options.map((o) => h('option', { value: o.id }, o.label)));
        sel.value = v || '';
        sel.addEventListener('change', () => {
          if (sel.value) state.perks[p.id] = sel.value;
          else delete state.perks[p.id];
          save();
          renderAll();
        });
        control = h('div', { class: 'perk-top' }, h('label', { for: `${prefix}-perk-${p.id}` }, p.label), sel);
      } else {
        const box = h('input', { type: 'checkbox', id: `${prefix}-perk-${p.id}` });
        box.checked = v === true;
        box.addEventListener('change', () => {
          if (box.checked) state.perks[p.id] = true;
          else delete state.perks[p.id];
          save();
          renderAll();
        });
        control = h('div', { class: 'perk-top' }, h('label', { for: `${prefix}-perk-${p.id}` }, box, p.label));
      }
      return h('div', { class: 'perk' + (v ? ' on' : '') },
        control,
        h('p', { class: 'hint' }, p.detail, p.source ? [' ', h('a', { href: p.source }, 'Source')] : null));
    }));
  }

  function renderSettings() {
    renderMembers($('#members'), 'set');
    renderServiceRows($('#services'), 'set');
    renderPerks($('#perks'), 'set');
    $('#perks-hint').textContent = `Memberships, phone plans and cards that include streaming. They count as free in your plan. Terms were checked on ${fmtDate(DATA.checked)}; they change often, so confirm your own plan.`;
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
    const plans = renderPlan(model);
    renderShows(model);
    renderSports(model);
    renderDownloads();
    renderSettings();
    if (!$('#onboarding').hidden) renderOnboarding(model);
    setCount('#count-alerts', lastAlerts.length);
    setCount('#count-plan', plans[0].rows.filter((r) => r.kind === 'add' || r.kind === 'pause' || r.kind === 'double').length);
    setCount('#count-shows', Object.keys(state.tracked).length);
    setCount('#count-sports', Object.keys(state.teams).length);
    setCount('#count-downloads', state.downloads.filter((d) => !d.done).length);
    document.title = lastAlerts.length ? `(${lastAlerts.length}) Episode Radar` : 'Episode Radar';
    if (!busy) setStatus(statusText());
  }

  // ---------- setup ----------

  const OB_STEPS = 4;
  let obStep = 1;
  let obKind = 'shows';
  let obResults = null;

  function setMainInert(on) {
    for (const id of ['.top', '#tabs', '#main']) {
      if (on) $(id).setAttribute('inert', '');
      else $(id).removeAttribute('inert');
    }
  }

  function focusTitle(n) {
    const title = $(`#ob-title-${n}`);
    title.setAttribute('tabindex', '-1');
    title.focus();
  }

  function openOnboarding() {
    obStep = 1;
    obResults = null;
    $('#onboarding').hidden = false;
    setMainInert(true);
    renderOnboarding(collect());
    focusTitle(1);
  }

  function closeOnboarding() {
    state.onboarded = true;
    save();
    $('#onboarding').hidden = true;
    setMainInert(false);
    showTab('plan');
    renderAll();
    if (Date.now() - state.lastRefresh > STALE_AFTER) refresh(false);
  }

  function goStep(n) {
    obStep = n;
    renderOnboarding(collect());
    focusTitle(n);
    $('#onboarding').scrollTop = 0;
  }

  function renderOnboardingStep4() {
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
    $('#ob-step').textContent = `Step ${obStep} of ${OB_STEPS}`;
    for (const dot of document.querySelectorAll('.ob-dot')) dot.classList.toggle('on', Number(dot.dataset.dot) <= obStep);
    for (const pane of document.querySelectorAll('.ob-pane')) pane.hidden = Number(pane.dataset.step) !== obStep;
    $('#onboarding').setAttribute('aria-labelledby', `ob-title-${obStep}`);
    if (obStep === 1) {
      renderMembers($('#ob-members'), 'ob');
      renderServiceRows($('#ob-services'), 'ob');
    }
    if (obStep === 2) renderPerks($('#ob-perks'), 'ob');
    if (obStep === 3) {
      for (const c of document.querySelectorAll('[data-obkind]')) c.setAttribute('aria-pressed', c.dataset.obkind === obKind ? 'true' : 'false');
      $('#ob-q').placeholder = obKind === 'teams' ? 'For example Eagles' : 'For example The Pitt';
      const clear = () => { obResults = null; renderOnboarding(collect()); };
      renderResults($('#ob-results'), obResults, obKind === 'teams' ? teamSearchCard : searchCard, clear);
      if (obKind === 'teams' && sportsStatus !== 'ok' && sportsStatus !== 'unknown' && obResults === null) {
        $('#ob-results').replaceChildren(sportsNotice());
      }
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
        : empty(busy ? 'Loading premieres…' : 'No premieres found yet', busy ? 'Reading the schedule. This takes about 20 seconds.' : 'Search above instead.'));
    }
    if (obStep === 4) renderOnboardingStep4();
  }

  // ---------- tabs ----------

  function showTab(name, focus) {
    if (name === 'tracking') name = 'shows';
    if (name === 'savings') name = 'plan';
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

  async function doSearch(q, kind, assign) {
    q = q.trim().slice(0, kind === 'teams' ? 40 : 100);
    if (!q) return;
    setStatus(`Searching for "${q}"…`);
    try {
      assign(kind === 'teams' ? await searchTeams(q) : await searchShows(q));
      setBanner('');
    } catch (e) {
      if (kind === 'teams') {
        sportsStatus = e.code || 'error';
        assign(null);
      } else setBanner("Search couldn't reach the TV listings. Check your connection and try again.");
    }
    renderAll();
  }

  function exportCalendar() {
    const { text, episodes, games, reminders } = buildICS(collect());
    if (!episodes && !games && !reminders) {
      setBanner('Nothing you follow has an announced upcoming episode or game yet, so there is nothing to add to your calendar.');
      return;
    }
    setBanner('');
    saveFile('episode-radar.ics', text, 'text/calendar;charset=utf-8');
    const parts = [];
    if (episodes) parts.push(`${episodes} episode${episodes === 1 ? '' : 's'}`);
    if (games) parts.push(`${games} game${games === 1 ? '' : 's'}`);
    if (reminders) parts.push(`${reminders} subscription reminder${reminders === 1 ? '' : 's'}`);
    setStatus(`Saved ${listJoin(parts)}. Open episode-radar.ics to add them to your calendar.`);
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
      doSearch($('#search-q').value, 'shows', (r) => { searchResults = r; });
    });
    $('#team-form').addEventListener('submit', (e) => {
      e.preventDefault();
      doSearch($('#team-q').value, 'teams', (r) => { teamResults = r; });
    });

    $('#export-ics').addEventListener('click', exportCalendar);
    $('#export-ics-2').addEventListener('click', exportCalendar);

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
      teamResults = null;
      $('#reset-confirm').hidden = true;
      renderAll();
      openOnboarding();
    });

    // Setup
    $('#ob-skip').addEventListener('click', closeOnboarding);
    $('#ob-next-1').addEventListener('click', () => {
      goStep(2);
      // Load premieres for the chosen services while the person continues.
      refresh(false);
    });
    $('#ob-back-2').addEventListener('click', () => goStep(1));
    $('#ob-next-2').addEventListener('click', () => goStep(3));
    $('#ob-back-3').addEventListener('click', () => goStep(2));
    $('#ob-next-3').addEventListener('click', () => goStep(4));
    $('#ob-back-4').addEventListener('click', () => goStep(3));
    $('#ob-done').addEventListener('click', closeOnboarding);
    for (const c of document.querySelectorAll('[data-obkind]')) {
      c.addEventListener('click', () => {
        obKind = c.dataset.obkind;
        obResults = null;
        renderOnboarding(collect());
      });
    }
    $('#ob-search').addEventListener('submit', (e) => {
      e.preventDefault();
      doSearch($('#ob-q').value, obKind, (r) => { obResults = r; });
    });
    $('#ob-notify').addEventListener('click', async () => {
      await enableNotifications();
      renderOnboardingStep4();
    });
    $('#ob-install').addEventListener('click', promptInstall);

    // Install and offline support.
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      installPrompt = e;
      renderSettings();
      if (!$('#onboarding').hidden) renderOnboardingStep4();
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
