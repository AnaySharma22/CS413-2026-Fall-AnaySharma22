"""Compositional compiler from extended LAMBDA into pure lambda terms.

Compilation never calls evaluate. Dead branches are still translated, so a
negative literal or an unsupported operator is rejected wherever it sits.
Fresh thunk binders are k_1, k_2, ... and are chosen against every name in
the terms they wrap. Source names, including s, z, t, f, and x, are kept.
"""

from __future__ import annotations

import boot  # noqa: F401  (adds assigns/05 to sys.path)

from church import FALSE, FST, IDENTITY, NOT, OPERATORS, PAIR, SND, TRUE, Z, numeral
from lambda1_vp import (
    D0ExpVisitor,
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
from target import App, FreshNames, Lam, Term, Var


class CompileError(Exception):
    pass


class CompileVisitor(D0ExpVisitor):
    def visit_int(self, dexp: D0Eint) -> Term:
        if dexp.arg1 < 0:
            raise CompileError(f"negative literal {dexp.arg1}")
        return numeral(dexp.arg1)

    def visit_btf(self, dexp: D0Ebtf) -> Term:
        return TRUE() if dexp.arg1 else FALSE()

    def visit_var(self, dexp: D0Evar) -> Term:
        return Var(dexp.arg1)

    def visit_lam(self, dexp: D0Elam) -> Term:
        return Lam(dexp.arg1, dexp.arg2.accept(self))

    def visit_app(self, dexp: D0Eapp) -> Term:
        return App(dexp.arg1.accept(self), dexp.arg2.accept(self))

    def visit_let(self, dexp: D0Elet) -> Term:
        init = dexp.arg2.accept(self)
        body = dexp.arg3.accept(self)
        return App(Lam(dexp.arg1, body), init)

    def visit_fix(self, dexp: D0Efix) -> Term:
        body = dexp.arg3.accept(self)
        return App(Z(), Lam(dexp.arg1, Lam(dexp.arg2, body)))

    def visit_if0(self, dexp: D0Eif0) -> Term:
        condition = dexp.arg1.accept(self)
        then_branch = dexp.arg2.accept(self)
        else_branch = dexp.arg3.accept(self)
        return _delayed(condition, then_branch, else_branch)

    def visit_op1(self, dexp: D0Eop1) -> Term:
        if dexp.name != "not":
            raise CompileError(f"unsupported operator {dexp.name}")
        return App(NOT(), dexp.arg1.accept(self))

    def visit_op2(self, dexp: D0Eop2) -> Term:
        left = dexp.arg1.accept(self)
        right = dexp.arg2.accept(self)
        if dexp.name == "and":
            return _delayed(left, right, FALSE())
        if dexp.name == "or":
            return _delayed(left, TRUE(), right)
        if dexp.name not in OPERATORS:
            raise CompileError(f"unsupported operator {dexp.name}")
        return App(App(OPERATORS[dexp.name](), left), right)

    def visit_pair(self, dexp: D0Epair) -> Term:
        return App(App(PAIR(), dexp.arg1.accept(self)), dexp.arg2.accept(self))

    def visit_pfst(self, dexp: D0Epfst) -> Term:
        return App(FST(), dexp.arg1.accept(self))

    def visit_psnd(self, dexp: D0Epsnd) -> Term:
        return App(SND(), dexp.arg1.accept(self))


def _delayed(condition: Term, then_branch: Term, else_branch: Term) -> Term:
    reserved = set(condition.names() | then_branch.names() | else_branch.names())
    fresh = FreshNames(reserved)
    then_thunk = Lam(fresh.allocate("k"), then_branch)
    else_thunk = Lam(fresh.allocate("k"), else_branch)
    return App(App(App(condition, then_thunk), else_thunk), IDENTITY())


def compile_expr(expression) -> Term:
    return expression.accept(CompileVisitor())
