# F1 Bezerk v2.0

The realism upgrade of F1 Bezerk, as of 18 November 2026. v1.0 is locked separately in `releases/F1-Bezerk-v1.0/`.

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
- **SHA-256 of `index.html`:** `d03f5f4a090046cf7db364649a9c310a3e299af9fa2694d87f5cada96f600aed`
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

## How to run it

- **Easiest:** open the live page link above.
- **From this folder:** opening `index.html` straight from your computer may not load the textures, because browsers block pages opened from disk from loading other files. Use a small local web server instead, then open http://localhost:8000.
  - On a Mac or Linux, run this inside the folder: `python3 -m http.server`
  - On Windows, install Python first and run the same command.
- **Offline fallback:** opened straight from disk, or without the `assets/` folder, the game runs with the simpler v1.0-style scenery.
- **Shared features:** phone betting, cheering and the phone driver view only work on the live claude.ai page.

## How to restore it as a live page

Publish this `index.html` with the `assets/` files to an artifact. Give it the capabilities `db`, `room`, `user` (with the profile scope) and `tts`, and the database rule `{ path: "pool", read: "view", write: "admin" }`.

## Credits and licences

- Textures, the sky, the scanned plants and the rocks are from Poly Haven, released as CC0 (public domain).
- Everything else was written for this project.
- A private, fan-made project, not affiliated with Formula 1. Sharing it publicly or selling it would need licences for driver names, likenesses and trademarks.
