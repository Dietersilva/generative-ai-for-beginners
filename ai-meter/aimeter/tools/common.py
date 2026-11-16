"""Shared helpers for collectors: timestamps, active-time and HTTP."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .. import __version__

TAIL_SECONDS = 60  # credit for the last event in a burst (reading the answer)


class CollectorError(Exception):
    """A readable problem to show the user (never contains secrets)."""


def to_epoch(value: Any) -> float | None:
    """Accept ISO-8601 strings, epoch seconds or epoch milliseconds."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        if v <= 0:
            return None
        return v / 1000.0 if v > 1e11 else v
    if isinstance(value, str):
        s = value.strip()
        try:
            return to_epoch(float(s))
        except ValueError:
            pass
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    return None


def local_day(epoch: float) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(epoch))


def to_int(v: Any) -> int:
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


def to_float(v: Any) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def active_seconds_by_day(stamps: list[float], idle_cap: float, tail: float = TAIL_SECONDS) -> dict[str, float]:
    """Estimate engaged time from event timestamps.

    Each event is credited with the gap to the next event when that gap is
    shorter than ``idle_cap`` (you were still working); otherwise it gets a
    short ``tail`` (you read the reply and walked away). Duplicate
    timestamps from parallel sub-agents are merged, so parallel work is
    never counted twice.
    """
    out: dict[str, float] = {}
    pts = sorted(set(int(s) for s in stamps if s))
    for i, t in enumerate(pts):
        gap = pts[i + 1] - t if i + 1 < len(pts) else None
        credit = gap if gap is not None and gap <= idle_cap else min(tail, idle_cap)
        day = local_day(t)
        out[day] = out.get(day, 0.0) + float(credit)
    return out


@dataclass
class ChatData:
    chat_id: str
    title: str = ""
    project: str = ""          # folder path or project name
    stamps: list[float] = field(default_factory=list)
    tokens: dict[str, int] = field(default_factory=dict)  # day -> tokens
    turns: dict[str, int] = field(default_factory=dict)   # day -> turns

    def merge(self, other: "ChatData") -> None:
        self.title = self.title or other.title
        self.project = self.project or other.project
        self.stamps.extend(other.stamps)
        for d, n in other.tokens.items():
            self.tokens[d] = self.tokens.get(d, 0) + n
        for d, n in other.turns.items():
            self.turns[d] = self.turns.get(d, 0) + n

    def to_json(self) -> dict[str, Any]:
        return {"chat_id": self.chat_id, "title": self.title, "project": self.project,
                "stamps": self.stamps, "tokens": self.tokens, "turns": self.turns}

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> "ChatData":
        return cls(d["chat_id"], d.get("title", ""), d.get("project", ""), list(d.get("stamps", [])),
                   dict(d.get("tokens", {})), dict(d.get("turns", {})))


def first_text(content: Any, limit: int = 90) -> str:
    """Pull a readable title out of a chat message body."""
    text = ""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") in ("text", "input_text") and isinstance(block.get("text"), str):
                text = block["text"]
                break
    text = " ".join(text.split())
    if not text or text.startswith("<"):
        return ""
    return text[:limit]


def http_json(url: str, *, method: str = "GET", headers: dict[str, str] | None = None,
              timeout: float = 15.0) -> dict[str, Any]:
    if not url.startswith("https://"):
        raise CollectorError("refusing non-HTTPS request")
    h = {"Accept": "application/json", "User-Agent": f"AI-Meter/{__version__}"}
    h.update(headers or {})
    data = b"" if method == "POST" else None
    if data is not None:
        h["Content-Type"] = "application/json"
        data = b"{}"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(4_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise CollectorError("sign-in expired") from None
        raise CollectorError(f"server returned HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise CollectorError(f"network error: {getattr(exc, 'reason', exc)}") from None
    try:
        out = json.loads(body)
    except ValueError:
        raise CollectorError("unexpected response format") from None
    return out if isinstance(out, dict) else {"data": out}
