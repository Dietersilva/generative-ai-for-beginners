"""Small always-on-top window with plan bars and top jobs."""

from __future__ import annotations

import threading
import time
import tkinter as tk
import webbrowser
from typing import Any, Callable

BG, PANEL, TEXT, MUTED, LINE = "#15171c", "#1d2027", "#e8eaee", "#9aa3af", "#2d323b"
BLUE, AMBER, RED, GREEN = "#4f8cf7", "#f2b84b", "#f26b6b", "#3ccf7c"
FONT = ("Segoe UI", 10)
WIDTH = 330


def _dur(sec: float) -> str:
    sec = int(sec or 0)
    if sec < 60:
        return "0m" if not sec else "<1m"
    h, m = divmod(sec // 60, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def _until(ts: float | None) -> str:
    if not ts:
        return ""
    s = ts - time.time()
    if s <= 0:
        return "reset due"
    d, rem = divmod(int(s), 86400)
    h, rem = divmod(rem, 3600)
    return f"{d}d {h}h" if d else f"{h}h {rem // 60}m" if h else f"{rem // 60}m"


def _money(v: float, cur: str) -> str:
    sym = {"USD": "$", "EUR": "€", "GBP": "£", "CAD": "$", "AUD": "$"}.get(cur, "")
    return f"{sym}{v:,.2f}" if sym else f"{v:,.2f} {cur}"


class Overlay:
    def __init__(self, get_state: Callable[[], dict[str, Any]], dashboard_url: str,
                 on_refresh: Callable[[], None], save_pos: Callable[[int, int, bool], None],
                 pos: dict[str, Any]) -> None:
        self.get_state = get_state
        self.url = dashboard_url
        self.on_refresh = on_refresh
        self.save_pos = save_pos
        self.toggle_flag = threading.Event()
        self.collapsed = bool(pos.get("collapsed"))
        self.expanded: set[str] = set()
        self.root = tk.Tk()
        self.root.title("AI-Meter")
        self.root.configure(bg=BG)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        try:
            self.root.attributes("-alpha", 0.96)
        except tk.TclError:
            pass
        x, y = pos.get("x"), pos.get("y")
        if x is None or y is None:
            x = self.root.winfo_screenwidth() - WIDTH - 24
            y = 80
        self.root.geometry(f"{WIDTH}x10+{int(x)}+{int(y)}")
        self._drag = (0, 0)
        self._build_header()
        self.body = tk.Frame(self.root, bg=BG)
        self.body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Open dashboard", command=self.open_dashboard)
        self.menu.add_command(label="Refresh now", command=self.refresh_now)
        self.menu.add_separator()
        self.menu.add_command(label="Quit AI-Meter", command=self.quit)
        self.root.bind("<Button-3>", lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        self.root.after(100, self.render)
        self.root.after(200, self._poll_toggle)

    # ---- header / window behaviour ---------------------------------------
    def _build_header(self) -> None:
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill="x", padx=10, pady=(8, 4))
        title = tk.Label(bar, text="● AI-Meter", fg=TEXT, bg=BG, font=("Segoe UI Semibold", 11))
        title.pack(side="left")
        for w in (bar, title):
            w.bind("<ButtonPress-1>", self._start_drag)
            w.bind("<B1-Motion>", self._on_drag)
            w.bind("<ButtonRelease-1>", lambda e: self._remember())
        for txt, cmd, tip in (("✕", self.hide, "Hide (Ctrl+Alt+M shows it again)"),
                              ("—", self.toggle_collapse, "Collapse"),
                              ("▤", self.open_dashboard, "Dashboard"),
                              ("⟳", self.refresh_now, "Refresh")):
            b = tk.Label(bar, text=txt, fg=MUTED, bg=BG, font=("Segoe UI Symbol", 11), cursor="hand2", padx=4)
            b.pack(side="right")
            b.bind("<Button-1>", lambda e, c=cmd: c())
            b.bind("<Enter>", lambda e, w=b: w.configure(fg=TEXT))
            b.bind("<Leave>", lambda e, w=b: w.configure(fg=MUTED))

    def _start_drag(self, e: tk.Event) -> None:
        self._drag = (e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y())

    def _on_drag(self, e: tk.Event) -> None:
        self.root.geometry(f"+{e.x_root - self._drag[0]}+{e.y_root - self._drag[1]}")

    def _remember(self) -> None:
        self.save_pos(self.root.winfo_x(), self.root.winfo_y(), self.collapsed)

    def _poll_toggle(self) -> None:
        if self.toggle_flag.is_set():
            self.toggle_flag.clear()
            if self.root.state() == "withdrawn":
                self.root.deiconify()
                self.root.attributes("-topmost", True)
            else:
                self.hide()
        self.root.after(200, self._poll_toggle)

    def hide(self) -> None:
        self.root.withdraw()

    def toggle_collapse(self) -> None:
        self.collapsed = not self.collapsed
        self._remember()
        self._redraw()

    def open_dashboard(self) -> None:
        webbrowser.open(self.url)

    def refresh_now(self) -> None:
        self.on_refresh()
        self.root.after(1500, self._redraw)

    def quit(self) -> None:
        self._remember()
        self.root.destroy()

    # ---- content -------------------------------------------------------------
    def _bar(self, parent: tk.Widget, pct: float) -> None:
        c = tk.Canvas(parent, height=6, bg=LINE, highlightthickness=0, bd=0)
        c.pack(fill="x", pady=(2, 6))
        color = RED if pct >= 90 else AMBER if pct >= 70 else BLUE

        def draw(_e: Any = None) -> None:
            c.delete("all")
            w = c.winfo_width()
            c.create_rectangle(0, 0, max(0, min(100, pct)) / 100 * w, 6, fill=color, width=0)
        c.bind("<Configure>", draw)

    def toggle_tool(self, sub_id: str) -> None:
        if sub_id in self.expanded:
            self.expanded.discard(sub_id)
        else:
            self.expanded.add(sub_id)
        self._redraw()

    def _click_all(self, widget: tk.Widget, fn) -> None:
        widget.bind("<Button-1>", lambda e: fn())
        widget.configure(cursor="hand2")
        for child in widget.winfo_children():
            self._click_all(child, fn)

    def render(self) -> None:
        self._redraw()
        self.root.after(5000, self.render)

    def _redraw(self) -> None:
        try:
            st = self.get_state()
        except Exception:  # keep the window alive
            st = {"error": True}
        for w in self.body.winfo_children():
            w.destroy()
        small = ("Segoe UI", 9)
        if "error" in st:
            tk.Label(self.body, text="Couldn't load data", fg=AMBER, bg=BG, font=FONT).pack(anchor="w")
        else:
            cur = st["currency"]
            for s in st["subscriptions"]:
                card = tk.Frame(self.body, bg=PANEL, padx=10, pady=8)
                card.pack(fill="x", pady=4)
                top = tk.Frame(card, bg=PANEL)
                top.pack(fill="x")
                arrow = "▾" if s["id"] in self.expanded else "▸"
                tk.Label(top, text=f"{arrow} {s['name']}", fg=TEXT, bg=PANEL, font=("Segoe UI Semibold", 10)).pack(side="left")
                tk.Label(top, text=f"today {_dur(s['today_seconds'])}", fg=MUTED, bg=PANEL, font=FONT).pack(side="right")
                if not s["windows"]:
                    tk.Label(card, text=s.get("no_plan_hint") or "no plan limits · time only", fg=MUTED, bg=PANEL,
                             font=small, wraplength=WIDTH - 50, justify="left").pack(anchor="w")
                windows = s["windows"] if not self.collapsed else sorted(
                    s["windows"], key=lambda w: w.get("left_pct") if w.get("left_pct") is not None else 100)[:1]
                for w in windows:
                    left = w.get("left_pct") or 0.0
                    row = tk.Frame(card, bg=PANEL)
                    row.pack(fill="x", pady=(4, 0))
                    tk.Label(row, text=f"{w['label']}", fg=MUTED, bg=PANEL, font=small).pack(side="left")
                    reset = _until(w.get("resets_at"))
                    color = RED if left <= 10 else AMBER if left <= 30 else TEXT
                    tk.Label(row, text=f"{left:.0f}% left" + (f" · {reset}" if reset else ""),
                             fg=color, bg=PANEL, font=small).pack(side="right")
                    self._bar(card, w.get("used_pct") or 0)
                if s.get("credits_remaining") is not None and not self.collapsed:
                    tk.Label(card, text=f"credits left: {s['credits_remaining']:,.0f}", fg=MUTED, bg=PANEL,
                             font=small).pack(anchor="w")
                if s["id"] in self.expanded:
                    tk.Label(card, text=f"THIS MONTH · {_dur(s['month_seconds'])}", fg=MUTED, bg=PANEL,
                             font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(6, 0))
                    if not s["projects"]:
                        tk.Label(card, text="no activity yet", fg=MUTED, bg=PANEL, font=small).pack(anchor="w")
                    for p in s["projects"][:6]:
                        r = tk.Frame(card, bg=PANEL)
                        r.pack(fill="x")
                        name = p["project"] if len(p["project"]) <= 22 else p["project"][:21] + "…"
                        tk.Label(r, text=name, fg=TEXT, bg=PANEL, font=small).pack(side="left")
                        tk.Label(r, text=f"{_dur(p['seconds'])} · {_money(p['cost'], cur)}", fg=MUTED, bg=PANEL,
                                 font=small).pack(side="right")
                self._click_all(card, lambda sid=s["id"]: self.toggle_tool(sid))
            if not self.collapsed:
                jobs = [j for j in st["top_jobs"] if j["seconds"] > 0]
                foot = tk.Frame(self.body, bg=BG)
                foot.pack(fill="x", pady=(8, 0))
                tk.Label(foot, text=f"TOP PROJECTS THIS MONTH · {_money(st['month_total'], cur)} PAID", fg=MUTED, bg=BG,
                         font=("Segoe UI", 8, "bold")).pack(anchor="w")
                if st.get("setup_needed"):
                    tk.Label(foot, text="Add your prices in the dashboard ▤", fg=AMBER, bg=BG, font=small).pack(anchor="w")
                for j in jobs[:4]:
                    r = tk.Frame(foot, bg=BG)
                    r.pack(fill="x")
                    name = j["job"] if len(j["job"]) <= 24 else j["job"][:23] + "…"
                    tk.Label(r, text=name, fg=TEXT, bg=BG, font=small).pack(side="left")
                    tk.Label(r, text=f"{_dur(j['seconds'])} · {_money(j['cost'], cur)}", fg=MUTED, bg=BG,
                             font=small).pack(side="right")
        self.root.update_idletasks()
        self.root.geometry(f"{WIDTH}x{self.root.winfo_reqheight()}")

    def run(self) -> None:
        self.root.mainloop()
