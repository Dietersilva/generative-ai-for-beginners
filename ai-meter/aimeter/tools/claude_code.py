"""Claude Code on this PC: reads the transcripts under ~/.claude/projects.

Claude Code in the browser (claude.ai/code) runs in the cloud; that one is
tracked by the browser extension instead.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..paths import HOME
from .common import ChatData, first_text, local_day, to_epoch, to_int

TOOL_ID = "claude_code"


def roots() -> list[Path]:
    out: list[Path] = []
    env = os.environ.get("CLAUDE_CONFIG_DIR", "")
    cands = [Path(p.strip()) for p in env.split(",") if p.strip()]
    cands += [HOME / ".claude", HOME / ".config" / "claude"]
    seen = set()
    for c in cands:
        key = str(c.resolve()) if c.exists() else str(c)
        if key not in seen and (c / "projects").is_dir():
            seen.add(key)
            out.append(c / "projects")
    return out


def files() -> list[Path]:
    found: list[Path] = []
    for r in roots():
        found.extend(p for p in r.rglob("*.jsonl") if p.is_file())
    return found


def parse_file(path: Path) -> list[ChatData]:
    chats: dict[str, ChatData] = {}
    seen_usage: set[str] = set()
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
            sid = str(rec.get("sessionId") or path.stem)
            ts = to_epoch(rec.get("timestamp"))
            chat = chats.setdefault(sid, ChatData(sid))
            if isinstance(rec.get("cwd"), str) and not chat.project:
                chat.project = rec["cwd"]
            rtype = rec.get("type")
            if rtype == "summary" and isinstance(rec.get("summary"), str):
                chat.title = rec["summary"][:90]
            if ts is None or rtype not in ("user", "assistant"):
                continue
            chat.stamps.append(int(ts))
            msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
            day = local_day(ts)
            if rtype == "user" and not rec.get("isSidechain"):
                text = first_text(msg.get("content"))
                if text:
                    chat.turns[day] = chat.turns.get(day, 0) + 1
                    if not chat.title:
                        chat.title = text
            usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else None
            if rtype == "assistant" and usage:
                # streamed replies repeat the same usage block; count once
                key = f"{msg.get('id', '')}|{rec.get('requestId', '')}"
                if key != "|" and key in seen_usage:
                    continue
                seen_usage.add(key)
                n = (to_int(usage.get("input_tokens")) + to_int(usage.get("output_tokens"))
                     + to_int(usage.get("cache_read_input_tokens"))
                     + to_int(usage.get("cache_creation_input_tokens")))
                chat.tokens[day] = chat.tokens.get(day, 0) + n
    return [c for c in chats.values() if c.stamps]
