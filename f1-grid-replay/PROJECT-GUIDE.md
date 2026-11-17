# Grid Replay — Project Guide

A private, fan-made Formula 1 race replay inspired by the "linear" running-order videos of the
F1Visualized YouTube channel: pick a race and watch the field as an animated running order (leader on
the right, cars trailing by their gap) or on the track map, with team colours, names, tyres, pit stops,
penalties, crashes, team radio with transcripts, analysis charts and a two-voice spoken commentary.

Status as of 17 November 2026. Personal, non-commercial use only — see "Licences and data" below.

---

## 1. Where everything is

| What | Where |
| --- | --- |
| Online version (private to you) | https://claude.ai/artifact/HpzTQcSf2n3zTQeMKndKRV (version 31) |
| Source code | GitHub `dietersilva/generative-ai-for-beginners`, branch `claude/optimistic-dirac-orjjnb`, folder `f1-grid-replay/` |
| Offline version | `Grid-Replay.html` + `Grid-Replay-2023/2024/2025/2026.zip` (unzip into one folder, double-click the HTML) |
| Backup | `Grid-Replay-backup-1..5` (online files + tools), plus the extra parts listed in section 12 |

## 2. What's in it

| Season | Races | Sprints | Qualifying | Team radio clips | Commentary voice |
| --- | --- | --- | --- | --- | --- |
| 2026 | 20 (+3 to come) | 6 | 26 + 3 previews | 446 | Natural (Piper), online and offline |
| 2025 | 24 | 6 | 29 | 737 | Natural offline; device voice online |
| 2024 | 24 | 6 | 30 | 1,792 | Natural offline; device voice online |
| 2023 | 22 | 6 | 28 (incl. sprint shootouts) | 1,778 | Natural offline; device voice online |

Commentary: 10,572 race lines (9.4 hours, 114 races and sprints) plus 912 qualifying lines (1.3 hours, 116 sessions).

2022 is not possible: OpenF1 starts in 2023, and F1's own live-timing archive now requires a login
(it answers 401 Unauthorized). An "estimated" 2022 from lap times only (Jolpica/Ergast) was offered and
put on hold.

## 3. Features of the page

- **Views:** Linear (running order by gap, leader on the right), Track, Follow and Chase cameras;
  zoom levels; collapsible timing tower; click a car for its driver panel (docked right).
- **Race events:** safety car / VSC / red flag bands, crashes and stopped cars (detected from GPS),
  contact, retirements, pit lane with BOX marker, tyre compound and age, steward chips (investigation,
  penalty, served, track limits), overtakes (must hold 10 s), battles (within 1.0 s for 3+ laps),
  fastest laps.
- **CRASH CAM** (on by default): slow-motion pop-up when a car crashes or stops; incident recreation.
- **Team radio:** plays as it happens, on-air box in the bottom strip, auto-transcripts in the log.
- **Commentary:** COMMENTARY button. Two-person booth (British lead + Scottish analyst). Pre-race
  build-up, lights out, lap-1 report, overtakes with memory, battles with gap trends, pit stops with
  tyres / stop times / undercut verdicts, safety cars, crashes, penalties, rain, 10-lap gap updates,
  team-radio lead-ins, quiet-spell stats and the odd dry joke, finish, podium, biggest mover and the
  championship picture. Faster playback speaks only the bigger moments; big moments cut in.
- **Analysis panel:** Head to head, Incidents, Positions, Lap times, Battles, Weather, Season (bar race).
- **Qualifying:** every driver's fastest lap as ghost cars, live gap to pole, Q1/Q2/Q3 order, tyres.
  Qualifying commentary (about 8 lines per session, timed to the ghost lap): intro, tyres, Q1/Q2
  knockouts, sector leaders, pole call with lap time and margin, front row and teammate/spread notes.
  Previews describe last year's laps. 116 sessions, 912 lines, every pole call checked against the data.
- **Weather overlay:** air/track temperature, wind, rain effect.
- **Video export:** REC button (WebM/MP4 via the browser; commentary audio is not captured).
- **Seasons:** year picker (2026, 2025, 2024, 2023); links like `#2025-round-12`, `#2024-s-<session>`.

## 4. How it is built (architecture)

**Data source:** OpenF1 API (`api.openf1.org/v1`): sessions, meetings, drivers, laps, location (GPS,
~3.7 Hz), position, intervals, stints, pit, race_control, session_result, weather, team_radio.
Team-radio audio files come from `livetiming.formula1.com` (public URLs listed by OpenF1).

**Race pack** (`data/<session_key>`): gzip of `u32 header_len | JSON header | int16 delta positions`.
Positions are resampled to a 0.5 s grid per driver, delta-encoded (shape drivers × samples × 2; cumulative
sum to decode). Location units are 10 per metre; y is flipped for drawing. The header holds drivers,
results, laps, positions, gaps/intervals, stints, pits (pit `date` = pit-lane exit time), race control,
stewards events, weather rows, estimated stretches (`est`) and notes.
Published online as `.mp3` *named* files (the host only serves media types; they are gzip, not audio).

**Radio pack** (`radio/<sk>.mp3`): `u32 header_len | JSON [{t,num,off,len,text}] | concatenated MP3 clips`.
Past seasons and 2026 re-encoded to 24 kbps mono (originals kept separately, see section 12).

**Commentary pack** (`comm/<sk>.mp3`): same layout, entries `{t,pri,who,e,text,radio?,off,len}`;
`who` L = lead, A = analyst; `e` energy 0–2; `pri` 1–3 controls what is spoken at higher speeds.

**Commentary pipeline:** the page itself writes the script (`buildCommScript` in page.html, seeded so it
is repeatable) → `tools/commscript_all.js` runs the page headless (Playwright) to dump each race's script →
`tools/build_comm.py` renders it with Piper and packs it. Without a pack the page reads the same script
with the device's speech voices.

**Offline versions:**
- *Split* (current): `Grid-Replay.html` (`tools/launcher.py`) loads `grid-replay-YYYY.js`
  (`SPLIT_JS=1 COMM_DIR=comm/YYYY tools/standalone.py ...`) from the same folder when a year is picked.
  Browsers allow script files from disk, so this works without a web server.
- *Single file* per season (`tools/standalone.py`) and combined (`tools/combine.py`) also exist.

## 5. Data notes (what is estimated or corrected)

- **2025 Miami GP:** OpenF1 has no lap records for laps 1–25. Lap starts were rebuilt from each car's
  GPS crossing of the timing line (median error 0.05 s against laps with official timing); lap 1 starts
  at lights out (20:03:42.6 UTC, from the GPS). Car positions are real GPS. Label: LAP TIMING FROM GPS.
  Stints were rebuilt from the pit records (OpenF1's stints were ~4 laps off).
- **2025 Azerbaijan qualifying:** missing (no lap data in OpenF1).
- **2023 points:** OpenF1's points were wrong for Saudi Arabia (Verstappen 2nd shown as 0) and the
  United States (everyone but the winner 0). Recomputed from positions with 2023 rules incl. the
  fastest-lap point (`tools/fix_points.py`). Final 2023 standings match the official table
  (VER 575, PER 285, HAM 234, ALO 206, LEC 206, NOR 205, SAI 200, RUS 175, PIA 97, STR 74).
- **Final standings checked:** 2025 NOR 423 / VER 421 / PIA 410; 2024 VER 437 / NOR 374 / LEC 356.
- **Estimated positions** (labelled ESTIMATED POSITIONS) fill GPS gaps from lap and sector times:
  2026 Monaco (data stops after ~7 min) and short stretches elsewhere; 2023 São Paulo ~13 min around
  the lap-1 red flag; 2023 Australia/Belgium and 2024 Belgium/Singapore/Abu Dhabi under 30 s.
- **Early-2024 radio** file names use UTC instead of local time; the packer picks whichever matches.
- **Transcripts** are automatic (Whisper small.en) and contain errors.

## 6. Commentary voices

Piper (open-source TTS, rhasspy/piper-voices on Hugging Face), version piper-tts 1.8.0:
- Lead: `en_GB-northern_english_male-medium` (trained on OpenSLR 83 data, CC BY-SA 4.0).
- Analyst: `en_GB-alba-medium` (trained on Edinburgh DataShare data, CC BY 4.0).
Rendered at 16 kbps MP3, 22.05 kHz mono. Only "Piastri" and "Bortoleto" are respelled for TTS.
The lines are original; no real commentator's voice or catchphrases are imitated.

## 7. Size budget (online)

The artifact allows 256 MB per version. Current total ≈ 239 MB (2026 data + radio + commentary,
2023–2025 data + radio). That is why race data is binary, radio is 24 kbps, and past-season commentary
audio is offline only. The three remaining 2026 races add ~6 MB plus ~2 MB of commentary. A 2027
season would need room to be made (e.g. moving a past season to a second artifact).

## 8. Scheduled tasks (automatic updates)

| Task | When (UTC) | What |
| --- | --- | --- |
| Grid Replay: add Las Vegas GP | 22 Nov 2026 14:00 | Builds new sessions with update_new.py, publishes |
| Grid Replay: add Qatar GP | 30 Nov 2026 02:00 | same |
| Grid Replay: add Abu Dhabi GP | 6 Dec 2026 23:00 | same (retries up to 3× every 6 h) |
| Grid Replay: voice the last 2026 races | 8 Dec 2026 15:00 | Natural voices for those races, new 2026 zip + backup part 2 sent to you |

New 2026 races use the device voice until the 8 December job voices them.

## 9. Rebuilding or updating (commands)

Requirements: Python 3, numpy, ffmpeg, Node + Playwright (Chromium), `pip install piper-tts faster-whisper`.
Network: `api.openf1.org`, `livetiming.formula1.com`, and Hugging Face for the Whisper model and Piper voices
(`huggingface.co`, `cdn-lfs.huggingface.co`, `cdn-lfs-us-1.hf.co`, `cas-bridge.xethub.hf.co`,
`cas-server.xethub.hf.co`, `us.aws.cdn.hf.co`; set `HF_HUB_DISABLE_XET=1`).

```bash
# a whole season (resumable; prints ADDED / NOT READY / FILES)
GR_YEAR=2024 HF_HUB_DISABLE_XET=1 python3 -I tools/update_new.py empty_index.json work2024
python3 tools/package2025.py 2024          # -> pub/2024 (also converts data to binary)
python3 tools/fix_points.py work2023        # only if OpenF1 points look wrong
python3 tools/shrink_radio.py in.mp3 out.mp3   # 24 kbps radio
# commentary
node tools/commscript_all.js comm/list.json   # page served locally with the test hook
./tools/render_all_comm.sh
# offline split version
python3 tools/launcher.py pub/index.html Grid-Replay.html
SPLIT_JS=1 COMM_DIR=comm/2025 python3 tools/standalone.py pub/index.html pub/2025/index.json grid-replay-2025.js 2025/
# backup parts
./tools/make_backup_parts.sh
```

Testing: `tools/testyear.js` (every session of a season loads, no errors), `/tmp`-style decode checks of
every radio and commentary clip in Chromium, and spot checks of standings and scripts against real results.

## 10. Known limitations

- Commentary audio cannot be captured in video export (browser restriction).
- Online past seasons (2023–2025) use the device voice (size limit); offline has natural voices.
- Very large single files (over ~250 MB) failed to download in the Claude app; everything is split
  into files under 80 MB.
- Google Drive upload from here is limited to 10 MB per file.
- Headless tests cannot listen; audio was checked by decoding and by speech recognition.

## 11. History (short)

1. 2026 season replay: linear view, radio, crashes, pit lane, penalties, tyres, transcripts.
2. All 2026 rounds, sprints, qualifying ghost laps, positions and lap-time charts, previews, weekend updates.
3. Head to head, overtakes, accident recreation, battle tracker, weather overlay, video export.
4. 2025 season (Miami GP rebuilt from GPS), season picker, offline single files.
5. Race commentary (device voice), 2024 season (radio timezone fix), 2023 season (points fix),
   binary data and radio compression to fit online.
6. Two-voice commentary with natural Piper voices; split offline version; backups in parts.

Git commits (oldest first): 0d8f82d, e7e8228, 5b70805, 7d977d1, d3fd6dd, 3450555, e9b1313, 584a7a4,
bea9690, 40d8c58, 63c01bf, 668506c.

## 12. What's in the backup parts

| File | Contents |
| --- | --- |
| Grid-Replay-backup-1-tools-scripts-readme.zip | README, all tools, commentary scripts (JSON) |
| Grid-Replay-backup-2-online-2026.zip | Online 2026 files incl. commentary |
| Grid-Replay-backup-3/4/5-online-2025/2024/2023.zip | Online past-season files + their commentary packs |
| Grid-Replay-extra-6-project-guide-and-dev-tools.zip | This guide, every working script incl. tests and page fragments, the code folder from git |
| Grid-Replay-extra-7..-original-radio-*.zip | Team radio at original quality (before 24 kbps), per season |
| Grid-Replay-extra-…-raw-miami-2025.zip | Raw OpenF1 downloads used to rebuild the 2025 Miami GP |

Not included, because they are public downloads: the Piper voice models and the Whisper model
(Hugging Face). The race packs in the online folders are the same data as the build files.

## 13. Licences and data

- Data: OpenF1 (openf1.org), an unofficial community API. Timing data and team radio belong to Formula 1.
- This is a private fan project for personal use. Please don't publish or share it publicly.
- Voices: CC BY-SA 4.0 / CC BY 4.0 training data (credit required if ever shared).
- No API keys, passwords or personal data are stored in any of the files.
