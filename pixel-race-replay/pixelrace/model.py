"""Data model shared by every race source and the renderer.

A race source (the fictional demo today, real timing data later) only has to
satisfy the ``RaceSource`` protocol. The renderer never knows where the data
came from.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Sequence

RGB = tuple[int, int, int]
Point = tuple[float, float]


class Status(str, Enum):
    RUNNING = "running"
    PIT = "pit"
    FINISHED = "finished"
    RETIRED = "retired"


@dataclass(frozen=True)
class Driver:
    code: str  # three-letter code shown on the leaderboard
    name: str
    color: RGB


@dataclass(frozen=True)
class CarState:
    code: str
    x: float  # world coordinates, same space as RaceSource.track
    y: float
    distance: float  # laps completed, including the fraction of the current lap
    status: Status
    gap: float | None  # seconds behind the leader; None for the leader
    laps_behind: int = 0  # > 0 when lapped; the gap is then shown in laps


class RaceSource(Protocol):
    title: str
    notice: str  # small print in the corner, e.g. a data-source credit
    total_laps: int
    drivers: Sequence[Driver]
    # Closed centreline in world coordinates, in racing direction, with
    # track[0] on the start/finish line.
    track: Sequence[Point]
    start_time: float  # seconds
    end_time: float  # seconds, when the last classified car takes the flag

    def state_at(self, t: float) -> list[CarState]:
        """Every car at race time ``t``, ordered by race position (P1 first)."""
        ...
