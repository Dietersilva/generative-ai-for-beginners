"""MiniMax Code desktop app.

* Plan windows + credit balance: MiniMax's own API, using the login the
  MiniMax Code app already stored on this PC. AI-Meter only READS that login
  file. It never refreshes or rewrites it, so it can't log you out of
  MiniMax Code. If the login has expired, open MiniMax Code once.
* Time and tokens per chat: MiniMax Code's local SQLite ledger, opened
  read-only.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from ..paths import HOME
from .common import ChatData, CollectorError, http_json, local_day, to_epoch, to_float, to_int

TOOL_ID = "minimax"
MINIMAX_HOME = HOME / ".minimax"
AGENT_BASE = "https://agent.minimax.io"
OPEN_API_BASE = "https://api.minimax.io"


def db_file() -> Path:
    return MINIMAX_HOME / "v2" / "sqlite" / "runtime-state.sqlite"


def installed() -> bool:
    return MINIMAX_HOME.is_dir()


def _auth_token() -> str:
    files = sorted((MINIMAX_HOME / "auth").glob("*/*/*/auth.json"))
    preferred = MINIMAX_HOME / "auth" / "prod" / "en" / "mcode-public" / "auth.json"
    if preferred in files:
        files.remove(preferred)
        files.insert(0, preferred)
    for f in files:
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        records = raw.get("records") if isinstance(raw, dict) else None
        for rec in (records or {}).values() if isinstance(records, dict) else []:
            if not isinstance(rec, dict) or not rec.get("accessToken"):
                continue
            expires = to_int(rec.get("expiresAtMs"))
            if expires and expires < time.time() * 1000:
                raise CollectorError("MiniMax login expired - open MiniMax Code to refresh it")
            return str(rec["accessToken"])
    raise CollectorError("not signed in - open MiniMax Code and log in")


def _reset_time(item: dict[str, Any], *names: str) -> float | None:
    for n in names:
        if n in item:
            v = to_epoch(item.get(n))
            if v:
                return v
    return None


def _shape(obj: Any, depth: int = 0) -> Any:
    """Field names and numbers only, for Diagnostics. Strings are reduced to
    their length so nothing sensitive can be stored or shown."""
    if depth > 4:
        return "..."
    if isinstance(obj, dict):
        return {str(k)[:60]: _shape(v, depth + 1) for k, v in list(obj.items())[:40]}
    if isinstance(obj, list):
        return [_shape(v, depth + 1) for v in obj[:5]]
    if isinstance(obj, bool) or obj is None or isinstance(obj, (int, float)):
        return obj
    return f"<text, {len(str(obj))} chars>"


def _pct(item: dict[str, Any], *prefixes: str) -> float | None:
    """used % for a window: direct percent, remaining percent, or used/total counts."""
    for k, v in item.items():
        kl = k.lower()
        if any(p in kl for p in prefixes) and "percent" in kl:
            f = to_float(v)
            if f is None:
                continue
            return max(0.0, min(100.0, 100.0 - f if "remain" in kl or "left" in kl else f))
    used = total = None
    for k, v in item.items():
        kl = k.lower()
        if not any(p in kl for p in prefixes):
            continue
        if "total" in kl or "limit" in kl:
            total = to_float(v)
        elif "usage" in kl or "used" in kl or "count" in kl:
            used = to_float(v)
    if used is not None and total:
        return max(0.0, min(100.0, 100.0 * used / total))
    return None


def _reset(item: dict[str, Any], *prefixes: str) -> float | None:
    for k, v in item.items():
        kl = k.lower()
        if any(p in kl for p in prefixes) and ("end" in kl or "reset" in kl):
            t = to_epoch(v)
            if t:
                return t
    return None


def parse_plan(raw: dict[str, Any]) -> list[dict[str, Any]]:
    data = raw.get("data") if isinstance(raw.get("data"), dict) else raw
    items = [i for i in (data.get("model_remains") or data.get("remains") or []) if isinstance(i, dict)]
    if not items and isinstance(data, dict):
        items = [data]
    windows: list[dict[str, Any]] = []
    many = len(items) > 1
    for item in items:
        prefix = f"{item.get('model_name')} " if many and item.get("model_name") else ""
        five = _pct(item, "interval", "5h", "five", "hour")
        week = _pct(item, "week")
        if five is not None:
            windows.append({"key": f"{prefix}five_hour".replace(" ", "_").lower(), "label": f"{prefix}5-hour window",
                            "used_pct": five,
                            "resets_at": _reset(item, "interval", "5h", "five", "hour") or to_epoch(item.get("end_time"))})
        if week is not None:
            windows.append({"key": f"{prefix}weekly".replace(" ", "_").lower(), "label": f"{prefix}Weekly",
                            "used_pct": week, "resets_at": _reset(item, "week")})
    return windows


def fetch_account() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Plan windows and credit balance from MiniMax's API."""
    token = _auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    windows: list[dict[str, Any]] = []
    status: dict[str, Any] = {}

    try:
        raw = http_json(f"{OPEN_API_BASE}/v1/api/openplatform/coding_plan/remains", headers=headers)
        status["plan_debug"] = _shape(raw)
        windows = parse_plan(raw)
        if not windows:
            status["plan_error"] = "MiniMax answered but sent no plan limits (see Diagnostics)"
    except CollectorError as exc:
        status["plan_error"] = f"MiniMax plan limits: {exc}"

    try:
        info = http_json(f"{AGENT_BASE}/matrix/api/v1/commerce/get_membership_info", method="POST", headers=headers)
        summary = info.get("op_credit_summary") if isinstance(info.get("op_credit_summary"), dict) else {}
        remaining = to_float(summary.get("total_remaining_amount"))
        if remaining is None:
            remaining = to_float(info.get("total_remains_credit"))
        status["credits_remaining"] = remaining
        status["subscription_type"] = info.get("subscription_type")
        status["has_token_plan"] = bool(info.get("has_token_plan"))
    except CollectorError as exc:
        status["credit_error"] = str(exc)
    return windows, status


def ledger_chats() -> list[ChatData]:
    path = db_file()
    if not path.exists():
        return []
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=5)
    try:
        cur = con.cursor()

        def cols(table: str) -> set[str]:
            return {r[1] for r in cur.execute(f"PRAGMA table_info({table})")}

        ucols = cols("local_runtime_token_usage")
        if not {"session_id", "ts"} <= ucols:
            return []
        scols = cols("local_runtime_sessions")
        pcols = cols("local_runtime_projects")

        projects: dict[str, str] = {}
        if {"project_id", "display_name"} <= pcols:
            for pid, name in cur.execute("SELECT project_id, display_name FROM local_runtime_projects"):
                if pid and name:
                    projects[str(pid)] = str(name)

        meta: dict[str, dict[str, Any]] = {}
        if "session_id" in scols:
            want = [c for c in ("session_id", "title", "workspace_dir", "project_workspace_dir",
                                "project_id", "parent_session_id") if c in scols]
            for row in cur.execute(f"SELECT {', '.join(want)} FROM local_runtime_sessions"):
                meta[str(row[0])] = dict(zip(want, row))

        def root_session(sid: str) -> str:
            seen = set()
            while sid in meta and meta[sid].get("parent_session_id") and sid not in seen:
                seen.add(sid)
                sid = str(meta[sid]["parent_session_id"])
            return sid

        tok_cols = [c for c in ("input_tokens", "output_tokens", "cache_read_tokens",
                                "cache_write_tokens", "reasoning_tokens") if c in ucols]
        tok_expr = " + ".join(f"COALESCE({c},0)" for c in tok_cols) or "0"
        chats: dict[str, ChatData] = {}
        for sid, ts, tokens in cur.execute(
                f"SELECT session_id, ts, {tok_expr} FROM local_runtime_token_usage"):
            epoch = to_epoch(ts)
            if not sid or epoch is None:
                continue
            root = root_session(str(sid))
            chat = chats.get(root)
            if chat is None:
                m = meta.get(root, {})
                project = projects.get(str(m.get("project_id") or "")) or m.get("project_workspace_dir") or m.get("workspace_dir") or ""
                chat = chats[root] = ChatData(root, str(m.get("title") or "")[:90], str(project))
            chat.stamps.append(int(epoch))
            day = local_day(epoch)
            chat.tokens[day] = chat.tokens.get(day, 0) + to_int(tokens)
            if str(sid) == root:
                chat.turns[day] = chat.turns.get(day, 0) + 1
        return list(chats.values())
    except sqlite3.Error as exc:
        raise CollectorError(f"MiniMax ledger unreadable: {exc}") from None
    finally:
        con.close()
