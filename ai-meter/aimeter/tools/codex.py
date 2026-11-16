"""OpenAI Codex CLI on this PC: ~/.codex/sessions rollouts.

Codex records the ChatGPT plan's rate-limit windows (5-hour / weekly) in
its rollouts, so this is also where a ChatGPT usage % can come from.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ..paths import HOME
from .common import ChatData, first_text, local_day, to_epoch, to_float, to_int

TOOL_ID = "codex"


def root() -> Path:
    return Path(os.environ.get("CODEX_HOME") or HOME / ".codex")


def files() -> list[Path]:
    out: list[Path] = []
    for sub in ("sessions", "archived_sessions"):
        d = root() / sub
        if d.is_dir():
            out.extend(p for p in d.rglob("*.jsonl") if p.is_file())
    return out


def _window_label(minutes: Any, fallback: str) -> tuple[str, str]:
    m = to_int(minutes)
    if m == 300:
        return "five_hour", "5-hour window"
    if m == 10080:
        return "weekly", "Weekly"
    if m:
        hours = m / 60
        return f"w{m}", f"{hours:g}-hour window" if hours < 48 else f"{hours / 24:g}-day window"
    return fallback, "5-hour window" if fallback == "five_hour" else "Weekly"


def parse_file(path: Path) -> tuple[list[ChatData], dict[str, Any] | None]:
    """Returns the chat plus the newest rate-limit snapshot in the file."""
    chat = ChatData(path.stem)
    limits: dict[str, Any] | None = None
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line[0] != "{":
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict):
                continue
            payload = rec.get("payload") if isinstance(rec.get("payload"), dict) else {}
            ts = to_epoch(rec.get("timestamp"))
            if rec.get("type") == "session_meta":
                chat.chat_id = str(payload.get("id") or chat.chat_id)
                if isinstance(payload.get("cwd"), str):
                    chat.project = payload["cwd"]
                continue
            if ts is None:
                continue
            chat.stamps.append(int(ts))
            if rec.get("type") != "event_msg":
                continue
            day = local_day(ts)
            ptype = payload.get("type")
            if ptype == "user_message":
                chat.turns[day] = chat.turns.get(day, 0) + 1
                if not chat.title:
                    chat.title = first_text(payload.get("message"))
            elif ptype == "token_count":
                info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
                last = info.get("last_token_usage") if isinstance(info.get("last_token_usage"), dict) else {}
                n = to_int(last.get("total_tokens")) or (to_int(last.get("input_tokens")) + to_int(last.get("output_tokens")))
                chat.tokens[day] = chat.tokens.get(day, 0) + n
                rl = payload.get("rate_limits")
                if isinstance(rl, dict):
                    limits = {"ts": ts, "raw": rl}
    return ([chat] if chat.stamps else []), limits


def plan_windows(snapshot: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    raw, ts = snapshot["raw"], snapshot["ts"]
    windows = []
    for name, fallback in (("primary", "five_hour"), ("secondary", "weekly")):
        w = raw.get(name)
        if not isinstance(w, dict):
            continue
        used = to_float(w.get("used_percent"))
        if used is None:
            continue
        key, label = _window_label(w.get("window_minutes"), fallback)
        resets = to_epoch(w.get("resets_at"))
        if resets is None and to_float(w.get("resets_in_seconds")) is not None:
            resets = ts + float(w["resets_in_seconds"])
        windows.append({"key": key, "label": label, "used_pct": max(0.0, min(100.0, used)), "resets_at": resets})
    plan = str(raw.get("plan_type") or "")
    return windows, plan
