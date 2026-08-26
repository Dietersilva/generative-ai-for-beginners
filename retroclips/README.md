# RetroClips

A prototype for a site that pairs a 6-7 second clip from a famous *older*
film with ~15-20 seconds of commentary underneath, plus a small
illustrated "reaction cam" watching along in the corner.

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

Each film card on the site shows its specific basis in a `Public
domain:` line, plus a caveat where the reasoning is more fact-dependent
(renewal-lapse cases in particular are more error-prone to verify than
a straightforward "published before 1930"). **This is not legal
advice** — verify a film's status yourself before relying on it,
especially for anything commercial.

## What's actually in this prototype

- `index.html`, `styles.css`, `script.js` — a static site, no build
  step. Renders a card per film from `data/films.json`: clip, title,
  director/year/genre, the scene shown, commentary, and the PD basis.
- `data/films.json` — six films with real metadata and hand-written
  commentary (in the target style/length for the auto-generation
  pipeline below).
- A CSS/SVG "reaction cam" in the bottom-right corner — an illustrated
  figure, not real video, so there's no likeness/rights question.

### The clips are placeholders, not real footage

This prototype was built inside a sandboxed environment whose network
policy blocks outbound access to archive.org and every general web
host (only package registries and Anthropic's own API are reachable
from here). That's a deliberate policy denial, not a bug, so this
build didn't attempt to route around it.

Instead, `scripts/make_placeholder_clips.sh` generates a synthetic
6.5s clip per film locally with ffmpeg (grain, vignette, title card) —
correct length, real `<video>` playback, honestly labeled as a
placeholder on the frame itself. It's what's currently sitting in
`assets/clips/`.

To swap in real footage:

1. Run `scripts/fetch_clip.py` **from a machine with normal internet
   access** (not this sandbox) — it takes a film id, a direct
   archive.org file URL, a start timestamp, and a duration, and uses
   ffmpeg's remote seeking (`-ss` before `-i`) to pull and trim just
   that segment without downloading the full film. See the script's
   docstring for how to find a source URL and a timestamp.
2. It overwrites `assets/clips/<film-id>.mp4` and regenerates the
   poster jpg in the site's target format.
3. Update that film's `clip.start_timestamp` and `clip.status` in
   `data/films.json`.

Alternatively: if you'd rather this environment could reach
archive.org directly, that's a setting on the environment itself
(network policy is chosen when it's created) — worth revisiting if
you want the whole pipeline runnable in one place.

### Commentary generation

`data/films.json`'s commentary was hand-written in the style/length
target (45-65 words, ~15-20 second read) that the real pipeline should
produce. `scripts/generate_commentary.py` is that real pipeline: given
a film's metadata and scene description, it calls the Claude API for a
commentary paragraph, and can write results back into `films.json`
with `--write`. It needs `ANTHROPIC_API_KEY` set — get one at
[console.anthropic.com](https://console.anthropic.com/).

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

## Not done yet / open questions

- **Domain / hosting** — `retroclips.com` isn't registered and this
  isn't deployed anywhere; it's a local prototype.
- **Real clips** — see above, blocked on network access from this
  environment.
- **Reaction cam** — currently a static illustrated loop. Options for
  a real version: a licensed stock reaction-footage loop, or an
  AI-generated avatar (avoids using any real person's likeness
  without consent) — either is a separate follow-up, not attempted
  here.
- **Scale** — six films is a proof of concept, not a catalog. The
  public-domain feature-film pool is large (archive.org alone lists
  hundreds), but each one still needs its PD status individually
  confirmed and a real in-point timestamped by hand — there's no
  shortcut for either step.
