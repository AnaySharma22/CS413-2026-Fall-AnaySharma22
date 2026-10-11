"""Shared inputs. Both suites assert against these; neither suite imports the other."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSIGN = ROOT.parent
sys.path.insert(0, str(ASSIGN))
sys.path.insert(0, str(ROOT))

from lambda1_vp import (
    D0Eapp,
    D0Ebtf,
    D0Efix,
    D0Eif0,
    D0Eint,
    D0Elam,
    D0Elet,
    D0Eop1,
    D0Eop2,
    D0Epair,
    D0Epfst,
    D0Epsnd,
    D0Evar,
)

x = D0Evar("x")
y = D0Evar("y")
z = D0Evar("z")
n = D0Evar("n")
f = D0Evar("f")


def pretty_cases():
    nested = D0Eapp(
        D0Elam("x", D0Eop2("+", x, D0Eint(1))),
        D0Eint(4),
    )
    return [
        (D0Eint(0), "0"),
        (D0Eint(42), "42"),
        (D0Eint(-2), "-2"),
        (D0Eint(10**40), "1" + "0" * 40),
        (D0Ebtf(True), "true"),
        (D0Ebtf(False), "false"),
        (x, "x"),
        (D0Eop1("-1", x), "(-1 x)"),
        (D0Eop2("+", x, z), "(x + z)"),
        (D0Eop2("/", D0Eint(1), D0Eint(0)), "(1 / 0)"),
        (D0Elam("x", D0Eop2("+", x, y)), "(lam x. (x + y))"),
        (D0Efix("f", "n", D0Eapp(f, n)), "(fix f(n). (f n))"),
        (D0Eapp(D0Evar("f"), D0Eint(1)), "(f 1)"),
        (nested, "((lam x. (x + 1)) 4)"),
        (
            D0Eif0(D0Ebtf(True), D0Eint(1), D0Eint(0)),
            "(if true then 1 else 0)",
        ),
        (D0Elet("x", x, D0Eop2("+", x, y)), "(let x = x in (x + y))"),
        (D0Epair(D0Eint(1), D0Ebtf(False)), "(pair 1 false)"),
        (D0Epfst(D0Epair(x, y)), "(fst (pair x y))"),
        (D0Epsnd(z), "(snd z)"),
    ]


def substitution_cases():
    """(expression, variable, replacement, expected pretty text)."""
    return [
        (D0Eop2("+", x, z), "x", D0Eint(3), "(3 + z)"),
        (D0Eop2("+", x, z), "y", D0Eint(3), "(x + z)"),
        (x, "x", D0Eop2("+", x, D0Eint(1)), "(x + 1)"),
        (D0Elam("x", D0Eop2("+", x, y)), "x", D0Eint(3), "(lam x. (x + y))"),
        (D0Elam("y", D0Eop2("+", x, y)), "x", y, "(lam y_1. (y + y_1))"),
        (D0Elet("x", x, D0Eop2("+", x, y)), "x", D0Eint(3), "(let x = 3 in (x + y))"),
        (D0Elet("y", x, D0Eop2("+", x, y)), "x", y, "(let y_1 = y in (y + y_1))"),
        (
            D0Efix("f", "n", D0Eop2("+", x, D0Eapp(f, n))),
            "x",
            f,
            "(fix f_1(n). (f + (f_1 n)))",
        ),
        (D0Eop1("-1", x), "x", D0Eint(4), "(-1 4)"),
        (D0Eapp(f, x), "x", D0Eint(2), "(f 2)"),
        (D0Eif0(x, y, z), "x", D0Ebtf(True), "(if true then y else z)"),
        (D0Epair(x, y), "x", D0Eint(1), "(pair 1 y)"),
        (D0Epfst(x), "x", D0Epair(D0Eint(1), D0Eint(2)), "(fst (pair 1 2))"),
        (D0Epsnd(x), "x", z, "(snd z)"),
        (
            D0Efix("f", "f", D0Eop2("+", x, f)),
            "x",
            D0Eint(1),
            "(fix f(f). (1 + f))",
        ),
        (
            D0Efix("f", "f", D0Eop2("+", x, f)),
            "x",
            f,
            "(fix f_1(f_1). (f + f_1))",
        ),
        (
            D0Efix("f", "n", D0Eop2("+", x, D0Eapp(f, n))),
            "x",
            D0Eop2("+", f, n),
            "(fix f_1(n_1). ((f + n) + (f_1 n_1)))",
        ),
        (
            D0Elam("y", D0Elam("y", D0Eop2("+", x, y))),
            "x",
            y,
            "(lam y_1. (lam y_2. (y + y_2)))",
        ),
        (
            D0Elam("y", D0Eop2("+", x, D0Evar("y_1"))),
            "x",
            y,
            "(lam y_2. (y + y_1))",
        ),
        (D0Eint(5), "x", y, "5"),
        (D0Ebtf(False), "x", y, "false"),
    ]


def fv_cases():
    return [
        (D0Eop2("+", x, z), "x", D0Eint(3)),
        (D0Elam("y", D0Eop2("+", x, y)), "x", y),
        (D0Elet("y", x, D0Eop2("+", x, y)), "x", y),
        (D0Elam("x", x), "x", D0Eint(3)),
        (D0Efix("f", "n", D0Eop2("+", x, D0Eapp(f, n))), "x", f),
    ]
