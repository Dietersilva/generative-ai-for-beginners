"""Start-up: one instance, local server, background collection, overlay."""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import urllib.request

from . import __version__
from .collect import Collector
from .config import Config
from .costing import build_state
from .server import App, Server
from .store import Store

POLL_SECONDS = 60
DESKTOP_TICK = 5.0


def _call_running(port: int, token: str, path: str) -> dict | None:
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method="POST" if path != "/api/ping" else "GET",
                                 headers={"X-AIMeter-Token": token, "Host": f"127.0.0.1:{port}"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # never route localhost via a proxy
    try:
        with opener.open(req, timeout=3) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ai-meter", description="AI subscription usage and cost per job")
    ap.add_argument("--no-overlay", action="store_true", help="run without the floating window")
    ap.add_argument("--dashboard", action="store_true", help="open the dashboard in your browser")
    ap.add_argument("--version", action="version", version=f"AI-Meter {__version__}")
    args = ap.parse_args(argv)

    config = Config()
    cfg = config.get()
    port, token = cfg["port"], cfg["token"]

    store = Store()
    collector = Collector(store, config)
    app = App(store, config, collector)
    try:
        server = Server(app)
    except OSError:
        # Already running? Then this launch (e.g. Ctrl+Alt+M) toggles it.
        if _call_running(port, token, "/api/ping"):
            _call_running(port, token, "/api/toggle")
            return 0
        print(f"AI-Meter: port {port} is used by another program.", file=sys.stderr)
        return 1
    server.start()
    url = f"http://127.0.0.1:{port}/"

    def poll_loop() -> None:
        first = True
        while True:
            collector.run_local(force_api=first)
            first = False
            app.refresh_event.wait(POLL_SECONDS)
            if app.refresh_event.is_set():
                app.refresh_event.clear()
                collector.run_local(force_api=True)

    def desktop_loop() -> None:
        while True:
            try:
                collector.desktop_tick(DESKTOP_TICK)
            except Exception:
                pass
            time.sleep(DESKTOP_TICK)

    threading.Thread(target=poll_loop, name="aimeter-poll", daemon=True).start()
    if sys.platform == "win32":
        threading.Thread(target=desktop_loop, name="aimeter-desktop", daemon=True).start()

    if args.dashboard:
        import webbrowser
        webbrowser.open(url)

    if args.no_overlay:
        print(f"AI-Meter {__version__} running at {url}  (Ctrl+C to stop)")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass
        server.stop()
        return 0

    from .overlay import Overlay

    def save_pos(x: int, y: int, collapsed: bool) -> None:
        config.update({"overlay": {"x": x, "y": y, "collapsed": collapsed}})

    overlay = Overlay(lambda: build_state(store, config), url, app.refresh_event.set, save_pos, cfg["overlay"])
    app.on_toggle = overlay.toggle_flag.set
    overlay.run()
    server.stop()
    return 0
