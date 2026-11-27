# F1 Bezerk v2.0

The realism upgrade of F1 Bezerk, as of 26 November 2026 (round 8). v1.0 is locked separately in `releases/F1-Bezerk-v1.0/`.

## What's in this folder

| File | What it is |
|---|---|
| `index.html` | The whole game (same as the live v2.0 page). |
| `assets/` | Textures, scanned plant image sheets and rock shapes from Poly Haven (CC0). They must stay next to `index.html`. |
| `README.md` | Every feature, round by round, plus the full v1.0 guide. |
| `RELEASE-NOTES.md` | This file. |
| `progress/` | The progress page with every round and its screenshots (open `progress/index.html`). |

## Version details

- **Live page:** https://claude.ai/artifact/51RaQNnxXYXN9voVZQa2Vx (private to you unless you share it).
- **Progress page:** https://claude.ai/artifact/NoagHvUYA67fxdHe5G9syZ
- **v1.0 live page (locked):** https://claude.ai/artifact/T78SFRzPEEh7yYV2BaSAXJ
- **Source in git:** `f1-grid-drop/v2/` on branch `claude/youthful-cerf-49o4ha`.
- **SHA-256 of `index.html`:** `969b43edd24a20bac7578aad34efac8b24f44dc1ad7a7ac9b1aa50fc3442b71e`
- **Libraries,** loaded from jsDelivr with pinned versions: three.js 0.160.0 (plus its add-ons) and cannon-es 0.20.0.

## What v2.0 adds over v1.0

- **Realism:**
  - Real photo-scanned grass, rock, snow and asphalt textures.
  - Car reflections from a real sky photo.
  - Smoother edges and soft contact shadows.
  - Sculpted cars with aerodynamic wing profiles.
  - Scanned trees, bushes, grass and rocks.
  - A rippled lake surface, soft clouds, sun glare and floating dust.
- **Night races:** floodlight pools and beams, real moving lights, rear lights with light trails, a moon and crowd camera flashes.
- **Creatures and venue:**
  - A smooth T-rex, raptors and long-necked dinosaurs.
  - Lattice light towers.
  - Grandstands with people, advertising boards and flags.
- **Controls:** a cleaner control bar, and a RACE SETUP menu with 🎲 RANDOMIZE and "Surprise me every race".
- **Phone driver view (📺):** friends watch the race live from inside their driver's cockpit.
- **Speed:** faster fast-forward (60 physics steps a second at 2× and above), plus a real-speed readout.
- **Championship:** a 5-race championship with F1 points and a champion's ceremony.
- **Lighter rendering:** about 3.6× fewer triangles per frame than round 5.
- **TV director and replays (round 7):** a 🎬 DIRECTOR camera that cuts like TV, replays that start before the moment and slow down at impact, and the same replays on phones.
- **Sound and liveries (round 7):** wind, crash, crowd and roar sounds made in the browser, plus team liveries and live gaps.
- **Fixes (round 8):** a car caught by a T-rex is held in its mouth, cameras can't sink under the track, and the phone betting slip no longer shows over the race on a local server.

## How to run it

- **Easiest:** open the live page link above.
- **From this folder:** opening `index.html` straight from your computer may not load the textures, because browsers block pages opened from disk from loading other files. Use a small local web server instead, then open http://localhost:8000.
  - On a Mac or Linux, run this inside the folder: `python3 -m http.server`
  - On Windows, install Python first and run the same command.
- **Garbled text:** if words show as `â€¦`, the local server isn't sending UTF-8. Python's plain `http.server` doesn't. Use a server that adds `charset=utf-8`, or the live page.
- **Offline fallback:** opened straight from disk, or without the `assets/` folder, the game runs with the simpler v1.0-style scenery.
- **Shared features:** phone betting, cheering and the phone driver view only work on the live claude.ai page.

## How to restore it as a live page

Publish this `index.html` with the `assets/` files to an artifact. Give it the capabilities `db`, `room`, `user` (with the profile scope) and `tts`, and the database rule `{ path: "pool", read: "view", write: "admin" }`.

## Credits and licences

- Textures, the sky, the scanned plants and the rocks are from Poly Haven, released as CC0 (public domain).
- Everything else was written for this project.
- A private, fan-made project, not affiliated with Formula 1. Sharing it publicly or selling it would need licences for driver names, likenesses and trademarks.
