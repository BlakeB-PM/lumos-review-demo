"""Read-only browser report over the same SQLite state used by MCP."""

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


def serve_report(reviews, port, open_browser=False):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
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
            self.send_response(200)
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
