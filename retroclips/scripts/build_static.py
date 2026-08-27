#!/usr/bin/env python3
"""
Generate the static, crawlable parts of the site from data/films.json:
film cards + JSON-LD in index.html, the PD-basis list in about.html, and
sitemap.xml.

Why this exists: index.html used to ship with an empty <main id="grid">
that script.js filled in at runtime via fetch() + DOM construction. That's
invisible to any crawler that doesn't execute JavaScript (most search
engine bots do run JS, but not reliably, and LLM/AI crawlers frequently
don't) -- and it also meant a strict Content-Security-Policy couldn't
lock connect-src down, since the page depended on a live fetch.

This script makes films.json's content part of the actual HTML at commit
time, the same "generate once, commit static output" pattern already used
for clips (fetch_clip.py) and narration (generate_narration.py). script.js
now only *enhances* this static markup (hover mood, sound toggle,
narration playback) -- it no longer builds the DOM or fetches anything.

Run this after any edit to data/films.json:
    python3 scripts/build_static.py

It rewrites content between marker comments in index.html and about.html
in place, so it's safe to run repeatedly (idempotent) and safe to run
before those markers exist for the first time is NOT supported -- the
markers must already be present in both files.
"""

import base64
import hashlib
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILMS_JSON = ROOT / "data" / "films.json"
INDEX_HTML = ROOT / "index.html"
ABOUT_HTML = ROOT / "about.html"
SITEMAP_XML = ROOT / "sitemap.xml"

SITE_URL = "https://dietersilva.github.io/generative-ai-for-beginners/retroclips/"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def inject(text: str, start: str, end: str, body: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = f"{start}\n{body}\n{end}"
    new_text, count = pattern.subn(replacement, text)
    if count != 1:
        sys.exit(f"expected exactly one '{start} ... {end}' region, found {count}")
    return new_text


def caption_duration_class(commentary: str) -> str:
    # Matches the old runtime formula (script.js used to set this via
    # element.style directly); rounded to a whole second so a fixed set
    # of CSS classes (duration-14 .. duration-28 in styles.css) can cover
    # it without any inline style -- inline styles need 'unsafe-inline'
    # in the CSP, which we're avoiding.
    seconds = min(28, max(14, round(len(commentary) * 0.09)))
    return f"duration-{seconds}"


def render_card(film: dict) -> str:
    fid = film["id"]
    title = esc(film["title"])
    year = film["year"]
    director = esc(film["director"])
    country = esc(film["country"])
    genre = esc(film["genre"])
    scene_label = esc(film["scene_label"])
    commentary = esc(film["commentary"])
    duration_class = caption_duration_class(film["commentary"])
    pd_title = esc(f'{film["pd_basis"]} {film["pd_caveat"]}' if film.get("pd_caveat") else film["pd_basis"])

    watch_link = ""
    if film["clip"].get("source_url"):
        watch_link = (
            f'<a class="watch-link" href="{esc(film["clip"]["source_url"])}" '
            f'target="_blank" rel="noopener noreferrer">&#9654; Watch the full film</a>'
        )

    return f"""    <article class="card" data-genre="{genre}">
      <div class="clip-frame">
        <video class="clip-video" src="assets/clips/{fid}.mp4" poster="assets/clips/{fid}.jpg" preload="metadata" muted loop playsinline aria-label="{title} ({year}) clip: {scene_label}"></video>
        <div class="clip-caption" aria-hidden="true">
          <div class="clip-caption-track {duration_class}">
            <span>{commentary}</span>
            <span>{commentary}</span>
          </div>
        </div>
        <button type="button" class="sound-badge" aria-label="Play clip with sound">&#128264;</button>
      </div>
      <div class="card-body">
        <div class="card-title-row">
          <h2>{title}</h2>
          <span class="card-year">{year}</span>
        </div>
        <div class="card-meta">{director} &mdash; {country} &mdash; {genre}</div>
        <div class="scene-label">{scene_label}</div>
        <div class="commentary-row">
          <p class="commentary">{commentary}</p>
          <audio class="narration-audio" preload="none" src="assets/narration/{fid}.mp3"></audio>
          <button type="button" class="narrate-btn" aria-label="Listen to the commentary for {title}, read over the clip">&#128264; Listen</button>
        </div>
        <div class="card-footer-row">
          {watch_link}
          <a class="pd-badge" href="about.html#{fid}" title="{pd_title}">&copy; Public Domain</a>
        </div>
      </div>
    </article>"""


POSTERSTRIP_DIR = ROOT / "assets" / "posterstrip"
POSTERSTRIP_FRAMES_PER_FILM = 3  # matches FRAME_TIMES in extract_posterstrip_frames.py


def poster_strip_images(films: list) -> list:
    # One frame from assets/clips/<id>.jpg (the video's own poster) plus
    # extract_posterstrip_frames.py's extra frames per film, if they've
    # been generated -- falls back to just the one clip poster per film
    # otherwise, so this doesn't hard-require that script having been run.
    per_film = []
    for film in films:
        fid = film["id"]
        frames = [f"assets/clips/{fid}.jpg"]
        for n in range(1, POSTERSTRIP_FRAMES_PER_FILM + 1):
            if (POSTERSTRIP_DIR / f"{fid}-{n}.jpg").exists():
                frames.append(f"assets/posterstrip/{fid}-{n}.jpg")
        per_film.append(frames)

    # Round-robin across films rather than grouping each film's frames
    # together -- four consecutive tiles from the same 6.5s clip read as
    # near-duplicates at a glance. Interleaving keeps every adjacent tile
    # a different film while still cycling through all of them.
    paths = []
    for i in range(max(len(f) for f in per_film)):
        for frames in per_film:
            if i < len(frames):
                paths.append(frames[i])
    return paths


def render_ad_slot(films: list, variant: str, slot_id: str) -> str:
    # Reserved ad space, no network wired in yet -- filled with a slow
    # horizontally-scrolling filmstrip of the site's own poster stills (a
    # real collection, not a stock photo) so it isn't a bare box. Named
    # .poster-strip rather than .ad-slot/.ad-carousel on purpose: generic
    # ad-blocker filter lists hide elements matching "ad-*" class/attribute
    # patterns regardless of what's actually inside them. The sequence is
    # duplicated back to back so the -50% translateX loop in
    # .poster-strip-track (styles.css) is seamless -- same trick as the
    # caption ticker.
    imgs = "\n          ".join(
        f'<img src="{src}" alt="">' for src in poster_strip_images(films)
    )
    return f"""    <div class="poster-strip poster-strip--{variant}" data-poster-strip="{slot_id}" aria-hidden="true">
      <div class="poster-strip-frame">
        <div class="poster-strip-track">
          {imgs}
          {imgs}
        </div>
      </div>
    </div>"""


def render_cards(films: list) -> str:
    parts = []
    for i, film in enumerate(films):
        parts.append(render_card(film))
        if i == 5:  # after the 6th card
            parts.append(render_ad_slot(films, "infeed", "in-feed"))
    return "\n".join(parts)


def render_about_entry(film: dict) -> str:
    title = esc(film["title"])
    year = film["year"]
    pd_basis = esc(film["pd_basis"])
    caveat = f'\n      <p class="about-caveat">{esc(film["pd_caveat"])}</p>' if film.get("pd_caveat") else ""
    return f"""    <div class="about-entry" id="{film['id']}">
      <h3>{title} <span class="card-year">{year}</span></h3>
      <p>{pd_basis}</p>{caveat}
    </div>"""


def render_json_ld(data: dict) -> str:
    films = data["films"]
    site = data["site"]
    items = []
    for i, film in enumerate(films, start=1):
        items.append({
            "@type": "ListItem",
            "position": i,
            "item": {
                "@type": "Movie",
                "name": film["title"],
                "datePublished": str(film["year"]),
                "director": {"@type": "Person", "name": film["director"]},
                "countryOfOrigin": film["country"],
                "genre": film["genre"],
                "description": film["commentary"],
                "url": film["clip"].get("source_url") or SITE_URL,
            },
        })

    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "name": site["name"],
                "url": SITE_URL,
                "description": site["tagline"],
            },
            {
                "@type": "ItemList",
                "name": "RetroClips public-domain film clips",
                "url": SITE_URL,
                "numberOfItems": len(films),
                "itemListElement": items,
            },
        ],
    }
    return json.dumps(graph, indent=2, ensure_ascii=False)


def csp_hash(script_body: str) -> str:
    digest = hashlib.sha256(script_body.encode("utf-8")).digest()
    return "sha256-" + base64.b64encode(digest).decode("ascii")


def build_index(data: dict) -> None:
    text = INDEX_HTML.read_text()

    ad_top = render_ad_slot(data["films"], "top", "top")
    text = inject(text, "<!-- SEO:ADTOP_START -->", "<!-- SEO:ADTOP_END -->", ad_top)

    cards = render_cards(data["films"])
    text = inject(text, "<!-- SEO:CARDS_START -->", "<!-- SEO:CARDS_END -->", cards)

    json_ld_body = render_json_ld(data)
    json_ld_script = f'<script type="application/ld+json">{json_ld_body}</script>'
    text = inject(text, "<!-- SEO:JSONLD_START -->", "<!-- SEO:JSONLD_END -->", json_ld_script)

    script_hash = csp_hash(json_ld_body)
    csp = (
        "default-src 'self'; "
        f"script-src 'self' '{script_hash}'; "
        "style-src 'self'; "
        "img-src 'self'; "
        "media-src 'self'; "
        "connect-src 'none'; "
        "object-src 'none'; "
        "base-uri 'none'; "
        "form-action 'none';"
    )
    csp_tag = f'<meta http-equiv="Content-Security-Policy" content="{csp}">'
    text = inject(text, "<!-- SEO:CSP_START -->", "<!-- SEO:CSP_END -->", csp_tag)

    INDEX_HTML.write_text(text)


def build_about(data: dict) -> None:
    text = ABOUT_HTML.read_text()
    entries = "\n".join(render_about_entry(film) for film in data["films"])
    text = inject(text, "<!-- SEO:ENTRIES_START -->", "<!-- SEO:ENTRIES_END -->", entries)
    ABOUT_HTML.write_text(text)


def build_sitemap() -> None:
    from datetime import date

    today = date.today().isoformat()
    urls = [SITE_URL, SITE_URL + "about.html"]
    entries = "\n".join(
        f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{today}</lastmod>\n  </url>" for u in urls
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>\n"
    )
    SITEMAP_XML.write_text(sitemap)


def main() -> None:
    data = json.loads(FILMS_JSON.read_text())
    build_index(data)
    build_about(data)
    build_sitemap()
    print(f"Wrote {INDEX_HTML}, {ABOUT_HTML}, {SITEMAP_XML}")


if __name__ == "__main__":
    main()
