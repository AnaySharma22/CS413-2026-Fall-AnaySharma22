"""Pure lambda terms: variables, single-argument lambdas, and applications.

Substitution follows the capture-avoiding policy from Assignment 5: a binder
is renamed only when it would capture a free name of the replacement, and the
fresh name is stem_1, stem_2, ... The reserved set is every name in the term
and the replacement, not only the free names.

The three classes are separate from the source AST. They accept the same
visit_var, visit_lam, and visit_app calls as D0Evar, D0Elam, and D0Eapp, so
the shared evaluator uses one case for each form in both languages.
"""

from __future__ import annotations


class Term:
    def fv(self) -> frozenset[str]:
        cached = getattr(self, "_fv", None)
        if cached is None:
            cached = frozenset(self._fv_calc())
            self._fv = cached
        return cached

    def names(self) -> frozenset[str]:
        cached = getattr(self, "_names", None)
        if cached is None:
            cached = frozenset(self._names_calc())
            self._names = cached
        return cached

    def _fv_calc(self) -> set[str]:
        raise NotImplementedError

    def _names_calc(self) -> set[str]:
        raise NotImplementedError


class Var(Term):
    """Dispatches to visit_var, like D0Evar; arg1 is the name."""

    def __init__(self, name: str):
        self.name = name

    @property
    def arg1(self) -> str:
        return self.name

    def accept(self, visitor):
        return visitor.visit_var(self)

    def _fv_calc(self) -> set[str]:
        return {self.name}

    def _names_calc(self) -> set[str]:
        return {self.name}

    def __repr__(self) -> str:
        return f"Var({self.name!r})"


class Lam(Term):
    """Dispatches to visit_lam, like D0Elam; arg1 is the binder, arg2 the body."""

    def __init__(self, name: str, body: Term):
        self.name = name
        self.body = body

    @property
    def arg1(self) -> str:
        return self.name

    @property
    def arg2(self) -> Term:
        return self.body

    def accept(self, visitor):
        return visitor.visit_lam(self)

    def _fv_calc(self) -> set[str]:
        return set(self.body.fv() - {self.name})

    def _names_calc(self) -> set[str]:
        return set(self.body.names() | {self.name})

    def __repr__(self) -> str:
        return f"Lam({self.name!r}, {self.body!r})"


class App(Term):
    """Dispatches to visit_app, like D0Eapp; arg1 is the function, arg2 the argument."""

    def __init__(self, fn: Term, arg: Term):
        self.fn = fn
        self.arg = arg

    @property
    def arg1(self) -> Term:
        return self.fn

    @property
    def arg2(self) -> Term:
        return self.arg

    def accept(self, visitor):
        return visitor.visit_app(self)

    def _fv_calc(self) -> set[str]:
        return set(self.fn.fv() | self.arg.fv())

    def _names_calc(self) -> set[str]:
        return set(self.fn.names() | self.arg.names())

    def __repr__(self) -> str:
        return f"App({self.fn!r}, {self.arg!r})"


def pretty(term: Term) -> str:
    if isinstance(term, Var):
        return term.name
    if isinstance(term, Lam):
        return f"(lam {term.name}. {pretty(term.body)})"
    if isinstance(term, App):
        return f"({pretty(term.fn)} {pretty(term.arg)})"
    raise TypeError(f"not a target term: {type(term).__name__}")


def only_target(term: Term) -> bool:
    if isinstance(term, Var):
        return True
    if isinstance(term, Lam):
        return only_target(term.body)
    if isinstance(term, App):
        return only_target(term.fn) and only_target(term.arg)
    return False


class FreshNames:
    """stem_1, stem_2, ... skipping every name already reserved."""

    def __init__(self, reserved: set[str]):
        self.reserved = set(reserved)

    def allocate(self, stem: str) -> str:
        number = 1
        while True:
            candidate = f"{stem}_{number}"
            if candidate not in self.reserved:
                self.reserved.add(candidate)
                return candidate
            number += 1


def substitute(term: Term, variable: str, replacement: Term) -> Term:
    """Replace free occurrences of variable. Does not mutate term or replacement."""
    if variable not in term.fv():
        return term
    if isinstance(term, Var):
        return replacement
    if isinstance(term, Lam):
        if term.name == variable:
            return term
        if term.name in replacement.fv():
            fresh = FreshNames(set(term.names() | replacement.names() | {variable}))
            renamed = fresh.allocate(term.name)
            body = substitute(term.body, term.name, Var(renamed))
            return Lam(renamed, substitute(body, variable, replacement))
        return Lam(term.name, substitute(term.body, variable, replacement))
    if isinstance(term, App):
        return App(
            substitute(term.fn, variable, replacement),
            substitute(term.arg, variable, replacement),
        )
    raise TypeError(f"not a target term: {type(term).__name__}")
