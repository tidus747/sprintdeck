"""Loopback HTTP API and static presentation routes."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
from pathlib import Path
from urllib.parse import urlsplit

from .state import ValidationError
from .recap import render_recap

MAX_BODY = 262144
STATIC = Path(__file__).parent / "static"
ROUTES = {"/control": ("control.html", "text/html"),
          **{f"/overlays/{scene}": ("overlay.html", "text/html") for scene in ("overview", "individual", "wrapup", "discussion", "welcome", "roadmap")},
          "/static/app.css": ("app.css", "text/css"),
          "/static/common.js": ("common.js", "text/javascript"),
          "/static/calendar.js": ("calendar.js", "text/javascript"),
          "/static/control.js": ("control.js", "text/javascript"),
          "/static/overlay.js": ("overlay.js", "text/javascript")}


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, store):
        self.store = store
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "SprintDeck/0.2"

    def log_message(self, format, *args):
        # Avoid logging imported session content or request paths.
        pass

    def respond(self, status, body, content_type="application/json", attachment=None):
        if content_type == "application/json":
            body = json.dumps(body, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if attachment:
            self.send_header("Content-Disposition", f'attachment; filename="{attachment}"')
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def trusted_host(self):
        return self.headers.get("Host", "") in {
            f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

    def do_GET(self):
        if not self.trusted_host():
            self.respond(403, {"error": "Only local hostnames are accepted"})
            return
        path = urlsplit(self.path).path
        if path == "/health":
            self.respond(200, {"status": "ok", "version": "0.2.0"})
        elif path == "/api/state":
            self.respond(200, self.server.store.snapshot())
        elif path == "/api/export":
            self.respond(200, self.server.store.export())
        elif path == "/api/recap":
            self.respond(200, render_recap(self.server.store.export()).encode("utf-8"), "text/markdown", "sprintdeck-recap.md")
        elif path == "/static/demo-session.json":
            self.respond(200, json.loads((STATIC.parent.parent / "examples" / "demo-session.json").read_text(encoding="utf-8")))
        elif path in ("/", "/control/"):
            self.send_response(302)
            self.send_header("Location", "/control")
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif path in ROUTES:
            filename, content_type = ROUTES[path]
            self.respond(200, (STATIC / filename).read_bytes(), content_type)
        else:
            self.respond(404, {"error": "Route not found"})

    def do_POST(self):
        self.close_connection = True
        if not self.trusted_host():
            self.respond(403, {"error": "Only local hostnames are accepted"})
            return
        origin = self.headers.get("Origin")
        if origin and origin not in {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}:
            self.respond(403, {"error": "Cross-origin requests are not allowed"})
            return
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            self.respond(403, {"error": "Cross-site requests are not allowed"})
            return
        if urlsplit(self.path).path != "/api/actions":
            self.respond(404, {"error": "Route not found"})
            return
        if self.headers.get_content_type() != "application/json":
            self.respond(415, {"error": "Content-Type must be application/json"})
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
            if length > MAX_BODY:
                self.respond(413, {"error": "Request exceeds the 256 KiB limit"})
                # Let clients receive the rejection before closing with unread upload bytes.
                # Drain at most one bounded body, with a short deadline, never the declared size.
                try:
                    self.connection.shutdown(socket.SHUT_WR)
                    self.connection.settimeout(0.25)
                    self.rfile.read(min(length, MAX_BODY + 1))
                except OSError:
                    pass
                return
            if length < 0 or self.headers.get("Transfer-Encoding"):
                raise ValidationError("A valid Content-Length is required")
            self.connection.settimeout(5)
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValidationError("Incomplete request body")
            action = json.loads(raw)
            state = self.server.store.apply(action)
            self.respond(200, state)
        except (ValueError, UnicodeError, RecursionError, TypeError) as exc:
            message = str(exc) if isinstance(exc, ValidationError) else "Invalid JSON request"
            self.respond(409 if message.startswith("Session changed") else 400, {"error": message})
        except OSError:
            self.respond(503, {"error": "Session could not be read or saved. Check local file access."})
