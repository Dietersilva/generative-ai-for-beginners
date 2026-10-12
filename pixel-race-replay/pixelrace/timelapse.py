"""The "gap timelapse" view.

Every car gets its own row, in race order. A car's horizontal position shows
how far it is behind the leader, and lap lines scroll past as the race goes
on. Cars that are fighting for a place drift into each other's rows, so
overtakes read as two cars swapping lines.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image, ImageDraw

from .font import GLYPH_H, draw_text, draw_text_right, fill, text_width
from .model import RGB, CarState, Driver, RaceSource, Status

HEADER_BG = (34, 34, 40)
BAND_A = (78, 78, 88)
BAND_B = (70, 70, 80)
OUTSIDE = (62, 62, 72)  # before the start line and beyond the flag
LAP_LINE = (112, 112, 124)
LAP_LABEL = (104, 104, 118)
FOLLOW_ROW = (92, 92, 106)
TEXT = (236, 238, 244)
MUTED = (150, 154, 166)
RETIRED = (112, 112, 120)
PIT_GREEN = (70, 210, 90)
FASTEST = (190, 80, 255)
TIRE = (18, 18, 22)

COMPOUND_COLORS = {
    "S": (235, 45, 45),
    "M": (245, 205, 30),
    "H": (235, 235, 235),
    "I": (50, 185, 70),
    "W": (40, 115, 235),
}

# Top-down car, nose to the right. P = livery, S = wings/helmet, K = tyres.
_CAR = (
    "..KK......KK....",
    "S.KK.PPPP.KK...S",
    "S..PPPPPPPPPP..S",
    "SSPPPPSPPPPPPPPS",
    "S..PPPPPPPPPP..S",
    "S.KK.PPPP.KK...S",
    "..KK......KK....",
)
CAR_W, CAR_H = len(_CAR[0]), len(_CAR)

_BADGE = (  # 7x7 tyre badge ring; the compound letter sits inside
    "..###..",
    ".#...#.",
    "#.....#",
    "#.....#",
    "#.....#",
    ".#...#.",
    "..###..",
)
_STOPWATCH = (
    ".###.",
    "#..##",
    "#.#.#",
    "#...#",
    ".###.",
)


def _sprite(rows: tuple[str, ...], colors: dict[str, RGB]) -> Image.Image:
    img = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell in colors:
                img.putpixel((x, y), colors[cell] + (255,))
    return img


def car_sprite(driver: Driver, retired: bool = False) -> Image.Image:
    if retired:
        return _sprite(_CAR, {"P": RETIRED, "S": (90, 90, 98), "K": (60, 60, 66)})
    return _sprite(_CAR, {"P": driver.color, "S": driver.secondary, "K": TIRE})


def tyre_age_color(age: int) -> RGB:
    """Fresh tyres green, worn tyres red."""
    if age < 6:
        return (60, 200, 70)
    if age < 12:
        return (170, 210, 40)
    if age < 18:
        return (240, 200, 30)
    if age < 25:
        return (245, 130, 30)
    return (230, 50, 40)


def format_race_time(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, rest = divmod(ms, 3_600_000)
    m, rest = divmod(rest, 60_000)
    s, ms = divmod(rest, 1000)
    return f"{h}:{m:02d}:{s:02d}.{ms:03d}" if h else f"{m}:{s:02d}.{ms:03d}"


def finish_label(state: CarState, position: int, start_time: float) -> str:
    if position == 1:
        return format_race_time(state.finish_time - start_time)
    if state.laps_behind > 0:
        return f"+{state.laps_behind} LAP" + ("S" if state.laps_behind > 1 else "")
    return f"+{state.gap:.3f}" if state.gap is not None else ""


def soft_ranks(states: list[CarState], blend: float = 0.002) -> list[float]:
    """Row for each car (0 = top). Finished and retired cars sit on their
    exact row; cars still racing get a smooth rank from their distance, so two
    cars side by side share a row and swap smoothly when one passes."""
    ranks = [float(i) for i in range(len(states))]
    racing = [i for i, s in enumerate(states) if s.status in (Status.RUNNING, Status.PIT)]
    finished = sum(s.status is Status.FINISHED for s in states)
    for i in racing:
        di = states[i].distance
        ahead = 0.0
        for j in racing:
            if j != i:
                z = (states[j].distance - di) / blend
                ahead += 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z))))
        ranks[i] = finished + ahead
    return ranks


@dataclass(frozen=True)
class TimelapseLayout:
    size: tuple[int, int]
    header_h: int = 13


LAYOUTS = {
    "landscape": TimelapseLayout((480, 270)),  # x4 = 1920x1080
    "portrait": TimelapseLayout((270, 480)),  # x4 = 1080x1920
}


class TimelapseRenderer:
    default_scale = 4

    def __init__(self, source: RaceSource, layout: str = "landscape", follow: str | None = None):
        if layout not in LAYOUTS:
            raise ValueError(f"unknown layout {layout!r}; choose from {', '.join(LAYOUTS)}")
        self.source = source
        self.layout = LAYOUTS[layout]
        self.drivers = {d.code: d for d in source.drivers}
        if follow is not None and follow not in self.drivers:
            raise ValueError(f"unknown driver {follow!r}; choose from {', '.join(self.drivers)}")
        self.follow = follow

        w, h = self.layout.size
        self.anchor = round(w * 0.72)  # where the leader's nose sits
        self.px_per_lap = w * 0.5
        self.min_x = 32  # cars further back pile up here
        self.top = self.layout.header_h + 4
        self.row_h = max(8, min(22, (h - self.top - 4) // max(1, len(source.drivers))))

        self._cars = {d.code: car_sprite(d) for d in source.drivers}
        self._retired = {d.code: car_sprite(d, retired=True) for d in source.drivers}
        self._badges = {c: _sprite(_BADGE, {"#": col}) for c, col in COMPOUND_COLORS.items()}
        self._stopwatch = _sprite(_STOPWATCH, {"#": FASTEST})

    @property
    def size(self) -> tuple[int, int]:
        return self.layout.size

    def x_of(self, distance: float, lead: float) -> float:
        return self.anchor - (lead - distance) * self.px_per_lap

    def frame(self, t: float, index: int = 0, lights: int | None = None) -> Image.Image:
        states = self.source.state_at(t)
        lead = max((s.distance for s in states if s.status is not Status.RETIRED), default=0.0)
        img = Image.new("RGB", self.size, OUTSIDE)
        self._draw_laps(img, lead)

        ranks = soft_ranks(states)
        if self.follow is not None:
            i = next(i for i, s in enumerate(states) if s.code == self.follow)
            y = self.top + round(ranks[i] * self.row_h)
            fill(img, (0, y, self.size[0] - 1, y + self.row_h - 1), FOLLOW_ROW)
        for i in sorted(range(len(states)), key=lambda i: -ranks[i]):  # back markers first
            self._draw_row(img, states[i], i + 1, ranks[i], lead)

        self._draw_header(img)
        if lights is not None:
            draw_start_lights(img, self.size[0] // 2, (self.top + self.size[1]) // 2, lights)
        return img

    def _draw_laps(self, img: Image.Image, lead: float) -> None:
        w, h = self.size
        total = self.source.total_laps
        first = max(0, math.floor(lead - self.anchor / self.px_per_lap) - 1)
        last = min(total, math.ceil(lead + (w - self.anchor) / self.px_per_lap) + 1)
        for k in range(first, last + 1):
            x0, x1 = max(0, round(self.x_of(k, lead))), min(w - 1, round(self.x_of(k + 1, lead)))
            if k < total and x0 <= x1:
                fill(img, (x0, self.layout.header_h, x1, h - 1), BAND_A if k % 2 else BAND_B)
        for k in range(first, last + 1):
            x = round(self.x_of(k, lead))
            if not 0 <= x < w:
                continue
            if k == total:
                for y in range(self.layout.header_h, h):  # chequered finish line
                    img.putpixel((x, y), TEXT if (y // 2) % 2 else (20, 20, 24))
                    if x + 1 < w:
                        img.putpixel((x + 1, y), (20, 20, 24) if (y // 2) % 2 else TEXT)
                label = "FINISH"
            else:
                fill(img, (x, self.layout.header_h, x, h - 1), LAP_LINE)
                label = f"LAP {k + 1}"
            draw_text(img, (x + 3, self.layout.header_h + 3), label, LAP_LABEL, size=2)

    def _draw_row(self, img: Image.Image, s: CarState, position: int, rank: float, lead: float) -> None:
        driver = self.drivers[s.code]
        cx = max(self.min_x, round(self.x_of(s.distance, lead)))  # car nose
        cy = self.top + round(rank * self.row_h) + self.row_h // 2  # row centre
        car_left, car_top = cx - CAR_W + 1, cy - CAR_H // 2
        text_y = cy - GLYPH_H // 2
        out = s.status is Status.RETIRED

        img.paste(self._retired[s.code] if out else self._cars[s.code], (car_left, car_top), self._cars[s.code])
        label_color = RETIRED if out else (TEXT if s.code != self.follow else (255, 255, 160))
        draw_text(img, (cx + 4, text_y), s.code, label_color)
        if s.fastest_lap and not out:
            img.paste(self._stopwatch, (cx + 4 + text_width(s.code) + 2, cy - 2), self._stopwatch)

        badge_left = car_left - 9
        if out:
            draw_text_right(img, car_left - 3, text_y, "DNF", RETIRED)
            return
        if s.compound in self._badges:
            badge = self._badges[s.compound]
            img.paste(badge, (badge_left, cy - 3), badge)
            draw_text(img, (badge_left + 2, cy - 2), s.compound, COMPOUND_COLORS[s.compound])
        if s.tyre_age is not None:
            fill(img, (badge_left - 4, cy - 2, badge_left - 3, cy + 2), tyre_age_color(s.tyre_age))

        if s.status is Status.PIT:
            box = (car_left - 10, cy - 4, cx + 1, cy + 4)
            ImageDraw.Draw(img).rectangle(box, fill=(18, 36, 22), outline=PIT_GREEN)
            draw_text(img, (box[0] + 2, text_y), "IN PIT", PIT_GREEN)
        elif s.status is Status.FINISHED:
            draw_text_right(img, badge_left - 7, text_y, finish_label(s, position, self.source.start_time), TEXT)

    def _draw_header(self, img: Image.Image) -> None:
        w = self.size[0]
        hh = self.layout.header_h
        fill(img, (0, 0, w - 1, hh - 1), HEADER_BG)
        draw_text(img, (3, 2), self.source.title, TEXT, size=2)
        if self.source.notice:
            draw_text_right(img, w - 3, (hh - GLYPH_H) // 2, self.source.notice, MUTED)


def draw_start_lights(img: Image.Image, cx: int, cy: int, lit: int) -> None:
    """Five light pods stacked vertically; the first ``lit`` are on."""
    draw = ImageDraw.Draw(img)
    pod_w, pod_h, gap = 15, 7, 2
    top = cy - (5 * pod_h + 4 * gap) // 2
    for i in range(5):
        y = top + i * (pod_h + gap)
        draw.rounded_rectangle((cx - pod_w // 2, y, cx + pod_w // 2, y + pod_h - 1), radius=2, fill=(16, 16, 20))
        for j in range(2):
            on = i < lit and j == 0
            lx = cx - pod_w // 2 + 2 + j * 6
            draw.ellipse((lx, y + 1, lx + 4, y + 5), fill=(235, 30, 30) if on else (58, 58, 64))
