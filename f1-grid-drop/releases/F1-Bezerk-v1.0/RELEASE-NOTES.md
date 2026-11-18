# F1 Bezerk v1.0

A frozen backup of F1 Bezerk exactly as it was on 18 November 2026, before the realism upgrade.

## What's in this folder

| File | What it is |
|---|---|
| `F1-Bezerk-v1.0.html` | The whole game in one file. Same as the live page, version 15. |
| `README.md` | Full feature guide: course, modes, cameras, betting, commentary, controls, tech. |
| `RELEASE-NOTES.md` | This file: version details, how to run it, and how to restore it. |
| `backups/f1-bezerk-2026-11-17-before-giant-views.html` | The older copy from before the performance work. |

## Version details

- **Version:** 1.0, matching live artifact version 15.
- **Live page:** https://claude.ai/artifact/T78SFRzPEEh7yYV2BaSAXJ (private to you unless you share it).
- **Source in git:** folder `f1-grid-drop/`, branch `claude/youthful-cerf-49o4ha`, commit `9c03bd7`.
- **SHA-256 of `F1-Bezerk-v1.0.html`:** `d9a8cff343282769bfaa4352c17b94f2030cfefe15a08a2a2d0a9aa20b45eeb3`. Use it to check the file hasn't changed.
- **Libraries**, loaded from jsDelivr with pinned versions:
  - three.js 0.160.0, with its Sky, bloom, output and shader-pass add-ons.
  - cannon-es 0.20.0.

## Features in v1.0

- **The race:** 22 cars of the 2026 grid with no engines, on a mountain course of about 0.91 km. Drop angles of 50°, 72° or 88°, with real-time physics.
- **Modes:**
  - Chaos, with 4 of 8 random obstacles.
  - Backwards.
  - Turbo.
  - Rain.
  - Showers (rain arrives halfway).
  - Moon gravity.
  - Giant car.
  - Dino Stampede.
  - SPEED from 1× to 4×, with a real-speed readout.
  - Day and night.
- **Monsters:**
  - T-rexes that eat cars.
  - A pterodactyl that snatches a car.
  - Roaming dinosaurs, giraffes and deer.
- **Watching:**
  - Six cameras: TV, side, chase, crow, drone and giant cockpit.
  - Zoom and full screen.
  - Driver-view window.
  - LIVE pop-ups for action off-screen.
  - Slow-motion replays and highlights.
- **Commentary:** two fictional hosts, Rex and Priya, with captions and voices, kept in step with the screen.
- **Betting:**
  - Shared betting from phones (open the link with `#bet` at the end), with live cheering emoji.
  - Pass-and-play betting on one screen.
  - Season points.
  - All-time records.
- **Celebrations:** winner's donuts, confetti and fireworks from the hillside sign.

## How to run it

- **Easiest:** open the live page link above.
- **From this download:** double-click `F1-Bezerk-v1.0.html` to open it in Chrome, Edge, Firefox or Safari.
  - It needs an internet connection the first time, to load three.js and cannon-es from jsDelivr.
  - The race, cameras, commentary, replays, season, records and pass-and-play betting all work.
  - Shared phone betting and cheering only work on the live claude.ai page, because they use the page's shared database and live room.

## How to restore it as the live page

Publishing this file to the same artifact link restores v1.0. The page also needs these settings, which are kept on the artifact itself, not in the file:

- **Capabilities:** `db`, `room`, `user`, `tts`.
- **Database rule:** `pool` can be read by viewers and written only by the owner or Editors (`{ path: "pool", read: "view", write: "admin" }`).

## Privacy and safety

- No analytics, no tracking and no personal data are collected.
- Saved in your browser only: day/night choice, betting players, season points, records and your nickname.
- In shared betting, the race screen accepts only the five cheer emoji, and shows names as plain text.

## Legal

A private, fan-made project, not affiliated with Formula 1. It uses real driver names and team colours for personal enjoyment. Sharing it publicly or selling it would need licences for those names, likenesses and trademarks.
