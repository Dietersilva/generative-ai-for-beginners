#!/bin/bash
# Full backup: the offline app (both seasons), the online version's files and the tools.
set -e
cd "$(dirname "$0")/.."
B=backup/Grid-Replay-Backup; rm -rf backup; mkdir -p $B/online $B/tools
cp Grid-Replay-2025-2026.html "$B/OPEN ME - Grid-Replay-2025-2026.html"
cp -r pub/* $B/online/
cp tools/*.py tools/*.sh tools/quali_view.js $B/tools/ 2>/dev/null || true
cat > $B/README.txt <<'TXT'
GRID REPLAY 2025 + 2026 - full backup
=====================================

TO WATCH: double-click  "OPEN ME - Grid-Replay-2025-2026.html"
  Both seasons are built into that one file: every race, sprint and qualifying
  session with team radio and transcripts. Pick the year at the top left.
  Works offline in Chrome, Edge, Firefox or Safari. Allow a few seconds to load.

online/   The multi-file version, exactly as published on claude.ai (2026 at the top
          level, 2025 in online/2025/). Browsers block a page from reading its data
          files from disk, so to run it start a small web server in that folder:
              python3 -m http.server 8000
          then open http://localhost:8000 in your browser.
          online/**/data/*.txt are the race replays (base64 of the packed .bin files).

tools/    The Python scripts that download data from OpenF1 and build everything:
          build_race.py, build_quali.py, fill_holes.py, build_radio.py, transcribe.py,
          update_new.py, package.py, package2025.py, standalone.py, combine.py,
          miami_laps.py / build_miami.py (2025 Miami GP, see below).

DATA NOTES
- 2025 Miami GP: the official feed has no lap timing for laps 1-25. Those lap starts were
  reconstructed from GPS (each car crossing the timing line); checked against the laps
  that do have official timing, the median error is 0.05 s. Car positions are real GPS.
  The replay shows "LAP TIMING FROM GPS" while it applies.
- 2025 Azerbaijan qualifying is missing: OpenF1 has no lap data for it.
- 2026 Monaco and a few other stretches use estimated positions where GPS is missing;
  the replay shows "ESTIMATED POSITIONS" while it applies.
- Radio transcripts are made automatically by speech recognition and contain errors.

The code is also on GitHub: dietersilva/generative-ai-for-beginners,
branch claude/optimistic-dirac-orjjnb, folder f1-grid-replay/.

Data: OpenF1 (openf1.org), an unofficial community API. Timing data and team radio
belong to Formula 1. Private fan project for personal use - please don't publish it.
TXT
cd backup && zip -qr -9 Grid-Replay-2025-2026-backup.zip Grid-Replay-Backup && ls -la Grid-Replay-2025-2026-backup.zip && unzip -tq Grid-Replay-2025-2026-backup.zip
