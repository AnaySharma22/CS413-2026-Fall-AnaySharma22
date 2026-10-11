"""Pretty printing and capture-avoiding substitution for the supplied LAMBDA AST.

Neither operation evaluates its input. Child traversals go through accept.
"""

import sys
from pathlib import Path

ASSIGN_DIR = Path(__file__).resolve().parent.parent
if str(ASSIGN_DIR) not in sys.path:
    sys.path.insert(0, str(ASSIGN_DIR))

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
    D0ExpVisitor,
    d0exp,
    d0exp_fvset,
    dvar,
)


class PrettyPrintVisitor(D0ExpVisitor[str]):
    """Render one expression on a single line. This visitor does not evaluate."""

    def visit_int(self, dexp: D0Eint) -> str:
        return str(dexp.arg1)

    def visit_btf(self, dexp: D0Ebtf) -> str:
        return "true" if dexp.arg1 else "false"

    def visit_var(self, dexp: D0Evar) -> str:
        return dexp.arg1

    def visit_op1(self, dexp: D0Eop1) -> str:
        return f"({dexp.name} {dexp.arg1.accept(self)})"

    def visit_op2(self, dexp: D0Eop2) -> str:
        return f"({dexp.arg1.accept(self)} {dexp.name} {dexp.arg2.accept(self)})"

    def visit_lam(self, dexp: D0Elam) -> str:
        return f"(lam {dexp.arg1}. {dexp.arg2.accept(self)})"

    def visit_fix(self, dexp: D0Efix) -> str:
        return f"(fix {dexp.arg1}({dexp.arg2}). {dexp.arg3.accept(self)})"

    def visit_app(self, dexp: D0Eapp) -> str:
        return f"({dexp.arg1.accept(self)} {dexp.arg2.accept(self)})"

    def visit_if0(self, dexp: D0Eif0) -> str:
        return (
            f"(if {dexp.arg1.accept(self)} then {dexp.arg2.accept(self)} "
            f"else {dexp.arg3.accept(self)})"
        )

    def visit_let(self, dexp: D0Elet) -> str:
        return (
            f"(let {dexp.arg1} = {dexp.arg2.accept(self)} in {dexp.arg3.accept(self)})"
        )

    def visit_pair(self, dexp: D0Epair) -> str:
        return f"(pair {dexp.arg1.accept(self)} {dexp.arg2.accept(self)})"

    def visit_pfst(self, dexp: D0Epfst) -> str:
        return f"(fst {dexp.arg1.accept(self)})"

    def visit_psnd(self, dexp: D0Epsnd) -> str:
        return f"(snd {dexp.arg1.accept(self)})"


def d0exp_pretty(expression: d0exp) -> str:
    return expression.accept(PrettyPrintVisitor())


class NameCollector(D0ExpVisitor[frozenset[dvar]]):
    """Every variable occurrence and every binder. Not only free names."""

    def visit_int(self, dexp: D0Eint) -> frozenset[dvar]:
        return frozenset()

    def visit_btf(self, dexp: D0Ebtf) -> frozenset[dvar]:
        return frozenset()

    def visit_var(self, dexp: D0Evar) -> frozenset[dvar]:
        return frozenset({dexp.arg1})

    def visit_lam(self, dexp: D0Elam) -> frozenset[dvar]:
        return frozenset({dexp.arg1}) | dexp.arg2.accept(self)

    def visit_fix(self, dexp: D0Efix) -> frozenset[dvar]:
        return frozenset({dexp.arg1, dexp.arg2}) | dexp.arg3.accept(self)

    def visit_let(self, dexp: D0Elet) -> frozenset[dvar]:
        return (
            frozenset({dexp.arg1})
            | dexp.arg2.accept(self)
            | dexp.arg3.accept(self)
        )

    def visit_op1(self, dexp: D0Eop1) -> frozenset[dvar]:
        return dexp.arg1.accept(self)

    def visit_pfst(self, dexp: D0Epfst) -> frozenset[dvar]:
        return dexp.arg1.accept(self)

    def visit_psnd(self, dexp: D0Epsnd) -> frozenset[dvar]:
        return dexp.arg1.accept(self)

    def visit_op2(self, dexp: D0Eop2) -> frozenset[dvar]:
        return dexp.arg1.accept(self) | dexp.arg2.accept(self)

    def visit_app(self, dexp: D0Eapp) -> frozenset[dvar]:
        return dexp.arg1.accept(self) | dexp.arg2.accept(self)

    def visit_pair(self, dexp: D0Epair) -> frozenset[dvar]:
        return dexp.arg1.accept(self) | dexp.arg2.accept(self)

    def visit_if0(self, dexp: D0Eif0) -> frozenset[dvar]:
        return dexp.arg1.accept(self) | dexp.arg2.accept(self) | dexp.arg3.accept(self)


class FreshNames:
    """stem_1, stem_2, ... skipping any name already reserved for this call."""

    def __init__(self, reserved: set[dvar]):
        self.reserved = set(reserved)

    def allocate(self, stem: dvar) -> dvar:
        number = 1
        while True:
            candidate = f"{stem}_{number}"
            if candidate not in self.reserved:
                self.reserved.add(candidate)
                return candidate
            number += 1


class SubstitutionVisitor(D0ExpVisitor[d0exp]):
    """Replace free occurrences of one variable. Binders are renamed only to avoid capture."""

    def __init__(self, target: dvar, replacement: d0exp, fresh: FreshNames):
        self.target = target
        self.replacement = replacement
        self.fresh = fresh

    def visit_int(self, dexp: D0Eint) -> d0exp:
        return dexp

    def visit_btf(self, dexp: D0Ebtf) -> d0exp:
        return dexp

    def visit_var(self, dexp: D0Evar) -> d0exp:
        if dexp.arg1 == self.target:
            return self.replacement
        return dexp

    def visit_lam(self, dexp: D0Elam) -> d0exp:
        binder, body = dexp.arg1, dexp.arg2
        if binder == self.target or self.target not in d0exp_fvset(body):
            return dexp
        if binder in d0exp_fvset(self.replacement):
            renamed = self.fresh.allocate(binder)
            body = _substitute(body, binder, D0Evar(renamed), self.fresh)
            body = _substitute(body, self.target, self.replacement, self.fresh)
            return D0Elam(renamed, body)
        new_body = body.accept(self)
        if new_body is body:
            return dexp
        return D0Elam(binder, new_body)

    def visit_fix(self, dexp: D0Efix) -> d0exp:
        function, parameter, body = dexp.arg1, dexp.arg2, dexp.arg3
        if (
            function == self.target
            or parameter == self.target
            or self.target not in d0exp_fvset(body)
        ):
            return dexp
        free = d0exp_fvset(self.replacement)
        if function == parameter:
            if function not in free:
                new_body = body.accept(self)
                if new_body is body:
                    return dexp
                return D0Efix(function, parameter, new_body)
            renamed = self.fresh.allocate(function)
            body = _substitute(body, function, D0Evar(renamed), self.fresh)
            body = _substitute(body, self.target, self.replacement, self.fresh)
            return D0Efix(renamed, renamed, body)
        current = body
        function2, parameter2 = function, parameter
        if function in free:
            function2 = self.fresh.allocate(function)
            current = _substitute(current, function, D0Evar(function2), self.fresh)
        if parameter in free:
            parameter2 = self.fresh.allocate(parameter)
            current = _substitute(current, parameter, D0Evar(parameter2), self.fresh)
        new_body = _substitute(current, self.target, self.replacement, self.fresh)
        if function2 == function and parameter2 == parameter and new_body is body:
            return dexp
        return D0Efix(function2, parameter2, new_body)

    def visit_let(self, dexp: D0Elet) -> d0exp:
        binder, init, body = dexp.arg1, dexp.arg2, dexp.arg3
        new_init = init.accept(self)
        if binder == self.target or self.target not in d0exp_fvset(body):
            if new_init is init:
                return dexp
            return D0Elet(binder, new_init, body)
        if binder in d0exp_fvset(self.replacement):
            renamed = self.fresh.allocate(binder)
            new_body = _substitute(body, binder, D0Evar(renamed), self.fresh)
            new_body = _substitute(new_body, self.target, self.replacement, self.fresh)
            return D0Elet(renamed, new_init, new_body)
        new_body = body.accept(self)
        if new_init is init and new_body is body:
            return dexp
        return D0Elet(binder, new_init, new_body)

    def visit_op1(self, dexp: D0Eop1) -> d0exp:
        child = dexp.arg1.accept(self)
        if child is dexp.arg1:
            return dexp
        return D0Eop1(dexp.name, child)

    def visit_pfst(self, dexp: D0Epfst) -> d0exp:
        child = dexp.arg1.accept(self)
        if child is dexp.arg1:
            return dexp
        return D0Epfst(child)

    def visit_psnd(self, dexp: D0Epsnd) -> d0exp:
        child = dexp.arg1.accept(self)
        if child is dexp.arg1:
            return dexp
        return D0Epsnd(child)

    def visit_op2(self, dexp: D0Eop2) -> d0exp:
        left = dexp.arg1.accept(self)
        right = dexp.arg2.accept(self)
        if left is dexp.arg1 and right is dexp.arg2:
            return dexp
        return D0Eop2(dexp.name, left, right)

    def visit_app(self, dexp: D0Eapp) -> d0exp:
        left = dexp.arg1.accept(self)
        right = dexp.arg2.accept(self)
        if left is dexp.arg1 and right is dexp.arg2:
            return dexp
        return D0Eapp(left, right)

    def visit_pair(self, dexp: D0Epair) -> d0exp:
        left = dexp.arg1.accept(self)
        right = dexp.arg2.accept(self)
        if left is dexp.arg1 and right is dexp.arg2:
            return dexp
        return D0Epair(left, right)

    def visit_if0(self, dexp: D0Eif0) -> d0exp:
        cond = dexp.arg1.accept(self)
        then_branch = dexp.arg2.accept(self)
        else_branch = dexp.arg3.accept(self)
        if (
            cond is dexp.arg1
            and then_branch is dexp.arg2
            and else_branch is dexp.arg3
        ):
            return dexp
        return D0Eif0(cond, then_branch, else_branch)


def _substitute(expression: d0exp, variable: dvar, replacement: d0exp, fresh: FreshNames) -> d0exp:
    return expression.accept(SubstitutionVisitor(variable, replacement, fresh))


def d0exp_substitute(expression: d0exp, variable: dvar, replacement: d0exp) -> d0exp:
    reserved = set(expression.accept(NameCollector()))
    reserved |= set(replacement.accept(NameCollector()))
    reserved.add(variable)
    return _substitute(expression, variable, replacement, FreshNames(reserved))
