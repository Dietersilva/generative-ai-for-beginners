"""Turn subscription costs into a cost per job.

For each subscription:

    cost of job J = monthly cost x (time spent on J / all time spent with that subscription)

Each subscription is split on its own, so an hour on a $20 plan and an hour
on a $200 plan aren't treated as the same thing. A subscription that wasn't
used at all in the month shows up as "Unused subscription" so the totals
always add up to what you actually paid.
"""

from __future__ import annotations

import calendar
import re
import time
from datetime import date
from pathlib import PurePath, PureWindowsPath
from typing import Any

from .config import Config
from .paths import HOME
from .store import Store

UNASSIGNED = "Unassigned"
UNUSED = "Unused subscription"
_ID_LIKE = re.compile(r"^(g-p-[0-9a-f]+|[0-9a-f-]{24,})$", re.I)


def month_bounds(month: str) -> tuple[str, str, int]:
    y, m = (int(x) for x in month.split("-"))
    days = calendar.monthrange(y, m)[1]
    return f"{y:04d}-{m:02d}-01", f"{y:04d}-{m:02d}-{days:02d}", days


def current_month() -> str:
    return time.strftime("%Y-%m")


def _folder_name(project: str) -> str:
    if not project:
        return ""
    p = PureWindowsPath(project) if ("\\" in project or re.match(r"^[A-Za-z]:", project)) else PurePath(project)
    return p.name or str(p)


def _is_home(project: str) -> bool:
    try:
        norm = project.replace("\\", "/").rstrip("/").lower()
        return norm == str(HOME).replace("\\", "/").rstrip("/").lower()
    except Exception:
        return False


def assign_job(chat: dict[str, Any], cfg: dict[str, Any], overrides: dict[tuple[str, str], str]) -> tuple[str, str]:
    """Returns (job, how). how: manual | rule | folder | none."""
    key = (chat["tool"], chat["chat_id"])
    if key in overrides:
        return overrides[key], "manual"
    title = (chat.get("title") or "").lower()
    project = (chat.get("project") or "").lower()
    for r in cfg["rules"]:
        if r["tool"] and r["tool"] != chat["tool"]:
            continue
        needle = r["contains"].lower()
        hay = {"title": title, "project": project}.get(r["field"], f"{title}\n{project}")
        if needle in hay:
            return r["job"], "rule"
    proj = chat.get("project") or ""
    if proj and not _ID_LIKE.match(proj):
        if cfg.get("home_folder_is_unassigned", True) and _is_home(proj):
            return UNASSIGNED, "none"
        name = _folder_name(proj)
        if name:
            return name, "folder"
    return UNASSIGNED, "none"


def build_report(store: Store, config: Config, month: str | None = None) -> dict[str, Any]:
    cfg = config.get()
    names = config.tool_names()
    month = month or current_month()
    first, last, days_in_month = month_bounds(month)
    today = date.today()
    is_current = month == today.strftime("%Y-%m")
    days_elapsed = today.day if is_current else days_in_month

    tool_sub: dict[str, dict[str, Any]] = {}
    for s in cfg["subscriptions"]:
        for t in s["tools"]:
            tool_sub[t] = s

    overrides = store.overrides()
    chats = []
    for a in store.activity_between(first, last):
        job, how = assign_job(a, cfg, overrides)
        sub = tool_sub.get(a["tool"])
        chats.append({**a, "job": job, "job_source": how, "sub": sub["id"] if sub else None,
                      "tool_name": names.get(a["tool"], a["tool"]), "cost": 0.0})

    jobs: dict[str, dict[str, Any]] = {}

    def job_row(name: str) -> dict[str, Any]:
        return jobs.setdefault(name, {"job": name, "seconds": 0.0, "tokens": 0, "cost": 0.0,
                                      "chats": 0, "by_sub": {}})

    subs_out = []
    for s in cfg["subscriptions"]:
        mine = [c for c in chats if c["sub"] == s["id"]]
        basis = s["basis"]
        weight = (lambda c: float(c["tokens"])) if basis == "tokens" else (lambda c: float(c["seconds"]))
        total_w = sum(weight(c) for c in mine)
        if basis == "tokens" and total_w <= 0:  # no token data (e.g. browser): fall back to time
            weight = lambda c: float(c["seconds"])  # noqa: E731
            total_w = sum(weight(c) for c in mine)
        secs = sum(c["seconds"] for c in mine)
        cost = s["monthly_cost"]
        for c in mine:
            c["cost"] = cost * weight(c) / total_w if total_w > 0 else 0.0
        if total_w <= 0 and cost > 0:
            row = job_row(UNUSED)
            row["cost"] += cost
            row["by_sub"].setdefault(s["id"], {"seconds": 0.0, "cost": 0.0})["cost"] += cost
        subs_out.append({
            "id": s["id"], "name": s["name"], "monthly_cost": cost, "basis": basis,
            "tools": [{"id": t, "name": names.get(t, t)} for t in s["tools"]],
            "seconds": secs, "tokens": sum(c["tokens"] for c in mine),
            "cost_per_hour": (cost / (secs / 3600)) if secs >= 60 and cost else None,
        })

    for c in chats:
        row = job_row(c["job"])
        row["seconds"] += c["seconds"]
        row["tokens"] += c["tokens"]
        row["cost"] += c["cost"]
        row["chats"] += 1
        if c["sub"]:
            bs = row["by_sub"].setdefault(c["sub"], {"seconds": 0.0, "cost": 0.0})
            bs["seconds"] += c["seconds"]
            bs["cost"] += c["cost"]

    total_cost = sum(s["monthly_cost"] for s in cfg["subscriptions"])
    total_secs = sum(c["seconds"] for c in chats)
    job_list = sorted(jobs.values(), key=lambda j: (-j["cost"], -j["seconds"], j["job"]))
    for j in job_list:
        j["pct_cost"] = 100.0 * j["cost"] / total_cost if total_cost else 0.0
        j["pct_time"] = 100.0 * j["seconds"] / total_secs if total_secs else 0.0
        j["cost"] = round(j["cost"], 4)
    chats.sort(key=lambda c: (-c["cost"], -c["seconds"]))
    for c in chats:
        c["cost"] = round(c["cost"], 4)

    unassigned_secs = sum(c["seconds"] for c in chats if c["job"] == UNASSIGNED)
    return {
        "month": month, "currency": cfg["currency"], "is_current": is_current,
        "days_elapsed": days_elapsed, "days_in_month": days_in_month,
        "total_cost": round(total_cost, 2), "total_seconds": total_secs,
        "unassigned_pct": 100.0 * unassigned_secs / total_secs if total_secs else 0.0,
        "subscriptions": subs_out, "jobs": job_list, "chats": chats[:2000],
        "known_jobs": sorted({j["job"] for j in job_list if j["job"] not in (UNASSIGNED, UNUSED)}
                             | {r["job"] for r in cfg["rules"]}),
    }


def build_state(store: Store, config: Config) -> dict[str, Any]:
    """Compact live view for the overlay and the dashboard header."""
    cfg = config.get()
    names = config.tool_names()
    plans = store.plans()
    statuses = store.statuses()
    today = time.strftime("%Y-%m-%d")
    first, last, _ = month_bounds(current_month())
    today_secs: dict[str, float] = {}
    for tool, day, secs in store.seconds_by_tool_day(today, today):
        today_secs[tool] = today_secs.get(tool, 0.0) + (secs or 0.0)

    plan_owner = {"claude": "claude_web", "codex": "codex", "minimax": "minimax"}
    month_start = time.mktime(time.strptime(first, "%Y-%m-%d"))
    subs = []
    for s in cfg["subscriptions"]:
        windows = []
        for provider, tool in plan_owner.items():
            if tool in s["tools"] and provider in plans:
                for w in plans[provider]:
                    peak = store.plan_peak(provider, w["key"], month_start, time.time() + 1)
                    windows.append({**w, "source": names.get(tool, tool), "month_peak": peak})
        windows.sort(key=lambda w: (0 if "five" in w["key"] else 1 if w["key"] in ("seven_day", "weekly") else 2, w["key"]))
        tool_status = {t: statuses.get(t, {}) for t in s["tools"]}
        extra = {}
        if "minimax" in s["tools"] and statuses.get("minimax", {}).get("credits_remaining") is not None:
            extra["credits_remaining"] = statuses["minimax"]["credits_remaining"]
        subs.append({"id": s["id"], "name": s["name"], "monthly_cost": s["monthly_cost"],
                     "windows": windows, "today_seconds": sum(today_secs.get(t, 0.0) for t in s["tools"]),
                     "tools": [{"id": t, "name": names.get(t, t), **{k: v for k, v in tool_status[t].items()
                                                                    if k in ("ok", "message", "updated_at")}}
                               for t in s["tools"]], **extra})
    report = build_report(store, config)
    return {"now": time.time(), "currency": cfg["currency"], "subscriptions": subs,
            "top_jobs": [{"job": j["job"], "cost": j["cost"], "pct_cost": j["pct_cost"], "seconds": j["seconds"]}
                         for j in report["jobs"][:5]],
            "month_total": report["total_cost"], "month": report["month"],
            "extension": statuses.get("browser_extension", {}),
            "setup_needed": all(s["monthly_cost"] == 0 for s in cfg["subscriptions"])}
