"""The shared evaluator for source ASTs and target terms.

EvaluateVisitor has one visit_var, one visit_lam, and one visit_app. Source
D0Evar/D0Elam/D0Eapp and target Var/Lam/App both dispatch to them. The other
visit methods are source-only rules. A target term contains only the three
shared forms, so its run never reaches a source operation.

Both languages use substitution-based, left-to-right call-by-value:
evaluate the function, then the argument, then substitute. Lambdas are values
and nothing is reduced under them. A beta-value step is counted for every
application of a lambda (and, in source, a fix). Target runs require a
nonnegative step budget. Source runs may omit it.

This module does not import the compiler.
"""

from __future__ import annotations

import sys

import boot  # noqa: F401  (adds assigns/05 to sys.path)

from lambda1_vp import (
    D0Ebtf,
    D0ExpVisitor,
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
    d0exp_fvset,
)
from target import Lam, Term, only_target, pretty, substitute
from visitors import d0exp_pretty, d0exp_substitute

sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))


class EvalError(Exception):
    pass


class Outcome:
    """status is "value", "exhausted", or "rejected"; steps counts beta-value steps."""

    def __init__(self, status: str, steps: int, value=None, message: str = ""):
        self.status = status
        self.steps = steps
        self.value = value
        self.message = message

    def __repr__(self) -> str:
        if isinstance(self.value, Term):
            shown = pretty(self.value)
        elif self.value is not None:
            shown = d0exp_pretty(self.value)
        else:
            shown = None
        return f"Outcome({self.status}, steps={self.steps}, value={shown}, {self.message})"


class _Tail:
    """An expression to continue with in tail position, so beta chains loop."""

    def __init__(self, expr):
        self.expr = expr


class _Exhausted(Exception):
    def __init__(self, steps: int):
        self.steps = steps


ARITHMETIC = {
    "+": lambda m, n: D0Eint(m + n),
    "-": lambda m, n: D0Eint(max(m - n, 0)),
    "*": lambda m, n: D0Eint(m * n),
    "<": lambda m, n: D0Ebtf(m < n),
    "<=": lambda m, n: D0Ebtf(m <= n),
    ">": lambda m, n: D0Ebtf(m > n),
    ">=": lambda m, n: D0Ebtf(m >= n),
    "==": lambda m, n: D0Ebtf(m == n),
    "!=": lambda m, n: D0Ebtf(m != n),
}


class EvaluateVisitor(D0ExpVisitor):
    def __init__(self, budget: int | None, trace: list | None = None):
        self.budget = budget
        self.trace = trace
        self.steps = 0

    def run(self, expr):
        while True:
            result = expr.accept(self)
            if not isinstance(result, _Tail):
                return result
            expr = result.expr

    def _note(self, event: str) -> None:
        if self.trace is not None:
            self.trace.append(event)

    # Shared by both languages.

    def visit_var(self, dexp):
        raise EvalError(f"open term: {dexp.arg1}")

    def visit_lam(self, dexp):
        return dexp

    def visit_app(self, dexp):
        self._note("function")
        function = self.run(dexp.arg1)
        self._note("argument")
        argument = self.run(dexp.arg2)
        return _Tail(self._beta(function, argument))

    def _beta(self, function, argument):
        if not isinstance(function, (Lam, D0Elam, D0Efix)):
            raise EvalError("application of a non-function")
        if self.budget is not None and self.steps >= self.budget:
            raise _Exhausted(self.steps)
        self.steps += 1
        self._note("beta")
        if isinstance(function, Lam):
            return substitute(function.body, function.name, argument)
        if isinstance(function, D0Elam):
            return d0exp_substitute(function.arg2, function.arg1, argument)
        body = function.arg3
        if function.arg1 != function.arg2:
            body = d0exp_substitute(body, function.arg1, function)
        return d0exp_substitute(body, function.arg2, argument)

    # Source-only rules. A target term never reaches these.

    def visit_fix(self, dexp: D0Efix):
        return dexp

    def visit_int(self, dexp: D0Eint):
        if dexp.arg1 < 0:
            raise EvalError(f"negative literal {dexp.arg1}")
        return dexp

    def visit_btf(self, dexp: D0Ebtf):
        return dexp

    def visit_op1(self, dexp: D0Eop1):
        if dexp.name != "not":
            raise EvalError(f"unsupported operator {dexp.name}")
        return D0Ebtf(not self._bool(self.run(dexp.arg1), "not"))

    def visit_op2(self, dexp: D0Eop2):
        name = dexp.name
        if name in ("and", "or"):
            left = self._bool(self.run(dexp.arg1), name)
            if left == (name == "or"):
                return D0Ebtf(left)
            return D0Ebtf(self._bool(self.run(dexp.arg2), name))
        if name not in ARITHMETIC:
            raise EvalError(f"unsupported operator {name}")
        left = self._nat(self.run(dexp.arg1), name)
        right = self._nat(self.run(dexp.arg2), name)
        return ARITHMETIC[name](left, right)

    def visit_if0(self, dexp: D0Eif0):
        condition = self._bool(self.run(dexp.arg1), "if")
        return _Tail(dexp.arg2 if condition else dexp.arg3)

    def visit_let(self, dexp: D0Elet):
        bound = self.run(dexp.arg2)
        return _Tail(d0exp_substitute(dexp.arg3, dexp.arg1, bound))

    def visit_pair(self, dexp: D0Epair):
        left = self.run(dexp.arg1)
        right = self.run(dexp.arg2)
        return D0Epair(left, right)

    def visit_pfst(self, dexp: D0Epfst):
        return self._pair(self.run(dexp.arg1), "fst").arg1

    def visit_psnd(self, dexp: D0Epsnd):
        return self._pair(self.run(dexp.arg1), "snd").arg2

    @staticmethod
    def _bool(value, where: str) -> bool:
        if not isinstance(value, D0Ebtf):
            raise EvalError(f"{where} requires a boolean")
        return value.arg1

    @staticmethod
    def _nat(value, where: str) -> int:
        if not isinstance(value, D0Eint):
            raise EvalError(f"{where} requires natural numbers")
        return value.arg1

    @staticmethod
    def _pair(value, where: str) -> D0Epair:
        if not isinstance(value, D0Epair):
            raise EvalError(f"{where} requires a pair")
        return value


def evaluate(expr, budget: int | None = None, trace: list | None = None) -> Outcome:
    """Evaluate a target term (budget required) or a closed source expression."""
    if isinstance(expr, Term):
        if not isinstance(budget, int) or isinstance(budget, bool) or budget < 0:
            raise EvalError("target evaluation requires a nonnegative step budget")
        if not only_target(expr):
            raise EvalError("a target term may contain only Var, Lam, and App")
        free = expr.fv()
    else:
        if budget is not None and (not isinstance(budget, int) or budget < 0):
            raise EvalError("a step budget must be a nonnegative integer")
        free = d0exp_fvset(expr)
    if free:
        return Outcome("rejected", 0, message="open term: " + ", ".join(sorted(free)))
    machine = EvaluateVisitor(budget, trace)
    try:
        value = machine.run(expr)
    except _Exhausted as stop:
        return Outcome("exhausted", stop.steps, message="step budget exhausted")
    return Outcome("value", machine.steps, value)


def source_data(result):
    """Turn a source value (or an Outcome holding one) into ints, bools, and tuples."""
    value = result.value if isinstance(result, Outcome) else result
    if isinstance(value, D0Eint):
        return value.arg1
    if isinstance(value, D0Ebtf):
        return value.arg1
    if isinstance(value, D0Epair):
        return (source_data(value.arg1), source_data(value.arg2))
    if isinstance(value, Term):
        return pretty(value)
    if value is None:
        return None
    return d0exp_pretty(value)
