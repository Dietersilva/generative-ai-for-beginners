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
before their real clip is sourced, not for the six that already have
one.

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
