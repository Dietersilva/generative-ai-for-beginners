"""Local web server: dashboard + endpoint for the browser extension.

Security model
--------------
* Listens on 127.0.0.1 only: unreachable from other computers.
* Rejects any request whose Host header isn't 127.0.0.1/localhost on our
  port, which blocks DNS-rebinding attacks from websites.
* Every /api call needs the secret pairing token (constant-time compare).
  Web pages can't send that header cross-site without a CORS preflight,
  which we never approve.
* Strict Content-Security-Policy, no framing, no caching, 1 MB body limit.
"""

from __future__ import annotations

import csv
import hmac
import io
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

from . import __version__
from .collect import Collector
from .config import Config, clean_text
from .costing import build_report, build_state
from .paths import resource_path
from .store import Store

MAX_BODY = 1_000_000
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
STATIC = {"/": ("dashboard.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/app.css": ("app.css", "text/css; charset=utf-8")}
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; "
                               "connect-src 'self'; img-src 'self' data:; base-uri 'none'; "
                               "form-action 'none'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Cross-Origin-Resource-Policy": "same-origin",
}


class App:
    """Everything the HTTP handler needs; also used by the overlay."""

    def __init__(self, store: Store, config: Config, collector: Collector,
                 on_toggle: Callable[[], None] | None = None) -> None:
        self.store = store
        self.config = config
        self.collector = collector
        self.on_toggle = on_toggle or (lambda: None)
        self.refresh_event = threading.Event()


def make_handler(app: App) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = f"AI-Meter/{__version__}"
        sys_version = ""

        def log_message(self, fmt: str, *args: Any) -> None:  # keep the console quiet
            return

        # ---- helpers -------------------------------------------------------
        def _send(self, code: int, body: bytes, ctype: str, extra: dict[str, str] | None = None) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for k, v in SECURITY_HEADERS.items():
                self.send_header(k, v)
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, code: int, obj: Any) -> None:
            self._send(code, json.dumps(obj).encode("utf-8"), "application/json")

        def _host_ok(self) -> bool:
            port = app.config.get()["port"]
            host = (self.headers.get("Host") or "").lower()
            return host in (f"127.0.0.1:{port}", f"localhost:{port}")

        def _token_ok(self) -> bool:
            given = self.headers.get("X-AIMeter-Token") or ""
            return hmac.compare_digest(given.encode(), app.config.get()["token"].encode())

        def _body(self) -> dict[str, Any] | None:
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                return None
            if length <= 0 or length > MAX_BODY:
                return None
            if "application/json" not in (self.headers.get("Content-Type") or ""):
                return None
            try:
                data = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return None
            return data if isinstance(data, dict) else None

        def _guard(self, need_token: bool) -> bool:
            if not self._host_ok():
                self._json(403, {"error": "bad host"})
                return False
            if need_token and not self._token_ok():
                self._json(401, {"error": "missing or wrong pairing token"})
                return False
            return True

        # ---- routes ----------------------------------------------------------
        def do_OPTIONS(self) -> None:  # never approve cross-origin preflights
            self._json(405, {"error": "not allowed"})

        def do_GET(self) -> None:
            url = urlparse(self.path)
            if url.path in STATIC:
                if not self._guard(need_token=False):
                    return
                name, ctype = STATIC[url.path]
                body = resource_path("web", name).read_bytes()
                if name == "dashboard.html":
                    # The page itself can only be read by same-origin code,
                    # so embedding the token here is safe.
                    body = body.replace(b"__AIMETER_TOKEN__", app.config.get()["token"].encode())
                self._send(200, body, ctype)
                return
            if url.path == "/favicon.ico":
                self._send(204, b"", "image/x-icon")
                return
            if not self._guard(need_token=True):
                return
            q = parse_qs(url.query)
            month = (q.get("month") or [""])[0]
            if month and not MONTH_RE.match(month):
                self._json(400, {"error": "bad month"})
                return
            if url.path == "/api/ping":
                self._json(200, {"ok": True, "app": "AI-Meter", "version": __version__})
            elif url.path == "/api/state":
                self._json(200, build_state(app.store, app.config))
            elif url.path == "/api/report":
                self._json(200, build_report(app.store, app.config, month or None))
            elif url.path == "/api/diagnostics":
                self._json(200, {"version": __version__, "statuses": app.store.statuses(),
                                 "plans": app.store.plans()})
            elif url.path == "/api/config":
                cfg = app.config.get()
                cfg.pop("token", None)
                self._json(200, cfg)
            elif url.path == "/api/export.csv":
                rep = build_report(app.store, app.config, month or None)
                buf = io.StringIO()
                w = csv.writer(buf)
                w.writerow(["month", "project", "hours", "cost", "currency", "pct_of_spend", "chats"])
                for j in rep["jobs"]:
                    w.writerow([rep["month"], _csv_safe(j["job"]), f"{j['seconds'] / 3600:.2f}",
                                f"{j['cost']:.2f}", rep["currency"], f"{j['pct_cost']:.1f}", j["chats"]])
                self._send(200, buf.getvalue().encode("utf-8-sig"), "text/csv; charset=utf-8",
                           {"Content-Disposition": f'attachment; filename="ai-meter-{rep["month"]}.csv"'})
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self) -> None:
            if not self._guard(need_token=True):
                return
            path = urlparse(self.path).path
            if path == "/api/toggle":
                app.on_toggle()
                self._json(200, {"ok": True})
                return
            if path == "/api/refresh":
                app.refresh_event.set()
                self._json(200, {"ok": True})
                return
            body = self._body()
            if body is None:
                self._json(400, {"error": "expected a JSON object"})
                return
            if path == "/api/ingest":
                self._json(200, {"ok": True, **app.collector.ingest(body)})
            elif path == "/api/config":
                cfg = app.config.update(body)
                cfg.pop("token", None)
                self._json(200, cfg)
            elif path == "/api/assign":
                tool = clean_text(body.get("tool"), 64)
                chat_id = clean_text(body.get("chat_id"), 200)
                job = clean_text(body.get("job"))
                if not tool or not chat_id:
                    self._json(400, {"error": "tool and chat_id required"})
                    return
                app.store.set_override(tool, chat_id, job)
                self._json(200, {"ok": True})
            else:
                self._json(404, {"error": "not found"})

        do_HEAD = do_GET

    return Handler


def _csv_safe(text: str) -> str:
    """Stop spreadsheet formula injection from chat titles."""
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


class Server:
    def __init__(self, app: App) -> None:
        port = app.config.get()["port"]
        self.httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(app))
        self.httpd.daemon_threads = True
        self.thread = threading.Thread(target=self.httpd.serve_forever, name="aimeter-http", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
