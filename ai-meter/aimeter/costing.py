"""Turn subscription costs into a cost per project.

For each tool (subscription):

    cost of project P = monthly price x (time on P with that tool / all time with that tool)

Each subscription is split on its own, so an hour on a $20 plan and an hour
on a $200 plan aren't treated as the same thing. A subscription that wasn't
used at all in the month shows up as "Unused subscription" so the totals
always add up to what you actually paid.

Projects are matched across tools by name: "CZ Trader", "cz-trader" and
"CZTrader" are the same project. Projects can also be merged by hand.
"""

from __future__ import annotations

import calendar
import re
import time
from datetime import date
from pathlib import PurePath, PureWindowsPath
from typing import Any

from .config import Config, project_key
from .paths import HOME
from .store import Store

UNASSIGNED = "Unassigned"
UNUSED = "Unused subscription"
_ID_LIKE = re.compile(r"^(g-p-[0-9a-z]+|[0-9a-f-]{24,})$", re.I)

# which plan-usage feed belongs to which tool
PLAN_FEEDS = {"claude": "claude_web", "chatgpt": "chatgpt_web", "codex": "codex", "minimax": "minimax"}


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
    norm = project.replace("\\", "/").rstrip("/").lower()
    return norm == str(HOME).replace("\\", "/").rstrip("/").lower()


def assign_project(chat: dict[str, Any], cfg: dict[str, Any], overrides: dict[tuple[str, str], str]) -> tuple[str, str]:
    """Returns (project, how). how: manual | rule | folder | none."""
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


# kept for older callers / tests
assign_job = assign_project


def build_report(store: Store, config: Config, month: str | None = None) -> dict[str, Any]:
    cfg = config.get()
    names = config.tool_names()
    month = month or current_month()
    first, last, days_in_month = month_bounds(month)
    today = date.today()
    is_current = month == today.strftime("%Y-%m")
    aliases = cfg.get("project_aliases", {})

    tool_sub: dict[str, dict[str, Any]] = {}
    for s in cfg["subscriptions"]:
        for t in s["tools"]:
            tool_sub[t] = s

    overrides = store.overrides()
    chats = []
    for a in store.activity_between(first, last):
        project, how = assign_project(a, cfg, overrides)
        k = project_key(project)
        if k in aliases:
            project = aliases[k]
        sub = tool_sub.get(a["tool"])
        chats.append({**a, "job": project, "project_name": project, "job_source": how,
                      "sub": sub["id"] if sub else None,
                      "tool_name": names.get(a["tool"], a["tool"]), "cost": 0.0})

    # one display name per project key: the spelling with the most time
    spelling: dict[str, dict[str, float]] = {}
    for c in chats:
        spelling.setdefault(project_key(c["job"]) or c["job"], {}).setdefault(c["job"], 0.0)
        spelling[project_key(c["job"]) or c["job"]][c["job"]] += c["seconds"] + 1
    display = {k: max(v.items(), key=lambda kv: kv[1])[0] for k, v in spelling.items()}
    for c in chats:
        c["job"] = c["project_name"] = display[project_key(c["job"]) or c["job"]]

    projects: dict[str, dict[str, Any]] = {}

    def prow(name: str) -> dict[str, Any]:
        return projects.setdefault(name, {"job": name, "project": name, "seconds": 0.0, "tokens": 0,
                                          "cost": 0.0, "chats": 0, "by_sub": {}})

    subs_out = []
    for s in cfg["subscriptions"]:
        mine = [c for c in chats if c["sub"] == s["id"]]
        weight = (lambda c: float(c["tokens"])) if s["basis"] == "tokens" else (lambda c: float(c["seconds"]))
        total_w = sum(weight(c) for c in mine)
        if s["basis"] == "tokens" and total_w <= 0:  # no token data (e.g. browser): fall back to time
            weight = lambda c: float(c["seconds"])  # noqa: E731
            total_w = sum(weight(c) for c in mine)
        cost = s["monthly_cost"]
        for c in mine:
            c["cost"] = cost * weight(c) / total_w if total_w > 0 else 0.0
        per_project: dict[str, dict[str, float]] = {}
        for c in mine:
            pp = per_project.setdefault(c["job"], {"seconds": 0.0, "cost": 0.0, "chats": 0})
            pp["seconds"] += c["seconds"]
            pp["cost"] += c["cost"]
            pp["chats"] += 1
        if total_w <= 0 and cost > 0:
            per_project[UNUSED] = {"seconds": 0.0, "cost": cost, "chats": 0}
        secs = sum(c["seconds"] for c in mine)
        subs_out.append({
            "id": s["id"], "name": s["name"], "monthly_cost": cost, "basis": s["basis"],
            "tools": [{"id": t, "name": names.get(t, t)} for t in s["tools"]],
            "seconds": secs, "tokens": sum(c["tokens"] for c in mine),
            "cost_per_hour": (cost / (secs / 3600)) if secs >= 60 and cost else None,
            "projects": sorted(({"project": k, "seconds": v["seconds"], "cost": round(v["cost"], 4),
                                 "chats": v["chats"], "pct_cost": 100.0 * v["cost"] / cost if cost else 0.0}
                                for k, v in per_project.items()),
                               key=lambda r: (-r["cost"], -r["seconds"])),
        })
        for name, v in per_project.items():
            row = prow(name)
            row["seconds"] += v["seconds"]
            row["cost"] += v["cost"]
            row["chats"] += v["chats"]
            bs = row["by_sub"].setdefault(s["id"], {"seconds": 0.0, "cost": 0.0})
            bs["seconds"] += v["seconds"]
            bs["cost"] += v["cost"]
    for c in chats:  # tools not paid by any subscription still count time
        if not c["sub"]:
            row = prow(c["job"])
            row["seconds"] += c["seconds"]
            row["chats"] += 1
    for c in chats:
        projects[c["job"]]["tokens"] += c["tokens"]

    total_cost = sum(s["monthly_cost"] for s in cfg["subscriptions"])
    total_secs = sum(c["seconds"] for c in chats)
    plist = sorted(projects.values(), key=lambda j: (-j["seconds"], -j["cost"], j["job"]))
    for j in plist:
        j["pct_cost"] = 100.0 * j["cost"] / total_cost if total_cost else 0.0
        j["pct_time"] = 100.0 * j["seconds"] / total_secs if total_secs else 0.0
        j["cost"] = round(j["cost"], 4)
    chats.sort(key=lambda c: (-c["seconds"], -c["cost"]))
    for c in chats:
        c["cost"] = round(c["cost"], 4)

    unassigned_secs = sum(c["seconds"] for c in chats if c["job"] == UNASSIGNED)
    return {
        "month": month, "currency": cfg["currency"], "is_current": is_current,
        "days_elapsed": today.day if is_current else days_in_month, "days_in_month": days_in_month,
        "total_cost": round(total_cost, 2), "total_seconds": total_secs,
        "unassigned_pct": 100.0 * unassigned_secs / total_secs if total_secs else 0.0,
        "subscriptions": subs_out, "projects": plist, "jobs": plist, "chats": chats[:2000],
        "known_jobs": sorted({j["job"] for j in plist if j["job"] not in (UNASSIGNED, UNUSED)}
                             | {r["job"] for r in cfg["rules"]}),
        "aliases": cfg.get("project_aliases", {}),
    }


def _window_kind(key: str) -> str:
    k = key.lower()
    if "five" in k or k in ("w300", "primary"):
        return "five_hour"
    if k in ("seven_day", "weekly", "w10080", "secondary"):
        return "weekly"
    return k


def plan_windows(store: Store, plans: dict[str, list[dict[str, Any]]], tools: list[str],
                 names: dict[str, str], month_start: float) -> list[dict[str, Any]]:
    """Newest reading per window (5-hour, weekly, ...) for a subscription's tools."""
    best: dict[str, dict[str, Any]] = {}
    for provider, tool in PLAN_FEEDS.items():
        if tool not in tools:
            continue
        for w in plans.get(provider, []):
            kind = _window_kind(w["key"])
            if kind in best and best[kind]["observed_at"] >= w["observed_at"]:
                continue
            peak = store.plan_peak(provider, w["key"], month_start, time.time() + 1)
            used = w.get("used_pct")
            best[kind] = {**w, "kind": kind, "source": names.get(tool, tool), "month_peak": peak,
                          "left_pct": None if used is None else max(0.0, 100.0 - used)}
    order = {"five_hour": 0, "weekly": 1}
    return sorted(best.values(), key=lambda w: (order.get(w["kind"], 2), w["key"]))


NO_PLAN_HINT = {
    "claude": "Pair the browser extension and open claude.ai to see your limits",
    "chatgpt": "Pair the browser extension and open chatgpt.com to see your limits",
    "minimax": "MiniMax didn't report plan limits (see Settings → Diagnostics)",
}


def build_state(store: Store, config: Config) -> dict[str, Any]:
    """Compact live view for the overlay and the dashboard header."""
    cfg = config.get()
    names = config.tool_names()
    plans = store.plans()
    statuses = store.statuses()
    today = time.strftime("%Y-%m-%d")
    first, _, _ = month_bounds(current_month())
    today_secs: dict[str, float] = {}
    for tool, _day, secs in store.seconds_by_tool_day(today, today):
        today_secs[tool] = today_secs.get(tool, 0.0) + (secs or 0.0)
    month_start = time.mktime(time.strptime(first, "%Y-%m-%d"))
    report = build_report(store, config)
    rep_subs = {s["id"]: s for s in report["subscriptions"]}

    subs = []
    for s in cfg["subscriptions"]:
        windows = plan_windows(store, plans, s["tools"], names, month_start)
        hint = ""
        if not windows:
            hint = NO_PLAN_HINT.get(s["id"], "This tool doesn't publish plan limits · time tracking only")
            if s["id"] == "minimax":
                st = statuses.get("minimax", {})
                hint = st.get("plan_error") or st.get("account_error") or (
                    st.get("message") if st.get("ok") is False else hint)
        extra = {}
        mm = statuses.get("minimax", {})
        if "minimax" in s["tools"] and mm.get("credits_remaining") is not None:
            extra["credits_remaining"] = mm["credits_remaining"]
        rs = rep_subs.get(s["id"], {})
        subs.append({"id": s["id"], "name": s["name"], "monthly_cost": s["monthly_cost"],
                     "windows": windows, "no_plan_hint": hint,
                     "today_seconds": sum(today_secs.get(t, 0.0) for t in s["tools"]),
                     "month_seconds": rs.get("seconds", 0.0), "cost_per_hour": rs.get("cost_per_hour"),
                     "projects": rs.get("projects", [])[:8],
                     "tools": [{"id": t, "name": names.get(t, t),
                                **{k: v for k, v in statuses.get(t, {}).items() if k in ("ok", "message", "updated_at")}}
                               for t in s["tools"]], **extra})
    return {"now": time.time(), "currency": cfg["currency"], "subscriptions": subs,
            "top_jobs": [{"job": j["job"], "cost": j["cost"], "pct_cost": j["pct_cost"], "seconds": j["seconds"]}
                         for j in report["projects"][:5]],
            "month_total": report["total_cost"], "month": report["month"],
            "extension": statuses.get("browser_extension", {}),
            "setup_needed": all(s["monthly_cost"] == 0 for s in cfg["subscriptions"])}
