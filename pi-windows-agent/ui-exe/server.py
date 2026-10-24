"""PiWin UI host — super-lightweight local server for the form UI.

- Serves ui/index.html on 127.0.0.1 only (never 0.0.0.0)
- Per-launch random token; every request must carry it
- Exact Host pinning (127.0.0.1:<port> / localhost:<port>)
- Rejects cross-origin (any Origin header)
- /approve, /confirm-second mirror the guard's mint/confirm_second rules
  (imports the same inventory constants)

Run:  python server.py   →  http://127.0.0.1:7431
"""
import http.server
import json
import os
import secrets
import socketserver
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prototype", "helper"))
from piwin_helper import (  # noqa: E402
    DENY_TOOLS, ALLOW_TOOLS, IRREVERSIBLE_ACTION_CLASSES, call_hash,
)

PORT = 7431
HERE = os.path.dirname(os.path.abspath(__file__))
LAUNCH_TOKEN = secrets.token_hex(32)
APPROVALS = {}  # hash -> {"target":..., "action_class":..., "requires_second":..., "second_confirmed":...}


def inventory_check(name: str):
    if name in DENY_TOOLS or name.startswith("mcp__"):
        raise ValueError(f"tool {name} is DENIED outright in v0.1")
    if name.startswith("ui.") or name in ALLOW_TOOLS:
        return
    raise ValueError(f"tool {name} is not in the v0.1 inventory")


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _guard(self):
        origin = self.headers.get("Origin")
        if origin:
            self._json(403, {"error": "cross-origin rejected"}); return False
        host = self.headers.get("Host", "")
        if host not in (f"127.0.0.1:{PORT}", f"localhost:{PORT}"):
            self._json(403, {"error": "bad host"}); return False
        return True

    def _auth(self, msg):
        if msg.get("token") != LAUNCH_TOKEN:
            self._json(401, {"error": "bad launch token"}); return False
        return True

    def do_GET(self):
        if not self._guard():
            return
        if self.path == "/":
            try:
                with open(os.path.join(HERE, "ui", "index.html"), "rb") as f:
                    body = f.read()
            except OSError:
                self._json(404, {"error": "index.html missing"}); return
            # inject the launch token once, at load — the page stores nothing else
            html = body.replace(b"__LAUNCH_TOKEN__", LAUNCH_TOKEN.encode())
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
        elif self.path == "/status":
            self._json(200, {"status": "ok"})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if not self._guard():
            return
        length = int(self.headers.get("Content-Length", 0))
        if length > 1_000_000:
            self._json(413, {"error": "too large"}); return
        try:
            msg = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "bad json"}); return
        if not self._auth(msg):
            return
        if self.path == "/approve" and msg.get("name") and "args" in msg:
            try:
                inventory_check(msg["name"])
            except ValueError as e:
                self._json(400, {"error": str(e)}); return
            target = msg.get("target")
            if msg["name"].startswith("ui.") and (
                not target or target.get("pid") is None
                or not target.get("window") or not target.get("control")
            ):
                self._json(400, {"error": "ui.* approval requires pid/window/control"})
                return
            action_class = msg.get("action_class", "ui")
            requires_second = (
                action_class in IRREVERSIBLE_ACTION_CLASSES
                or bool(msg.get("extra_confirm"))
            )
            h = call_hash(msg["name"], msg["args"])
            APPROVALS[h] = {"target": target, "action_class": action_class,
                            "requires_second": requires_second, "second_confirmed": False}
            self._json(200, {"hash": h})
        elif self.path == "/confirm-second" and msg.get("hash"):
            ap = APPROVALS.get(msg["hash"])
            t = msg.get("target")
            if not ap or not t or not ap["target"] or (
                t.get("pid") != ap["target"].get("pid")
                or t.get("window") != ap["target"].get("window")
                or t.get("control") != ap["target"].get("control")
            ):
                self._json(400, {"error": "second confirmation target mismatch"})
                return
            ap["second_confirmed"] = True
            self._json(200, {"status": "confirmed"})
        elif self.path == "/status":
            self._json(200, {"status": "ok"})
        else:
            self._json(404, {"error": "not found"})

    def log_message(self, *a):  # quiet
        pass


def main():
    print("Launch token (also injected into the page at load):", LAUNCH_TOKEN)
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.daemon_threads = True
        print(f"PiWin UI on http://127.0.0.1:{PORT}  (localhost only)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nbye")


if __name__ == "__main__":
    main()
