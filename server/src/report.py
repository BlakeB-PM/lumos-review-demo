"""Local access review workspace over the same SQLite state used by MCP."""

import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from mcp_stdio import obj, string
from chatgpt_review import ReviewWorkflow, TOOLS
from reviews import ROOT

ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/report.css": ("report.css", "text/css; charset=utf-8"),
    "/report.js": ("report.js", "text/javascript; charset=utf-8"),
}
RESET_SCHEMA = obj(("run_id",), run_id=string())


def serve_report(reviews, port, open_browser, decision_schema, validate):
    workflow = ReviewWorkflow(reviews, "local_review_ui")
    routes = {"/api/prepare": "prepare_review_batch", "/api/record": "record_review_batch",
              "/api/defer": "defer_review_items"}
    class Handler(BaseHTTPRequestHandler):
        def local_host(self):
            return self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}"

        def do_GET(self):
            if not self.local_host():
                self.send_error(403)
                return
            path = urlsplit(self.path).path
            if path == "/api/report":
                body = json.dumps(reviews.audit_report(reviews.campaign_id)).encode("utf-8")
                content_type = "application/json; charset=utf-8"
            elif path in ASSETS:
                name, content_type = ASSETS[path]
                body = (ROOT / "report" / name).read_bytes()
            else:
                self.send_error(404)
                return
            self.respond(200, body, content_type)

        def do_POST(self):
            if self.path not in (*routes, "/api/reset"):
                self.send_error(404)
                return
            if not self.local_host() or self.headers.get("Origin") != f"http://127.0.0.1:{self.server.server_port}":
                self.send_error(403)
                return
            resetting = self.path == "/api/reset"
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if self.headers.get_content_type() != "application/json" or not 0 < size <= 65_536:
                    raise ValueError("Expected a bounded JSON submission.")
                payload = json.loads(self.rfile.read(size))
                validate(payload, RESET_SCHEMA if resetting else TOOLS[routes[self.path]][1])
            except ValueError as error:
                self.respond(400, json.dumps({"error": str(error)}).encode(), "application/json")
                return
            try:
                if resetting:
                    result = {"run_id": reviews.reset(expected_run_id=payload["run_id"])}
                else:
                    result = getattr(workflow, routes[self.path])(**payload)
            except ValueError as error:
                self.respond(409 if resetting else 400, json.dumps({"error": str(error)}).encode(), "application/json")
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
