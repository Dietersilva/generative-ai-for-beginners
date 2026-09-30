'use strict';

// Local preview: serves the app and the /api/sports function the way Vercel
// does, with the same security headers. Listens on this computer only.
//   THESPORTSDB_KEY=yourkey node dev-server.js     then open http://localhost:8080
// Without a key the app works; the Sports tab says sports is not set up.

const http = require('http');
const fs = require('fs');
const path = require('path');
const sports = require('./api/sports.js');

const ROOT = __dirname;
const PORT = Number(process.env.PORT) || 8080;
const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.webmanifest': 'application/manifest+json',
  '.txt': 'text/plain; charset=utf-8',
};
const vercel = JSON.parse(fs.readFileSync(path.join(ROOT, 'vercel.json'), 'utf8'));
const baseHeaders = vercel.headers[0].headers.filter((h) => h.key !== 'Strict-Transport-Security');

http.createServer((req, res) => {
  for (const h of baseHeaders) res.setHeader(h.key, h.value);
  const url = new URL(req.url, 'http://localhost');
  if (url.pathname === '/api/sports') return sports(req, res);

  // Only files inside this folder; never dotfiles, the api source or this script.
  const rel = decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname);
  const file = path.normalize(path.join(ROOT, rel));
  const blocked = !file.startsWith(ROOT + path.sep) || rel.split('/').some((p) => p.startsWith('.'))
    || file.startsWith(path.join(ROOT, 'api')) || file === __filename;
  if (req.method !== 'GET' || blocked || !TYPES[path.extname(file)]) {
    res.statusCode = 404;
    return res.end('Not found');
  }
  fs.readFile(file, (err, body) => {
    if (err) {
      res.statusCode = 404;
      return res.end('Not found');
    }
    res.setHeader('Content-Type', TYPES[path.extname(file)]);
    res.setHeader('Cache-Control', 'no-cache');
    res.end(body);
  });
}).listen(PORT, '127.0.0.1', () => {
  console.log(`Episode Radar on http://localhost:${PORT}${process.env.THESPORTSDB_KEY ? '' : ' (sports off: THESPORTSDB_KEY not set)'}`);
});
