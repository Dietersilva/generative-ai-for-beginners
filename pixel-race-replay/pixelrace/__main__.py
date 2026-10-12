"""Command line: render the demo race to an MP4 or a single PNG frame.

    python -m pixelrace --out out/demo.mp4
    python -m pixelrace --layout portrait --follow CRU --out out/demo-short.mp4
    python -m pixelrace --still 0.5 --out out/halfway.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .demo import DemoRace
from .render import LAYOUTS, Renderer, race_times
from .video import save_png, write_mp4


def _bounded(kind, low, high):
    def parse(text: str):
        value = kind(text)
        if not low <= value <= high:
            raise argparse.ArgumentTypeError(f"must be between {low} and {high}")
        return value
    return parse


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pixelrace", description="Render a pixel-art race replay (fictional demo data).")
    p.add_argument("--layout", choices=sorted(LAYOUTS), default="landscape",
                   help="landscape = 1920x1080 for YouTube; portrait = 1080x1920 for Shorts/Reels/TikTok")
    p.add_argument("--follow", metavar="CODE", help="driver code to highlight, e.g. CRU")
    p.add_argument("--duration", type=_bounded(float, 1, 600), default=30.0, help="seconds of video for the race (default 30)")
    p.add_argument("--hold", type=_bounded(float, 0, 30), default=3.0, help="seconds to hold the final result (default 3)")
    p.add_argument("--fps", type=_bounded(int, 1, 60), default=30)
    p.add_argument("--scale", type=_bounded(int, 1, 12), default=6, help="pixel upscale factor (default 6)")
    p.add_argument("--laps", type=_bounded(int, 3, 100), default=20)
    p.add_argument("--seed", type=int, default=7, help="demo race seed; same seed, same race")
    p.add_argument("--still", type=_bounded(float, 0, 1), metavar="FRACTION",
                   help="save one PNG at this point of the race (0 = start, 1 = finish) instead of a video")
    p.add_argument("--out", type=Path, default=None, help="output file (default out/demo.mp4 or out/still.png)")
    args = p.parse_args(argv)

    race = DemoRace(seed=args.seed, laps=args.laps)
    try:
        renderer = Renderer(race, layout=args.layout, follow=args.follow.upper() if args.follow else None)
    except ValueError as err:
        p.error(str(err))

    if args.still is not None:
        out = args.out or Path("out/still.png")
        t = race.start_time + (race.end_time - race.start_time) * args.still
        save_png(renderer.frame(t), out, args.scale)
    else:
        out = args.out or Path("out/demo.mp4")
        times = race_times(race, args.duration, args.fps, args.hold)
        frames = (renderer.frame(t, i) for i, t in enumerate(times))
        write_mp4(frames, out, renderer.size, args.fps, args.scale)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
