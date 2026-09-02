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
RSS_XML = ROOT / "feed.xml"

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
    # Rounded to a whole second so a fixed set of CSS classes
    # (duration-20 .. duration-120 in styles.css) can cover it without any
    # inline style -- inline styles need 'unsafe-inline' in the CSP, which
    # we're avoiding.
    #
    # 0.13s/char, floor 20s/ceiling 120s. The original 0.09s/char with a
    # 28s ceiling was tuned when commentary blurbs ran short; the catalog's
    # commentary is now consistently 300-800 chars (batches with real
    # trivia/history), so the 28s cap was binding for ~98% of films --
    # every card scrolled its caption at the same fixed pace regardless of
    # how much text it actually had, turning the longer, richer blurbs
    # into an unreadable blur. The new ceiling (120s) comfortably clears
    # today's longest commentary (~800 chars -> ~104s) so duration once
    # again reflects actual content length across the real range.
    seconds = min(120, max(20, round(len(commentary) * 0.13)))
    return f"duration-{seconds}"


def poster_strip_duration_class(num_tiles: int) -> str:
    # Same reasoning as caption_duration_class: a fixed set of CSS classes
    # (strip-duration-180 .. strip-duration-1800 in styles.css, step 30)
    # instead of an inline animation-duration.
    #
    # The strip's animation always scrolls exactly 50% of its own width
    # (the tile sequence is duplicated back to back for a seamless loop),
    # so a *fixed* duration means its px/s speed rises every time a batch
    # adds more tiles -- the strip has been getting faster with every
    # film shipped, not just taking longer to loop. ~2.5s per tile keeps
    # the crossing speed roughly constant as the catalog grows (currently
    # ~400 tiles -> ~1000s/loop; at 180x9 fixed it had sped up to ~2.2
    # tiles/s, a blur), clamped to a wide range so it stays sane at both
    # a small and a very large catalog size.
    seconds = min(1800, max(180, round(num_tiles * 2.5 / 30) * 30))
    return f"strip-duration-{seconds}"


CATEGORIES = ["horror", "comedy", "sci-fi", "drama"]
CATEGORY_LABELS = {"horror": "Horror", "comedy": "Comedy", "sci-fi": "Sci-Fi", "drama": "Drama"}


def category_for_genre(genre: str) -> str:
    # Same bucketing script.js's moodForGenre uses for the reaction-cam,
    # reused here as the genre-filter taxonomy so the two stay consistent
    # -- filtering to "Horror" shows exactly the cards that make the
    # reaction cam flinch. Individual genre strings are too varied/specific
    # ("Action-Comedy / Silent", "Screwball Comedy", "Drama / Propaganda")
    # to use directly as filter buttons.
    g = genre.lower()
    if "horror" in g or "psychological" in g:
        return "horror"
    if "comedy" in g:
        return "comedy"
    if "science" in g:
        return "sci-fi"
    return "drama"


def render_card(film: dict) -> str:
    fid = film["id"]
    title = esc(film["title"])
    year = film["year"]
    director = esc(film["director"])
    country = esc(film["country"])
    genre = esc(film["genre"])
    category = category_for_genre(film["genre"])
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

    return f"""    <article class="card" data-genre="{genre}" data-category="{category}">
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
        <div class="listen-row">
          <audio class="narration-audio" preload="none" src="assets/narration/{fid}.mp3"></audio>
          <button type="button" class="narrate-btn" aria-label="Listen to the commentary for {title}, read over the clip">&#127911; Narration</button>
        </div>
        <div class="card-title-row">
          <h2><a href="{fid}.html" class="card-title-link">{title}</a></h2>
          <span class="card-year">{year}</span>
        </div>
        <div class="card-meta">{director} &mdash; {country} &mdash; {genre}</div>
        <div class="scene-label">{scene_label}</div>
        <p class="commentary">{commentary}</p>
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
    # Each entry carries the owning film too, since every tile now links
    # to that film's own page.
    per_film = []
    for film in films:
        fid = film["id"]
        frames = [f"assets/clips/{fid}.jpg"]
        for n in range(1, POSTERSTRIP_FRAMES_PER_FILM + 1):
            if (POSTERSTRIP_DIR / f"{fid}-{n}.jpg").exists():
                frames.append(f"assets/posterstrip/{fid}-{n}.jpg")
        per_film.append([(src, film) for src in frames])

    # Round-robin across films rather than grouping each film's frames
    # together -- four consecutive tiles from the same ~10s clip read as
    # near-duplicates at a glance. Interleaving keeps every adjacent tile
    # a different film while still cycling through all of them.
    entries = []
    for i in range(max(len(f) for f in per_film)):
        for frames in per_film:
            if i < len(frames):
                entries.append(frames[i])
    return entries


def render_ad_slot(films: list, variant: str, slot_id: str) -> str:
    # Reserved ad space, no network wired in yet -- filled with a slow
    # horizontally-scrolling filmstrip of the site's own poster stills (a
    # real collection, not a stock photo) so it isn't a bare box, and each
    # tile links to that film's own page -- real navigation, not just
    # decoration, so the slot itself is no longer aria-hidden. Named
    # .poster-strip rather than .ad-slot/.ad-carousel on purpose: generic
    # ad-blocker filter lists hide elements matching "ad-*" class/attribute
    # patterns regardless of what's actually inside them. The sequence is
    # duplicated back to back so the -50% translateX loop in
    # .poster-strip-track (styles.css) is seamless -- same trick as the
    # caption ticker.
    def tile(src: str, film: dict) -> str:
        label = esc(f'{film["title"]} ({film["year"]})')
        return f'<a href="{film["id"]}.html" aria-label="{label}"><img src="{src}" alt=""></a>'

    entries = poster_strip_images(films)
    imgs = "\n          ".join(tile(src, film) for src, film in entries)
    duration_class = poster_strip_duration_class(len(entries))
    return f"""    <div class="poster-strip poster-strip--{variant}" data-poster-strip="{slot_id}">
      <div class="poster-strip-frame">
        <div class="poster-strip-track {duration_class}">
          {imgs}
          {imgs}
        </div>
      </div>
    </div>"""


def render_filter_bar(films: list) -> str:
    present = [c for c in CATEGORIES if any(category_for_genre(f["genre"]) == c for f in films)]
    buttons = ['    <button type="button" class="filter-btn is-active" data-filter="all">All</button>']
    for cat in present:
        buttons.append(
            f'    <button type="button" class="filter-btn" data-filter="{cat}">{CATEGORY_LABELS[cat]}</button>'
        )
    return '  <div class="filter-bar" role="group" aria-label="Filter by genre">\n' + "\n".join(buttons) + "\n  </div>"


IN_FEED_AD_FIRST = 5  # 0-indexed: insert after the 6th card
IN_FEED_AD_REPEAT = 8  # ...then every 8 cards after that


def render_cards(films: list) -> str:
    parts = []
    slot_n = 0
    for i, film in enumerate(films):
        parts.append(render_card(film))
        if i >= IN_FEED_AD_FIRST and (i - IN_FEED_AD_FIRST) % IN_FEED_AD_REPEAT == 0:
            slot_n += 1
            parts.append(render_ad_slot(films, "infeed", f"in-feed-{slot_n}"))
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


def asset_version() -> str:
    # Cache-busting query param for styles.css/script.js. Without this, a
    # deploy can leave a visitor's browser (or a CDN edge) serving last
    # version's CSS/JS alongside this version's HTML -- which is exactly
    # what happened a few times while iterating on the ad-slot styling
    # ("it's still broken" after a fix that was, in fact, already live).
    # Hashing the files themselves means the query string only changes
    # when their content actually does.
    h = hashlib.sha256()
    for name in ("styles.css", "script.js"):
        h.update((ROOT / name).read_bytes())
    return h.hexdigest()[:10]


def apply_asset_version(text: str, version: str) -> str:
    # Regex (not a plain string replace) so this is idempotent -- safe to
    # re-run against a file that already has a "?v=..." from a prior build.
    text = re.sub(r'href="styles\.css(\?v=[a-f0-9]+)?"', f'href="styles.css?v={version}"', text)
    text = re.sub(r'src="script\.js(\?v=[a-f0-9]+)?"', f'src="script.js?v={version}"', text)
    return text


def apply_site_url(text: str) -> str:
    # Idempotent: rewrites the domain+path prefix in canonical/og:url/og:image/
    # twitter:image to the current SITE_URL, regardless of what was previously
    # baked in (including a github.io subpath), so index.html and about.html
    # (patched in place, not regenerated from scratch) can't silently drift to
    # a stale domain/path on a future rebuild. Matched by known trailing
    # suffix rather than by prefix, since SITE_URL itself can contain slashes
    # (a github.io subpath), which a prefix-based replace would double up.
    def replace_url(match: "re.Match") -> str:
        attr, old_url = match.group(1), match.group(2)
        if old_url.endswith("about.html"):
            return f'{attr}{SITE_URL}about.html"'
        if "assets/clips/" in old_url:
            filename = old_url.split("assets/clips/")[-1]
            return f'{attr}{SITE_URL}assets/clips/{filename}"'
        return f'{attr}{SITE_URL}"'

    text = re.sub(
        r'(<link rel="canonical" href="|<meta property="og:url" content=")(https?://[^"]+)"',
        replace_url,
        text,
    )
    text = re.sub(
        r'(<meta property="og:image" content="|<meta name="twitter:image" content=")(https?://[^"]+)"',
        replace_url,
        text,
    )
    return text


def csp_hash(script_body: str) -> str:
    digest = hashlib.sha256(script_body.encode("utf-8")).digest()
    return "sha256-" + base64.b64encode(digest).decode("ascii")


def csp_for_json_ld(json_ld_body: str) -> str:
    script_hash = csp_hash(json_ld_body)
    return (
        "default-src 'self'; "
        f"script-src 'self' '{script_hash}'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "media-src 'self'; "
        "connect-src 'none'; "
        "object-src 'none'; "
        "base-uri 'none'; "
        "form-action 'none';"
    )


def build_index(data: dict, version: str) -> None:
    text = INDEX_HTML.read_text()
    text = apply_asset_version(text, version)
    text = apply_site_url(text)

    filter_bar = render_filter_bar(data["films"])
    text = inject(text, "<!-- SEO:FILTERBAR_START -->", "<!-- SEO:FILTERBAR_END -->", filter_bar)

    ad_top = render_ad_slot(data["films"], "top", "top")
    text = inject(text, "<!-- SEO:ADTOP_START -->", "<!-- SEO:ADTOP_END -->", ad_top)

    cards = render_cards(data["films"])
    text = inject(text, "<!-- SEO:CARDS_START -->", "<!-- SEO:CARDS_END -->", cards)

    json_ld_body = render_json_ld(data)
    json_ld_script = f'<script type="application/ld+json">{json_ld_body}</script>'
    text = inject(text, "<!-- SEO:JSONLD_START -->", "<!-- SEO:JSONLD_END -->", json_ld_script)

    csp_tag = f'<meta http-equiv="Content-Security-Policy" content="{csp_for_json_ld(json_ld_body)}">'
    text = inject(text, "<!-- SEO:CSP_START -->", "<!-- SEO:CSP_END -->", csp_tag)

    INDEX_HTML.write_text(text)


def render_film_json_ld(film: dict) -> str:
    movie = {
        "@context": "https://schema.org",
        "@type": "Movie",
        "name": film["title"],
        "datePublished": str(film["year"]),
        "director": {"@type": "Person", "name": film["director"]},
        "countryOfOrigin": film["country"],
        "genre": film["genre"],
        "description": film["commentary"],
        "image": f"{SITE_URL}assets/clips/{film['id']}.jpg",
        "url": film["clip"].get("source_url") or SITE_URL,
    }
    return json.dumps(movie, indent=2, ensure_ascii=False)


def render_film_page(film: dict, version: str) -> str:
    fid = film["id"]
    title = esc(film["title"])
    year = film["year"]
    scene_label = esc(film["scene_label"])
    description = esc(film["commentary"])
    page_title = f"{title} ({year}) &mdash; {scene_label}"
    page_url = f"{SITE_URL}{fid}.html"
    og_image = f"{SITE_URL}assets/clips/{fid}.jpg"

    json_ld_body = render_film_json_ld(film)
    json_ld_script = f'<script type="application/ld+json">{json_ld_body}</script>'
    csp = csp_for_json_ld(json_ld_body)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<title>{page_title} | RetroClips</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{page_url}">
<link rel="alternate" type="application/rss+xml" title="RetroClips — New Films" href="feed.xml">
<meta property="og:type" content="video.other">
<meta property="og:site_name" content="RetroClips">
<meta property="og:title" content="{page_title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{page_url}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{page_title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{og_image}">
<meta http-equiv="Referrer-Policy" content="strict-origin-when-cross-origin">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<link rel="stylesheet" href="styles.css?v={version}">
{json_ld_script}
</head>
<body>

<header class="site-header">
  <div class="brand">
    <a href="index.html" class="brand-link"><span class="brand-mark">RC</span></a>
    <h1><a href="index.html" class="brand-link">RetroClips</a></h1>
  </div>
  <p class="tagline">{title} ({year})</p>
  <p class="home-link"><a href="index.html" aria-label="Home">&larr; Retour</a></p>
</header>

<main class="film-page">
  <div class="grid grid--single">
{render_card(film)}
  </div>
  <p class="film-page-back"><a href="index.html">&larr; Back to all clips</a></p>
</main>

<footer class="site-footer">
  <p class="pd-note">Every clip on this site is public domain, not a fair-use claim &mdash; <a href="about.html">read why</a>.</p>
</footer>

<script src="script.js?v={version}"></script>
</body>
</html>
"""


def build_film_pages(data: dict, version: str) -> list:
    ids = []
    for film in data["films"]:
        fid = film["id"]
        out = ROOT / f"{fid}.html"
        out.write_text(render_film_page(film, version))
        ids.append(fid)
    return ids


def build_about(data: dict, version: str) -> None:
    text = ABOUT_HTML.read_text()
    text = apply_asset_version(text, version)
    text = apply_site_url(text)
    entries = "\n".join(render_about_entry(film) for film in data["films"])
    text = inject(text, "<!-- SEO:ENTRIES_START -->", "<!-- SEO:ENTRIES_END -->", entries)
    ABOUT_HTML.write_text(text)


def build_sitemap(film_ids: list) -> None:
    from datetime import date

    today = date.today().isoformat()
    urls = [SITE_URL, SITE_URL + "about.html"] + [SITE_URL + f"{fid}.html" for fid in film_ids]
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


def build_rss(data: dict) -> None:
    from datetime import datetime, timezone
    from email.utils import format_datetime

    films = sorted(
        data["films"],
        key=lambda f: (f.get("date_added", "1970-01-01"), f["id"]),
        reverse=True,
    )[:30]

    def rfc822(date_str: str) -> str:
        dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
        return format_datetime(dt)

    items = []
    for film in films:
        fid = film["id"]
        page_url = f"{SITE_URL}{fid}.html"
        pub_date = rfc822(film.get("date_added", "1970-01-01"))
        description = f"{film['scene_label']} — {film['commentary']}"
        items.append(
            "  <item>\n"
            f"    <title>{esc(film['title'])} ({film['year']})</title>\n"
            f"    <link>{page_url}</link>\n"
            f"    <guid isPermaLink=\"true\">{page_url}</guid>\n"
            f"    <pubDate>{pub_date}</pubDate>\n"
            f"    <description>{esc(description)}</description>\n"
            "  </item>"
        )

    build_date = format_datetime(datetime.now(timezone.utc))
    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "<channel>\n"
        "  <title>RetroClips — New Films</title>\n"
        f"  <link>{SITE_URL}</link>\n"
        "  <description>New public-domain film clips added to RetroClips.</description>\n"
        "  <language>en-us</language>\n"
        f"  <lastBuildDate>{build_date}</lastBuildDate>\n"
        + "\n".join(items)
        + "\n</channel>\n</rss>\n"
    )
    RSS_XML.write_text(rss)


def main() -> None:
    data = json.loads(FILMS_JSON.read_text())
    version = asset_version()
    build_index(data, version)
    build_about(data, version)
    film_ids = build_film_pages(data, version)
    build_sitemap(film_ids)
    build_rss(data)
    print(f"Wrote {INDEX_HTML}, {ABOUT_HTML}, {len(film_ids)} film pages, {SITEMAP_XML}, {RSS_XML} (asset version {version})")


if __name__ == "__main__":
    main()
