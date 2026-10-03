"""Free-variable analysis, lint, and interpretation. No web server."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT))

import lambda1 as lang
from backend import Backend, perform, read_source, run_bounded


class FreeVariableTests(unittest.TestCase):
    def test_every_constructor_scope_and_duplicates(self):
        cases = {
            "D0Eint(2)": set(),
            "D0Ebtf(True)": set(),
            "D0Evar('x')": {"x"},
            'D0Eop1("+1", D0Evar("x"))': {"x"},
            'D0Eop2("+", D0Evar("x"), D0Evar("x"))': {"x"},
            'D0Elam("x", D0Eint(1))': set(),
            'D0Elam("x", D0Elam("x", D0Evar("x")))': set(),
            'D0Elam("x", D0Elam("y", D0Epair(D0Evar("x"), D0Evar("z"))))': {"z"},
            'D0Efix("f", "x", D0Eapp(D0Evar("f"), D0Evar("x")))': set(),
            'D0Efix("f", "x", D0Evar("y"))': {"y"},
            'D0Eapp(D0Evar("f"), D0Evar("x"))': {"f", "x"},
            'D0Eif0(D0Ebtf(False), D0Evar("left"), D0Evar("right"))': {"left", "right"},
            'D0Elet("x", D0Evar("x"), D0Eint(1))': {"x"},
            'D0Elet("x", D0Eint(1), D0Evar("x"))': set(),
            'D0Elet("x", D0Eint(1), D0Elet("y", D0Evar("x"), D0Evar("z")))': {"z"},
            'D0Epair(D0Evar("a"), D0Evar("b"))': {"a", "b"},
            'D0Epfst(D0Evar("a"))': {"a"},
            'D0Epsnd(D0Evar("a"))': {"a"},
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                found = lang.d0exp_fvset(read_source(source))
                self.assertIsInstance(found, frozenset)
                self.assertEqual(found, expected)

    def test_reader_accepts_comments_and_negatives(self):
        expr = read_source("# note\nD0Eint(-2)")
        self.assertEqual(expr.arg1, -2)

    def test_reader_rejects_arbitrary_python(self):
        samples = [
            '__import__("os")',
            "D0Eint(True)",
            "D0Evar(1)",
            "D0Eint(1+2)",
            "D0Eint(arg1=2)",
            "[D0Eint(2)]",
            "D0E000()",
            "   ",
        ]
        for source in samples:
            with self.subTest(source=source):
                with self.assertRaises((ValueError, SyntaxError)):
                    read_source(source)


class LintAndInterpretTests(unittest.TestCase):
    def test_lint_success_and_open_program(self):
        closed = perform("lint", 'D0Elam("x", D0Evar("x"))')
        self.assertEqual(closed["outcome"], "success")
        opened = perform("lint", 'D0Epair(D0Evar("z"), D0Evar("a"))')
        self.assertEqual(opened["outcome"], "language_error")
        self.assertEqual(opened["text"], "Undeclared variables: a, z")

    def test_lint_does_not_evaluate_division_by_zero(self):
        source = 'D0Eop2("/", D0Eint(1), D0Eint(0))'
        with patch.object(lang, "d0exp_evaluate", side_effect=AssertionError("evaluated")):
            result = perform("lint", source)
        self.assertEqual(result["outcome"], "success")
        interpreted = perform("interpret", source)
        self.assertEqual(interpreted["outcome"], "runtime_error")
        self.assertIn("ZeroDivisionError", interpreted["text"])

    def test_examples_and_base_cases(self):
        expected = {
            "Arithmetic": 42,
            "Factorial": 120,
            "Fibonacci": 55,
        }
        for name, value in expected.items():
            source = (ROOT / "examples" / f"{name}.lambda").read_text(encoding="utf-8")
            result = perform("interpret", source)
            self.assertEqual(result, {"outcome": "success", "text": f"D0Vint(arg1={value})"})
            if name == "Arithmetic":
                continue
            for n in (0, 1):
                base = source.rsplit("D0Eint(", 1)[0] + f"D0Eint({n}))"
                base_result = perform("interpret", base)
                wanted = 1 if name == "Factorial" else n
                self.assertEqual(base_result["text"], f"D0Vint(arg1={wanted})")

    def test_malformed_input_and_error_sentinel(self):
        self.assertEqual(perform("interpret", "D0Eint(")["outcome"], "input_error")
        self.assertEqual(
            perform("interpret", 'D0Epair(D0Eint(1), D0Evar("x"))')["outcome"],
            "runtime_error",
        )
        self.assertNotEqual(
            perform("interpret", 'D0Evar("x")')["outcome"],
            "success",
        )

    def test_worker_and_timeout(self):
        source = (ROOT / "examples" / "Arithmetic.lambda").read_text(encoding="utf-8")
        self.assertEqual(
            Backend().run("interpret", source)["text"],
            "D0Vint(arg1=42)",
        )
        timed_out = run_bounded(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            "D0Eint(1)",
            0.2,
        )
        self.assertEqual(timed_out["outcome"], "backend_error")
        self.assertIn("3-second", timed_out["text"])

    def test_placeholders_are_not_success(self):
        for operation in ("typecheck", "compile", "execute"):
            result = perform(operation, "D0Eint(1)")
            self.assertEqual(result["outcome"], "not_implemented")
            self.assertNotIn("success", result["outcome"])
            self.assertNotEqual(result["text"], "")


if __name__ == "__main__":
    unittest.main()
