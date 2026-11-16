#!/bin/bash
# Render every commentary script in comm/<year>/*.json to comm/<year>/<sk>.mp3 with Piper (skips ones already done).
cd "$(dirname "$0")/.."
for f in comm/*/*.json; do o="${f%.json}.mp3"; [ -s "$o" ] && [ "$o" -nt "$f" ] && continue; python3 tools/build_comm.py "$f" "$o" 16k || echo "FAILED $f"; done
echo RENDER DONE
