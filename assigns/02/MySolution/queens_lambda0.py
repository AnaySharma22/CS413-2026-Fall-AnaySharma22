"""Eight-queens as a closed LAMBDA0 term, evaluated by t0erm_cbv_evaluate0.

Source translated: assigns/02/MySolution/queens.dats
(ATS2 textbook / Piazza excerpt used in Assignment 1).

Board representation
--------------------
A board of size N is a right-nested list of N column indices:

    pair(c0, pair(c1, ... pair(c_{N-1}, nil)...))

with nil = -1. board_get / board_set are unrolled if-chains, matching the
ATS2 tuple accessors. safety_test1, safety_test2, and search are expressed
with T0Mlam / T0Mfix / T0Mapp inside the lambda-term.

Because substitution-based CBV re-embeds the Fix AST on every recursive
call, full enumeration for N=8 is impractical (RecursionError). We:

  * count all solutions for small N (1..5), matching known totals
  * for N=8, return the first solution board from a LAMBDA0 search term
    (with a raised recursion limit), matching the ATS2 first board

Extra interpreter ops: abs, <, <=, >, >=, =, != (comparisons -> T0Mbtf).

Run:
  python queens_lambda0.py
"""

from __future__ import annotations

import sys

from lambda0 import (
    T0Mint, T0Mbtf, T0Mvar, T0Mlam, T0Mfix, T0Mapp, T0Mif0, T0Mop1, T0Mop2,
    T0Mpair, T0Mpfst, T0Mpsnd,
    t0erm_cbv_evaluate0, t0erm_fvset,
)

# Substitution walks very deep Fix ASTs during 8-queens search.
sys.setrecursionlimit(20000)

def V(name): return T0Mvar(name)
def I(n): return T0Mint(n)
def B(b): return T0Mbtf(b)
def Lam(x, body): return T0Mlam(x, body)
def Fix(f, x, body): return T0Mfix(f, x, body)
def App(f, *args):
    term = f
    for a in args:
        term = T0Mapp(term, a)
    return term
def If(c, t, e): return T0Mif0(c, t, e)
def Op1(op, a): return T0Mop1(op, a)
def Op2(op, a, b): return T0Mop2(op, a, b)
def Pair(a, b): return T0Mpair(a, b)
def Fst(t): return T0Mpfst(t)
def Snd(t): return T0Mpsnd(t)
def Land(a, b): return If(a, b, B(False))

NIL = I(-1)


def make_board(columns):
    term = NIL
    for col in reversed(columns):
        term = Pair(I(col), term)
    return term


def empty_board(n: int):
    return make_board([0] * n)


def board_to_list(term, n: int) -> list[int]:
    cols: list[int] = []
    cur = term
    for _ in range(n):
        if not isinstance(cur, T0Mpair) or not isinstance(cur.arg1, T0Mint):
            raise TypeError(f"bad board cell: {cur}")
        cols.append(cur.arg1.arg1)
        cur = cur.arg2
    return cols


def board_get_term(n: int):
    """Unrolled like ATS board_get."""
    def column_at(depth: int):
        term = V("bd")
        for _ in range(depth):
            term = Snd(term)
        return Fst(term)

    body: object = I(-1)
    for idx in range(n - 1, -1, -1):
        body = If(Op2("=", V("i"), I(idx)), column_at(idx), body)
    return Lam("bd", Lam("i", body))


def board_set_term(n: int):
    """Unrolled like ATS board_set."""
    def rebuild(depth: int):
        def col(k: int):
            term = V("bd")
            for _ in range(k):
                term = Snd(term)
            return Fst(term)

        term = NIL
        for k in range(n - 1, -1, -1):
            term = Pair(V("j") if k == depth else col(k), term)
        return term

    body: object = V("bd")
    for idx in range(n - 1, -1, -1):
        body = If(Op2("=", V("i"), I(idx)), rebuild(idx), body)
    return Lam("bd", Lam("i", Lam("j", body)))


def safety_test1_term():
    return Lam("i0", Lam("j0", Lam("i1", Lam("j1",
        Land(
            Op2("!=", V("j0"), V("j1")),
            Op2("!=",
                Op1("abs", Op2("-", V("i0"), V("i1"))),
                Op1("abs", Op2("-", V("j0"), V("j1")))))))))


def safety_test2_term(get_term):
    i0 = Fst(Fst(V("args")))
    j0 = Snd(Fst(V("args")))
    bd = Fst(Snd(V("args")))
    i = Snd(Snd(V("args")))
    return Fix("st2", "args",
        If(Op2(">=", i, I(0)),
           If(App(App(App(App(safety_test1_term(), i0), j0), i),
                  App(App(get_term, bd), i)),
              App(V("st2"), Pair(Fst(V("args")), Pair(bd, Op2("-", i, I(1))))),
              B(False)),
           B(True)))


def search_count_term(n: int, get_term, set_term, st2_term):
    bd = Fst(Fst(V("args")))
    i = Snd(Fst(V("args")))
    j = Fst(Snd(V("args")))
    nsol = Snd(Snd(V("args")))

    def pack(bd_t, i_t, j_t, nsol_t):
        return Pair(Pair(bd_t, i_t), Pair(j_t, nsol_t))

    test = App(st2_term, Pair(Pair(i, j), Pair(bd, Op2("-", i, I(1)))))
    bd1 = App(App(App(set_term, bd), i), j)

    then_branch = If(
        Op2("=", Op2("+", i, I(1)), I(n)),
        App(V("search"), pack(bd, i, Op2("+", j, I(1)), Op2("+", nsol, I(1)))),
        App(V("search"), pack(bd1, Op2("+", i, I(1)), I(0), nsol)),
    )

    j_lt_n = If(
        test,
        then_branch,
        App(V("search"), pack(bd, i, Op2("+", j, I(1)), nsol)),
    )

    backtrack = If(
        Op2(">", i, I(0)),
        App(V("search"), pack(
            bd,
            Op2("-", i, I(1)),
            Op2("+", App(App(get_term, bd), Op2("-", i, I(1))), I(1)),
            nsol,
        )),
        nsol,
    )

    return Fix("search", "args", If(Op2("<", j, I(n)), j_lt_n, backtrack))


def search_first_term(n: int, get_term, set_term, st2_term):
    """args = pair(pair(bd, i), j); result = pair(found?, board)."""
    bd = Fst(Fst(V("args")))
    i = Snd(Fst(V("args")))
    j = Snd(V("args"))

    def pack(bd_t, i_t, j_t):
        return Pair(Pair(bd_t, i_t), j_t)

    none = Pair(B(False), NIL)
    test = App(st2_term, Pair(Pair(i, j), Pair(bd, Op2("-", i, I(1)))))
    bd1 = App(App(App(set_term, bd), i), j)
    deeper = App(V("search"), pack(bd1, Op2("+", i, I(1)), I(0)))
    try_next = App(V("search"), pack(bd, i, Op2("+", j, I(1))))

    after_deeper = App(
        Lam("res", If(Fst(V("res")), V("res"), try_next)),
        deeper,
    )
    after_place = If(
        Op2("=", Op2("+", i, I(1)), I(n)),
        Pair(B(True), bd1),
        after_deeper,
    )
    j_lt_n = If(test, after_place, try_next)
    backtrack = If(
        Op2(">", i, I(0)),
        App(V("search"), pack(
            bd,
            Op2("-", i, I(1)),
            Op2("+", App(App(get_term, bd), Op2("-", i, I(1))), I(1)),
        )),
        none,
    )
    return Fix("search", "args", If(Op2("<", j, I(n)), j_lt_n, backtrack))


def queens_count_term(n: int):
    get_t = board_get_term(n)
    set_t = board_set_term(n)
    st2_t = safety_test2_term(get_t)
    search_t = search_count_term(n, get_t, set_t, st2_t)
    return App(search_t, Pair(Pair(empty_board(n), I(0)), Pair(I(0), I(0))))


def queens_first_term(n: int):
    get_t = board_get_term(n)
    set_t = board_set_term(n)
    st2_t = safety_test2_term(get_t)
    search_t = search_first_term(n, get_t, set_t, st2_t)
    return App(search_t, Pair(Pair(empty_board(n), I(0)), I(0)))


def count_solutions(n: int) -> int:
    term = queens_count_term(n)
    assert t0erm_fvset(term) == frozenset()
    result = t0erm_cbv_evaluate0(term)
    if not isinstance(result, T0Mint):
        raise TypeError(f"expected int, got {result}")
    return result.arg1


def first_solution(n: int) -> list[int] | None:
    term = queens_first_term(n)
    assert t0erm_fvset(term) == frozenset()
    result = t0erm_cbv_evaluate0(term)
    if not isinstance(result, T0Mpair) or not isinstance(result.arg1, T0Mbtf):
        raise TypeError(f"expected option pair, got {result}")
    if not result.arg1.arg1:
        return None
    return board_to_list(result.arg2, n)


def is_safe_placement(cols: list[int]) -> bool:
    n = len(cols)
    if len(set(cols)) != n:
        return False
    for i0 in range(n):
        for i1 in range(i0):
            if abs(i0 - i1) == abs(cols[i0] - cols[i1]):
                return False
    return True


KNOWN_COUNTS = {1: 1, 2: 0, 3: 0, 4: 2, 5: 10, 6: 4, 7: 40, 8: 92}
FIRST_SOLUTION_N8 = [0, 4, 7, 5, 2, 6, 1, 3]


def main():
    print("Eight-queens LAMBDA0 translation")
    print("Source: queens.dats (ATS2 Assignment 1 excerpt)")
    for n in (1, 4, 5):
        total = count_solutions(n)
        print(f"  count N={n}: {total} (expected {KNOWN_COUNTS[n]})")
        assert total == KNOWN_COUNTS[n]

    board4 = first_solution(4)
    print(f"  first N=4 board: {board4}")
    assert board4 is not None and is_safe_placement(board4)

    board = first_solution(8)
    print(f"  first N=8 board: {board}")
    assert board == FIRST_SOLUTION_N8
    assert is_safe_placement(board)
    print("OK")


if __name__ == "__main__":
    main()
