#!/usr/bin/env python3
"""
Extract extra still frames from each film's already-fetched clip, for the
poster-strip montage in the reserved ad slots (see .poster-strip in
styles.css). The video element still uses assets/clips/<film-id>.jpg (the
1.5s frame fetch_clip.py grabs) as its poster -- these are additional
frames, at different points in the same ~10s clip, purely so the
poster-strip has more than one image per film to cycle through.

Run after any new film's clip is fetched:
    python3 scripts/extract_posterstrip_frames.py

Writes assets/posterstrip/<film-id>-<n>.jpg (n = 1..3) for every film that
has a clip in assets/clips/. Local-only -- reads the already-downloaded
mp4, no network access needed.
"""

import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLIPS_DIR = ROOT / "assets" / "clips"
OUT_DIR = ROOT / "assets" / "posterstrip"
FILMS_JSON = ROOT / "data" / "films.json"

# Seconds into the clip to grab each frame -- spread across the ~10s clip,
# deliberately not 1.5s (that's the existing video-poster frame already in
# assets/clips/<id>.jpg, no need to duplicate it here).
FRAME_TIMES = [0.5, 4.5, 8.5]


def main() -> None:
    films = json.loads(FILMS_JSON.read_text())["films"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    written = 0
    for film in films:
        fid = film["id"]
        clip = CLIPS_DIR / f"{fid}.mp4"
        if not clip.exists():
            print(f"skip {fid}: no clip at {clip}")
            continue
        for n, t in enumerate(FRAME_TIMES, start=1):
            out = OUT_DIR / f"{fid}-{n}.jpg"
            subprocess.run(
                ["ffmpeg", "-nostdin", "-y", "-loglevel", "error",
                 "-ss", str(t), "-i", str(clip),
                 "-frames:v", "1", "-q:v", "3", str(out)],
                check=True,
            )
            written += 1

    print(f"Wrote {written} frames to {OUT_DIR}/")


if __name__ == "__main__":
    main()
