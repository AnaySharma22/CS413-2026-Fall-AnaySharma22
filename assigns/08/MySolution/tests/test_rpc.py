"""JSON-RPC envelope, queens methods, lifecycle, and validation."""

from __future__ import annotations

import json
import unittest

from support import Client, Limits, StreamTable, QueensSolver, build_app


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class RpcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solver = QueensSolver()

    def setUp(self):
        self.client = Client(build_app(table=StreamTable(solver=self.solver)))

    def test_health_preserves_id(self):
        body = self.client.call("service.health", {}, id="h1")
        self.assertEqual(body, {"jsonrpc": "2.0", "id": "h1",
                                "result": {"status": "ok", "version": "1.0"}})

    def test_open_does_not_force_and_next_respects_limits(self):
        opened = self.client.call("queens.open", {"size": 5}, id=2)["result"]
        self.assertEqual(opened["size"], 5)
        self.assertIsInstance(opened["stream_id"], str)
        self.assertGreaterEqual(len(opened["stream_id"]), 32)
        one = self.client.call(
            "queens.next", {"stream_id": opened["stream_id"], "limit": 1}, id=3
        )["result"]
        self.assertEqual(len(one["events"]), 1)
        self.assertFalse(one["done"])
        many = self.client.call(
            "queens.next", {"stream_id": opened["stream_id"], "limit": 32}, id=4
        )["result"]
        self.assertLessEqual(len(many["events"]), 32)
        self.client.call("queens.close", {"stream_id": opened["stream_id"]}, id=5)

    def test_close_unknown_and_repeated_next_after_done(self):
        opened = self.client.call("queens.open", {"size": 4})["result"]
        stream_id = opened["stream_id"]
        done = False
        while not done:
            result = self.client.call(
                "queens.next", {"stream_id": stream_id, "limit": 32}
            )["result"]
            done = result["done"]
        again = self.client.call(
            "queens.next", {"stream_id": stream_id, "limit": 1}
        )["result"]
        self.assertEqual(again, {"events": [], "done": True})
        closed = self.client.call("queens.close", {"stream_id": stream_id})["result"]
        self.assertEqual(closed, {"closed": True})
        missing = self.client.call("queens.next", {"stream_id": stream_id, "limit": 1})
        self.assertEqual(missing["error"]["code"], -32020)
        again_close = self.client.call("queens.close", {"stream_id": stream_id})
        self.assertEqual(again_close["error"]["code"], -32020)

    def test_unknown_method_and_invalid_params(self):
        self.assertEqual(
            self.client.call("nope", {})["error"]["code"], -32601
        )
        for params, reason in (
            ({}, "missing"),
            ({"size": 3}, "out_of_range"),
            ({"size": 11}, "out_of_range"),
            ({"size": 8.5}, "not_an_integer"),
            ({"size": True}, "not_an_integer"),
            ({"size": "8"}, "not_an_integer"),
        ):
            with self.subTest(params=params):
                error = self.client.call("queens.open", params)["error"]
                self.assertEqual(error["code"], -32602)
                self.assertEqual(error["data"]["reason"], reason)
        opened = self.client.call("queens.open", {"size": 4})["result"]["stream_id"]
        for params in (
            {"stream_id": opened},
            {"stream_id": opened, "limit": 0},
            {"stream_id": opened, "limit": 33},
            {"stream_id": opened, "limit": 1.5},
        ):
            with self.subTest(params=params):
                self.assertEqual(
                    self.client.call("queens.next", params)["error"]["code"], -32602
                )

    def test_malformed_envelope_and_notification(self):
        response = self.client.raw(b'{"jsonrpc":')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["error"]["code"], -32700)
        bad = self.client.call("service.health", {}, id=True)
        # id True never becomes a request; parse_request rejects before call
        # so we send a raw body instead.
        response = self.client.raw(
            json.dumps({"jsonrpc": "1.0", "method": "service.health", "id": 1})
        )
        self.assertEqual(response.get_json()["id"], None)
        self.assertEqual(response.get_json()["error"]["code"], -32600)
        response = self.client.raw(
            json.dumps({"jsonrpc": "2.0", "method": "service.health", "params": {}})
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.get_data(), b"")

    def test_expired_stream_is_unknown(self):
        clock = Clock()
        table = StreamTable(
            solver=self.solver, limits=Limits(stream_idle_seconds=10), clock=clock
        )
        client = Client(build_app(Limits(stream_idle_seconds=10), table))
        stream_id = client.call("queens.open", {"size": 4})["result"]["stream_id"]
        clock.now = 11
        error = client.call("queens.next", {"stream_id": stream_id, "limit": 1})["error"]
        self.assertEqual(error["code"], -32020)

    def test_event_json_shapes(self):
        stream_id = self.client.call("queens.open", {"size": 4})["result"]["stream_id"]
        seen = set()
        while True:
            result = self.client.call(
                "queens.next", {"stream_id": stream_id, "limit": 32}
            )["result"]
            for event in result["events"]:
                seen.add(event["event"])
                if event["event"] == "done":
                    self.assertEqual(set(event), {"event"})
                elif event["event"] == "solution":
                    self.assertEqual(set(event), {"event", "board"})
                else:
                    self.assertEqual(set(event), {"event", "column", "row", "board"})
            if result["done"]:
                break
        self.assertEqual(seen, {"try", "place", "reject", "backtrack", "solution", "done"})


if __name__ == "__main__":
    unittest.main()
