"""End-to-end HTTP client flow and a lightweight UI contract check."""

from __future__ import annotations

import re
import unittest

from support import Client, SOLUTION_DIR, StreamTable, QueensSolver, build_app


class ClientFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solver = QueensSolver()
        cls.app = build_app(table=StreamTable(solver=cls.solver))
        cls.client = Client(cls.app)

    def test_http_flow_finds_all_eight_queens_solutions(self):
        opened = self.client.call("queens.open", {"size": 8})["result"]
        stream_id = opened["stream_id"]
        solutions = []
        event_count = 0
        done = False
        while not done:
            result = self.client.call(
                "queens.next", {"stream_id": stream_id, "limit": 32}
            )["result"]
            event_count += len(result["events"])
            self.assertLessEqual(len(result["events"]), 32)
            for event in result["events"]:
                if event["event"] == "solution":
                    solutions.append(tuple(event["board"]))
                if event["event"] == "done":
                    self.assertTrue(result["done"])
            done = result["done"]
        self.assertEqual(len(solutions), 92)
        self.assertEqual(len(set(solutions)), 92)
        self.assertGreater(event_count, 92)
        closed = self.client.call("queens.close", {"stream_id": stream_id})["result"]
        self.assertEqual(closed, {"closed": True})

    def test_static_page_exposes_required_controls(self):
        page = self.app.test_client().get("/")
        self.assertEqual(page.status_code, 200)
        html = page.get_data(as_text=True)
        for control in ("start", "step", "play", "pause", "next-solution", "reset"):
            self.assertIn(f'id="{control}"', html)
        css = self.app.test_client().get("/static/app.css")
        js = self.app.test_client().get("/static/app.js")
        self.assertEqual(css.status_code, 200)
        self.assertEqual(js.status_code, 200)
        script = js.get_data(as_text=True)
        self.assertIn("queens.open", script)
        self.assertIn("queens.next", script)
        self.assertIn("queens.close", script)
        # Incremental fetch: the client asks for a small batch, not the whole trace.
        self.assertRegex(script, r"limit:\s*BATCH|limit:\s*\d+")
        self.assertNotRegex(script, r"limit:\s*100000|limit:\s*999999")
        self.assertIn("showError", script)

    def test_browser_checklist_is_documented(self):
        testing = (SOLUTION_DIR / "TESTING.md").read_text(encoding="utf-8")
        self.assertIn("Browser checklist", testing)
        for label in ("Start", "Step", "Play", "Pause", "Next solution", "Reset", "RPC failure"):
            self.assertTrue(re.search(label, testing), label)


if __name__ == "__main__":
    unittest.main()
