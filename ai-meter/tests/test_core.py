"""Run with:  python -m unittest discover -s tests"""

import json
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="aimeter-test-")
os.environ["AIMETER_HOME"] = TMP

from aimeter import config as cfgmod  # noqa: E402
from aimeter.collect import Collector  # noqa: E402
from aimeter.config import Config, sanitize  # noqa: E402
from aimeter.costing import UNASSIGNED, UNUSED, assign_job, build_report  # noqa: E402
from aimeter.server import _csv_safe  # noqa: E402
from aimeter.store import Store  # noqa: E402
from aimeter.tools import claude_code, codex, minimax  # noqa: E402
from aimeter.tools.common import active_seconds_by_day, to_epoch  # noqa: E402


def iso(t: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t)) + ".000Z"


class ActiveTime(unittest.TestCase):
    def test_gaps_capped(self):
        base = 1_800_000_000
        # 3 events 60s apart, then a 2h break, then 1 event
        stamps = [base, base + 60, base + 120, base + 7320]
        total = sum(active_seconds_by_day(stamps, idle_cap=300).values())
        self.assertEqual(total, 60 + 60 + 60 + 60)  # 2 gaps + tail after break + final tail

    def test_parallel_duplicates_not_double_counted(self):
        base = 1_800_000_000
        a = active_seconds_by_day([base, base + 30], 300)
        b = active_seconds_by_day([base, base, base + 30, base + 30], 300)
        self.assertEqual(a, b)

    def test_to_epoch(self):
        self.assertAlmostEqual(to_epoch("2026-01-01T00:00:00Z"), 1767225600.0)
        self.assertEqual(to_epoch(1767225600000), 1767225600.0)
        self.assertIsNone(to_epoch("garbage"))


class Parsers(unittest.TestCase):
    def test_claude_code_transcript(self):
        d = Path(tempfile.mkdtemp())
        f = d / "abc.jsonl"
        t = 1_800_000_000
        recs = [
            {"type": "user", "sessionId": "abc", "cwd": "C:\\Users\\me\\TradingBot", "timestamp": iso(t),
             "message": {"role": "user", "content": "Build the backtester"}},
            {"type": "assistant", "sessionId": "abc", "timestamp": iso(t + 20), "requestId": "r1",
             "message": {"id": "m1", "usage": {"input_tokens": 10, "output_tokens": 5}}},
            {"type": "assistant", "sessionId": "abc", "timestamp": iso(t + 21), "requestId": "r1",
             "message": {"id": "m1", "usage": {"input_tokens": 10, "output_tokens": 5}}},  # streamed duplicate
        ]
        f.write_text("\n".join(json.dumps(r) for r in recs) + "\nnot json\n", encoding="utf-8")
        chats = claude_code.parse_file(f)
        self.assertEqual(len(chats), 1)
        c = chats[0]
        self.assertEqual(c.title, "Build the backtester")
        self.assertEqual(sum(c.tokens.values()), 15)
        self.assertEqual(c.project, "C:\\Users\\me\\TradingBot")

    def test_codex_rollout_and_limits(self):
        d = Path(tempfile.mkdtemp())
        f = d / "rollout-1.jsonl"
        t = 1_800_000_000
        recs = [
            {"timestamp": iso(t), "type": "session_meta", "payload": {"id": "s1", "cwd": "/work/site"}},
            {"timestamp": iso(t + 1), "type": "event_msg", "payload": {"type": "user_message", "message": "fix css"}},
            {"timestamp": iso(t + 30), "type": "event_msg", "payload": {
                "type": "token_count", "info": {"last_token_usage": {"total_tokens": 1234}},
                "rate_limits": {"primary": {"used_percent": 12.5, "window_minutes": 300, "resets_in_seconds": 600},
                                "secondary": {"used_percent": 40, "window_minutes": 10080, "resets_at": t + 86400}}}},
        ]
        f.write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
        chats, lim = codex.parse_file(f)
        self.assertEqual(chats[0].chat_id, "s1")
        self.assertEqual(chats[0].title, "fix css")
        windows, _ = codex.plan_windows(lim)
        self.assertEqual([(w["label"], w["used_pct"]) for w in windows], [("5-hour window", 12.5), ("Weekly", 40.0)])
        self.assertAlmostEqual(windows[0]["resets_at"], t + 30 + 600)

    def test_minimax_ledger(self):
        home = Path(tempfile.mkdtemp())
        db = home / "v2" / "sqlite" / "runtime-state.sqlite"
        db.parent.mkdir(parents=True)
        con = sqlite3.connect(db)
        con.executescript("""
            CREATE TABLE local_runtime_token_usage (session_id TEXT, turn_id TEXT, model TEXT, ts INTEGER,
              input_tokens INT, output_tokens INT, cache_read_tokens INT, cache_write_tokens INT, reasoning_tokens INT);
            CREATE TABLE local_runtime_sessions (session_id TEXT, title TEXT, workspace_dir TEXT,
              project_workspace_dir TEXT, agent_name TEXT, project_id TEXT, parent_session_id TEXT);
            CREATE TABLE local_runtime_projects (project_id TEXT, display_name TEXT, workspace_dir TEXT);
        """)
        t = 1_800_000_000_000
        con.execute("INSERT INTO local_runtime_projects VALUES ('p1','Credits overlay','/x')")
        con.execute("INSERT INTO local_runtime_sessions VALUES ('s1','Build overlay','/x','/x','a','p1',NULL)")
        con.execute("INSERT INTO local_runtime_sessions VALUES ('s2','sub','/x','/x','a','p1','s1')")
        con.execute("INSERT INTO local_runtime_token_usage VALUES ('s1','t','m',?,1,2,3,4,5)", (t,))
        con.execute("INSERT INTO local_runtime_token_usage VALUES ('s2','t','m',?,1,1,1,1,1)", (t + 30_000,))
        con.commit()
        con.close()
        old = minimax.MINIMAX_HOME
        minimax.MINIMAX_HOME = home
        try:
            chats = minimax.ledger_chats()
        finally:
            minimax.MINIMAX_HOME = old
        self.assertEqual(len(chats), 1)  # sub-agent rolled into parent chat
        self.assertEqual(chats[0].project, "Credits overlay")
        self.assertEqual(sum(chats[0].tokens.values()), 20)


class ConfigAndCosting(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.config = Config(self.dir / "config.json")
        self.store = Store(self.dir / "db.sqlite")

    def test_token_created_and_private(self):
        self.assertGreaterEqual(len(self.config.get()["token"]), 24)

    def test_broken_v2_settings_are_repaired(self):
        # every tool ticked under MiniMax, Claude/ChatGPT left empty (seen in the field)
        c = sanitize({"subscriptions": [
            {"id": "claude", "name": "Claude", "monthly_cost": 20, "tools": []},
            {"id": "chatgpt", "name": "ChatGPT Work", "monthly_cost": 20, "tools": []},
            {"id": "minimax", "name": "MiniMax Code", "monthly_cost": 20,
             "tools": ["claude_web", "claude_code", "chatgpt_web", "codex", "minimax"]}]})
        tools = {s["id"]: s["tools"] for s in c["subscriptions"]}
        self.assertEqual(tools["claude"], ["claude_web", "claude_code"])
        self.assertEqual(tools["chatgpt"], ["chatgpt_web", "codex"])
        self.assertEqual(tools["minimax"], ["minimax"])
        self.assertEqual([s["monthly_cost"] for s in c["subscriptions"]], [20, 20, 20])

    def test_custom_tool_has_own_price(self):
        c = sanitize({"custom_tools": [{"name": "Perplexity", "sites": ["perplexity.ai"], "monthly_cost": 20}]})
        sub = [s for s in c["subscriptions"] if s["id"].startswith("custom_")][0]
        self.assertEqual((sub["name"], sub["monthly_cost"], sub["tools"]), ("Perplexity", 20, [c["custom_tools"][0]["id"]]))

    def test_dashboard_cannot_change_token(self):
        tok = self.config.get()["token"]
        self.config.update({"token": "x" * 30, "port": 1234})
        self.assertEqual(self.config.get()["token"], tok)
        self.assertEqual(self.config.get()["port"], cfgmod.DEFAULT_PORT)

    def test_cost_split_by_time_per_subscription(self):
        self.config.update({"subscriptions": [
            {"id": "claude", "name": "Claude", "monthly_cost": 100},
            {"id": "chatgpt", "name": "GPT", "monthly_cost": 30},
            {"id": "minimax", "name": "MiniMax", "monthly_cost": 20}],
            "rules": [{"contains": "router", "job": "Home network"}]})
        day = time.strftime("%Y-%m-%d")
        col = Collector(self.store, self.config)
        col.ingest({"source": "t", "time": [
            {"tool": "claude_web", "chat_id": "a", "day": day, "seconds": 3000, "title": "Router setup"},
            {"tool": "claude_web", "chat_id": "b", "day": day, "seconds": 1000, "title": "Invoice for ACME"},
            {"tool": "chatgpt_web", "chat_id": "c", "day": day, "seconds": 600, "title": "Router firmware"},
            {"tool": "nope", "chat_id": "d", "day": day, "seconds": 600}]})
        self.store.set_override("claude_web", "b", "ACME")
        rep = build_report(self.store, self.config)
        jobs = {j["job"]: j for j in rep["jobs"]}
        self.assertAlmostEqual(jobs["Home network"]["cost"], 75 + 30)
        self.assertAlmostEqual(jobs["ACME"]["cost"], 25)
        self.assertAlmostEqual(jobs[UNUSED]["cost"], 20)
        self.assertAlmostEqual(sum(j["cost"] for j in rep["jobs"]), 150)
        # idempotent: resending the same totals doesn't double count
        col.ingest({"source": "t", "time": [{"tool": "claude_web", "chat_id": "a", "day": day, "seconds": 3000}]})
        self.assertAlmostEqual(build_report(self.store, self.config)["total_seconds"], 4600)

    def test_projects_combined_across_tools(self):
        self.config.update({"subscriptions": [
            {"id": "claude", "monthly_cost": 20, "name": "Claude"},
            {"id": "chatgpt", "monthly_cost": 30, "name": "ChatGPT"},
            {"id": "minimax", "monthly_cost": 0, "name": "MiniMax"}]})
        day = time.strftime("%Y-%m-%d")
        col = Collector(self.store, self.config)
        col.ingest({"source": "t", "time": [
            {"tool": "claude_web", "chat_id": "a", "day": day, "seconds": 1800, "project": "Trading Bot"},
            {"tool": "chatgpt_web", "chat_id": "b", "day": day, "seconds": 600, "project": "trading-bot"},
            {"tool": "chatgpt_web", "chat_id": "c", "day": day, "seconds": 600, "project": "Website"}]})
        rep = build_report(self.store, self.config)
        projects = {p["project"]: p for p in rep["projects"]}
        self.assertIn("Trading Bot", projects)  # spelling with the most time wins
        tb = projects["Trading Bot"]
        self.assertAlmostEqual(tb["seconds"], 2400)
        self.assertAlmostEqual(tb["cost"], 20 + 15)
        self.assertEqual(set(tb["by_sub"]), {"claude", "chatgpt"})
        chatgpt = [s for s in rep["subscriptions"] if s["id"] == "chatgpt"][0]
        self.assertEqual([(p["project"], p["cost"]) for p in chatgpt["projects"]], [("Trading Bot", 15.0), ("Website", 15.0)])
        # merge "Website" into "Trading Bot"
        self.config.update({"project_aliases": {"Website": "Trading Bot"}})
        rep = build_report(self.store, self.config)
        self.assertEqual([p["project"] for p in rep["projects"]], ["Trading Bot"])
        self.assertAlmostEqual(rep["projects"][0]["cost"], 50)

    def test_home_folder_unassigned(self):
        from aimeter.paths import HOME
        cfg = self.config.get()
        job, _ = assign_job({"tool": "claude_code", "chat_id": "x", "title": "", "project": str(HOME)}, cfg, {})
        self.assertEqual(job, UNASSIGNED)
        job, how = assign_job({"tool": "claude_code", "chat_id": "x", "title": "", "project": "C:\\Users\\me\\TradingBot"}, cfg, {})
        self.assertEqual((job, how), ("TradingBot", "folder"))

    def test_csv_injection_guard(self):
        self.assertEqual(_csv_safe("=HYPERLINK(1)"), "'=HYPERLINK(1)")
        self.assertEqual(_csv_safe("Normal"), "Normal")


if __name__ == "__main__":
    unittest.main()
