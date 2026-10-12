"""Draws one low-resolution pixel-art frame per race moment.

Frames are drawn small (320x180 or 180x320) and scaled up with
nearest-neighbour sampling when the video is encoded, which keeps every
pixel sharp.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image, ImageDraw

from .font import GLYPH_H, draw_text, draw_text_right, fill
from .model import CarState, RaceSource, Status

BG = (16, 20, 28)
TRACK_EDGE = (92, 100, 118)
ASPHALT = (46, 50, 60)
TEXT = (232, 236, 242)
MUTED = (120, 128, 144)
HIGHLIGHT = (40, 48, 66)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

Box = tuple[int, int, int, int]  # left, top, right, bottom (inclusive)


@dataclass(frozen=True)
class Layout:
    size: tuple[int, int]
    track: Box
    board: Box
    row_h: int
    show_names: bool
    footer_y: int


LAYOUTS = {
    # 320x180 scales to 1920x1080 at 6x: YouTube.
    "landscape": Layout((320, 180), track=(6, 14, 206, 168), board=(214, 16, 314, 168),
                        row_h=8, show_names=False, footer_y=172),
    # 180x320 scales to 1080x1920 at 6x: Shorts, Reels, TikTok.
    "portrait": Layout((180, 320), track=(8, 18, 172, 178), board=(8, 186, 172, 304),
                       row_h=10, show_names=True, footer_y=310),
}


def gap_label(state: CarState, position: int) -> str:
    if state.status is Status.RETIRED:
        return "OUT"
    if state.status is Status.PIT:
        return "PIT"
    if position == 1:
        return "WINNER" if state.status is Status.FINISHED else "LEADER"
    if state.laps_behind > 0:
        return f"+{state.laps_behind} LAP" + ("S" if state.laps_behind > 1 else "")
    if state.gap is None:
        return ""
    return f"+{state.gap:.1f}"


class Renderer:
    def __init__(self, source: RaceSource, layout: str = "landscape", follow: str | None = None):
        if layout not in LAYOUTS:
            raise ValueError(f"unknown layout {layout!r}; choose from {', '.join(LAYOUTS)}")
        self.source = source
        self.layout = LAYOUTS[layout]
        self.drivers = {d.code: d for d in source.drivers}
        if follow is not None and follow not in self.drivers:
            raise ValueError(f"unknown driver {follow!r}; choose from {', '.join(self.drivers)}")
        self.follow = follow
        self._fit_track()
        self._background = self._draw_background()

    @property
    def size(self) -> tuple[int, int]:
        return self.layout.size

    def _fit_track(self) -> None:
        xs = [p[0] for p in self.source.track]
        ys = [p[1] for p in self.source.track]
        left, top, right, bottom = self.layout.track
        margin = 5  # room for the track's width
        w = max(max(xs) - min(xs), 1e-9)
        h = max(max(ys) - min(ys), 1e-9)
        self._scale = min((right - left - 2 * margin) / w, (bottom - top - 2 * margin) / h)
        self._ox = (left + right) / 2 - (min(xs) + max(xs)) / 2 * self._scale
        self._oy = (top + bottom) / 2 - (min(ys) + max(ys)) / 2 * self._scale

    def to_px(self, x: float, y: float) -> tuple[int, int]:
        return round(self._ox + x * self._scale), round(self._oy + y * self._scale)

    def _draw_background(self) -> Image.Image:
        img = Image.new("RGB", self.size, BG)
        draw = ImageDraw.Draw(img)
        pts = [self.to_px(x, y) for x, y in self.source.track]
        loop = pts + pts[:2]
        draw.line(loop, fill=TRACK_EDGE, width=7, joint="curve")
        draw.line(loop, fill=ASPHALT, width=5, joint="curve")

        # Chequered start/finish line across the track at track[0].
        (x0, y0), (x1, y1) = self.source.track[0], self.source.track[1]
        length = math.hypot(x1 - x0, y1 - y0) or 1.0
        tx, ty = (x1 - x0) / length, (y1 - y0) / length
        sx, sy = self._ox + x0 * self._scale, self._oy + y0 * self._scale
        for k in range(-3, 4):
            for j in range(2):
                px, py = round(sx - ty * k + tx * j), round(sy + tx * k + ty * j)
                img.putpixel((px, py), WHITE if (k + j) % 2 else BLACK)
        return img

    def frame(self, t: float, index: int = 0) -> Image.Image:
        states = self.source.state_at(t)
        img = self._background.copy()
        self._draw_cars(img, states, index)
        self._draw_header(img, states)
        self._draw_board(img, states)
        if self.source.notice:
            draw_text(img, (self.layout.track[0], self.layout.footer_y), self.source.notice, MUTED)
        return img

    def _draw_cars(self, img: Image.Image, states: list[CarState], index: int) -> None:
        # Back markers first, so the leader is drawn on top.
        for s in reversed(states):
            if s.status is Status.RETIRED:
                continue
            px, py = self.to_px(s.x, s.y)
            if s.code == self.follow and (index // 6) % 2 == 0:
                ImageDraw.Draw(img).rectangle((px - 2, py - 2, px + 2, py + 2), outline=WHITE)
            fill(img, (px - 1, py - 1, px + 1, py + 1), self.drivers[s.code].color)

    def _draw_header(self, img: Image.Image, states: list[CarState]) -> None:
        left, _, _, _ = self.layout.track
        right = self.layout.board[2]
        y = self.layout.track[1] - GLYPH_H - 4
        draw_text(img, (left, y), self.source.title, TEXT)
        leader = states[0]
        total = self.source.total_laps
        if leader.status is Status.FINISHED:
            label = "FINISH"
        else:
            label = f"LAP {min(total, math.floor(max(leader.distance, 0.0)) + 1)}/{total}"
        draw_text_right(img, right, y, label, TEXT)

    def _draw_board(self, img: Image.Image, states: list[CarState]) -> None:
        left, top, right, _ = self.layout.board
        row_h = self.layout.row_h
        pad = (row_h - GLYPH_H) // 2
        for i, s in enumerate(states):
            y = top + i * row_h
            driver = self.drivers[s.code]
            out = s.status is Status.RETIRED
            color = MUTED if out else TEXT
            if s.code == self.follow:
                fill(img, (left, y, right, y + row_h - 1), HIGHLIGHT)
            draw_text_right(img, left + 9, y + pad, str(i + 1), color)
            fill(img, (left + 12, y + pad, left + 13, y + pad + GLYPH_H - 1), driver.color)
            draw_text(img, (left + 16, y + pad), s.code, color)
            if self.layout.show_names:
                draw_text(img, (left + 32, y + pad), driver.name, MUTED)
            draw_text_right(img, right - 1, y + pad, gap_label(s, i + 1), color)

        if self.follow is not None:
            pos = next(i for i, s in enumerate(states) if s.code == self.follow) + 1
            y = top + len(states) * row_h + 6
            draw_text(img, (left, y), f"FOLLOWING {self.follow}", MUTED)
            draw_text_right(img, right - 1, y, f"P{pos}", TEXT)


def race_times(source: RaceSource, duration: float, fps: int, hold: float) -> list[float]:
    """Race time for every video frame: the whole race squeezed into
    ``duration`` seconds, then ``hold`` seconds frozen on the result."""
    n = max(2, round(duration * fps))
    span = source.end_time - source.start_time
    times = [source.start_time + span * i / (n - 1) for i in range(n)]
    return times + [source.end_time] * round(hold * fps)
