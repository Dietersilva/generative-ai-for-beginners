"""Settings stored as JSON in the user's own profile folder.

Holds subscriptions (what you pay per month and which tools it covers),
custom tools, job rules and the pairing token for the browser extension.
"""

from __future__ import annotations

import copy
import json
import os
import re
import secrets
import sys
import threading
from pathlib import Path
from typing import Any

from .paths import config_dir, ensure_private_dir

DEFAULT_PORT = 47821

# Built-in tools. "kind" says where the data comes from.
BUILTIN_TOOLS: dict[str, dict[str, str]] = {
    "claude_web": {"name": "Claude (browser)", "kind": "browser"},
    "claude_code": {"name": "Claude Code (this PC)", "kind": "local"},
    "chatgpt_web": {"name": "ChatGPT (browser)", "kind": "browser"},
    "codex": {"name": "Codex CLI (this PC)", "kind": "local"},
    "minimax": {"name": "MiniMax Code", "kind": "local"},
}

DEFAULTS: dict[str, Any] = {
    "version": 2,
    "port": DEFAULT_PORT,
    "token": "",
    "idle_cap_minutes": 5,
    "currency": "USD",
    "subscriptions": [
        {"id": "claude", "name": "Claude", "monthly_cost": 0.0,
         "tools": ["claude_web", "claude_code"], "basis": "time"},
        {"id": "chatgpt", "name": "ChatGPT Work", "monthly_cost": 0.0,
         "tools": ["chatgpt_web", "codex"], "basis": "time"},
        {"id": "minimax", "name": "MiniMax Code", "monthly_cost": 0.0,
         "tools": ["minimax"], "basis": "time"},
    ],
    "custom_tools": [],
    "rules": [],
    "home_folder_is_unassigned": True,
    "overlay": {"x": None, "y": None, "collapsed": False},
}

_ID_RE = re.compile(r"[^a-z0-9_]+")
MAX_NAME = 80


def clean_text(value: Any, limit: int = MAX_NAME) -> str:
    text = str(value if value is not None else "").replace("\x00", "")
    text = " ".join(text.split())
    return text[:limit]


def make_id(name: str, prefix: str = "") -> str:
    base = _ID_RE.sub("_", name.lower()).strip("_")[:32] or "item"
    return f"{prefix}{base}"


def _clean_domain(d: Any) -> str | None:
    d = clean_text(d, 253).lower()
    d = re.sub(r"^https?://", "", d).split("/")[0].split(":")[0]
    if d.startswith("*."):
        d = d[2:]
    if re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)+", d):
        return d
    return None


def _clean_app(a: Any) -> str | None:
    a = clean_text(a, 120)
    a = a.replace("\\", "/").split("/")[-1]
    if re.fullmatch(r"[\w .()+-]+", a or ""):
        return a.lower()
    return None


def _num(v: Any, default: float = 0.0, lo: float = 0.0, hi: float = 1e6) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    if f != f:  # NaN
        return default
    return max(lo, min(hi, f))


def sanitize(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate a config dict (from disk or from the dashboard)."""
    cfg = copy.deepcopy(DEFAULTS)
    if not isinstance(raw, dict):
        return cfg
    cfg["port"] = int(_num(raw.get("port"), DEFAULT_PORT, 1024, 65535))
    tok = raw.get("token")
    if isinstance(tok, str) and re.fullmatch(r"[A-Za-z0-9_-]{24,128}", tok):
        cfg["token"] = tok
    cfg["idle_cap_minutes"] = _num(raw.get("idle_cap_minutes"), 5, 1, 60)
    cfg["currency"] = clean_text(raw.get("currency") or "USD", 8) or "USD"
    cfg["home_folder_is_unassigned"] = bool(raw.get("home_folder_is_unassigned", True))

    customs = []
    seen_ids: set[str] = set(BUILTIN_TOOLS)
    for t in raw.get("custom_tools") or []:
        if not isinstance(t, dict):
            continue
        name = clean_text(t.get("name"))
        if not name:
            continue
        tid = t.get("id") if isinstance(t.get("id"), str) and t["id"].startswith("custom_") else make_id(name, "custom_")
        tid = _ID_RE.sub("_", tid.lower())[:48]
        while tid in seen_ids:
            tid += "_2"
        seen_ids.add(tid)
        sites = [d for d in (_clean_domain(x) for x in (t.get("sites") or [])[:20]) if d]
        apps = [a for a in (_clean_app(x) for x in (t.get("apps") or [])[:20]) if a]
        customs.append({"id": tid, "name": name, "sites": sites, "apps": apps})
    cfg["custom_tools"] = customs

    known_tools = set(BUILTIN_TOOLS) | {t["id"] for t in customs}
    subs = []
    sub_ids: set[str] = set()
    claimed: set[str] = set()
    raw_subs = raw.get("subscriptions")
    if not isinstance(raw_subs, list):
        raw_subs = DEFAULTS["subscriptions"]
    for s in raw_subs[:30]:
        if not isinstance(s, dict):
            continue
        name = clean_text(s.get("name"))
        if not name:
            continue
        sid = s.get("id") if isinstance(s.get("id"), str) else make_id(name)
        sid = _ID_RE.sub("_", sid.lower())[:48] or make_id(name)
        while sid in sub_ids:
            sid += "_2"
        sub_ids.add(sid)
        tools = []
        for tool in s.get("tools") or []:
            # A tool can only belong to one subscription, otherwise its time
            # would be paid for twice.
            if tool in known_tools and tool not in claimed:
                tools.append(tool)
                claimed.add(tool)
        basis = s.get("basis") if s.get("basis") in ("time", "tokens") else "time"
        subs.append({"id": sid, "name": name,
                     "monthly_cost": round(_num(s.get("monthly_cost")), 2),
                     "tools": tools, "basis": basis})
    cfg["subscriptions"] = subs

    rules = []
    for r in (raw.get("rules") or [])[:500]:
        if not isinstance(r, dict):
            continue
        contains = clean_text(r.get("contains"), 120)
        job = clean_text(r.get("job"))
        if not contains or not job:
            continue
        field = r.get("field") if r.get("field") in ("any", "project", "title") else "any"
        tool = r.get("tool") if r.get("tool") in known_tools else ""
        rules.append({"contains": contains, "job": job, "field": field, "tool": tool})
    cfg["rules"] = rules

    ov = raw.get("overlay") if isinstance(raw.get("overlay"), dict) else {}
    cfg["overlay"] = {
        "x": int(ov["x"]) if isinstance(ov.get("x"), (int, float)) else None,
        "y": int(ov["y"]) if isinstance(ov.get("y"), (int, float)) else None,
        "collapsed": bool(ov.get("collapsed", False)),
    }
    return cfg


class Config:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (config_dir() / "config.json")
        self._lock = threading.RLock()
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        raw: dict[str, Any] = {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raw = {}
        cfg = sanitize(raw)
        if not cfg["token"]:
            cfg["token"] = secrets.token_urlsafe(24)
            self.data = cfg
            self.save()
        return cfg

    def get(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self.data)

    def update(self, patch: dict[str, Any]) -> dict[str, Any]:
        """Apply settings from the dashboard. Token and port are never changed here."""
        with self._lock:
            merged = copy.deepcopy(self.data)
            for key in ("subscriptions", "custom_tools", "rules", "idle_cap_minutes",
                        "currency", "home_folder_is_unassigned", "overlay"):
                if key in patch:
                    merged[key] = patch[key]
            cleaned = sanitize(merged)
            cleaned["token"] = self.data["token"]
            cleaned["port"] = self.data["port"]
            self.data = cleaned
            self.save()
            return copy.deepcopy(self.data)

    def save(self) -> None:
        with self._lock:
            ensure_private_dir(self.path.parent)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
            if sys.platform != "win32":
                os.chmod(tmp, 0o600)
            os.replace(tmp, self.path)

    def tool_names(self) -> dict[str, str]:
        names = {k: v["name"] for k, v in BUILTIN_TOOLS.items()}
        for t in self.data["custom_tools"]:
            names[t["id"]] = t["name"]
        return names
