"""Batches, notifications, request ids, and HTTP transport behavior."""

from __future__ import annotations

import json
import unittest

from support import Client, Limits, build_app


def request(method, params=None, id=None, *, notification=False):
    item = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        item["params"] = params
    if not notification:
        item["id"] = id
    return item


def health(id=None, *, notification=False):
    return request("service.health", {}, id, notification=notification)


class BatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client(build_app())

    def test_mixed_batch_is_answered_per_item_and_omits_notifications(self):
        body = self.client.answer([
            request("lambda.interpret", {"source": "6 * 7"}, "answer"),
            health(notification=True),
            request("lambda.typecheck", {"source": "(1, true)"}, 8),
            request("lambda.typecheck", {"source": "if then"}, "bad"),
            request("nope", {}, notification=True),
            42,
        ])
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 4)
        by_id = {item["id"]: item for item in body}
        self.assertEqual(by_id["answer"]["result"], {"type": "sint", "value": "42"})
        self.assertEqual(by_id[8]["result"], {"type": "(sint, bool)"})
        self.assertEqual(by_id["bad"]["error"]["code"], -32010)
        self.assertEqual(by_id[None]["error"]["code"], -32600)
        self.assertEqual(by_id[None]["error"]["data"], {"reason": "not_an_object"})

    def test_malformed_members_each_get_a_null_id_error(self):
        body = self.client.answer([health("ok"), "not-a-request-object",
                                   {"jsonrpc": "2.0", "id": 3}])
        self.assertEqual(len(body), 3)
        self.assertEqual(body[0], {"jsonrpc": "2.0", "id": "ok",
                                   "result": {"status": "ok", "version": "1.0"}})
        for item in body[1:]:
            self.assertEqual((item["id"], item["error"]["code"]), (None, -32600))

    def test_notification_only_batch_returns_204(self):
        response = self.client.post([
            health(notification=True),
            request("lambda.typecheck", {"source": "1 + 2"}, notification=True),
            request("lambda.interpret", {"source": "if then"}, notification=True),
        ])
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.get_data(), b"")

    def test_single_notification_returns_204_even_when_it_fails(self):
        for item in (health(notification=True),
                     request("does.not.exist", {}, notification=True),
                     request("lambda.interpret", {"source": ""}, notification=True)):
            with self.subTest(method=item["method"]):
                response = self.client.post(item)
                self.assertEqual(response.status_code, 204)
                self.assertEqual(response.get_data(), b"")

    def test_null_id_is_a_call_not_a_notification(self):
        body = self.client.answer(health(None))
        self.assertEqual(body, {"jsonrpc": "2.0", "id": None,
                                "result": {"status": "ok", "version": "1.0"}})

    def test_empty_batch_is_one_invalid_request(self):
        self.assertEqual(self.client.answer([]),
                         {"jsonrpc": "2.0", "id": None,
                          "error": {"code": -32600, "message": "Invalid Request",
                                    "data": {"reason": "empty_batch"}}})

    def test_batch_size_limit(self):
        body = self.client.answer([health(n) for n in range(20)])
        self.assertEqual(sorted(item["id"] for item in body), list(range(20)))
        too_many = self.client.answer([health(n) for n in range(21)])
        self.assertEqual(too_many["id"], None)
        self.assertEqual(too_many["error"]["data"], {"reason": "batch_too_large", "limit": 20})

    def test_nested_batch_is_an_invalid_item(self):
        body = self.client.answer([[health(1)]])
        self.assertEqual(body, [{"jsonrpc": "2.0", "id": None,
                                 "error": {"code": -32600, "message": "Invalid Request",
                                           "data": {"reason": "not_an_object"}}}])


class IdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client(build_app())

    def test_ids_are_copied_unchanged(self):
        for request_id in ("abc", "", "\u03bb-1", 0, -7, 1.5, 2**53, None):
            with self.subTest(id=request_id):
                body = self.client.answer(health(request_id))
                self.assertEqual(body["id"], request_id)
                self.assertIs(type(body["id"]), type(request_id))

    def test_error_responses_keep_the_id(self):
        body = self.client.call("lambda.interpret", {"source": "1 + true"}, id="keep-me")
        self.assertEqual(body["id"], "keep-me")


class TransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = build_app(Limits(max_body_bytes=4096))
        cls.client = Client(cls.app)
        cls.http = cls.app.test_client()

    def test_rpc_errors_use_http_200(self):
        response = self.client.post(request("does.not.exist", {}, 1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        response = self.client.post(raw=b"{")
        self.assertEqual(response.status_code, 200)

    def test_charset_parameter_is_accepted(self):
        response = self.client.post(health(1), content_type="application/json; charset=utf-8")
        self.assertEqual(response.status_code, 200)

    def test_other_media_types_are_415(self):
        body = json.dumps(health(1))
        for content_type in ("text/plain", "application/x-www-form-urlencoded",
                             "application/json; charset=latin-1"):
            with self.subTest(content_type=content_type):
                response = self.http.post("/rpc", data=body, content_type=content_type)
                self.assertEqual(response.status_code, 415)
                self.assertEqual(response.mimetype, "text/plain")
        response = self.http.post("/rpc", data=body)
        self.assertEqual(response.status_code, 415)

    def test_oversized_body_is_413(self):
        response = self.client.post(raw=b" " * 4097)
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.mimetype, "text/plain")

    def test_other_http_methods_are_405(self):
        for method in ("get", "put", "delete"):
            with self.subTest(method=method):
                response = getattr(self.http, method)("/rpc")
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response.headers["Allow"], "POST")

    def test_other_paths_are_404(self):
        for path in ("/", "/rpc/health", "/typecheck"):
            with self.subTest(path=path):
                response = self.http.post(path, data=json.dumps(health(1)),
                                          content_type="application/json")
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.mimetype, "text/plain")


if __name__ == "__main__":
    unittest.main()
