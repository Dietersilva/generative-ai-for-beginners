#!/usr/bin/env python3
"""
Fetch and trim a single public-domain film clip for RetroClips.

NOT RUNNABLE IN THE BUILD SANDBOX THIS SITE WAS PROTOTYPED IN: that
environment's network policy blocks outbound access to archive.org and
every other general web host (only package registries and Anthropic's
own API are reachable there). Run this on a machine with normal
internet access instead -- your own laptop, a CI runner, wherever.

Usage:
    python3 scripts/fetch_clip.py \
        --film-id nosferatu-1922 \
        --source-url "https://archive.org/download/<identifier>/<file>.mp4" \
        --start 00:14:32 \
        --duration 10

What it does:
    1. Seeks directly into the *remote* file with ffmpeg's -ss placed
       before -i, so ffmpeg only pulls the bytes it needs over HTTP
       range requests instead of downloading the whole film first.
    2. Re-encodes the trimmed segment to the site's target format
       (854x480 h264/aac mp4) so file size and look stay consistent
       with the placeholder clips it replaces.
    3. Extracts a poster frame (1.5s into the clip) as a jpg, same as
       make_placeholder_clips.sh does for the placeholders.
    4. Writes both into assets/clips/<film-id>.{mp4,jpg}.

Finding a source URL:
    Search archive.org for the film title (e.g. "Nosferatu 1922
    public domain"), open the item page, and copy the direct link to
    an actual video file under "DOWNLOAD OPTIONS" -- not the
    streaming player page. Check the item's rights/license field
    actually says public domain before using it; not everything
    uploaded to archive.org is what its title claims.

Finding a timestamp:
    There's no shortcut here -- watch the source and note the in-point
    of the scene you want. A practical workflow: run this script once
    with a generous --duration (say 30s) around your rough guess,
    review the output, then narrow --start/--duration down to the
    real 9-10s beat and re-run.
"""

import argparse
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLIPS_DIR = ROOT / "assets" / "clips"
FILMS_JSON = ROOT / "data" / "films.json"

TARGET_WIDTH = 854
TARGET_HEIGHT = 480


def load_film(film_id: str) -> dict:
    films = json.loads(FILMS_JSON.read_text())["films"]
    for film in films:
        if film["id"] == film_id:
            return film
    known = ", ".join(f["id"] for f in films)
    sys.exit(f"Unknown --film-id '{film_id}'. Known ids: {known}")


def proxy_args() -> list[str]:
    """
    ffmpeg doesn't read the HTTPS_PROXY env var the way curl does, so on a
    machine that sandboxes outbound traffic through an HTTP(S) proxy (like
    the one this prototype was built in), ffmpeg needs to be told about it
    explicitly or every fetch 403s. On a normal machine with no such proxy,
    HTTPS_PROXY is unset and this is a no-op.
    """
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if not proxy:
        return []
    args = ["-http_proxy", proxy]
    for ca_path in (os.environ.get("SSL_CERT_FILE"), "/root/.ccr/ca-bundle.crt"):
        if ca_path and pathlib.Path(ca_path).is_file():
            args += ["-ca_file", ca_path]
            break
    return args


def run_ffmpeg(args: list[str]) -> None:
    # ffmpeg rejects -http_proxy/-ca_file outright when the input isn't a
    # network URL (e.g. the local-file poster-frame extraction below), so
    # only attach them when an argument actually looks like one.
    is_remote = any(a.startswith("http://") or a.startswith("https://") for a in args)
    extra = proxy_args() if is_remote else []
    full_args = ["ffmpeg", "-nostdin", "-y", "-loglevel", "error", *extra, *args]
    print("+", " ".join(full_args))
    subprocess.run(full_args, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--film-id", required=True, help="id from data/films.json, e.g. nosferatu-1922")
    parser.add_argument("--source-url", required=True, help="direct URL to the source video file (not a player page)")
    parser.add_argument("--start", required=True, help="timestamp to start the clip, e.g. 00:14:32 or 872")
    parser.add_argument("--duration", type=float, default=10.0, help="clip length in seconds (default 10, keep to 9-11)")
    args = parser.parse_args()

    if not (9.0 <= args.duration <= 11.0):
        print(f"warning: duration {args.duration}s is outside the site's 9-11s target range", file=sys.stderr)

    film = load_film(args.film_id)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    out_mp4 = CLIPS_DIR / f"{args.film_id}.mp4"
    out_jpg = CLIPS_DIR / f"{args.film_id}.jpg"

    print(f"Fetching clip for: {film['title']} ({film['year']}) -- {film['scene_label']}")

    # -ss before -i triggers input seeking: ffmpeg asks the HTTP server for
    # a byte range starting near that timestamp instead of downloading the
    # file from byte zero. Requires the server to support range requests,
    # which archive.org's direct file links generally do.
    run_ffmpeg([
        "-ss", args.start,
        "-i", args.source_url,
        "-t", str(args.duration),
        "-vf", f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
               f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "medium",
        "-c:a", "aac", "-b:a", "96k",
        str(out_mp4),
    ])

    run_ffmpeg(["-ss", "1.5", "-i", str(out_mp4), "-frames:v", "1", "-q:v", "3", str(out_jpg)])

    print(f"Done: {out_mp4}")
    print(f"Done: {out_jpg}")
    print()
    print(f"Update data/films.json for '{args.film_id}': set clip.start_timestamp to "
          f"\"{args.start}\" and clip.status to \"sourced\".")


if __name__ == "__main__":
    main()
