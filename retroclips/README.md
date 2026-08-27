# RetroClips

A prototype for a site that pairs a 6-7 second clip from a famous *older*
film with ~15-20 seconds of commentary underneath, plus a small
illustrated "reaction cam" watching along in the corner.

**Live:** https://dietersilva.github.io/generative-ai-for-beginners/retroclips/
(served via GitHub Pages from this branch — see "Not done yet" below).

## Why public domain, not fair use

The original pitch was "scrape clips from famous movies." Six-second
clips paired with commentary is roughly what a lot of YouTube reaction
channels do, but that's not evidence the practice is legally safe to
build a site on: there's no bright-line duration that makes a clip
"fair use," it's a case-by-case four-factor test, and what actually
protects most of those YouTube channels is platform-specific (YouTube's
Content ID lets a studio monetize instead of suing, and YouTube absorbs
the takedown process) — a standalone site has neither cushion.

So this prototype only uses films whose US copyright has **expired or
lapsed**, meaning the film itself can legally be hosted outright, no
fair-use argument required. Two ways a film ends up here:

- **Term expiration** — anything published before 1930 is now out of
  copyright in the US regardless of anything else (*Nosferatu*, *The
  Cabinet of Dr. Caligari*, *The General*).
- **Notice/renewal lapse** — some later films fell into the public
  domain because of a technicality under the copyright law in effect
  when they were made: a missing copyright notice (*Night of the Living
  Dead*) or an unrenewed registration (*His Girl Friday*).

Each film card shows a small `© Public Domain` badge; the specific
basis per film (plus a caveat where the reasoning is more
fact-dependent — renewal-lapse cases in particular are more
error-prone to verify than a straightforward "published before 1930")
lives on `about.html`, generated live from `data/films.json` so it
can't drift out of sync with the actual data. **This is not legal
advice** — verify a film's status yourself before relying on it,
especially for anything commercial.

## What's actually in this prototype

- `index.html`, `styles.css`, `script.js` — a static site, no build
  step at *serve* time (there is a small build step at *edit* time —
  see "Static HTML generation" below). `script.js` is pure
  progressive enhancement: it attaches hover/sound/narration behavior
  to markup that already exists, and never fetches anything or builds
  DOM from scratch.
- `about.html` — the full "why public domain" rationale plus a
  per-film basis list, statically generated from `data/films.json`.
- `data/films.json` — ten films with real metadata and hand-written
  commentary (in the target style/length for the auto-generation
  pipeline below). This is the single source of truth; both HTML
  pages are generated from it (see below), so they can't drift out of
  sync with the actual data.
- A CSS/SVG "reaction cam" in the bottom-right corner — an illustrated
  figure, not real video, so there's no likeness/rights question. Its
  expression reacts to whichever card's genre you're hovering (scared
  for horror, laughing for comedy, amazed for sci-fi) via a
  `data-mood` attribute swapped in `script.js`.

### Static HTML generation, SEO, and security

`scripts/build_static.py` reads `data/films.json` and writes the film
cards + JSON-LD structured data into `index.html`, and the per-film PD
basis list into `about.html`, replacing the content between
`<!-- SEO:...START -->` / `<!-- SEO:...END -->` marker comments in
each file. Run it after any edit to `data/films.json`:

```bash
python3 scripts/build_static.py
```

Why this exists: the film grid used to be an empty `<main id="grid">`
that `script.js` filled in at runtime via `fetch()`. That's invisible
to any crawler that doesn't execute JavaScript — most search engines
do run JS, but not reliably, and a lot of LLM/AI crawlers don't at
all. Baking the content into the actual HTML fixes that, and it's also
what let the CSP below get genuinely strict instead of needing to
leave a hole open for a live fetch.

Along with that:

- **Meta tags** — description, Open Graph, Twitter Card, and a
  canonical URL on both pages, so shared links get a real title/
  description/image instead of nothing.
- **JSON-LD** (`index.html` only) — a `WebSite` + `ItemList` of
  `Movie` entries, generated from the same film data, for search
  engines and LLM crawlers that read structured data.
- **Content-Security-Policy** — `script-src 'self' '<hash>'` (the
  hash covers only the generated JSON-LD block; everything else is
  the external `script.js`, no inline scripts anywhere), plus locked
  `style-src`/`img-src`/`media-src` to `'self'`, `connect-src 'none'`
  (nothing on either page fetches anything at runtime anymore),
  `object-src`/`base-uri`/`form-action` all disabled. Verified with a
  Playwright check that an injected inline `<script>` is actually
  refused, not just declared. GitHub Pages can't set custom HTTP
  headers, so this ships as a `<meta http-equiv>` tag instead of a
  real header — one real limitation of that: `frame-ancestors`
  (clickjacking protection) is **not** supported via `<meta>` at all
  per spec, so this site currently has no defense against being
  framed. Fixing that for real needs either a custom domain behind
  something that can set headers (Cloudflare, or a host like Netlify/
  Vercel with a `_headers` file) or GitHub Pages growing header
  support.
- **`robots.txt`** — present, but **only cosmetic at this URL**.
  robots.txt is only honored by crawlers when served from a domain's
  actual root (`dietersilva.github.io/robots.txt`), not from a
  subpath (`.../retroclips/robots.txt`) — this repo doesn't control
  that root today. Kept so it's already correct the day this moves to
  a real domain or a Pages user-site root.
- **`sitemap.xml`** — regenerated by `build_static.py`, lists both
  pages. Submit it manually in Google Search Console / Bing Webmaster
  Tools; it isn't auto-discovered without a root-level robots.txt
  `Sitemap:` line for the reason above.
- **`llms.txt`** — a plain-language summary of the site for AI
  crawlers, following the emerging (not yet standardized) llms.txt
  convention.

### Ad slots

There are two reserved ad slots — one under the header, one in-feed
after the sixth film card (`.ad-slot`/`.ad-carousel` in `styles.css`,
both generated into `index.html` by `build_static.py`). Neither loads
a real ad yet; there's no ad network account to point them at. Rather
than sit empty, each shows a slow horizontally-scrolling filmstrip of
the site's own ten poster stills (a real collection, not a stock
photo) — each tile sized to the image's own 16:9 aspect ratio so the
whole picture shows, not a stretched sliver of it, dimmed slightly so
it doesn't compete with the real film grid. To activate one for real:
sign up for a network (Google AdSense is the obvious first stop,
though very low-traffic/prototype sites are frequently rejected until
there's real traffic — worth revisiting once this has an audience),
then swap the `.ad-carousel` markup inside the corresponding
`.ad-slot` element for that network's script/tag.

### Monetization status

Ad slots and the archive.org "watch the full film" links are both
built, but two things still need a decision only you can make, since
I can't create accounts on your behalf: which ad network to sign up
for (AdSense vs. an alternative), and whether to pursue affiliate
links at all (there's no natural affiliate program for public-domain
films on archive.org — the free "watch the full film" link already
covers that — so affiliate revenue here would more likely come from
something adjacent, like Amazon links to Blu-ray reissues or
criterion-style physical media of these titles, which I haven't
built since it wasn't clear that's actually what you had in mind).

### The clips are real footage, sourced from archive.org

This prototype was originally built inside a sandboxed environment
whose network policy blocked outbound access to archive.org and every
general web host (only package registries and Anthropic's own API were
reachable). That was a deliberate policy denial, not a bug, so the
first pass didn't attempt to route around it — it shipped with
synthetic placeholder clips instead, generated locally with
`scripts/make_placeholder_clips.sh` (grain, vignette, title card,
correct 6.5s length, honestly labeled as a placeholder on the frame).

The environment's network policy was then reconfigured to allow
`archive.org` and its file-serving CDN subdomains (`*.us.archive.org`
— archive.org serves actual video files from per-item hosts like
`ia601606.us.archive.org`, so the wildcard is required, not just the
apex domain). With that open, every clip in `assets/clips/` was
re-sourced for real using `scripts/fetch_clip.py`:

1. Search archive.org for a print of the film, and sanity-check it
   (not `is_dark`, plausible runtime, actually black-and-white where
   that matters — see the Metropolis note below).
2. Scout for the right moment by pulling low-res contact-sheet frames
   at coarse intervals across the likely part of the film, then
   narrowing in — all via ranged HTTP requests against the remote
   file, no full download needed.
3. Run `fetch_clip.py` with the film id, the direct file URL, and the
   in-point timestamp found by scouting. It seeks directly into the
   remote file (`-ss` before `-i`) and re-encodes just that 6.5s
   segment, so it never downloads the full film.
4. Update `clip.start_timestamp`/`status`/`source_identifier`/
   `source_url` in `data/films.json` (`fetch_clip.py` prints the line
   to change), and correct `scene_label`/`scene_description`/
   `commentary` if the actual footage doesn't match what was guessed
   before sourcing — several did shift (e.g. Nosferatu's clip turned
   out to be the claw-hand silhouette at the window, not a literal
   staircase shot as first assumed; His Girl Friday's is the editor's
   office scene, not the newsroom bullpen).

**ffmpeg needs to be told about the proxy explicitly** in an
environment like this one — unlike `curl`, it doesn't read
`HTTPS_PROXY` automatically, so `fetch_clip.py` detects the env var
and passes `-http_proxy`/`-ca_file` to ffmpeg itself when set (see
`proxy_args()` in the script). On a normal machine with no such proxy
this is a no-op.

**Metropolis caveat**: the only readily-available prints on
archive.org are the 2010 "complete" restoration (~150 min), which adds
footage discovered after the film's original 1927 release. That
newly-restored material has its own preservation-era copyright
question. This clip is limited to the robot-transformation shot
specifically, which was present in every prior public-domain cut of
the film — a plain rescan of pre-existing PD frames is unlikely to
carry its own copyright, but this is a narrower claim than the other
five films' and is called out in that film's `pd_caveat`.

Re-running `make_placeholder_clips.sh` would overwrite these with
synthetic placeholders again — it's kept for adding new films quickly
before their real clip is sourced, not for the ten that already have
one.

### Commentary generation

`data/films.json`'s commentary was hand-written in the style/length
target (45-65 words, ~15-20 second read) that the real pipeline should
produce. `scripts/generate_commentary.py` is that real pipeline: given
a film's metadata and scene description, it calls the Claude API for a
commentary paragraph, and can write results back into `films.json`
with `--write`. It needs `ANTHROPIC_API_KEY` set — get one at
[console.anthropic.com](https://console.anthropic.com/).

### Narration

Each "Listen" button plays a pre-generated voice clip rather than
calling any API live from the browser — a static site can't hide an
API key from visitors, so narration has to be baked into a static
asset the same way the film clips are. `scripts/generate_narration.py`
calls ElevenLabs' TTS API once per film and writes
`assets/narration/<film-id>.mp3`. It needs `ELEVENLABS_API_KEY` set
and a `--voice-id`:

```bash
python3 scripts/generate_narration.py --voice-id <voice_id>
```

If a film's MP3 is missing (e.g. a new film added before running this
script) or fails to load, `script.js` falls back to the browser's
built-in speech synthesis automatically — same as before narration
audio existed at all. Both paths are deliberately paced a little
slower than each API's default (ElevenLabs' `voice_settings.speed:
0.85`; the browser fallback's `utterance.rate = 0.85`) after early
feedback that the default pace read too fast.

## Running it locally

No build step needed:

```bash
cd retroclips
python3 -m http.server 8000
# open http://localhost:8000/
```

## Adding a new film

1. Confirm its US copyright status is actually expired or lapsed —
   don't take a random site's word for it.
2. Add an entry to `data/films.json` (copy an existing one as a
   template) with `clip.status: "placeholder"`.
3. Run `scripts/make_placeholder_clips.sh` to get a placeholder clip
   for it immediately, or `scripts/fetch_clip.py` if you already have
   a real source URL and timestamp.
4. Optionally run `scripts/generate_commentary.py --film-id <id>
   --write` instead of writing the commentary by hand.
5. Run `scripts/generate_narration.py --film-id <id>` to generate its
   narration audio.
6. Run `scripts/build_static.py` to regenerate the static HTML card
   in `index.html`, its entry in `about.html`, and `sitemap.xml` —
   without this step the new film won't actually appear on the site.

## Not done yet / open questions

- **Domain** — `retroclips.com` itself isn't registered. The site is
  live on GitHub Pages (see link at the top) instead, serving straight
  off this branch — worth moving to a real domain if this goes past
  prototype, and worth flipping the Pages source over to `main` once
  this branch's PR is merged (Pages settings on GitHub, not something
  set in this repo's files).
- **Reaction cam** — still an illustrated SVG, not real video, so
  there's no likeness/rights question, but its four expressions
  (neutral/scared/laughing/amazed) are simple shape swaps. A real
  video version would need either licensed stock reaction footage or
  an AI-generated avatar — not attempted here.
- **Scale** — ten films is still a proof of concept, not a catalog.
  The public-domain feature-film pool is large (archive.org alone
  lists hundreds), but each one still needs its PD status individually
  confirmed and a real in-point timestamped by hand — there's no
  shortcut for either step.
