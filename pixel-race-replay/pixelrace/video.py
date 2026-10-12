"""Encodes frames to MP4 by piping raw pixels into ffmpeg."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Iterable

from PIL import Image


def write_mp4(frames: Iterable[Image.Image], out: Path, size: tuple[int, int], fps: int, scale: int) -> None:
    """Write ``frames`` (all ``size``, RGB) to ``out`` as H.264, scaled up
    ``scale`` times with nearest-neighbour sampling so pixels stay square."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg was not found on PATH; install it to export video")
    w, h = size
    out = Path(out).resolve()  # absolute, so the name can never be read as an ffmpeg option
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
        "-vf", f"scale={w * scale}:{h * scale}:flags=neighbor",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-tune", "animation",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for frame in frames:
            proc.stdin.write(frame.tobytes())
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise RuntimeError(f"ffmpeg exited with status {code}")


def save_png(frame: Image.Image, out: Path, scale: int) -> None:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    w, h = frame.size
    frame.resize((w * scale, h * scale), Image.Resampling.NEAREST).save(out)
