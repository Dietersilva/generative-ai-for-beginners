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
WIDTH = 310


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
        self.render()

    def open_dashboard(self) -> None:
        webbrowser.open(self.url)

    def refresh_now(self) -> None:
        self.on_refresh()
        self.root.after(1500, self.render)

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

    def render(self) -> None:
        try:
            st = self.get_state()
        except Exception as exc:  # keep the window alive
            st = {"error": str(exc)}
        for w in self.body.winfo_children():
            w.destroy()
        if "error" in st:
            tk.Label(self.body, text="Couldn't load data", fg=AMBER, bg=BG, font=FONT).pack(anchor="w")
        else:
            cur = st["currency"]
            for s in st["subscriptions"]:
                if not s["tools"]:
                    continue
                card = tk.Frame(self.body, bg=PANEL, padx=10, pady=8)
                card.pack(fill="x", pady=4)
                top = tk.Frame(card, bg=PANEL)
                top.pack(fill="x")
                tk.Label(top, text=s["name"], fg=TEXT, bg=PANEL, font=("Segoe UI Semibold", 10)).pack(side="left")
                tk.Label(top, text=f"today {_dur(s['today_seconds'])}", fg=MUTED, bg=PANEL, font=FONT).pack(side="right")
                if self.collapsed:
                    worst = max((w["used_pct"] or 0 for w in s["windows"]), default=None)
                    if worst is not None:
                        self._bar(card, worst)
                    continue
                if not s["windows"]:
                    tk.Label(card, text="no plan % · time tracking only", fg=MUTED, bg=PANEL,
                             font=("Segoe UI", 9)).pack(anchor="w")
                for w in s["windows"]:
                    pct = w["used_pct"] or 0
                    row = tk.Frame(card, bg=PANEL)
                    row.pack(fill="x", pady=(4, 0))
                    tk.Label(row, text=w["label"], fg=MUTED, bg=PANEL, font=("Segoe UI", 9)).pack(side="left")
                    reset = _until(w.get("resets_at"))
                    tk.Label(row, text=f"{pct:.0f}% used" + (f" · {reset}" if reset else ""),
                             fg=RED if pct >= 90 else TEXT, bg=PANEL, font=("Segoe UI", 9)).pack(side="right")
                    self._bar(card, pct)
                if s.get("credits_remaining") is not None:
                    tk.Label(card, text=f"credits left: {s['credits_remaining']:,.0f}", fg=MUTED, bg=PANEL,
                             font=("Segoe UI", 9)).pack(anchor="w")
            if not self.collapsed:
                jobs = [j for j in st["top_jobs"] if j["cost"] > 0 or j["seconds"] > 0]
                foot = tk.Frame(self.body, bg=BG)
                foot.pack(fill="x", pady=(8, 0))
                tk.Label(foot, text=f"THIS MONTH · {_money(st['month_total'], cur)} PAID", fg=MUTED, bg=BG,
                         font=("Segoe UI", 8, "bold")).pack(anchor="w")
                if st.get("setup_needed"):
                    tk.Label(foot, text="Add your subscription prices in the dashboard ▤", fg=AMBER, bg=BG,
                             font=("Segoe UI", 9), cursor="hand2").pack(anchor="w")
                for j in jobs[:4]:
                    r = tk.Frame(foot, bg=BG)
                    r.pack(fill="x")
                    name = j["job"] if len(j["job"]) <= 26 else j["job"][:25] + "…"
                    tk.Label(r, text=name, fg=TEXT, bg=BG, font=("Segoe UI", 9)).pack(side="left")
                    tk.Label(r, text=f"{_money(j['cost'], cur)} · {j['pct_cost']:.0f}%", fg=MUTED, bg=BG,
                             font=("Segoe UI", 9)).pack(side="right")
        self.root.update_idletasks()
        h = self.root.winfo_reqheight()
        self.root.geometry(f"{WIDTH}x{h}")
        self.root.after(5000, self.render)

    def run(self) -> None:
        self.root.mainloop()
