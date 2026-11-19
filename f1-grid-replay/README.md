# Pit Wall Redux (formerly Grid Replay)

A private, fan-made replay of the 2026 season: every Grand Prix and sprint as an animated
running order (linear view) or track map, plus qualifying fastest laps as ghost cars.
Data comes from [OpenF1](https://openf1.org), an unofficial community API. This folder holds
only the code; the race data, team radio and the published page are not stored in git.

## Files

| File | What it does |
| --- | --- |
| `page.html` | The replay page (published as a claude.ai artifact) |
| `tools/build_race.py` | Downloads one race or sprint and packs car positions, timing, tyres, pits and race control |
| `tools/fill_holes.py` | Fills gaps in car-position data from lap and sector times (labelled "estimated" on the page) |
| `tools/stewards.py` | Turns race-control messages into investigation / penalty / track-limits events |
| `tools/build_radio.py` | Downloads and packs team radio clips |
| `tools/build_quali.py` | Fastest lap of every driver in a qualifying session, with tyre compound |
| `tools/transcribe.py` | Auto-transcribes team radio with Whisper (`pip install faster-whisper`; needs Hugging Face access for the model) |
| `tools/package.py` | Assembles the publishable folder and season standings |
| `tools/update_new.py` | Finds finished sessions missing from the published index and builds them |
| `tools/standalone.py` | Builds the single-file offline version |

## Adding newly finished sessions

Needs network access to `api.openf1.org` and `livetiming.formula1.com`, plus `ffmpeg`.

```bash
python3 -I f1-grid-replay/tools/update_new.py index.json work
```

`index.json` is the published artifact's current index. The script prints the files to
publish from `work/publish/`; publish them (plus `page.html` as the page) to the same artifact.
