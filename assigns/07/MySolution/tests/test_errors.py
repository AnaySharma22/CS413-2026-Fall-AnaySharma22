"""Error paths: LAMBDA errors, envelope and params validation, and failures.

LAMBDA syntax, type, and runtime errors and the real deadline run LAMBDA3.
Test doubles replace the worker only to inject failures that a correct
LAMBDA3 cannot produce on demand (a crash, an unexpected exception, or an
instant timeout).
"""

from __future__ import annotations

import time
import unittest

from support import Client, Limits, build_app

from lambda_rpc.worker import WorkerFailure, WorkerTimeout

FIB = (
    "let fib : sint -> sint = fix fib(n: sint): sint => "
    "if n <= 1 then n else fib(n - 1) + fib(n - 2) in fib({n}) end"
)
SUM = (
    "let sum : sint -> sint = fix sum(n: sint): sint => "
    "if n <= 0 then 0 else n + sum(n - 1) in sum({n}) end"
)


class LambdaErrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client(build_app())

    def error(self, method, source, **params):
        body = self.client.call(method, {"source": source, **params}, id="e")
        self.assertEqual(body["id"], "e")
        self.assertNotIn("result", body)
        return body["error"]

    def test_syntax_and_type_errors_have_distinct_codes(self):
        syntax = self.error("lambda.typecheck", "if then")
        type_error = self.error("lambda.typecheck", "1 + true")
        self.assertEqual(syntax["code"], -32010)
        self.assertEqual(syntax["message"], "LAMBDA syntax error")
        self.assertEqual(type_error["code"], -32011)
        self.assertEqual(type_error["message"], "LAMBDA type error")

    def test_syntax_error_reports_position(self):
        self.assertEqual(self.error("lambda.typecheck", "if then")["data"],
                         {"message": "Expected an expression", "line": 1, "column": 4,
                          "source_line": "if then"})
        data = self.error("lambda.interpret", "let x : sint = 1 in\n  x +\nend")["data"]
        self.assertEqual(data["line"], 3)

    def test_each_source_method_checks_before_running(self):
        for method, extra in (("lambda.typecheck", {}), ("lambda.interpret", {}),
                              ("lambda.compile", {"target": "python"})):
            with self.subTest(method=method):
                self.assertEqual(self.error(method, "if then", **extra)["code"], -32010)
                self.assertEqual(self.error(method, "1 + true", **extra)["code"], -32011)

    def test_unbound_variable_is_rejected(self):
        for method, extra in (("lambda.typecheck", {}), ("lambda.interpret", {}),
                              ("lambda.compile", {"target": "javascript"})):
            with self.subTest(method=method):
                error = self.error(method, "y + 1", **extra)
                self.assertEqual(error, {"code": -32011, "message": "LAMBDA type error",
                                         "data": {"message": "unbound variable 'y'"}})

    def test_ill_typed_program_is_never_evaluated(self):
        error = self.error("lambda.interpret", "let u : unit = print(5) in u + 1 end")
        self.assertEqual(error["code"], -32011)
        self.assertNotIn("output", error.get("data", {}))

    def test_runtime_errors(self):
        cases = {
            "list_head(list_nil())": "list_head: nonempty list expected",
            "10 / 0": "division by zero",
        }
        for source, message in cases.items():
            with self.subTest(source=source):
                self.assertEqual(self.error("lambda.interpret", source),
                                 {"code": -32013, "message": "LAMBDA runtime error",
                                  "data": {"message": message, "kind": "runtime"}})
        index = self.error("lambda.interpret", "a1sz_getat(a1sz_make_ncpy(3, 7), 5)")
        self.assertEqual((index["code"], index["data"]["kind"]), (-32013, "runtime"))

    def test_recursion_too_deep_for_the_interpreter(self):
        client = Client(build_app(Limits(recursion_limit=20_000)))
        error = client.call("lambda.interpret", {"source": SUM.format(n=10_000)})["error"]
        self.assertEqual(error["code"], -32013)
        self.assertEqual(error["data"]["kind"], "recursion_depth")


class RealDeadlineTests(unittest.TestCase):
    def test_slow_program_is_stopped_and_service_keeps_working(self):
        client = Client(build_app(Limits(time_limit_seconds=1.0)))
        started = time.perf_counter()
        body = client.call("lambda.interpret", {"source": FIB.format(n=27)}, id="slow")
        elapsed = time.perf_counter() - started
        self.assertEqual(body, {"jsonrpc": "2.0", "id": "slow",
                                "error": {"code": -32012, "message": "Execution timeout",
                                          "data": {"limit_seconds": 1.0}}})
        self.assertLess(elapsed, 10)
        quick = client.call("lambda.interpret", {"source": FIB.format(n=10)}, id="quick")
        self.assertEqual(quick["result"], {"type": "sint", "value": "55"})


class EnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client(build_app())

    def assert_invalid(self, body, reason):
        self.assertEqual(body, {"jsonrpc": "2.0", "id": None,
                                "error": {"code": -32600, "message": "Invalid Request",
                                          "data": {"reason": reason}}})

    def test_malformed_json(self):
        for raw in (b'{"jsonrpc":', b"", b"{'jsonrpc': '2.0'}", b"\xff\xfe", b"[1,]"):
            with self.subTest(raw=raw):
                body = self.client.answer(raw=raw)
                self.assertEqual(body["id"], None)
                self.assertEqual(body["error"]["code"], -32700)
                self.assertEqual(body["error"]["data"], {"reason": "invalid_json"})

    def test_non_json_constants_are_parse_errors(self):
        for constant in (b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(constant=constant):
                raw = b'{"jsonrpc": "2.0", "method": "service.health", "id": ' + constant + b"}"
                self.assertEqual(self.client.answer(raw=raw)["error"]["code"], -32700)

    def test_deeply_nested_json_is_a_parse_error(self):
        body = self.client.answer(raw=b"[" * 200_000 + b"]" * 200_000)
        self.assertEqual(body["error"]["code"], -32700)
        self.assertEqual(body["error"]["data"], {"reason": "nesting_too_deep"})

    def test_invalid_envelopes_answer_with_null_id(self):
        base = {"jsonrpc": "2.0", "method": "service.health", "id": 9}
        cases = [
            (42, "not_an_object"),
            ("service.health", "not_an_object"),
            (None, "not_an_object"),
            ({**base, "jsonrpc": "1.0"}, "jsonrpc_must_be_2.0"),
            ({**base, "jsonrpc": 2.0}, "jsonrpc_must_be_2.0"),
            ({"method": "service.health", "id": 9}, "jsonrpc_must_be_2.0"),
            ({"jsonrpc": "2.0", "id": 9}, "method_must_be_string"),
            ({**base, "method": 5}, "method_must_be_string"),
            ({**base, "params": "x"}, "params_must_be_object_or_array"),
            ({**base, "params": None}, "params_must_be_object_or_array"),
            ({**base, "id": True}, "invalid_id"),
            ({**base, "id": {"n": 1}}, "invalid_id"),
            ({**base, "id": [1]}, "invalid_id"),
            ({**base, "extra": 1}, "unknown_member"),
        ]
        for payload, reason in cases:
            with self.subTest(payload=payload):
                self.assert_invalid(self.client.answer(payload), reason)

    def test_unknown_method_keeps_the_id(self):
        for method in ("does.not.exist", "rpc.discover", "Service.Health", ""):
            with self.subTest(method=method):
                body = self.client.call(method, {}, id="m")
                self.assertEqual(body, {"jsonrpc": "2.0", "id": "m",
                                        "error": {"code": -32601, "message": "Method not found",
                                                  "data": {"method": method}}})

    def test_positional_params_are_invalid_params(self):
        body = self.client.call("lambda.typecheck", ["1 + 2"], id=3)
        self.assertEqual(body["id"], 3)
        self.assertEqual(body["error"]["code"], -32602)
        self.assertEqual(body["error"]["data"], {"param": None, "reason": "params_not_object"})


class ParamsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client(build_app())

    def invalid(self, method, params):
        body = self.client.call(method, params, id="p")
        self.assertEqual(body["id"], "p")
        self.assertEqual(body["error"]["code"], -32602)
        self.assertEqual(body["error"]["message"], "Invalid params")
        return body["error"]["data"]

    def test_absent_source(self):
        for method in ("lambda.typecheck", "lambda.interpret"):
            with self.subTest(method=method):
                self.assertEqual(self.invalid(method, {}),
                                 {"param": "source", "reason": "missing"})
        body = self.client.call("lambda.interpret", None, id="no-params")
        self.assertEqual(body["error"]["data"], {"param": "source", "reason": "missing"})

    def test_source_of_the_wrong_type(self):
        for source in (12, None, True, ["1"], {"text": "1"}):
            with self.subTest(source=source):
                self.assertEqual(self.invalid("lambda.interpret", {"source": source}),
                                 {"param": "source", "reason": "not_a_string"})

    def test_blank_source(self):
        for source in ("", "   ", "\n\t "):
            with self.subTest(source=source):
                self.assertEqual(self.invalid("lambda.interpret", {"source": source}),
                                 {"param": "source", "reason": "blank"})

    def test_oversized_source(self):
        for source in ("1" + " " * 65_536, "1" + "\u00e9" * 32_768):
            with self.subTest(chars=len(source)):
                self.assertEqual(self.invalid("lambda.typecheck", {"source": source}),
                                 {"param": "source", "reason": "too_large",
                                  "limit_bytes": 65_536})

    def test_source_at_the_size_limit_is_accepted(self):
        body = self.client.call("lambda.typecheck", {"source": "1" + " " * 65_535})
        self.assertEqual(body["result"], {"type": "sint"})

    def test_unknown_param(self):
        self.assertEqual(self.invalid("lambda.interpret", {"src": "1 + 2"}),
                         {"param": "src", "reason": "unknown_param"})
        self.assertEqual(self.invalid("lambda.typecheck", {"source": "1", "target": "python"}),
                         {"param": "target", "reason": "unknown_param"})

    def test_compile_target(self):
        allowed = ["python", "javascript"]
        self.assertEqual(self.invalid("lambda.compile", {"source": "1 + 2"}),
                         {"param": "target", "reason": "missing", "allowed": allowed})
        for target in ("ruby", "Python", "", 5, None):
            with self.subTest(target=target):
                self.assertEqual(self.invalid("lambda.compile", {"source": "1", "target": target}),
                                 {"param": "target", "reason": "unsupported", "allowed": allowed})

    def test_libraries(self):
        allowed = ["list", "optn", "a1sz", "strm"]
        for libraries in ("list", ["nope"], ["list", "list"], [1], {"list": True}, None):
            with self.subTest(libraries=libraries):
                self.assertEqual(
                    self.invalid("lambda.interpret", {"source": "1", "libraries": libraries}),
                    {"param": "libraries", "reason": "invalid", "allowed": allowed})


class RecordingRunner:
    def __init__(self):
        self.jobs = []

    def run(self, job):
        self.jobs.append(job)
        return {"ok": {"type": "sint"}}


class RaisingRunner:
    def __init__(self, error):
        self.error = error

    def run(self, job):
        raise self.error


class OutcomeRunner:
    def __init__(self, outcome):
        self.outcome = outcome

    def run(self, job):
        return self.outcome


SECRET = r'Traceback (most recent call last):\n  File "C:\secret\lambda3.py", line 9'


class InjectedFailureTests(unittest.TestCase):
    def assert_internal_error(self, runner, request_id):
        client = Client(build_app(runner=runner))
        with self.assertLogs("lambda_rpc", level="ERROR") as logs:
            body = client.call("lambda.interpret", {"source": "1 + 2"}, id=request_id)
        self.assertEqual(body["id"], request_id)
        self.assertEqual(body["error"]["code"], -32603)
        self.assertEqual(body["error"]["message"], "Internal error")
        reference = body["error"]["data"]["reference"]
        self.assertEqual(set(body["error"]["data"]), {"reference"})
        self.assertIn(f"reference={reference}", "\n".join(logs.output))
        return logs

    def test_unexpected_exception_preserves_id_without_traceback(self):
        logs = self.assert_internal_error(RaisingRunner(RuntimeError(SECRET)), "req-17")
        self.assertIn("secret", "\n".join(logs.output))

    def test_worker_crash_preserves_id(self):
        self.assert_internal_error(RaisingRunner(WorkerFailure("exit code -11")), 17)

    def test_worker_internal_outcome_is_logged_not_returned(self):
        logs = self.assert_internal_error(OutcomeRunner({"internal": SECRET}), None)
        self.assertIn("secret", "\n".join(logs.output))

    def test_injected_timeout_preserves_id(self):
        client = Client(build_app(Limits(time_limit_seconds=2.5), RaisingRunner(WorkerTimeout())))
        for request_id in ("t-1", 0, None):
            with self.subTest(id=request_id):
                body = client.call("lambda.interpret", {"source": "1"}, id=request_id)
                self.assertEqual(body, {"jsonrpc": "2.0", "id": request_id,
                                        "error": {"code": -32012, "message": "Execution timeout",
                                                  "data": {"limit_seconds": 2.5}}})

    def test_failure_in_one_batch_item_does_not_affect_the_others(self):
        client = Client(build_app(runner=RaisingRunner(RuntimeError(SECRET))))
        with self.assertLogs("lambda_rpc", level="ERROR"):
            body = client.answer([
                {"jsonrpc": "2.0", "method": "lambda.interpret", "params": {"source": "1"}, "id": "a"},
                {"jsonrpc": "2.0", "method": "service.health", "id": "b"},
            ])
        by_id = {item["id"]: item for item in body}
        self.assertEqual(by_id["a"]["error"]["code"], -32603)
        self.assertEqual(by_id["b"]["result"], {"status": "ok", "version": "1.0"})

    def test_invalid_params_never_reach_lambda3(self):
        runner = RecordingRunner()
        client = Client(build_app(runner=runner))
        for params in ({}, {"source": ""}, {"source": 1}, {"source": "1", "x": 1}):
            client.call("lambda.interpret", params)
        client.call("lambda.compile", {"source": "1", "target": "ruby"})
        self.assertEqual(runner.jobs, [])


if __name__ == "__main__":
    unittest.main()
