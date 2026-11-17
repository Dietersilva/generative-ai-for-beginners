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

# The three built-in plans. Their tools are fixed so a tool can never be
# filed under the wrong subscription.
BUILTIN_PLANS: list[dict[str, Any]] = [
    {"id": "claude", "name": "Claude", "tools": ["claude_web", "claude_code"]},
    {"id": "chatgpt", "name": "ChatGPT Work", "tools": ["chatgpt_web", "codex"]},
    {"id": "minimax", "name": "MiniMax Code", "tools": ["minimax"]},
]

DEFAULTS: dict[str, Any] = {
    "version": 3,
    "port": DEFAULT_PORT,
    "token": "",
    "idle_cap_minutes": 5,
    "currency": "USD",
    "subscriptions": [{**p, "monthly_cost": 0.0, "basis": "time"} for p in BUILTIN_PLANS],
    "custom_tools": [],
    "rules": [],
    "project_aliases": {},
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


def project_key(name: str) -> str:
    """Names that differ only in case, spaces, dashes or underscores are the same project."""
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())[:80]


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

    raw_subs = raw.get("subscriptions") if isinstance(raw.get("subscriptions"), list) else []
    by_id = {s.get("id"): s for s in raw_subs if isinstance(s, dict)}

    customs = []
    seen_ids: set[str] = set(BUILTIN_TOOLS) | {p["id"] for p in BUILTIN_PLANS}
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
        cost = t.get("monthly_cost")
        if cost is None and isinstance(by_id.get(tid), dict):  # migrate from v2
            cost = by_id[tid].get("monthly_cost")
        customs.append({"id": tid, "name": name, "sites": sites, "apps": apps,
                        "monthly_cost": round(_num(cost), 2)})
    cfg["custom_tools"] = customs

    subs = []
    for p in BUILTIN_PLANS:
        s = by_id.get(p["id"]) or {}
        subs.append({"id": p["id"], "name": clean_text(s.get("name")) or p["name"],
                     "monthly_cost": round(_num(s.get("monthly_cost")), 2),
                     "tools": list(p["tools"]),
                     "basis": s.get("basis") if s.get("basis") in ("time", "tokens") else "time"})
    for t in customs:
        subs.append({"id": t["id"], "name": t["name"], "monthly_cost": t["monthly_cost"],
                     "tools": [t["id"]], "basis": "time"})
    cfg["subscriptions"] = subs
    known_tools = set(BUILTIN_TOOLS) | {t["id"] for t in customs}

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

    aliases = {}
    raw_alias = raw.get("project_aliases") if isinstance(raw.get("project_aliases"), dict) else {}
    for k, v in list(raw_alias.items())[:1000]:
        key, target = project_key(str(k)), clean_text(v)
        if key and target and project_key(target) != key:
            aliases[key] = target
    cfg["project_aliases"] = aliases

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
        if raw and (raw.get("version") != cfg["version"] or raw.get("subscriptions") != cfg["subscriptions"]):
            self.data = cfg  # write back repaired / upgraded settings
            self.save()
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
                        "currency", "home_folder_is_unassigned", "overlay", "project_aliases"):
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
