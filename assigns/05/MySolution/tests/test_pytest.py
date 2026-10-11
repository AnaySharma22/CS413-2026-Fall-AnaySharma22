"""pytest suite. Run with: python -m pytest MySolution/tests/test_pytest.py -q

These are plain test functions. They are not unittest.TestCase cases.
"""

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT))

import lambda1_vp
from lambda1_vp import D0Eint, D0Elam, D0Eop2, D0ExpVisitor, D0Evar, d0exp_fvset
from samples import fv_cases, pretty_cases, substitution_cases
from visitors import d0exp_pretty, d0exp_substitute


class _Structure(D0ExpVisitor[None]):
    def __init__(self):
        self.rows = []

    def _kids(self, dexp, *children):
        self.rows.append((id(dexp), dexp.ctag, tuple(id(child) for child in children)))
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


def _shape(expression):
    visitor = _Structure()
    expression.accept(visitor)
    return tuple(visitor.rows)


def test_pretty_every_constructor_literals_and_nesting():
    for expression, expected in pretty_cases():
        printed = d0exp_pretty(expression)
        assert printed == expected
        assert not printed.endswith("\n")


def test_substitution_every_constructor_and_spec_examples():
    for expression, variable, replacement, expected in substitution_cases():
        assert d0exp_pretty(d0exp_substitute(expression, variable, replacement)) == expected


def test_replacement_that_contains_the_target_is_inserted_once():
    replacement = D0Eop2("+", D0Evar("x"), D0Eint(1))
    assert d0exp_substitute(D0Evar("x"), "x", replacement) is replacement


def test_shadowing_capture_let_split_and_fresh_collisions():
    # Covered by substitution_cases; this names the edge groups explicitly.
    texts = {expected for _, _, _, expected in substitution_cases()}
    assert "(lam x. (x + y))" in texts
    assert "(lam y_1. (y + y_1))" in texts
    assert "(let x = 3 in (x + y))" in texts
    assert "(let y_1 = y in (y + y_1))" in texts
    assert "(fix f_1(n). (f + (f_1 n)))" in texts
    assert "(fix f_1(f_1). (f + f_1))" in texts
    assert "(fix f_1(n_1). ((f + n) + (f_1 n_1)))" in texts
    assert "(lam y_1. (lam y_2. (y + y_2)))" in texts
    assert "(lam y_2. (y + y_1))" in texts


def test_free_variable_property():
    for expression, variable, replacement in fv_cases():
        before = d0exp_fvset(expression)
        result = d0exp_substitute(expression, variable, replacement)
        after = d0exp_fvset(result)
        if variable in before:
            assert after == (before - {variable}) | d0exp_fvset(replacement)
        else:
            assert after == before
            assert d0exp_pretty(result) == d0exp_pretty(expression)


def test_inputs_stay_intact_and_results_repeat():
    expression = D0Elam("y", D0Eop2("+", D0Evar("x"), D0Evar("y")))
    replacement = D0Evar("y")
    before_expr = _shape(expression)
    before_repl = _shape(replacement)
    first = d0exp_pretty(d0exp_substitute(expression, "x", replacement))
    second = d0exp_pretty(d0exp_substitute(expression, "x", replacement))
    assert first == second == "(lam y_1. (y + y_1))"
    assert _shape(expression) == before_expr
    assert _shape(replacement) == before_repl


def test_no_evaluation_during_print_or_substitute():
    term = D0Eop2("/", D0Eint(1), D0Eint(0))
    with patch.object(lambda1_vp, "d0exp_evaluate", side_effect=AssertionError("evaluated")):
        assert d0exp_pretty(term) == "(1 / 0)"
        assert d0exp_pretty(d0exp_substitute(term, "x", D0Eint(1))) == "(1 / 0)"
