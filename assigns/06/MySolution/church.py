"""Closed Church encodings. Names such as TRUE and Z are Python builders.

Every combinator is expanded into Var, Lam, and App. Nothing here is a
target-language primitive. Predecessor of zero is zero: iteration starts at
the pair (0, 0) and shifts, so zero iterations leaves the first component 0.
"""

from __future__ import annotations

from target import App, Lam, Term, Var


def _lam(name: str, body: Term) -> Lam:
    return Lam(name, body)


def TRUE() -> Term:
    return _lam("t", _lam("f", Var("t")))


def FALSE() -> Term:
    return _lam("t", _lam("f", Var("f")))


def numeral(n: int) -> Term:
    if n < 0:
        raise ValueError("numerals are natural numbers")
    body: Term = Var("z")
    for _ in range(n):
        body = App(Var("s"), body)
    return _lam("s", _lam("z", body))


def PAIR() -> Term:
    return _lam("a", _lam("b", _lam("p", App(App(Var("p"), Var("a")), Var("b")))))


def FST() -> Term:
    return _lam("p", App(Var("p"), _lam("a", _lam("b", Var("a")))))


def SND() -> Term:
    return _lam("p", App(Var("p"), _lam("a", _lam("b", Var("b")))))


def SUCC() -> Term:
    return _lam(
        "n",
        _lam("s", _lam("z", App(Var("s"), App(App(Var("n"), Var("s")), Var("z"))))),
    )


def PRED() -> Term:
    """fst (n (shift) (pair 0 0)), where shift moves (previous, current) forward."""
    zero = numeral(0)
    shift = _lam(
        "p",
        App(
            App(PAIR(), App(SND(), Var("p"))),
            App(SUCC(), App(SND(), Var("p"))),
        ),
    )
    start = App(App(PAIR(), zero), zero)
    return _lam("n", App(FST(), App(App(Var("n"), shift), start)))


def ISZERO() -> Term:
    return _lam("n", App(App(Var("n"), _lam("x", FALSE())), TRUE()))


def ADD() -> Term:
    return _lam(
        "m",
        _lam(
            "n",
            _lam(
                "s",
                _lam("z", App(App(Var("m"), Var("s")), App(App(Var("n"), Var("s")), Var("z")))),
            ),
        ),
    )


def MUL() -> Term:
    return _lam(
        "m",
        _lam(
            "n",
            _lam("s", _lam("z", App(App(Var("m"), App(Var("n"), Var("s"))), Var("z")))),
        ),
    )


def SUB() -> Term:
    return _lam("m", _lam("n", App(App(Var("n"), PRED()), Var("m"))))


def LEQ() -> Term:
    return _lam("m", _lam("n", App(ISZERO(), App(App(SUB(), Var("m")), Var("n")))))


def NOT() -> Term:
    return _lam("b", App(App(Var("b"), FALSE()), TRUE()))


def AND() -> Term:
    """Church conjunction of two boolean values. Source `and` does not use this."""
    return _lam("a", _lam("b", App(App(Var("a"), Var("b")), FALSE())))


def OR() -> Term:
    """Church disjunction of two boolean values. Source `or` does not use this."""
    return _lam("a", _lam("b", App(App(Var("a"), TRUE()), Var("b"))))


def LT() -> Term:
    return _lam("m", _lam("n", App(NOT(), App(App(LEQ(), Var("n")), Var("m")))))


def GT() -> Term:
    return _lam("m", _lam("n", App(NOT(), App(App(LEQ(), Var("m")), Var("n")))))


def GEQ() -> Term:
    return _lam("m", _lam("n", App(App(LEQ(), Var("n")), Var("m"))))


def EQ() -> Term:
    return _lam(
        "m",
        _lam(
            "n",
            App(
                App(AND(), App(App(LEQ(), Var("m")), Var("n"))),
                App(App(LEQ(), Var("n")), Var("m")),
            ),
        ),
    )


def NEQ() -> Term:
    return _lam("m", _lam("n", App(NOT(), App(App(EQ(), Var("m")), Var("n")))))


def Z() -> Term:
    """Call-by-value fixed point. Ordinary Y would unfold before it is a value."""

    def half() -> Term:
        return _lam(
            "x",
            App(Var("g"), _lam("v", App(App(Var("x"), Var("x")), Var("v")))),
        )

    return _lam("g", App(half(), half()))


def IDENTITY() -> Term:
    """Closed dummy value used to force a selected thunk. Binder w is local."""
    return _lam("w", Var("w"))


OPERATORS = {
    "+": ADD,
    "-": SUB,
    "*": MUL,
    "<": LT,
    "<=": LEQ,
    ">": GT,
    ">=": GEQ,
    "==": EQ,
    "!=": NEQ,
}


def combinators() -> dict[str, Term]:
    built = {
        "TRUE": TRUE(),
        "FALSE": FALSE(),
        "PAIR": PAIR(),
        "FST": FST(),
        "SND": SND(),
        "SUCC": SUCC(),
        "PRED": PRED(),
        "ISZERO": ISZERO(),
        "ADD": ADD(),
        "MUL": MUL(),
        "SUB": SUB(),
        "LEQ": LEQ(),
        "NOT": NOT(),
        "AND": AND(),
        "OR": OR(),
        "LT": LT(),
        "GT": GT(),
        "GEQ": GEQ(),
        "EQ": EQ(),
        "NEQ": NEQ(),
        "Z": Z(),
        "IDENTITY": IDENTITY(),
        "NUM0": numeral(0),
        "NUM2": numeral(2),
    }
    return built
