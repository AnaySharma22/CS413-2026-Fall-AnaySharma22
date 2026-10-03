"""HTTP checks for source entry, rejection, and dispatch. The view files are not imported."""

import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import serve
from backend import Backend
from controller import Controller


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.controller = Controller(Backend(bounded=False))
        self.server = serve(self.controller, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base = f"http://{host}:{port}"

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=2)

    def request(self, path, data=None, headers=None, method=None):
        req = urllib.request.Request(
            self.base + path,
            data=data,
            headers=headers or {},
            method=method,
        )
        try:
            with urllib.request.urlopen(req) as response:
                body = response.read()
                return response.status, dict(response.headers), body
        except urllib.error.HTTPError as error:
            return error.code, dict(error.headers), error.read()

    def test_manual_input_edit_and_rejected_replacement(self):
        page, _, html = self.request("/")
        self.assertEqual(page, 200)
        self.assertIn(b"Apply changes", html)
        self.assertIn(b"Execute", html)
        status, _, raw = self.request(
            "/api/source",
            json.dumps({"source": "D0Eint(1)", "name": "Manual input"}).encode(),
            {"Content-Type": "application/json"},
        )
        self.assertEqual(status, 200)
        state = json.loads(raw)
        self.assertEqual(state["revision"], 1)
        status, _, raw = self.request(
            "/api/source",
            json.dumps({"source": "   ", "name": "Bad"}).encode(),
            {"Content-Type": "application/json"},
        )
        self.assertEqual(status, 400)
        self.assertIn(b"empty", raw)
        state = self.controller.state()
        self.assertEqual(state["source"], "D0Eint(1)")
        self.assertEqual(state["revision"], 1)
        status, _, raw = self.request(
            "/api/upload",
            b"\xff\xfe",
            {"X-File-Name": "bad.lambda", "Content-Type": "application/octet-stream"},
        )
        self.assertEqual(status, 400)
        self.assertIn(b"UTF-8", raw)
        self.assertEqual(self.controller.state()["source"], "D0Eint(1)")

    def test_action_uses_editor_text_and_reports_outcome(self):
        self.controller.apply('D0Evar("x")', "Manual input")
        status, _, raw = self.request(
            "/api/action",
            json.dumps({"operation": "lint", "editor": 'D0Evar("x")'}).encode(),
            {"Content-Type": "application/json"},
        )
        self.assertEqual(status, 200)
        result = json.loads(raw)["result"]
        self.assertEqual(result["operation"], "lint")
        self.assertEqual(result["outcome"], "language_error")
        self.assertIn("x", result["text"])
        status, _, _raw = self.request(
            "/api/action",
            json.dumps({"operation": "execute", "editor": 'D0Evar("x")'}).encode(),
            {"Content-Type": "application/json"},
        )
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
