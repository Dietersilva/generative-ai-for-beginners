#!/bin/bash
# Full backup: the offline app, the online version's files, the tools, and the raw data.
set -e
cd "$(dirname "$0")/.."
B=backup/Grid-Replay-2026; rm -rf backup; mkdir -p $B/online $B/tools $B/raw
cp Grid-Replay-2026-Season.html "$B/OPEN ME - Grid-Replay-2026-Season.html"
cp -r pub/* $B/online/
cp tools/*.py tools/*.sh tools/quali_view.js $B/tools/ 2>/dev/null || true
mkdir -p $B/raw/races $B/raw/sprints $B/raw/qualifying
cp out/data/*.bin $B/raw/races/; cp out/radio/*.bin $B/raw/races/ 2>/dev/null || true
cp out_sprint/data/*.bin $B/raw/sprints/; cp out_sprint/radio/*.bin $B/raw/sprints/ 2>/dev/null || true
cp out_quali/*.json $B/raw/qualifying/
rm -f $B/raw/races/*.orig
cat > $B/README.txt <<'TXT'
GRID REPLAY 2026 - full backup
==============================

TO WATCH: double-click  "OPEN ME - Grid-Replay-2026-Season.html"
  Everything is built into that one file (all races, sprints, qualifying, team radio
  and transcripts). Works offline in Chrome, Edge, Firefox or Safari. Allow a few
  seconds to load.

online/   The multi-file version (as published on claude.ai). It cannot be opened by
          double-clicking index.html - browsers block a page from reading its data
          files from disk. To run it, start a small web server in that folder:
              python3 -m http.server 8000
          then open http://localhost:8000 in your browser.

tools/    The Python scripts that download data from OpenF1 and build everything.
          See tools/build_race.py, build_quali.py, fill_holes.py, build_radio.py,
          transcribe.py, update_new.py, package.py and standalone.py.

raw/      The packed data as built (race replays, radio packs, qualifying laps).

The code is also on GitHub: dietersilva/generative-ai-for-beginners,
branch claude/optimistic-dirac-orjjnb, folder f1-grid-replay/.

Data: OpenF1 (openf1.org), an unofficial community API. Timing data and team radio
belong to Formula 1. Private fan project for personal use - please don't publish it.
Radio transcripts are made automatically by speech recognition and contain errors.
TXT
cd backup && zip -qr -9 Grid-Replay-2026-backup.zip Grid-Replay-2026 && ls -la Grid-Replay-2026-backup.zip
