# Episode Radar

A standalone, installable web app for streaming households. It alerts you to
**new series**, **new seasons** and **new episodes** on the services you pay
for, and shows **which services you can pause** to save money.

Static site: no framework, no build step, no server, no accounts, no API keys.
It installs to a phone's home screen and works offline.

## What it does

| Tab | What you get |
| --- | --- |
| **Setup** (first run) | Three steps: pick your services and what they cost, pick shows to follow, then turn on notifications and install. Takes about a minute. |
| **Alerts** | Series and season premieres on your services, from 7 days back to 21 days ahead (both adjustable), plus new episodes of every show you follow, on any service. Each alert has Follow, Add to downloads, Open (service) and Dismiss. |
| **My shows** | Search any show, see its latest and next episode, and export upcoming episodes to your calendar (`.ics`) with a 9 AM reminder. |
| **Downloads** | A checklist of episodes or seasons to download **in the service's own app**. Episode Radar never downloads, records or decrypts video. |
| **Savings** | For each service: **Keep** while a show you follow is airing (an episode in the last 14 days or the next 30), or **Pause** and rejoin 3 days before the next show returns, with the money saved. The calendar export includes those resubscribe reminders. |
| **Settings** | Services and prices, alert window, notifications, install, backup/restore, run setup again, erase. |

## How it gets data

The browser calls the public [TVmaze API](https://www.tvmaze.com/api) directly:

- `GET /schedule/web?date=YYYY-MM-DD` for each day in the alert window. Episode 1
  of a season is a premiere. Season 1 means a new series.
- `GET /shows/:id?embed=episodes` for each followed show.
- `GET /search/shows?q=` for search.

Requests are spaced 550 ms apart to stay under TVmaze's rate limit (about 20
requests per 10 seconds). Results are cached on the device for 6 hours. The
first check takes about 20 seconds.

TVmaze data is licensed CC BY-SA 4.0, and the footer credits TVmaze as that
license requires.

### Known limits

- **Where a show is made, not everywhere it streams.** TVmaze lists a show's
  home channel. A show licensed to Hulu from another network isn't flagged as
  a Hulu premiere. Follow it directly and you'll still get its episode alerts.
- **Checks happen while the app is open.** There is no server yet (that's
  Phase 2), so notifications fire when the app checks: on open, when it comes
  back to the foreground, and every 6 hours while it stays open. For reminders
  at any time, use **Add to calendar**.
- **iPhone and iPad** only allow notifications after the app is added to the
  Home Screen (Share → Add to Home Screen). The setup screen explains this.
- **Savings advice counts only shows you follow.** Movies, sports and shows you
  don't follow are not considered.
- **Your data is stored per device.** Use **Save backup** / **Restore backup**
  to move it to another device.

## Run it

It must be served over **https** or **localhost**. Installing, offline mode and
notifications don't work from a `file://` page.

**Locally:**

```
cd episode-radar
python3 -m http.server 8080
# open http://localhost:8080
```

**On Vercel** (same setup as `thesecondhalfguide`):

- **Root Directory:** `episode-radar`
- **Framework Preset:** Other
- **Build Command:** *(none)*
- **Output Directory:** *(none; serves the root)*

`vercel.json` sets the security headers and caching.

### Shipping an update

The service worker uses a network-first strategy, so people get new code the
next time they open the app while online. When you change the list of app
files in `sw.js`, bump `VERSION` in `sw.js` so old offline caches are cleared.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | Page structure and the setup screens |
| `styles.css` | Design tokens (light and dark), layout, phone tab bar |
| `app.js` | All app logic: data, alerts, planner, calendar export, setup |
| `sw.js` | Service worker: offline app files and notifications on phones |
| `manifest.webmanifest`, `icons/` | Makes the app installable |
| `vercel.json` | Security headers, caching |

## Security and privacy

- A strict Content-Security-Policy, set both in `vercel.json` and as a `<meta>`
  tag. It allows only this site's own script, styles, manifest and service
  worker, TVmaze API calls and TVmaze poster images. There are no inline
  scripts, third-party scripts, analytics or web fonts.
- No `innerHTML`. API text is always rendered as text. TVmaze's HTML summaries
  are reduced to plain text through an inert `DOMParser` document, with script
  and style contents removed.
- Links must be `https:` and open with `noopener noreferrer`. Images must come
  from `static.tvmaze.com`.
- The service worker only handles this site's own files. It never caches or
  touches requests to TVmaze or any other host.
- Stored data and restored backups are validated field by field. Prices are
  whole cents between 0 and $1,000.
- There are no passwords, cookies or accounts. Nothing is sent anywhere except
  the TVmaze requests above, and those carry no referrer.

## Search engines

The page is set to **noindex** (a `<meta name="robots">` tag, an
`X-Robots-Tag` header and `robots.txt`). It's a personal tool, and all the data
that matters lives on the user's device. To make it a public, indexable page
instead:

1. Change the robots meta tag to `index, follow`.
2. Remove the `X-Robots-Tag` header from `vercel.json`.
3. Delete `robots.txt`, or replace it with one that allows crawling and points
   to a sitemap.

## Roadmap

See the v2 plan: Phase 2 adds accounts, sync, server-side alerts (push even
when the app is closed) and a live calendar feed. It needs a database and
sign-in provider, which are decisions for the owner.
