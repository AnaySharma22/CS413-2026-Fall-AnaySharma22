"""Tests for pairs and projections in MySolution/lambda0.py.

Run with: python TEST/test02_lambda0.py
Requires Python 3.12 or later.
"""

import sys
import unittest
from pathlib import Path

# Import the extended interpreter from MySolution/, not the starter copy.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lambda0 import (
    T0Mint, T0Mbtf, T0Mstr, T0Mvar, T0Mlam, T0Mfix, T0Mapp, T0Mif0, T0Mop1, T0Mop2,
    T0Mpair, T0Mpfst, T0Mpsnd,
    t0erm_size, t0erm_fvset, t0erm_subst0, t0erm_cbv_evaluate0,
)


class TestSize(unittest.TestCase):
    def test_pair_of_ints(self):
        self.assertEqual(t0erm_size(T0Mpair(T0Mint(1), T0Mint(2))), 3)

    def test_projections(self):
        self.assertEqual(t0erm_size(T0Mpfst(T0Mpair(T0Mint(1), T0Mint(2)))), 4)
        self.assertEqual(t0erm_size(T0Mpsnd(T0Mint(0))), 2)

    def test_nested_pair(self):
        term = T0Mpair(T0Mpair(T0Mint(1), T0Mint(2)), T0Mint(3))
        self.assertEqual(t0erm_size(term), 5)


class TestFvset(unittest.TestCase):
    def test_pair_and_projection(self):
        term = T0Mpfst(T0Mpair(T0Mvar("x"), T0Mvar("y")))
        self.assertEqual(t0erm_fvset(term), frozenset({"x", "y"}))

    def test_bound_under_lambda(self):
        term = T0Mlam("x", T0Mpair(T0Mvar("x"), T0Mvar("y")))
        self.assertEqual(t0erm_fvset(term), frozenset({"y"}))

    def test_bound_under_fix(self):
        term = T0Mfix("f", "x", T0Mpsnd(T0Mpair(T0Mvar("x"), T0Mvar("z"))))
        self.assertEqual(t0erm_fvset(term), frozenset({"z"}))


class TestSubst(unittest.TestCase):
    def test_into_pair_components(self):
        term = T0Mpair(T0Mvar("x"), T0Mvar("y"))
        result = t0erm_subst0(term, "x", T0Mint(1))
        self.assertEqual(result, T0Mpair(T0Mint(1), T0Mvar("y")))

    def test_into_projection(self):
        term = T0Mpfst(T0Mvar("p"))
        result = t0erm_subst0(term, "p", T0Mpair(T0Mint(3), T0Mint(4)))
        self.assertEqual(result, T0Mpfst(T0Mpair(T0Mint(3), T0Mint(4))))

    def test_under_lambda_binder(self):
        term = T0Mlam("x", T0Mpair(T0Mvar("x"), T0Mvar("y")))
        result = t0erm_subst0(term, "y", T0Mint(9))
        self.assertEqual(result, T0Mlam("x", T0Mpair(T0Mvar("x"), T0Mint(9))))
        # Shadowing: do not substitute the bound name.
        self.assertEqual(t0erm_subst0(term, "x", T0Mint(0)), term)

    def test_under_fix_binder(self):
        term = T0Mfix("f", "x", T0Mpsnd(T0Mpair(T0Mvar("x"), T0Mvar("y"))))
        result = t0erm_subst0(term, "y", T0Mint(2))
        self.assertEqual(
            result,
            T0Mfix("f", "x", T0Mpsnd(T0Mpair(T0Mvar("x"), T0Mint(2)))),
        )


class TestEvaluatePairs(unittest.TestCase):
    def test_assignment_examples(self):
        self.assertEqual(t0erm_size(T0Mpair(T0Mint(1), T0Mint(2))), 3)
        self.assertEqual(
            t0erm_fvset(T0Mpfst(T0Mpair(T0Mvar("x"), T0Mvar("y")))),
            frozenset({"x", "y"}),
        )
        result = t0erm_cbv_evaluate0(
            T0Mpsnd(T0Mpair(T0Mint(1), T0Mop2("+", T0Mint(2), T0Mint(3))))
        )
        self.assertEqual(result, T0Mint(5))

    def test_pair_evaluates_components(self):
        term = T0Mpair(
            T0Mop2("+", T0Mint(1), T0Mint(2)),
            T0Mop2("*", T0Mint(3), T0Mint(4)),
        )
        self.assertEqual(t0erm_cbv_evaluate0(term), T0Mpair(T0Mint(3), T0Mint(12)))

    def test_both_projections(self):
        pair = T0Mpair(T0Mint(10), T0Mint(20))
        self.assertEqual(t0erm_cbv_evaluate0(T0Mpfst(pair)), T0Mint(10))
        self.assertEqual(t0erm_cbv_evaluate0(T0Mpsnd(pair)), T0Mint(20))

    def test_nested_pairs(self):
        term = T0Mpfst(T0Mpsnd(T0Mpair(T0Mint(1), T0Mpair(T0Mint(2), T0Mint(3)))))
        self.assertEqual(t0erm_cbv_evaluate0(term), T0Mint(2))

    def test_pair_of_function_and_int(self):
        term = T0Mapp(
            T0Mpfst(T0Mpair(T0Mlam("x", T0Mop2("+", T0Mvar("x"), T0Mint(1))), T0Mint(0))),
            T0Mint(41),
        )
        self.assertEqual(t0erm_cbv_evaluate0(term), T0Mint(42))

    def test_function_returning_pair(self):
        # (lambda x. pair(x, x+1))(3) = pair(3, 4)
        term = T0Mapp(
            T0Mlam("x", T0Mpair(T0Mvar("x"), T0Mop2("+", T0Mvar("x"), T0Mint(1)))),
            T0Mint(3),
        )
        self.assertEqual(t0erm_cbv_evaluate0(term), T0Mpair(T0Mint(3), T0Mint(4)))

    def test_function_accepting_pair(self):
        # (lambda p. fst(p) + snd(p))(pair(2, 5)) = 7
        term = T0Mapp(
            T0Mlam("p", T0Mop2("+", T0Mpfst(T0Mvar("p")), T0Mpsnd(T0Mvar("p")))),
            T0Mpair(T0Mint(2), T0Mint(5)),
        )
        self.assertEqual(t0erm_cbv_evaluate0(term), T0Mint(7))

    def test_projection_of_non_pair_raises(self):
        with self.assertRaises(TypeError):
            t0erm_cbv_evaluate0(T0Mpfst(T0Mint(1)))
        with self.assertRaises(TypeError):
            t0erm_cbv_evaluate0(T0Mpsnd(T0Mbtf(True)))

    def test_left_to_right_pair_evaluation(self):
        # Left division error happens before the right type error.
        term = T0Mpair(
            T0Mop2("/", T0Mint(1), T0Mint(0)),
            T0Mop1("-", T0Mstr("bad")),
        )
        with self.assertRaises(ZeroDivisionError):
            t0erm_cbv_evaluate0(term)

    def test_projection_evaluates_unused_component(self):
        # fst(pair(1, 1/0)) must still evaluate the unused right component.
        term = T0Mpfst(T0Mpair(T0Mint(1), T0Mop2("/", T0Mint(1), T0Mint(0))))
        with self.assertRaises(ZeroDivisionError):
            t0erm_cbv_evaluate0(term)

    def test_comparisons_for_queens_support(self):
        self.assertEqual(t0erm_cbv_evaluate0(T0Mop2("<", T0Mint(1), T0Mint(2))), T0Mbtf(True))
        self.assertEqual(t0erm_cbv_evaluate0(T0Mop2("=", T0Mint(3), T0Mint(3))), T0Mbtf(True))
        self.assertEqual(t0erm_cbv_evaluate0(T0Mop2("!=", T0Mint(3), T0Mint(4))), T0Mbtf(True))
        self.assertEqual(t0erm_cbv_evaluate0(T0Mop2(">=", T0Mint(0), T0Mint(0))), T0Mbtf(True))
        self.assertEqual(t0erm_cbv_evaluate0(T0Mop1("abs", T0Mint(-5))), T0Mint(5))


if __name__ == "__main__":
    unittest.main(verbosity=2)
