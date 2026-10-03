"""Loopback HTTP server. Routes call the controller and do not evaluate LAMBDA."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from controller import Controller

ROOT = Path(__file__).resolve().parent
EXAMPLES = ROOT / "examples"
STATIC = ROOT / "static"
MAX_REQUEST_BYTES = 400_000

PAGES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}


def make_handler(controller):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            return

        def _send(self, code, body, content_type):
            if isinstance(body, (dict, list)):
                data = json.dumps(body).encode("utf-8")
                content_type = "application/json; charset=utf-8"
            elif isinstance(body, str):
                data = body.encode("utf-8")
            else:
                data = body
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def _reject_cross_origin(self):
            origin = self.headers.get("Origin")
            host = self.headers.get("Host")
            if origin not in (None, f"http://{host}"):
                self._send(403, {"error": "Cross-origin requests are not allowed."}, "")
                return True
            return False

        def _read_body(self):
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > MAX_REQUEST_BYTES:
                raise ValueError("Request is too large.")
            return self.rfile.read(length)

        def do_GET(self):
            if self.path == "/api/state":
                self._send(200, controller.state(), "")
                return
            if self.path == "/api/examples":
                examples = {
                    path.stem: path.read_text(encoding="utf-8")
                    for path in sorted(EXAMPLES.glob("*.lambda"))
                }
                self._send(200, examples, "")
                return
            if self.path not in PAGES:
                self._send(404, {"error": "Not found."}, "")
                return
            name, kind = PAGES[self.path]
            self._send(200, (STATIC / name).read_bytes(), kind)

        def do_POST(self):
            if self._reject_cross_origin():
                return
            try:
                raw = self._read_body()
                if self.path == "/api/upload":
                    name = self.headers.get("X-File-Name", "upload.lambda")
                    try:
                        text = raw.decode("utf-8")
                    except UnicodeError:
                        raise ValueError(
                            "The upload is not valid UTF-8. The applied source was not changed."
                        ) from None
                    state = controller.apply(text, name)
                elif self.path == "/api/source":
                    data = json.loads(raw.decode("utf-8"))
                    state = controller.apply(data["source"], data.get("name", "Manual input"))
                elif self.path == "/api/action":
                    data = json.loads(raw.decode("utf-8"))
                    state = controller.run(data["operation"], data["editor"])
                else:
                    self._send(404, {"error": "Not found."}, "")
                    return
                self._send(200, state, "")
            except (ValueError, KeyError, TypeError, json.JSONDecodeError, UnicodeError) as error:
                self._send(400, {"error": str(error)}, "")

    return Handler


def serve(controller, port=0):
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(controller))
    return server


def main():
    parser = argparse.ArgumentParser(description="LAMBDA workbench")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = serve(Controller(), args.port)
    print(f"LAMBDA workbench: http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
