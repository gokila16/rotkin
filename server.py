#!/usr/bin/env python3
"""Rotkin dashboard. Run `python3 server.py` and open http://localhost:8765"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import rotkin

PAGE = Path(__file__).with_name("dashboard.html")
# Only answer requests sent to this address (blocks DNS rebinding),
# and only take button presses from the dashboard page itself (blocks other websites).
HOSTS = {"localhost:8765", "127.0.0.1:8765"}
ORIGINS = {"http://" + h for h in HOSTS}


class Handler(BaseHTTPRequestHandler):
    def reply(self, body, content_type="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.headers.get("Host") not in HOSTS:
            return self.send_error(403)
        if self.path == "/":
            self.reply(PAGE.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/state":
            self.reply(rotkin.apply(rotkin.view))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.headers.get("Host") not in HOSTS or self.headers.get("Origin") not in ORIGINS:
            return self.send_error(403)
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or "{}")
        if self.path == "/grass":
            rotkin.apply(rotkin.on_grass)
            ok, message = True, "🌱 Certified grass. Your pumpkin feels alive again!"
        elif self.path == "/think":
            ok, message = rotkin.apply(rotkin.on_think, body.get("text", ""))
        elif self.path == "/reset":
            rotkin.apply(rotkin.reset)
            ok, message = True, "Fresh pumpkin!"
        else:
            return self.send_error(404)
        self.reply({"ok": ok, "message": message, **rotkin.apply(rotkin.view)})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("🎃 Rotkin is watching at http://localhost:8765")
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
