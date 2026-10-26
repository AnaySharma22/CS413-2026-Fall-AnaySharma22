"""Source programs shared by the demonstration and the tests."""

import boot  # noqa: F401  (adds assigns/05 to sys.path)

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


def n(value: int):
    return D0Eint(value)


def b(value: bool):
    return D0Ebtf(value)


def v(name: str):
    return D0Evar(name)


def op(name: str, left, right):
    return D0Eop2(name, left, right)


def LOOP():
    return D0Eapp(D0Efix("loop", "x", D0Eapp(v("loop"), v("x"))), n(0))


def factorial():
    number = v("n")
    function = v("fact")
    body = D0Eif0(
        op("==", number, n(0)),
        n(1),
        op("*", number, D0Eapp(function, op("-", number, n(1)))),
    )
    return D0Eapp(D0Efix("fact", "n", body), n(4))


def fibonacci():
    number = v("n")
    function = v("fib")
    body = D0Eif0(
        op("==", number, n(0)),
        n(0),
        D0Eif0(
            op("==", number, n(1)),
            n(1),
            op(
                "+",
                D0Eapp(function, op("-", number, n(1))),
                D0Eapp(function, op("-", number, n(2))),
            ),
        ),
    )
    return D0Eapp(D0Efix("fib", "n", body), n(5))


def demonstrations():
    """(title, expression, kind or None when the run must exhaust, expected)."""
    return [
        ("2 + 3 * 4", op("+", n(2), op("*", n(3), n(4))), "nat", 14),
        ("2 - 5", op("-", n(2), n(5)), "nat", 0),
        ("if 2 <= 3 then 7 else 9", D0Eif0(op("<=", n(2), n(3)), n(7), n(9)), "nat", 7),
        (
            "let x = 3 in (lam y. x + y) 4",
            D0Elet("x", n(3), D0Eapp(D0Elam("y", op("+", v("x"), v("y"))), n(4))),
            "nat",
            7,
        ),
        ("fst (pair 2 true)", D0Epfst(D0Epair(n(2), b(True))), "nat", 2),
        ("snd (pair 2 true)", D0Epsnd(D0Epair(n(2), b(True))), "bool", True),
        (
            "(lam f. f 3) (lam x. x + 1)",
            D0Eapp(D0Elam("f", D0Eapp(v("f"), n(3))), D0Elam("x", op("+", v("x"), n(1)))),
            "nat",
            4,
        ),
        ("true and false", op("and", b(True), b(False)), "bool", False),
        ("false or true", op("or", b(False), b(True)), "bool", True),
        ("if true then 1 else LOOP", D0Eif0(b(True), n(1), LOOP()), "nat", 1),
        ("(lam x. 0) LOOP", D0Eapp(D0Elam("x", n(0)), LOOP()), None, "exhausted"),
        ("factorial 4", factorial(), "nat", 24),
        ("fibonacci 5", fibonacci(), "nat", 5),
        ("LOOP", LOOP(), None, "exhausted"),
    ]
