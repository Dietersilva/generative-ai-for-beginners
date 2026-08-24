# thesecondhalfguide.com

Static site. No framework, no build step, no server-side code — Vercel serves
these files directly.

## Vercel project settings

- **Root Directory:** `thesecondhalfguide`
- **Framework Preset:** Other
- **Build Command:** *(none)*
- **Output Directory:** *(none — serve the root)*

`vercel.json` sets `cleanUrls` (so `/about` serves `about.html`) and the
security headers, including a strict Content-Security-Policy.

## Regenerating

Page content is generated from the builders in `_src/`, which is excluded from
the deploy via `.vercelignore`.

```
cd _src
python3 build_pages.py <about-url> <contact-url> <privacy-url>   # policy pages
python3 build_articles.py <same three urls>                      # articles
python3 build_site.py                                            # assemble ../
```

`build_site.py` inlines nothing: it writes the shared `styles.css`, decodes the
fonts to `fonts/*.woff2`, rewrites cross-links to root-relative paths, and
regenerates `sitemap.xml`, `robots.txt` and `vercel.json`.

## When AdSense is added

`script-src` in the CSP is currently a single hash covering the one inline
script (the topic form's mailto builder). Adding AdSense means widening
`script-src`, `frame-src` and `img-src` for Google's domains — do that
deliberately in `build_site.py`, not by removing the policy.
