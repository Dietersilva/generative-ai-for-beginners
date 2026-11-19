#!/bin/bash
# Offline Classic files for one season: offline_classic/Pit_Wall_Redux_Classic-YYYY.zip (+ refreshed HTML), then a disk test.
set -e; cd "$(dirname "$0")/.."; Y=$1
python3 tools/make_classic_site.py pub/index.html classic >/dev/null
python3 tools/launcher.py classic/index.html offline_classic/Pit_Wall_Redux_Classic.html >/dev/null
rm -f offline_classic/files/grid-replay-$Y*.js
SPLIT_MB=32 SPLIT_JS=1 python3 tools/standalone.py classic/index.html classic/$Y/index.json offline_classic/files/grid-replay-$Y.js $Y/ >/dev/null
rm -f offline_classic/Pit_Wall_Redux_Classic-$Y*.zip
(cd offline_classic/files && zip -q -9 -X ../Pit_Wall_Redux_Classic-$Y.zip grid-replay-$Y-*.js)
U=$PWD/userdir_c; mkdir -p $U; cp offline_classic/files/grid-replay-$Y-*.js $U/
python3 tools/make_classic_site.py pt_hook.html classic classic/_hook.html >/dev/null; python3 tools/launcher.py classic/_hook.html $U/Pit_Wall_Redux_Classic.html >/dev/null; rm classic/_hook.html
URL=file://$U/Pit_Wall_Redux_Classic.html YEAR=$Y timeout 1500 node tools/testyear.js 2>&1 | grep -o "^20..: loaded [0-9/]*"
ls -la offline_classic/Pit_Wall_Redux_Classic-$Y.zip offline_classic/Pit_Wall_Redux_Classic.html | awk '{printf "%.1f MB %s\n", $5/1e6, $9}'
