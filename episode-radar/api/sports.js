'use strict';

// Vercel serverless function: GET /api/sports
//   ?action=teams&q=<team name>   -> { teams: [...] }
//   ?action=games&id=<team id>    -> { games: [...] } with US TV channels per game
//
// It proxies TheSportsDB with the paid key kept in the THESPORTSDB_KEY
// environment variable, so the key never reaches a browser. Only these two
// fixed lookups are possible (no caller-supplied URLs), inputs are validated,
// output is reduced to known fields, and successful answers carry a shared
// CDN cache header so the key's rate limit is spent once for all users.
// TheSportsDB's terms require crediting it as the data source; the app does.

const BASE = 'https://www.thesportsdb.com/api/v1/json/';
const TIMEOUT_MS = 8000;
const MAX_BYTES = 2_000_000;
const MAX_GAMES = 10;
const US = new Set(['united states', 'usa', 'us', 'united states of america']);
const IMG_HOSTS = new Set(['www.thesportsdb.com', 'r2.thesportsdb.com']);

// Best-effort limit per server instance. Add a Vercel Firewall rate-limit rule
// for a limit that holds across instances.
const hits = new Map();
function limited(ip) {
  const now = Date.now();
  const e = hits.get(ip) || { t: now, n: 0 };
  if (now - e.t > 60e3) {
    e.t = now;
    e.n = 0;
  }
  e.n += 1;
  hits.set(ip, e);
  if (hits.size > 5000) hits.clear();
  return e.n > 60;
}

const str = (v, max) => (typeof v === 'string' ? v.trim().slice(0, max) : '');
const isId = (v, digits) => new RegExp(`^\\d{1,${digits}}$`).test(String(v));

function img(v) {
  try {
    const u = new URL(v);
    return u.protocol === 'https:' && IMG_HOSTS.has(u.hostname) ? u.href : null;
  } catch {
    return null;
  }
}

// TheSportsDB wraps each list in a single named key ({"teams": [...]},
// {"events": [...]}, {"tvevent": [...]}); a missing list is null.
function firstArray(obj) {
  if (!obj || typeof obj !== 'object') return [];
  for (const v of Object.values(obj)) if (Array.isArray(v)) return v;
  return [];
}

async function tsdb(key, path) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(BASE + encodeURIComponent(key) + path, {
      signal: ctrl.signal,
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) throw new Error(`upstream ${res.status}`);
    const text = await res.text();
    if (text.length > MAX_BYTES) throw new Error('upstream response too large');
    return text ? JSON.parse(text) : {};
  } finally {
    clearTimeout(timer);
  }
}

// Kick-off as an ISO UTC string, or null when the listing has no usable time.
function startOf(e) {
  const ts = str(e.strTimestamp, 40);
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$/.test(ts)) return new Date(ts + 'Z').toISOString();
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(Z|[+-]\d{2}:?\d{2})$/.test(ts)) return new Date(ts).toISOString();
  // strTime is UTC unless it carries its own offset.
  const d = str(e.dateEvent, 10);
  const m = /^(\d{2}:\d{2})(:\d{2})?(Z|[+-]\d{2}:?\d{2})?$/.exec(str(e.strTime, 16));
  if (/^\d{4}-\d{2}-\d{2}$/.test(d) && m) {
    const when = new Date(`${d}T${m[1]}${m[2] || ':00'}${m[3] || 'Z'}`);
    return Number.isNaN(when.getTime()) ? null : when.toISOString();
  }
  return null;
}

async function usChannels(key, eventId) {
  try {
    const tv = await tsdb(key, `/lookuptv.php?id=${eventId}`);
    const names = firstArray(tv)
      .filter((c) => c && US.has(str(c.strCountry, 60).toLowerCase()))
      .map((c) => str(c.strChannel, 60))
      .filter(Boolean);
    return [...new Set(names)].slice(0, 8);
  } catch {
    return null; // Listing unavailable, as opposed to "no US channel".
  }
}

async function teams(key, q) {
  const data = await tsdb(key, `/searchteams.php?t=${encodeURIComponent(q)}`);
  return firstArray(data)
    .filter((t) => t && isId(t.idTeam, 9))
    .slice(0, 10)
    .map((t) => ({
      id: Number(t.idTeam),
      name: str(t.strTeam, 80),
      league: str(t.strLeague, 80),
      sport: str(t.strSport, 40),
      country: str(t.strCountry, 60),
      badge: img(t.strBadge || t.strTeamBadge),
    }));
}

async function games(key, id) {
  const data = await tsdb(key, `/eventsnext.php?id=${id}`);
  const events = firstArray(data).filter((e) => e && isId(e.idEvent, 12)).slice(0, MAX_GAMES);
  const out = [];
  // Look up TV listings a few at a time to stay polite to the upstream API.
  for (let i = 0; i < events.length; i += 4) {
    const batch = events.slice(i, i + 4);
    const channels = await Promise.all(batch.map((e) => usChannels(key, e.idEvent)));
    batch.forEach((e, j) => {
      out.push({
        id: Number(e.idEvent),
        name: str(e.strEvent, 120),
        league: str(e.strLeague, 80),
        home: str(e.strHomeTeam, 80),
        away: str(e.strAwayTeam, 80),
        date: /^\d{4}-\d{2}-\d{2}$/.test(e.dateEvent) ? e.dateEvent : '',
        start: startOf(e),
        channels: channels[j],
      });
    });
  }
  return out;
}

module.exports = async function handler(req, res) {
  const send = (status, body, cache) => {
    res.statusCode = status;
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.setHeader('Cache-Control', cache || 'no-store');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.end(JSON.stringify(body));
  };

  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return send(405, { error: 'method_not_allowed' });
  }
  const ip = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || (req.socket && req.socket.remoteAddress) || 'unknown';
  if (limited(ip)) return send(429, { error: 'rate_limited' });

  const key = process.env.THESPORTSDB_KEY;
  if (!key || !/^[A-Za-z0-9]{1,64}$/.test(key)) return send(503, { error: 'not_configured' });

  let url;
  try {
    url = new URL(req.url, 'http://localhost');
  } catch {
    return send(400, { error: 'bad_request' });
  }
  const action = url.searchParams.get('action');
  try {
    if (action === 'teams') {
      const q = (url.searchParams.get('q') || '').trim();
      if (!/^[\p{L}\p{N} .'&-]{2,40}$/u.test(q)) return send(400, { error: 'bad_query' });
      return send(200, { teams: await teams(key, q) }, 'public, s-maxage=86400, stale-while-revalidate=604800');
    }
    if (action === 'games') {
      const id = url.searchParams.get('id') || '';
      if (!isId(id, 9)) return send(400, { error: 'bad_id' });
      return send(200, { games: await games(key, id) }, 'public, s-maxage=21600, stale-while-revalidate=86400');
    }
    return send(400, { error: 'unknown_action' });
  } catch {
    return send(502, { error: 'upstream_unavailable' });
  }
};
