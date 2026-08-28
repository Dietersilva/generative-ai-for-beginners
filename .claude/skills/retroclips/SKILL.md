---
name: retroclips
description: Load this before doing any work on the RetroClips site (sourcing films, editing the reaction-cam, touching build_static.py, or anything SEO/security-related). Encodes the project's standing conventions so they don't have to be rediscovered each session.
---

# RetroClips

RetroClips pairs a ~10 second clip from a public-domain classic film with
~20 seconds of commentary, narration audio, and a small illustrated
"reaction cam." It is an offshoot project in the **In60Seconds Media**
universe (see `in60secondsmedia.com`, a sibling Vercel project on the same
account) — a separate site, not sharing code or infra, but part of the same
portfolio.

**Always concise, slick, topical, accurate — checked, then double-checked.
Secure, then doubly secure.** Verify before asserting; don't guess at a film
count, a URL, or a PD basis when the actual file is one read away.

## Two repos, kept in lockstep

- `Dietersilva/retroclips` (`/home/user/retroclips`) — the real home,
  deploys to Vercel. Canonical domain: **https://retroclips.org**
  (also aliased at `retroclips.vercel.app`).
- `Dietersilva/generative-ai-for-beginners`, subdirectory `retroclips/`
  (`/home/user/generative-ai-for-beginners/retroclips`) — GitHub Pages
  mirror, live at `https://dietersilva.github.io/generative-ai-for-beginners/retroclips/`.
  Work happens on branch `claude/retro-movie-clips-site-egaqql`, tracked by
  PR #2.

Every file in both repos is byte-identical **except** `SITE_URL` in
`scripts/build_static.py` and everything downstream of it (canonical/og
tags, JSON-LD `url` fields, sitemap.xml, the CSP script-hash, which changes
because the JSON-LD body it hashes changes). After any change, rebuild both
and `diff` the two `index.html` files — the diff should be limited to those
URL-derived lines and nothing else. If it's wider than that, something
didn't sync.

`asset_version()` in `build_static.py` hashes `styles.css` + `script.js`
into a `?v=` cache-busting query param. Confirm both repos produce the
*same* asset-version hash after a CSS/JS change — if they don't match, the
two copies of the CSS/JS have diverged.

## Content pipeline (sourcing a new film)

1. WebSearch to sanity-check PD status, then confirm on archive.org's
   `metadata` API — look for `licenseurl` containing
   `creativecommons.org/publicdomain/mark/1.0/`. Films published in the US
   before 1931 also qualify via simple copyright-term expiration even
   without an explicit PD Mark tag (matches the site's existing convention
   for e.g. `traffic-in-souls-1913`, `grass-1925`) — prefer the explicit
   Mark when available, fall back to term-expiration reasoning otherwise.
2. Full local download via backgrounded `curl` — **never remote-seek**.
   For 1GB+ files, use `nohup curl -sL -o file.mp4 URL &` then a Monitor /
   `run_in_background` wait, not manual polling.
   Verify completeness: compare final byte size against archive.org's
   reported size, AND try extracting a frame near the very end of the
   reported duration — a truncated file with a faststart moov atom can
   still report a plausible duration via ffprobe while being cut off.
   Resume a truncated download with `curl -C -`, don't restart from zero.
3. `ffmpeg` contact-sheet grids (`fps=1/N,scale=W:-1,tile=RxC`) to scout
   for the iconic scene, narrowed progressively. **`tile` fills row-major**
   (left to right, then next row down) — don't assume column-major when
   computing a frame's timestamp from its grid position.
4. Trim a 10s clip:
   `scale=854:480:force_original_aspect_ratio=decrease,pad=854:480:(ow-iw)/2:(oh-ih)/2`,
   `libx264 -crf 23 -preset medium`, `aac -b:a 96k`.
5. Poster frame: try `-ss 1.5` into the clip first, but check a few offsets
   — the "best" frame for the poster isn't always the first one, especially
   if the clip opens on a different character or a transition.
6. Write the `films.json` entry (schema: `id`, `title`, `year`, `director`,
   `country`, `genre`, `scene_label`, `scene_description`, `commentary`,
   `pd_basis`, `pd_caveat`, `clip: {status, source_url, source_identifier,
   start_timestamp, duration_sec}`). `films.json` **is** the site's PD-use
   audit log — every film's sourcing basis lives there already; there's no
   separate log to maintain.
7. `python3 scripts/generate_narration.py --film-id <id>` (ElevenLabs). If
   this hits a quota error, that's a real stopping point, not a bug to work
   around — ship without narration (the site already falls back to browser
   `speechSynthesis` via `onerror`/`.catch()` on the `<audio>` element) and
   note the gap; don't fabricate audio or skip the film.
8. `python3 scripts/extract_posterstrip_frames.py --film-id <id>` (3 frames
   per film, used for the ad-slot filmstrip filler).
9. `python3 scripts/build_static.py` from **within that repo's own
   directory** — rebuilds `index.html`, `about.html`, every film page,
   `sitemap.xml`.
10. Playwright smoke test: page loads, correct video count, zero console
    errors, correct mood-genre mapping for the new film(s).
11. `git diff | grep -iE "api[_-]?key|secret|token"` before staging —
    check it's not just the word "secret" appearing in film commentary
    prose (it often does).
12. Mirror every asset + the `films.json` diff into the other repo, rebuild
    it too, re-diff to confirm it's still URL-only, re-test, then commit +
    push both. `generative-ai-for-beginners` pushes need the
    Co-Authored-By/Claude-Session footer per that repo's global conventions.

## Content-sensitivity judgment

Avoid clip moments depicting real racial violence, death, or similarly
disturbing content even when it's the historically "defining" scene of the
film — pick a different scene, or swap the film entirely for a comparable
pick, without needing to ask first. Reserve flagging-to-the-user for cases
where *no* scene can represent the film's significance without depicting
the objectionable content itself (e.g. *Within Our Gates*, 1920 — still an
open item awaiting the user's call, not currently blocking anything since
other films are being sourced instead).

## Reaction-cam mood system

`moodForGenre(genre)` in `script.js` — order matters, first match wins:
pre-code → wink, horror/psychological → scared, screwball/romantic →
swoon, comedy → laughing, surreal → dizzy, science → amazed,
western/action → thrilled, noir → suspicious, documentary → sleepy,
crime/exploitation/propaganda/melodrama/drama → tense, else → neutral.
11 moods total (neutral, scared, laughing, amazed, tense, thrilled, swoon,
sleepy, wink, dizzy, suspicious) — no spit-take, it was removed for being
unreliable (fragile cross-element prop alignment). New reactions should be
self-contained inside the SVG's own coordinate space, not a separate
sibling element trying to line up with it.

When adding a film with a genre string, sanity-check its mood resolution
with a quick Node eval of the function against the new genre before
shipping — silent mismatches are easy to miss by eye.

## SEO / security standing checks

- `SITE_URL` (top of `build_static.py`) is the single source of truth for
  canonical URLs, OG tags, JSON-LD, and `sitemap.xml`. **Individual film
  pages are fully regenerated from scratch each build and pick this up
  automatically.** `index.html` and `about.html` are only *patched* in
  place (via `apply_asset_version` / `apply_site_url` / marker-delimited
  `inject()` calls) — if you ever add a new head tag to those two pages,
  make sure it's covered by `apply_site_url()` or it will silently freeze
  at whatever value it had on the day it was written, immune to future
  `SITE_URL` changes. This already happened once (canonical/og:url/
  og:image/twitter:image were frozen at the old `retroclips.vercel.app`
  domain for a while after `retroclips.org` was connected) — don't
  reintroduce it.
- `apply_site_url()` matches by known trailing suffix (`about.html`,
  `assets/clips/<file>`, or bare root), not by prefix — `SITE_URL` itself
  can contain a path (the GitHub Pages mirror's is a subpath), and a
  prefix-based replace will double it up.
- `robots.txt` and `llms.txt` are **not** auto-generated — hand-maintained,
  and will go stale (wrong film count, wrong domain) if not updated
  alongside a domain change or a large batch. Check them whenever either
  changes.
- `vercel.json` sets `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, a server-level `frame-ancestors 'none'` CSP,
  `Referrer-Policy: strict-origin-when-cross-origin`, a locked-down
  `Permissions-Policy`, and HSTS with preload. The per-page `<meta>` CSP
  (script-src pinned to a sha256 hash of the JSON-LD body, no
  `unsafe-inline`, `connect-src 'none'`, `object-src 'none'`) is generated
  fresh every build from the actual JSON-LD content — don't hand-edit it.
- No secrets are ever committed. `ELEVENLABS_API_KEY` is read from the
  environment only, never hardcoded. `.gitignore` covers `.env`,
  `__pycache__`, etc.
- Run a link/asset audit after any batch or structural change: every
  internal `href`/`src` resolves to a real file, every `about.html#<id>`
  fragment has a matching `id=` in `about.html`, every film in
  `films.json` has its clip mp4/jpg, 3 posterstrip frames, and (ideally) a
  narration mp3.

## Git/process quirks specific to this project

- Never chain `pkill` with a following important command in the same Bash
  call — it can abort the whole chain with a misleading exit code. Run
  `pkill` alone, verify state with a separate call, then proceed.
- Never create an empty commit or push half-finished batch work (missing
  narration/posterstrip/rebuild) just to "ship something" — an uncommitted,
  unpushed working tree with real completed sourcing work in it is fine to
  leave as-is between sessions; it's safer than a broken live page.
- When told to keep sourcing films "until credit limits," that means an
  actual usage/quota error (ElevenLabs 401 quota_exceeded, a Vercel
  API-deployment rate limit, etc.) — not a natural stopping point you
  invent. Keep batching until something actually blocks.
