"""Runs the collectors and writes their results into the store."""

from __future__ import annotations

import re
import threading
import time
from pathlib import Path
from typing import Any

from .config import BUILTIN_TOOLS, Config, clean_text
from .store import Store
from .tools import claude_code, codex, desktop, minimax
from .tools.common import ChatData, CollectorError, active_seconds_by_day, to_epoch, to_float

DAY_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
PLAN_PROVIDERS = {"claude": "claude_web", "codex": "codex", "minimax": "minimax"}
MINIMAX_API_EVERY = 300  # seconds


def _write_chats(store: Store, tool: str, chats: list[ChatData], idle_cap: float) -> int:
    merged: dict[str, ChatData] = {}
    for c in chats:
        if c.chat_id in merged:
            merged[c.chat_id].merge(c)
        else:
            merged[c.chat_id] = ChatData(c.chat_id, c.title, c.project, list(c.stamps), dict(c.tokens), dict(c.turns))
    rows = []
    for c in merged.values():
        per_day = active_seconds_by_day(c.stamps, idle_cap)
        days = set(per_day) | set(c.tokens) | set(c.turns)
        for d in days:
            rows.append((c.chat_id, d, per_day.get(d, 0.0), c.tokens.get(d, 0), c.turns.get(d, 0)))
        store.upsert_chat(tool, c.chat_id, c.title, c.project, float(max(c.stamps)) if c.stamps else 0.0)
    store.replace_local_activity(tool, rows)
    return len(merged)


class Collector:
    def __init__(self, store: Store, config: Config) -> None:
        self.store = store
        self.config = config
        self._lock = threading.Lock()
        self._last_minimax_api = 0.0

    # ---- local transcripts ----------------------------------------------------
    def _cached_parse(self, path: Path, parser):
        try:
            st = path.stat()
        except OSError:
            return None
        key = str(path)
        cached = self.store.cache_get(key, st.st_mtime, st.st_size)
        if cached is not None:
            return cached
        try:
            data = parser(path)
        except OSError:
            return None
        self.store.cache_put(key, st.st_mtime, st.st_size, data)
        return data

    def collect_claude_code(self, idle_cap: float) -> None:
        paths = claude_code.files()
        if not paths:
            self.store.set_status("claude_code", {"ok": False, "message": "No Claude Code transcripts on this PC"})
            return
        chats: list[ChatData] = []
        for p in paths:
            data = self._cached_parse(p, lambda q: [c.to_json() for c in claude_code.parse_file(q)])
            for c in data or []:
                chats.append(ChatData.from_json(c))
        n = _write_chats(self.store, "claude_code", chats, idle_cap)
        self.store.set_status("claude_code", {"ok": True, "message": f"{n} sessions on this PC"})

    def collect_codex(self, idle_cap: float) -> None:
        paths = codex.files()
        if not paths:
            self.store.set_status("codex", {"ok": False, "message": "Codex CLI not used on this PC"})
            return
        chats: list[ChatData] = []
        newest: dict[str, Any] | None = None

        def parse(q: Path):
            cs, lim = codex.parse_file(q)
            return {"chats": [c.to_json() for c in cs], "limits": lim}

        for p in paths:
            data = self._cached_parse(p, parse)
            if not data:
                continue
            chats.extend(ChatData.from_json(c) for c in data.get("chats", []))
            lim = data.get("limits")
            if lim and (newest is None or lim["ts"] > newest["ts"]):
                newest = lim
        n = _write_chats(self.store, "codex", chats, idle_cap)
        status: dict[str, Any] = {"ok": True, "message": f"{n} sessions on this PC"}
        if newest:
            windows, plan = codex.plan_windows(newest)
            if windows:
                self.store.set_plan("codex", windows)
            status["plan"] = plan
        self.store.set_status("codex", status)

    def collect_minimax(self, idle_cap: float) -> None:
        if not minimax.installed():
            self.store.set_status("minimax", {"ok": False, "message": "MiniMax Code not found on this PC"})
            return
        status: dict[str, Any] = {"ok": True}
        try:
            n = _write_chats(self.store, "minimax", minimax.ledger_chats(), idle_cap)
            status["message"] = f"{n} chats"
        except CollectorError as exc:
            status.update(ok=False, message=str(exc))
        if time.time() - self._last_minimax_api >= MINIMAX_API_EVERY:
            self._last_minimax_api = time.time()
            try:
                windows, account = minimax.fetch_account()
                if windows:
                    self.store.set_plan("minimax", windows)
                status.update(account)
            except CollectorError as exc:
                status["account_error"] = str(exc)
        else:
            prev = self.store.statuses().get("minimax", {})
            for k in ("credits_remaining", "subscription_type", "has_token_plan", "plan_error",
                      "credit_error", "account_error"):
                if k in prev:
                    status[k] = prev[k]
        self.store.set_status("minimax", status)

    def run_local(self, force_api: bool = False) -> None:
        with self._lock:
            if force_api:
                self._last_minimax_api = 0.0
            idle_cap = self.config.get()["idle_cap_minutes"] * 60
            for fn in (self.collect_claude_code, self.collect_codex, self.collect_minimax):
                try:
                    fn(idle_cap)
                except Exception as exc:  # one broken tool must not stop the others
                    tool = fn.__name__.replace("collect_", "")
                    self.store.set_status(tool, {"ok": False, "message": f"error: {type(exc).__name__}"})

    # ---- browser extension ---------------------------------------------------------
    def ingest(self, payload: dict[str, Any]) -> dict[str, int]:
        cfg = self.config.get()
        allowed = {t for t, v in BUILTIN_TOOLS.items() if v["kind"] == "browser"}
        allowed |= {t["id"] for t in cfg["custom_tools"] if t["sites"]}
        source = clean_text(payload.get("source"), 64) or "browser"
        source = "ext:" + re.sub(r"[^A-Za-z0-9_-]", "", source)[:48]
        accepted = 0
        for item in (payload.get("time") or [])[:2000]:
            if not isinstance(item, dict):
                continue
            tool = item.get("tool")
            day = item.get("day")
            chat_id = clean_text(item.get("chat_id"), 200)
            secs = to_float(item.get("seconds"))
            if tool not in allowed or not isinstance(day, str) or not DAY_RE.fullmatch(day) or not chat_id:
                continue
            if secs is None or secs < 0:
                continue
            secs = min(secs, 86400.0)
            self.store.set_activity(tool, chat_id, day, source, secs)
            self.store.upsert_chat(tool, chat_id, clean_text(item.get("title"), 200),
                                   clean_text(item.get("project"), 200), time.time())
            accepted += 1
        plans = 0
        for p in (payload.get("plans") or [])[:10]:
            if not isinstance(p, dict) or p.get("provider") not in ("claude",):
                continue
            windows = []
            for w in (p.get("windows") or [])[:12]:
                if not isinstance(w, dict):
                    continue
                key = re.sub(r"[^a-z0-9_]", "", str(w.get("key", "")).lower())[:40]
                used = to_float(w.get("used_pct"))
                if not key or used is None:
                    continue
                windows.append({"key": key, "label": clean_text(w.get("label") or key, 40),
                                "used_pct": max(0.0, min(100.0, used)),
                                "resets_at": to_epoch(w.get("resets_at"))})
            if windows:
                self.store.set_plan(p["provider"], windows)
                self.store.set_status("claude_web", {"ok": True, "message": "plan usage from claude.ai"})
                plans += 1
        if accepted:
            self.store.set_status("browser_extension", {"ok": True, "message": "connected"})
        return {"time": accepted, "plans": plans}

    # ---- desktop apps (Windows) ---------------------------------------------------
    def desktop_tick(self, interval: float) -> None:
        cfg = self.config.get()
        apps = {a: t["id"] for t in cfg["custom_tools"] for a in t["apps"]}
        if not apps:
            return
        fg = desktop.sample()
        if fg is None or fg.exe not in apps:
            return
        if fg.idle_seconds > cfg["idle_cap_minutes"] * 60:
            return
        tool = apps[fg.exe]
        chat = desktop.chat_key(fg.title)
        day = time.strftime("%Y-%m-%d")
        self.store.add_activity(tool, chat, day, "desktop", interval)
        self.store.upsert_chat(tool, chat, chat, "", time.time())
