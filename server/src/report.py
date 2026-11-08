"""Local access review workspace over the same SQLite state used by MCP."""

import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from reviews import ROOT

ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/report.css": ("report.css", "text/css; charset=utf-8"),
    "/report.js": ("report.js", "text/javascript; charset=utf-8"),
}


def serve_report(reviews, port, open_browser, decision_schema, validate):
    class Handler(BaseHTTPRequestHandler):
        def local_host(self):
            return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

        def do_GET(self):
            if not self.local_host():
                self.send_error(403)
                return
            path = urlsplit(self.path).path
            if path == "/api/report":
                body = json.dumps(reviews.audit_report("Q4-DATA")).encode("utf-8")
                content_type = "application/json; charset=utf-8"
            elif path in ASSETS:
                name, content_type = ASSETS[path]
                body = (ROOT / "report" / name).read_bytes()
            else:
                self.send_error(404)
                return
            self.respond(200, body, content_type)

        def do_POST(self):
            if self.path != "/api/decisions":
                self.send_error(404)
                return
            if not self.local_host() or self.headers.get("Origin") != f"http://127.0.0.1:{self.server.server_port}":
                self.send_error(403)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if self.headers.get_content_type() != "application/json" or not 0 < size <= 65_536:
                    raise ValueError("Expected a bounded JSON submission.")
                payload = json.loads(self.rfile.read(size))
                validate(payload, decision_schema)
                result = reviews.submit_decisions(**payload, client="local_review_ui")
            except ValueError as error:
                self.respond(400, json.dumps({"error": str(error)}).encode(), "application/json")
                return
            self.respond(200, json.dumps(result).encode(), "application/json")

        def respond(self, status, body, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; object-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            pass

    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as server:
        url = f"http://127.0.0.1:{server.server_port}/"
        print(f"Audit report: {url}", flush=True)
        if open_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
