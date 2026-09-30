# Episode Radar

A personal "season pass" for streaming services. It alerts you to **new series**,
**new seasons** and **new episodes** on the services you subscribe to. From any
alert you can **Track** the show or **Add to downloads**.

Static site: three files, no framework, no build step, no server, no accounts,
no API keys.

## What it does

| Tab | What you get |
| --- | --- |
| **Alerts** | Series and season premieres on your selected services, from 7 days back to 21 days ahead (you can change both), plus new episodes of every show you track, on any service. Each alert has Track, Add to downloads, Open (service) and Dismiss. |
| **Tracking** | Search any show (for example *The Pitt*, which streams on HBO Max), see its latest and next episode, and export upcoming episodes to your calendar as an `.ics` file with a 9 AM reminder. |
| **Downloads** | A checklist of episodes or seasons to download **in the service's own app**. Episode Radar never downloads, records or decrypts video. |
| **Settings** | Services, alert window, browser notifications, backup/restore, erase. |

## How it gets data

The browser calls the public [TVmaze API](https://www.tvmaze.com/api) directly:

- `GET /schedule/web?date=YYYY-MM-DD` for each day in the alert window. Episode 1
  of a season is a premiere. Season 1 means a new series.
- `GET /shows/:id?embed=episodes` for each tracked show.
- `GET /search/shows?q=` for search.

Requests are spaced 550 ms apart to stay under TVmaze's rate limit (about 20
requests per 10 seconds), and results are cached in the browser for 6 hours.
The first check takes about 20 seconds.

TVmaze data is licensed CC BY-SA 4.0, and the footer credits TVmaze as that
license requires.

### Known limits

- **Where a show is made, not everywhere it streams.** TVmaze lists a show's
  home channel. A show licensed to Hulu from another network (for example
  next-day FX or ABC episodes) isn't flagged as a Hulu premiere. Track it
  directly and you'll still get its episode alerts.
- **Alerts appear while the page is open.** There is no server, so nothing runs
  when the page is closed. To get reminders on your phone anyway, use
  **Add upcoming to calendar**, and re-export after you track new shows.
- **Your lists are stored per browser.** Use **Save backup** / **Restore backup**
  to move them to another device.

## Run it

It has to be served over **https** or **localhost**. Browser notifications and
some storage features don't work from a `file://` page.

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

`vercel.json` sets the security headers.

## Security and privacy

- A strict Content-Security-Policy, set both in `vercel.json` and as a `<meta>`
  tag. It allows only this site's own script and styles, TVmaze API calls and
  TVmaze poster images. There are no inline scripts, third-party scripts,
  analytics or fonts.
- No `innerHTML`. API text is always rendered as text, and TVmaze's HTML
  summaries are reduced to plain text through an inert `DOMParser` document.
- Links must be `https:` and open with `noopener noreferrer`. Images must come
  from `static.tvmaze.com`.
- Stored data and restored backups are validated field by field before use.
- There are no passwords, cookies or accounts. Nothing is sent anywhere except
  the TVmaze requests above, and those carry no referrer.

## Search engines

The page is set to **noindex** (a `<meta name="robots">` tag, an
`X-Robots-Tag` header and `robots.txt`). It's a personal tool, and the only
data that matters lives in your own browser. To make it a public, indexable
page instead:

1. Change the robots meta tag to `index, follow`.
2. Remove the `X-Robots-Tag` header from `vercel.json`.
3. Delete `robots.txt`, or replace it with one that allows crawling and points
   to a sitemap.
