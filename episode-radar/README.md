# Episode Radar

**One streaming plan for the whole household.** Episode Radar looks at the
shows everyone follows, your teams' games, and the streaming you already get
through memberships, phone plans, cards or a TV antenna. It then tells you what
to keep, pause or add over the next 90 days, and flags services you may be
paying for twice.

It installs to a phone's home screen and works offline. It never asks for
streaming passwords or bank logins.

## What makes it different

Other apps each cover one piece: episode trackers, cancel-and-resubscribe
planners, sports cost calculators, credit-card perk trackers. Episode Radar
combines them into one household plan:

- **Household:** each show and team belongs to one or more people, and the
  plan shows who needs each service.
- **Streaming you already get:** Walmart+, Instacart+, Amazon Prime, T-Mobile,
  Verizon perks, Spotify Student, Chase Sapphire Reserve, the Amex Platinum
  credit, a TV antenna or a live TV package all count as covered.
- **Sports:** every game is matched to its US channel and then to the cheapest
  way you can watch it, including the plan tier that game needs (for example,
  HBO Max Basic with Ads has no live sports).
- **Paying twice:** if you pay for Netflix and T-Mobile already includes it,
  the plan says so.
- **Privacy:** no accounts, passwords or bank links. Data stays on the device.

## Tabs

| Tab | What you get |
| --- | --- |
| **Setup** (first run) | Four steps: household and services with prices, streaming you already get, shows and teams to follow, notifications and install. |
| **Alerts** | Game days (the next 3 days) with how to watch; new series and seasons on your services; new episodes of followed shows. |
| **Plan** | Three rolling 30-day periods (matching how streaming bills): Subscribe, Keep, Pause (with a rejoin date), Paying twice, Already covered, and games that need cable or a league package. Totals include the Amex credit. |
| **Shows** | Follow shows, choose who they're for, see latest and next episodes. |
| **Sports** | Follow teams, see upcoming games with channels and how you can watch each one. |
| **Downloads** | A checklist for downloading in each service's own app. Episode Radar never downloads, records or decrypts video. |
| **Settings** | Household, services and prices, perks (each with a source link), alert window, notifications, install, backup and restore. |

**Add to calendar** exports episodes (all-day, 9 AM reminder), games (timed,
30-minute reminder) and "Resubscribe to …" reminders 3 days before a paused
service is needed again.

## Data sources

| Data | Source | Cost | Where it's called |
| --- | --- | --- | --- |
| TV schedules and episodes | [TVmaze API](https://www.tvmaze.com/api), CC BY-SA 4.0 | Free | From the browser |
| Teams, games, US TV channels | [TheSportsDB](https://www.thesportsdb.com/) v1 API | $9 a month (premium key) | From `api/sports.js` on the server, so the key stays secret |
| Perks and which service carries which channel | `data.js`, checked by hand with a source link for each fact | Your time | Bundled with the app |

TheSportsDB's terms allow paid subscribers to build apps and require crediting
it as the source; the footer does. Its TV listings are community-maintained, so
a channel can be missing or late.

**`data.js` must be reviewed monthly.** Perks change often. While this was
being built, DoorDash's free HBO Max perk ended and Amex stopped counting
bundled Peacock plans. Update the facts, their `source` links and `checked`
date together.

## Set up sports (one time)

1. Subscribe to TheSportsDB's premium API ($9 a month) through their Patreon
   and copy your API key.
2. In Vercel, open the project → **Settings → Environment Variables** and add
   `THESPORTSDB_KEY` with your key, for Production (and Preview if you want).
   Never put the key in the code, in chat or in a commit.
3. Redeploy. The Sports tab then finds teams and games.
4. Recommended: in Vercel **Firewall**, add a rate-limit rule for
   `/api/sports` (for example, 60 requests a minute per IP). The function also
   has a per-instance limit, but that doesn't hold across instances.

Without the key the rest of the app works normally, and the Sports tab
explains that sports is not switched on.

## Run it

**Locally, with sports:**

```
cd episode-radar
THESPORTSDB_KEY=yourkey node dev-server.js
# open http://localhost:8080
```

`dev-server.js` serves the app and `/api/sports` with the same security
headers as production, and only listens on your own computer. Without a key it
still runs; sports shows as not set up.

**On Vercel** (same setup as `thesecondhalfguide`):

- **Root Directory:** `episode-radar`
- **Framework Preset:** Other
- **Build Command:** *(none)*
- **Output Directory:** *(none; serves the root)*

Vercel runs `api/sports.js` as a serverless function automatically.
`vercel.json` sets the security headers, and `.vercelignore` keeps
`dev-server.js` out of the deploy.

### Shipping an update

The service worker is network-first, so people get new code the next time they
open the app online. When you add or rename app files, update the list in
`sw.js` and bump its `VERSION`.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | Page structure and the setup screens |
| `styles.css` | Design tokens (light and dark), layout, phone tab bar |
| `data.js` | Services, sports channel rules and perks, each with sources |
| `app.js` | App logic: alerts, household plan, coverage, calendar, setup |
| `api/sports.js` | Server function that proxies TheSportsDB with the secret key |
| `sw.js` | Service worker: offline app files and notifications on phones |
| `manifest.webmanifest`, `icons/` | Makes the app installable |
| `dev-server.js` | Local preview server (not deployed) |
| `vercel.json`, `.vercelignore` | Security headers, caching, deploy exclusions |

## Security and privacy

- **Strict Content-Security-Policy** (in `vercel.json` and a `<meta>` tag):
  only this site's own scripts and styles, TVmaze and this site's API for data,
  TVmaze and TheSportsDB for images. No inline or third-party scripts, no
  analytics, no web fonts.
- **No `innerHTML`.** All outside text is rendered as text. TVmaze's HTML
  summaries are reduced to plain text through an inert `DOMParser` document.
- **Links must be `https:`.** Images must come from the TVmaze or TheSportsDB
  image hosts.
- **`api/sports.js`** accepts only two fixed lookups. It validates every input
  (team names up to 40 letters, numeric IDs only), never takes a URL from the
  caller, returns only known fields, times out after 8 seconds, hides upstream
  errors, and keeps the key in an environment variable. Successful answers are
  cached at Vercel's edge, so one lookup serves everyone.
- **The service worker** caches only the app's own files. It never touches
  TVmaze, other hosts or `/api/`.
- **Local data is validated field by field**, including restored backups.
  Household names stay on the device.
- **No passwords, cookies, accounts or bank links.**

## Known limits

- **Checks happen while the app is open.** Server-side push alerts come with
  accounts in Phase 2. Until then, the calendar export covers reminders when
  the app is closed.
- **iPhone and iPad** allow notifications only after Add to Home Screen.
- **TV shows are matched by the channel they're made for** (TVmaze), not every
  service that licenses them.
- **Sports listings are US channels only.** Local blackouts, regional sports
  networks and league packages (NFL Sunday Ticket, NBA League Pass, MLB.tv)
  show up as "check how to watch".
- **The plan counts only what the household follows.** Movies and unfollowed
  shows aren't considered.

## Search engines

The app is set to **noindex** (robots meta tag, `X-Robots-Tag` header,
`robots.txt`), because it's a personal tool. For a public marketing page,
build a separate landing page rather than indexing the app.
