"""unittest suite. Run with: python -m unittest discover -s MySolution/tests -v"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT))

import lambda1_vp
from lambda1_vp import D0Eint, D0Elam, D0Eop2, D0Evar, d0exp_fvset
from samples import fv_cases, pretty_cases, substitution_cases
from visitors import d0exp_pretty, d0exp_substitute


class TreeIds:
    def __init__(self):
        self.rows = []

    def walk(self, expression):
        from lambda1_vp import D0ExpVisitor

        visitor = _Structure(self)
        expression.accept(visitor)
        return tuple(self.rows)


class _Structure(lambda1_vp.D0ExpVisitor[None]):
    def __init__(self, box):
        self.box = box

    def _kids(self, dexp, *children):
        self.box.rows.append((id(dexp), dexp.ctag, tuple(id(child) for child in children)))
        for child in children:
            if hasattr(child, "accept"):
                child.accept(self)

    def visit_int(self, dexp):
        self._kids(dexp)

    def visit_btf(self, dexp):
        self._kids(dexp)

    def visit_var(self, dexp):
        self._kids(dexp)

    def visit_lam(self, dexp):
        self._kids(dexp, dexp.arg2)

    def visit_fix(self, dexp):
        self._kids(dexp, dexp.arg3)

    def visit_let(self, dexp):
        self._kids(dexp, dexp.arg2, dexp.arg3)

    def visit_op1(self, dexp):
        self._kids(dexp, dexp.arg1)

    def visit_pfst(self, dexp):
        self._kids(dexp, dexp.arg1)

    def visit_psnd(self, dexp):
        self._kids(dexp, dexp.arg1)

    def visit_op2(self, dexp):
        self._kids(dexp, dexp.arg1, dexp.arg2)

    def visit_app(self, dexp):
        self._kids(dexp, dexp.arg1, dexp.arg2)

    def visit_pair(self, dexp):
        self._kids(dexp, dexp.arg1, dexp.arg2)

    def visit_if0(self, dexp):
        self._kids(dexp, dexp.arg1, dexp.arg2, dexp.arg3)


class PrettyTests(unittest.TestCase):
    def test_every_constructor_and_literals(self):
        for expression, expected in pretty_cases():
            with self.subTest(expected=expected):
                self.assertEqual(d0exp_pretty(expression), expected)
                self.assertFalse(d0exp_pretty(expression).endswith("\n"))


class SubstitutionTests(unittest.TestCase):
    def test_spec_and_every_constructor(self):
        for expression, variable, replacement, expected in substitution_cases():
            with self.subTest(expected=expected):
                result = d0exp_substitute(expression, variable, replacement)
                self.assertEqual(d0exp_pretty(result), expected)

    def test_inserted_replacement_is_not_rewritten(self):
        replacement = D0Eop2("+", D0Evar("x"), D0Eint(1))
        result = d0exp_substitute(D0Evar("x"), "x", replacement)
        self.assertIs(result, replacement)

    def test_free_variable_property(self):
        for expression, variable, replacement in fv_cases():
            with self.subTest(variable=variable):
                before = d0exp_fvset(expression)
                result = d0exp_substitute(expression, variable, replacement)
                after = d0exp_fvset(result)
                if variable in before:
                    self.assertEqual(after, (before - {variable}) | d0exp_fvset(replacement))
                else:
                    self.assertEqual(after, before)
                    self.assertEqual(d0exp_pretty(result), d0exp_pretty(expression))

    def test_inputs_are_not_mutated_and_repeat_is_stable(self):
        expression = D0Elam("y", D0Eop2("+", D0Evar("x"), D0Evar("y")))
        replacement = D0Evar("y")
        before_expr = TreeIds().walk(expression)
        before_repl = TreeIds().walk(replacement)
        first = d0exp_pretty(d0exp_substitute(expression, "x", replacement))
        second = d0exp_pretty(d0exp_substitute(expression, "x", replacement))
        self.assertEqual(first, second)
        self.assertEqual(TreeIds().walk(expression), before_expr)
        self.assertEqual(TreeIds().walk(replacement), before_repl)

    def test_printing_and_substitution_do_not_evaluate(self):
        term = D0Eop2("/", D0Eint(1), D0Eint(0))
        with patch.object(lambda1_vp, "d0exp_evaluate", side_effect=AssertionError("evaluated")):
            self.assertEqual(d0exp_pretty(term), "(1 / 0)")
            self.assertEqual(d0exp_pretty(d0exp_substitute(term, "x", D0Eint(1))), "(1 / 0)")


if __name__ == "__main__":
    unittest.main()
