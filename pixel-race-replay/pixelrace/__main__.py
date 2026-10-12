"""Command line: render the demo race to an MP4 or a single PNG frame.

    python -m pixelrace --out out/demo.mp4
    python -m pixelrace --follow CRU --out out/demo-follow.mp4
    python -m pixelrace --style map --layout portrait --out out/demo-map.mp4
    python -m pixelrace --still 0.5 --out out/halfway.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .demo import DemoRace
from .render import Renderer, race_times, start_lights
from .timelapse import TimelapseRenderer
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
    p.add_argument("--style", choices=("timelapse", "map"), default="timelapse",
                   help="timelapse = one row per car, sliding by gap to the leader; map = cars on the circuit")
    p.add_argument("--layout", choices=("landscape", "portrait"), default="landscape",
                   help="landscape = 1920x1080 for YouTube; portrait = 1080x1920 for Shorts/Reels/TikTok")
    p.add_argument("--follow", metavar="CODE", help="driver code to highlight, e.g. CRU")
    p.add_argument("--duration", type=_bounded(float, 1, 600), default=30.0, help="seconds of video for the race (default 30)")
    p.add_argument("--hold", type=_bounded(float, 0, 30), default=3.0, help="seconds to hold the final result (default 3)")
    p.add_argument("--intro", type=_bounded(float, 0, 10), default=2.4, help="seconds of start lights (default 2.4)")
    p.add_argument("--fps", type=_bounded(int, 1, 60), default=30)
    p.add_argument("--scale", type=_bounded(int, 1, 12), default=None,
                   help="pixel upscale factor (default: 4 for timelapse, 6 for map, giving 1920x1080)")
    p.add_argument("--laps", type=_bounded(int, 3, 100), default=20)
    p.add_argument("--seed", type=int, default=7, help="demo race seed; same seed, same race")
    p.add_argument("--still", type=_bounded(float, 0, 1), metavar="FRACTION",
                   help="save one PNG at this point of the race (0 = start, 1 = finish) instead of a video")
    p.add_argument("--out", type=Path, default=None, help="output file (default out/demo.mp4 or out/still.png)")
    args = p.parse_args(argv)

    race = DemoRace(seed=args.seed, laps=args.laps)
    try:
        renderer_cls = TimelapseRenderer if args.style == "timelapse" else Renderer
        renderer = renderer_cls(race, layout=args.layout, follow=args.follow.upper() if args.follow else None)
    except ValueError as err:
        p.error(str(err))

    scale = args.scale or renderer.default_scale
    if args.still is not None:
        out = args.out or Path("out/still.png")
        t = race.start_time + (race.end_time - race.start_time) * args.still
        save_png(renderer.frame(t), out, scale)
    else:
        out = args.out or Path("out/demo.mp4")
        timeline = [(race.start_time, lit) for lit in start_lights(args.fps, args.intro)]
        timeline += [(t, None) for t in race_times(race, args.duration, args.fps, args.hold)]
        frames = (renderer.frame(t, i, lights) for i, (t, lights) in enumerate(timeline))
        write_mp4(frames, out, renderer.size, args.fps, scale)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
