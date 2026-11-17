#!/bin/bash
# Backup in parts small enough to download (each under ~80 MB). Unzip all parts into one folder.
set -e
cd "$(dirname "$0")/.."
B=backup/Grid-Replay-Backup; rm -rf $B backup/parts; mkdir -p $B/online $B/tools $B/commentary-scripts backup/parts
cp -r pub/* $B/online/
for y in 2025 2024 2023; do mkdir -p $B/online/$y/comm && cp comm/$y/*.mp3 comm/${y}q/*.mp3 $B/online/$y/comm/; done
for y in 2026 2025 2024 2023; do mkdir -p $B/commentary-scripts/$y $B/commentary-scripts/$y-qualifying && cp comm/$y/*.json $B/commentary-scripts/$y/ && cp comm/${y}q/*.json $B/commentary-scripts/$y-qualifying/; done
cp PROJECT-GUIDE.md $B/
cp tools/*.py tools/*.sh tools/*.js $B/tools/ 2>/dev/null || true
cat > $B/README.txt <<'TXT'
GRID REPLAY - full backup (2023, 2024, 2025, 2026)
==================================================

TO WATCH OFFLINE: use the separate download set - Grid-Replay.html plus Grid-Replay-2023..2026.zip.
  Put them in one folder, unzip the zips there, double-click Grid-Replay.html.

THIS BACKUP (unzip all 5 parts into the same folder to rebuild it):
online/   The multi-file version, exactly as published on claude.ai (2026 at the top level, past
          seasons in online/2025/, online/2024/, online/2023/). Browsers block a page from reading
          data files from disk, so run a small web server in that folder:
              python3 -m http.server 8000
          then open http://localhost:8000 in your browser.
          data/*.mp3 = race replays (gzip packs served under an audio extension because the host
          only serves media types - not audio). radio/*.mp3 = team radio packs.
          comm/*.mp3 = commentary packs (natural voices) for races and qualifying. For 2023-2025 these
          are included here but not listed in online/<year>/index.json (no room online).
commentary-scripts/  The commentary text for every race and qualifying session (JSON).
PROJECT-GUIDE.md     Everything about the project in one document.
tools/    The scripts that download data from OpenF1 and build everything (build_race.py,
          update_new.py, build_radio.py, transcribe.py, build_comm.py, commscript_all.js,
          standalone.py, launcher.py, ...).

DATA NOTES
- 2025 Miami GP: lap timing for laps 1-25 reconstructed from GPS (median error 0.05 s).
- 2025 Azerbaijan qualifying missing (no data in OpenF1).
- 2023: points recomputed from positions for Saudi Arabia and the United States (OpenF1 values
  were wrong); final standings match the official table.
- Short stretches of estimated positions are labelled ESTIMATED POSITIONS in the replay.
- Team radio is stored at 24 kbps mono; transcripts are automatic and contain errors.
- Commentary voices: Piper (rhasspy/piper-voices) en_GB northern_english_male (trained on CC BY-SA
  4.0 data) and en_GB alba (CC BY 4.0 data). Commentary is generated from the timing data.

Code: GitHub dietersilva/generative-ai-for-beginners, branch claude/optimistic-dirac-orjjnb,
folder f1-grid-replay/. Data: OpenF1 (openf1.org), unofficial. Timing data and team radio belong
to Formula 1. Private fan project for personal use - please don't publish it.
TXT
cd $B
zip -qr -9 ../parts/Grid-Replay-backup-1-tools-scripts-readme.zip README.txt PROJECT-GUIDE.md tools commentary-scripts
zip -qr -9 ../parts/Grid-Replay-backup-2-online-2026.zip online/index.html online/index.json online/season.json online/data online/radio online/quali online/comm
zip -qr -9 ../parts/Grid-Replay-backup-3-online-2025.zip online/2025
zip -qr -9 ../parts/Grid-Replay-backup-4-online-2024.zip online/2024
zip -qr -9 ../parts/Grid-Replay-backup-5-online-2023.zip online/2023
cd ../parts && for f in *.zip; do unzip -tq "$f" >/dev/null && echo "ok $f"; done && ls -la
