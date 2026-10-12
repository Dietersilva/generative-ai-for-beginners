"""A fictional race for building and testing the renderer before real data
is wired in.

Everything here is invented: the circuit, the drivers, their colours and the
results. Nothing represents a real event, team or person.
"""

from __future__ import annotations

import math
import random
from bisect import bisect_right
from dataclasses import dataclass, field

from .model import CarState, Driver, Point, Status

DEMO_DRIVERS = (
    Driver("AXL", "Axel Varn", (230, 57, 70)),
    Driver("BRN", "Bruna Lio", (255, 159, 28)),
    Driver("CRU", "Cruz Odell", (255, 221, 51)),
    Driver("DAV", "Dava Kemp", (46, 196, 182)),
    Driver("ELM", "Elmo Strand", (58, 134, 255)),
    Driver("FOX", "Foxa Rhee", (131, 56, 236)),
    Driver("GRY", "Gray Tolle", (255, 0, 110)),
    Driver("HAL", "Hal Merin", (139, 201, 38)),
    Driver("IVO", "Ivo Saari", (240, 240, 240)),
    Driver("JET", "Jet Amaro", (120, 144, 156)),
)

GRID_GAP = 0.006  # laps between grid slots
PIT_LOSS = 21.0  # seconds stationary in the pit lane


class Polyline:
    """A closed polyline addressed by fraction of its length (0..1)."""

    def __init__(self, points: list[Point]):
        self.points = points
        self.cum = [0.0]
        for a, b in zip(points, points[1:] + points[:1]):
            self.cum.append(self.cum[-1] + math.dist(a, b))
        self.length = self.cum[-1]

    def at(self, frac: float) -> Point:
        s = (frac % 1.0) * self.length
        i = min(bisect_right(self.cum, s) - 1, len(self.points) - 1)
        a, b = self.points[i], self.points[(i + 1) % len(self.points)]
        seg = self.cum[i + 1] - self.cum[i]
        u = (s - self.cum[i]) / seg if seg else 0.0
        return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


def make_track(rng: random.Random, samples: int = 720) -> list[Point]:
    """A random closed circuit. The radius never reaches zero, so the curve
    is star-shaped around the origin and can never cross itself."""
    p1, p2, p3 = (rng.uniform(0, 2 * math.pi) for _ in range(3))
    points = []
    for i in range(samples):
        th = 2 * math.pi * i / samples
        r = 1 + 0.22 * math.sin(2 * th + p1) + 0.12 * math.sin(3 * th + p2) + 0.06 * math.sin(5 * th + p3)
        points.append((1.6 * r * math.cos(th), -r * math.sin(th)))
    return points


@dataclass
class _Segment:
    t0: float
    t1: float
    d0: float
    d1: float
    status: Status


@dataclass
class _Timeline:
    driver: Driver
    segments: list[_Segment] = field(default_factory=list)
    finish_time: float | None = None
    retire_time: float | None = None

    def distance_at(self, t: float) -> tuple[float, Status]:
        segs = self.segments
        if t <= segs[0].t0:
            return segs[0].d0, Status.RUNNING
        i = bisect_right([s.t0 for s in segs], t) - 1
        s = segs[i]
        if t >= s.t1:
            if self.finish_time is not None and t >= self.finish_time:
                return segs[-1].d1, Status.FINISHED
            if self.retire_time is not None and t >= self.retire_time:
                return segs[-1].d1, Status.RETIRED
            return s.d1, s.status
        u = (t - s.t0) / (s.t1 - s.t0)
        return s.d0 + (s.d1 - s.d0) * u, s.status

    def time_at(self, d: float) -> float | None:
        """First time this car reached distance ``d``."""
        for s in self.segments:
            if s.d1 >= d:
                if s.d1 == s.d0 or d <= s.d0:
                    return s.t0
                return s.t0 + (s.t1 - s.t0) * (d - s.d0) / (s.d1 - s.d0)
        return None


class DemoRace:
    """A deterministic fictional race. Same seed, same race."""

    def __init__(self, seed: int = 7, laps: int = 20):
        if laps < 3:
            raise ValueError("a demo race needs at least 3 laps")
        rng = random.Random(seed)
        self.title = "DEMO GP"
        self.notice = "FICTIONAL DEMO DATA"
        self.total_laps = laps
        self.drivers = DEMO_DRIVERS
        self.track = make_track(rng)
        self._line = Polyline(self.track)

        cx = sum(p[0] for p in self.track) / len(self.track)
        cy = sum(p[1] for p in self.track) / len(self.track)
        sx, sy = self._line.at(0.0)
        self._pit_point = (sx + (cx - sx) * 0.12, sy + (cy - sy) * 0.12)

        retiree = rng.randrange(2, len(self.drivers))
        timelines = [
            self._simulate(rng, drv, grid, laps, retire=(grid == retiree))
            for grid, drv in enumerate(self.drivers)
        ]
        self._finish(timelines, laps)
        self._timelines = {tl.driver.code: tl for tl in timelines}
        self.start_time = 0.0
        self.end_time = max(tl.finish_time for tl in timelines if tl.finish_time is not None)

    @staticmethod
    def _simulate(rng: random.Random, drv: Driver, grid: int, laps: int, retire: bool) -> _Timeline:
        base = 88.0 + grid * 0.12 + rng.uniform(0.0, 0.6)
        degradation = rng.uniform(0.08, 0.16)  # seconds lost per lap on old tyres
        pit_lap = rng.randint(laps // 3, 2 * laps // 3)
        retire_lap = rng.randint(laps // 4 + 1, 3 * laps // 4) if retire else None

        tl = _Timeline(drv)
        t, d, tyre_age = 0.0, -GRID_GAP * grid, 0
        for lap in range(1, laps + 1):
            lap_time = base + degradation * tyre_age + rng.gauss(0.0, 0.35) + (2.5 if lap == 1 else 0.0)
            if lap == retire_lap:
                stop = lap - 1 + rng.uniform(0.2, 0.8)
                t_stop = t + lap_time * (stop - d)
                tl.segments.append(_Segment(t, t_stop, d, stop, Status.RUNNING))
                tl.retire_time = t_stop
                return tl
            t_end = t + lap_time * (lap - d)
            tl.segments.append(_Segment(t, t_end, d, float(lap), Status.RUNNING))
            t, d, tyre_age = t_end, float(lap), tyre_age + 1
            if lap == pit_lap:
                tl.segments.append(_Segment(t, t + PIT_LOSS, d, d, Status.PIT))
                t, tyre_age = t + PIT_LOSS, 0
        return tl

    @staticmethod
    def _finish(timelines: list[_Timeline], laps: int) -> None:
        """Apply the chequered flag: once the winner finishes, everyone else
        finishes the next time they cross the line."""
        flag = min(tl.time_at(laps) for tl in timelines if tl.retire_time is None)
        for tl in timelines:
            if tl.retire_time is not None and tl.retire_time <= flag:
                continue
            d_at_flag, _ = tl.distance_at(flag)
            target = min(laps, math.floor(d_at_flag) + 1)
            if tl.segments[-1].d1 < target:
                continue  # retires after the flag, before reaching the line
            kept = []
            for s in tl.segments:
                kept.append(s)
                if s.d1 >= target and s.d1 > s.d0:
                    break
            tl.segments = kept
            tl.finish_time = kept[-1].t1
            tl.retire_time = None

    def state_at(self, t: float) -> list[CarState]:
        rows = []
        for tl in self._timelines.values():
            d, status = tl.distance_at(t)
            if status is Status.FINISHED:
                reached = tl.finish_time
            elif status is Status.RETIRED:
                reached = tl.retire_time
            else:
                reached = t
            rows.append((tl, d, status, reached))
        rows.sort(key=lambda r: (r[2] is Status.RETIRED, -r[1], r[3]))

        leader_tl, leader_d = rows[0][0], rows[0][1]
        states = []
        for i, (tl, d, status, reached) in enumerate(rows):
            x, y = self._pit_point if status is Status.PIT else self._line.at(d)
            gap, laps_behind = None, 0
            if i > 0 and status is not Status.RETIRED:
                laps_behind = max(0, math.floor(leader_d - d + 1e-9))
                leader_t = leader_tl.time_at(d)
                gap = max(0.0, reached - leader_t) if leader_t is not None else None
            states.append(CarState(tl.driver.code, x, y, d, status, gap, laps_behind))
        return states
