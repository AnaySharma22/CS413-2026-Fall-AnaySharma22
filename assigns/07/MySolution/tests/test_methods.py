"""Successful method calls. These all run the real LAMBDA3 implementation."""

from __future__ import annotations

import re
import unittest

from support import SOLUTION_DIR, Client, Limits, build_app

from lambda_rpc import lambda3_bridge

FACT = (
    "let fact : sint -> sint = fix fact(n: sint): sint => "
    "if n <= 1 then 1 else n * fact(n - 1) in fact({n}) end"
)


class HealthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client(build_app())

    def test_health_reports_status_and_version(self):
        body = self.client.call("service.health", {}, id="health-1")
        self.assertEqual(body, {"jsonrpc": "2.0", "id": "health-1",
                                "result": {"status": "ok", "version": "1.0"}})

    def test_health_accepts_absent_params(self):
        body = self.client.call("service.health", id=2)
        self.assertEqual(body["result"], {"status": "ok", "version": "1.0"})

    def test_health_rejects_unknown_params(self):
        error = self.client.call("service.health", {"verbose": True})["error"]
        self.assertEqual(error["code"], -32602)
        self.assertEqual(error["data"], {"param": "verbose", "reason": "unknown_param"})


class TypecheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client(build_app())

    def test_types_are_formatted_by_lambda3(self):
        cases = {
            "1 + 2": "sint",
            "1 < 2": "bool",
            "(1, true)": "(sint, bool)",
            "lam (x: sint) => (x, x <= 1)": "sint -> (sint, bool)",
            "list_cons(1, list_cons(2, list_nil()))": "List[sint]",
            "print(1)": "unit",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                body = self.client.call("lambda.typecheck", {"source": source})
                self.assertEqual(body["result"], {"type": expected})

    def test_typecheck_does_not_evaluate(self):
        body = self.client.call("lambda.typecheck", {"source": "print(7)"})
        self.assertEqual(body["result"], {"type": "unit"})
        body = self.client.call("lambda.typecheck", {"source": "10 / 0"})
        self.assertEqual(body["result"], {"type": "sint"})


class InterpretTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client(build_app())

    def interpret(self, source, **params):
        return self.client.call("lambda.interpret", {"source": source, **params})

    def test_arithmetic(self):
        self.assertEqual(self.interpret("20 + 22")["result"], {"type": "sint", "value": "42"})
        self.assertEqual(self.interpret("(7 - 10) * 3")["result"], {"type": "sint", "value": "-9"})

    def test_factorial(self):
        self.assertEqual(self.interpret(FACT.format(n=6))["result"],
                         {"type": "sint", "value": "720"})
        self.assertEqual(self.interpret(FACT.format(n=30))["result"]["value"],
                         "265252859812191058636308480000000")

    def test_tuple(self):
        self.assertEqual(self.interpret("(1, true)")["result"],
                         {"type": "(sint, bool)", "value": "(1, true)"})

    def test_list(self):
        self.assertEqual(self.interpret("list_cons(1, list_cons(2, list_nil()))")["result"],
                         {"type": "List[sint]", "value": "[1, 2]"})

    def test_functions_are_formatted_without_their_closure(self):
        cases = {
            "let f : sint -> sint = lam (x: sint) => x in f end": "<lam>",
            "let y : sint = 12345 in lam (x: sint) => x + y end": "<lam>",
            "fix f(n: sint): sint => n": "<fix>",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                result = self.interpret(source)["result"]
                self.assertEqual(result, {"type": "sint -> sint", "value": expected})
                self.assertNotIn("12345", str(result))

    def test_printed_text_is_returned_as_output(self):
        result = self.interpret("print(1234567890)")["result"]
        self.assertEqual(result, {"type": "unit", "value": "()", "output": "1234567890\n"})

    def test_printed_text_is_truncated_at_the_output_limit(self):
        client = Client(build_app(Limits(max_output_chars=4)))
        result = client.call("lambda.interpret", {"source": "print(1234567890)"})["result"]
        self.assertEqual(result["output"], "1234")
        self.assertIs(result["output_truncated"], True)

    def test_deepest_source_that_fits_the_size_limit(self):
        depth = (65_536 - 1) // 2
        source = "(" * depth + "1" + ")" * depth
        self.assertEqual(self.interpret(source)["result"], {"type": "sint", "value": "1"})


class LibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client(build_app())

    def interpret(self, source, libraries):
        return self.client.call("lambda.interpret", {"source": source, "libraries": libraries})

    def test_each_library_can_be_used(self):
        cases = [
            ("list_reverse(list_range(1, 5))", ["list"], "List[sint]", "[4, 3, 2, 1]"),
            ("optn_get_default(optn_nil(), 9)", ["optn"], "sint", "9"),
            ("a1sz_length(a1sz_make_ncpy(3, 7))", ["a1sz"], "sint", "3"),
            ("strm_to_list(strm_take(strm_range(0, 100), 3))", ["strm"], "List[sint]", "[0, 1, 2]"),
            ("list_length(list_range(0, 5))", ["list", "optn", "a1sz", "strm"], "sint", "5"),
        ]
        for source, libraries, typ, value in cases:
            with self.subTest(source=source):
                self.assertEqual(self.interpret(source, libraries)["result"],
                                 {"type": typ, "value": value})

    def test_library_names_are_unbound_without_the_library(self):
        error = self.client.call("lambda.interpret",
                                 {"source": "list_range(1, 5)"})["error"]
        self.assertEqual(error["code"], -32011)

    def test_syntax_error_positions_refer_to_the_client_source(self):
        body = self.client.call("lambda.typecheck",
                                {"source": "1 +\n  if then", "libraries": ["list"]})
        self.assertEqual(body["error"]["code"], -32010)
        self.assertEqual(body["error"]["data"]["line"], 2)
        self.assertEqual(body["error"]["data"]["source_line"], "  if then")


class CompileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client(build_app())
        cls.lambda3 = lambda3_bridge.load()

    def compile(self, source, target):
        return self.client.call("lambda.compile", {"source": source, "target": target})

    def test_code_is_exactly_what_lambda3_generates(self):
        source = FACT.format(n=5)
        expression, _ = self.lambda3.d0exp_parse_and_typecheck(source)
        expected = {
            "python": self.lambda3.d0exp_compile(expression),
            "javascript": self.lambda3.d0exp_compile_js(expression),
        }
        for target, code in expected.items():
            with self.subTest(target=target):
                result = self.compile(source, target)["result"]
                self.assertEqual(result, {"target": target, "code": code})

    def test_compiled_code_is_returned_not_run(self):
        for target in ("python", "javascript"):
            with self.subTest(target=target):
                result = self.compile("print(424242)", target)["result"]
                self.assertEqual(set(result), {"target", "code"})
                self.assertIn("424242", result["code"])

    def test_service_never_executes_generated_code(self):
        forbidden = re.compile(
            r"(?<!def )(?<![.\w])(exec|eval|compile|__import__)\s*\(|subprocess|os\.system|\bnode\b"
        )
        for path in (SOLUTION_DIR / "lambda_rpc").glob("*.py"):
            for number, line in enumerate(path.read_text("utf-8").splitlines(), 1):
                code = line.split("#", 1)[0]
                with self.subTest(file=path.name, line=number):
                    self.assertIsNone(forbidden.search(code), line)

    def test_oversized_generated_code_is_rejected(self):
        client = Client(build_app(Limits(max_result_chars=50)))
        error = client.call("lambda.compile", {"source": "1 + 2", "target": "python"})["error"]
        self.assertEqual(error, {"code": -32014, "message": "Result too large",
                                 "data": {"limit_chars": 50}})


if __name__ == "__main__":
    unittest.main()
