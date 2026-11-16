"""SQLite storage for activity, plan usage and per-chat job assignments."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Iterable

from .paths import data_dir, ensure_private_dir

SCHEMA = """
CREATE TABLE IF NOT EXISTS chats (
    tool TEXT NOT NULL, chat_id TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '', project TEXT NOT NULL DEFAULT '',
    last_ts REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (tool, chat_id)
);
CREATE TABLE IF NOT EXISTS activity (
    tool TEXT NOT NULL, chat_id TEXT NOT NULL, day TEXT NOT NULL,
    source TEXT NOT NULL, seconds REAL NOT NULL DEFAULT 0,
    tokens INTEGER NOT NULL DEFAULT 0, turns INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (tool, chat_id, day, source)
);
CREATE INDEX IF NOT EXISTS activity_day ON activity(day);
CREATE TABLE IF NOT EXISTS overrides (
    tool TEXT NOT NULL, chat_id TEXT NOT NULL, job TEXT NOT NULL,
    PRIMARY KEY (tool, chat_id)
);
CREATE TABLE IF NOT EXISTS plans (
    provider TEXT NOT NULL, window_key TEXT NOT NULL, label TEXT NOT NULL,
    used_pct REAL, resets_at REAL, observed_at REAL NOT NULL,
    PRIMARY KEY (provider, window_key)
);
CREATE TABLE IF NOT EXISTS plan_history (
    provider TEXT NOT NULL, window_key TEXT NOT NULL,
    used_pct REAL NOT NULL, observed_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS plan_history_t ON plan_history(provider, observed_at);
CREATE TABLE IF NOT EXISTS status (
    provider TEXT PRIMARY KEY, data TEXT NOT NULL, updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS file_cache (
    path TEXT PRIMARY KEY, mtime REAL NOT NULL, size INTEGER NOT NULL, data TEXT NOT NULL
);
"""


class Store:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (data_dir() / "aimeter.db")
        ensure_private_dir(self.path.parent)
        self._lock = threading.RLock()
        self.con = sqlite3.connect(str(self.path), check_same_thread=False, timeout=10)
        self.con.execute("PRAGMA journal_mode=WAL")
        self.con.executescript(SCHEMA)
        self.con.commit()

    # ---- generic helpers -------------------------------------------------
    def query(self, sql: str, args: Iterable[Any] = ()) -> list[tuple]:
        with self._lock:
            return self.con.execute(sql, tuple(args)).fetchall()

    def close(self) -> None:
        with self._lock:
            self.con.close()

    # ---- chats / activity -------------------------------------------------
    def upsert_chat(self, tool: str, chat_id: str, title: str, project: str, last_ts: float) -> None:
        with self._lock:
            self.con.execute(
                """INSERT INTO chats(tool, chat_id, title, project, last_ts) VALUES (?,?,?,?,?)
                   ON CONFLICT(tool, chat_id) DO UPDATE SET
                     title = CASE WHEN excluded.title != '' THEN excluded.title ELSE chats.title END,
                     project = CASE WHEN excluded.project != '' THEN excluded.project ELSE chats.project END,
                     last_ts = MAX(chats.last_ts, excluded.last_ts)""",
                (tool, chat_id, title, project, last_ts))
            self.con.commit()

    def replace_local_activity(self, tool: str, rows: list[tuple[str, str, float, int, int]]) -> None:
        """Replace all locally computed rows for one tool: (chat_id, day, seconds, tokens, turns)."""
        with self._lock:
            self.con.execute("DELETE FROM activity WHERE tool = ? AND source = 'local'", (tool,))
            self.con.executemany(
                "INSERT INTO activity(tool, chat_id, day, source, seconds, tokens, turns) VALUES (?,?,?,'local',?,?,?)",
                [(tool, c, d, s, tk, tu) for c, d, s, tk, tu in rows])
            self.con.commit()

    def set_activity(self, tool: str, chat_id: str, day: str, source: str, seconds: float) -> None:
        """Absolute value (idempotent): used for totals reported by the browser extension."""
        with self._lock:
            self.con.execute(
                """INSERT INTO activity(tool, chat_id, day, source, seconds) VALUES (?,?,?,?,?)
                   ON CONFLICT(tool, chat_id, day, source) DO UPDATE SET seconds = MAX(activity.seconds, excluded.seconds)""",
                (tool, chat_id, day, source, seconds))
            self.con.commit()

    def add_activity(self, tool: str, chat_id: str, day: str, source: str, seconds: float) -> None:
        with self._lock:
            self.con.execute(
                """INSERT INTO activity(tool, chat_id, day, source, seconds) VALUES (?,?,?,?,?)
                   ON CONFLICT(tool, chat_id, day, source) DO UPDATE SET seconds = activity.seconds + excluded.seconds""",
                (tool, chat_id, day, source, seconds))
            self.con.commit()

    def activity_between(self, first_day: str, last_day: str) -> list[dict[str, Any]]:
        rows = self.query(
            """SELECT a.tool, a.chat_id, SUM(a.seconds), SUM(a.tokens), SUM(a.turns),
                      COALESCE(c.title, ''), COALESCE(c.project, ''), COALESCE(c.last_ts, 0)
               FROM activity a LEFT JOIN chats c ON c.tool = a.tool AND c.chat_id = a.chat_id
               WHERE a.day >= ? AND a.day <= ?
               GROUP BY a.tool, a.chat_id""", (first_day, last_day))
        return [{"tool": r[0], "chat_id": r[1], "seconds": r[2] or 0.0, "tokens": r[3] or 0,
                 "turns": r[4] or 0, "title": r[5], "project": r[6], "last_ts": r[7]} for r in rows]

    def seconds_by_tool_day(self, first_day: str, last_day: str) -> list[tuple[str, str, float]]:
        return self.query(
            "SELECT tool, day, SUM(seconds) FROM activity WHERE day >= ? AND day <= ? GROUP BY tool, day",
            (first_day, last_day))

    # ---- job overrides ------------------------------------------------------
    def overrides(self) -> dict[tuple[str, str], str]:
        return {(t, c): j for t, c, j in self.query("SELECT tool, chat_id, job FROM overrides")}

    def set_override(self, tool: str, chat_id: str, job: str) -> None:
        with self._lock:
            if job:
                self.con.execute(
                    "INSERT INTO overrides(tool, chat_id, job) VALUES (?,?,?) "
                    "ON CONFLICT(tool, chat_id) DO UPDATE SET job = excluded.job", (tool, chat_id, job))
            else:
                self.con.execute("DELETE FROM overrides WHERE tool = ? AND chat_id = ?", (tool, chat_id))
            self.con.commit()

    # ---- plan usage -------------------------------------------------------
    def set_plan(self, provider: str, windows: list[dict[str, Any]]) -> None:
        now = time.time()
        with self._lock:
            for w in windows:
                key = str(w["key"])
                prev = self.con.execute(
                    "SELECT used_pct, observed_at FROM plans WHERE provider = ? AND window_key = ?",
                    (provider, key)).fetchone()
                self.con.execute(
                    """INSERT INTO plans(provider, window_key, label, used_pct, resets_at, observed_at)
                       VALUES (?,?,?,?,?,?) ON CONFLICT(provider, window_key) DO UPDATE SET
                       label = excluded.label, used_pct = excluded.used_pct,
                       resets_at = excluded.resets_at, observed_at = excluded.observed_at""",
                    (provider, key, w["label"], w.get("used_pct"), w.get("resets_at"), now))
                used = w.get("used_pct")
                if used is not None and (prev is None or prev[0] != used or now - prev[1] > 900):
                    self.con.execute(
                        "INSERT INTO plan_history(provider, window_key, used_pct, observed_at) VALUES (?,?,?,?)",
                        (provider, key, used, now))
            self.con.commit()

    def plans(self) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {}
        for p, k, label, used, resets, obs in self.query(
                "SELECT provider, window_key, label, used_pct, resets_at, observed_at FROM plans ORDER BY provider, window_key DESC"):
            out.setdefault(p, []).append(
                {"key": k, "label": label, "used_pct": used, "resets_at": resets, "observed_at": obs})
        return out

    def plan_peak(self, provider: str, key: str, since: float, until: float) -> float | None:
        row = self.query(
            "SELECT MAX(used_pct) FROM plan_history WHERE provider = ? AND window_key = ? AND observed_at >= ? AND observed_at < ?",
            (provider, key, since, until))
        return row[0][0] if row and row[0][0] is not None else None

    # ---- provider status ----------------------------------------------------
    def set_status(self, provider: str, data: dict[str, Any]) -> None:
        with self._lock:
            self.con.execute(
                "INSERT INTO status(provider, data, updated_at) VALUES (?,?,?) "
                "ON CONFLICT(provider) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at",
                (provider, json.dumps(data), time.time()))
            self.con.commit()

    def statuses(self) -> dict[str, dict[str, Any]]:
        out = {}
        for p, d, t in self.query("SELECT provider, data, updated_at FROM status"):
            try:
                v = json.loads(d)
            except ValueError:
                v = {}
            v["updated_at"] = t
            out[p] = v
        return out

    # ---- parse cache for transcript files -------------------------------------
    def cache_get(self, path: str, mtime: float, size: int) -> Any | None:
        row = self.query("SELECT mtime, size, data FROM file_cache WHERE path = ?", (path,))
        if row and row[0][0] == mtime and row[0][1] == size:
            try:
                return json.loads(row[0][2])
            except ValueError:
                return None
        return None

    def cache_put(self, path: str, mtime: float, size: int, data: Any) -> None:
        with self._lock:
            self.con.execute(
                "INSERT INTO file_cache(path, mtime, size, data) VALUES (?,?,?,?) "
                "ON CONFLICT(path) DO UPDATE SET mtime = excluded.mtime, size = excluded.size, data = excluded.data",
                (path, mtime, size, json.dumps(data)))
            self.con.commit()
