"""Decode Church data with the same call-by-value engine.

Contexts and the shapes Python inspects afterwards:

- natural: evaluate `v STEP BASE`. The value is a spine of
  `lam c. lam z. c tail` nodes ending in `lam c. lam z. z`; the count of
  `c tail` nodes is the number. Binder names are not compared.
- boolean: evaluate `v MARK_TRUE MARK_FALSE`. The value has to be one of the
  two markers, compared up to alpha-renaming.
- pair: evaluate `FST v` and `SND v`, then observe each component with its
  own kind. Nested pairs repeat this.

The caller names the kind because NUM(0) and FALSE are the same lambda. One
observation budget is shared by every reduction in a call and is separate
from the execution budget. Exhaustion and a malformed shape are different
statuses. Python counts and compares final shapes only; it never does the
arithmetic.
"""

from __future__ import annotations

import boot  # noqa: F401  (adds assigns/05 to sys.path)

from church import FST, SND
from evaluate import Outcome, evaluate
from target import App, Lam, Term, Var


class ObserveError(Exception):
    pass


def STEP() -> Term:
    return Lam("tail", Lam("c", Lam("z", App(Var("c"), Var("tail")))))


def BASE() -> Term:
    return Lam("c", Lam("z", Var("z")))


def MARK_TRUE() -> Term:
    """lam a. lam b. lam c. a. Applying a marker to anything is not a marker."""
    return Lam("a", Lam("b", Lam("c", Var("a"))))


def MARK_FALSE() -> Term:
    """lam a. lam b. lam c. b."""
    return Lam("a", Lam("b", Lam("c", Var("b"))))


class Observation:
    def __init__(self, status: str, steps: int, value=None, message: str = ""):
        self.status = status
        self.steps = steps
        self.value = value
        self.message = message


def observe(value: Term, kind, budget: int) -> Observation:
    """kind is 'nat', 'bool', or ('pair', kind, kind)."""
    counter = {"steps": 0}

    def spend(outcome: Outcome) -> Term:
        counter["steps"] += outcome.steps
        if outcome.status == "exhausted":
            raise _Stop("exhausted", counter["steps"])
        if outcome.status != "value":
            raise _Stop("malformed", counter["steps"], outcome.message or outcome.status)
        return outcome.value

    try:
        decoded = _decode(value, kind, budget, counter, spend)
    except _Stop as stop:
        return Observation(stop.status, stop.steps, message=stop.message)
    return Observation("value", counter["steps"], decoded)


def _decode(value: Term, kind, budget: int, counter: dict, spend):
    remaining = budget - counter["steps"]
    if remaining < 0:
        raise _Stop("exhausted", counter["steps"])
    if kind == "nat":
        outcome = evaluate(App(App(value, STEP()), BASE()), remaining)
        node = spend(outcome)
        try:
            return _count_spine(node)
        except ObserveError as error:
            raise _Stop("malformed", counter["steps"], str(error)) from error
    if kind == "bool":
        outcome = evaluate(App(App(value, MARK_TRUE()), MARK_FALSE()), remaining)
        chosen = spend(outcome)
        if _same_marker(chosen, MARK_TRUE()):
            return True
        if _same_marker(chosen, MARK_FALSE()):
            return False
        raise _Stop("malformed", counter["steps"], "boolean marker was not selected")
    if isinstance(kind, tuple) and kind and kind[0] == "pair":
        left_kind, right_kind = kind[1], kind[2]
        left_out = evaluate(App(FST(), value), remaining)
        left_value = spend(left_out)
        right_out = evaluate(App(SND(), value), budget - counter["steps"])
        right_value = spend(right_out)
        left = _decode(left_value, left_kind, budget, counter, spend)
        right = _decode(right_value, right_kind, budget, counter, spend)
        return (left, right)
    raise ObserveError(f"unknown kind {kind!r}")


def _count_spine(term: Term) -> int:
    if not isinstance(term, Lam) or not isinstance(term.body, Lam):
        raise ObserveError("natural spine is not a double lambda")
    outer = term.name
    inner = term.body.name
    body = term.body.body
    if isinstance(body, Var) and body.name == inner:
        return 0
    if isinstance(body, App) and isinstance(body.fn, Var) and body.fn.name == outer:
        return 1 + _count_spine(body.arg)
    raise ObserveError("natural spine does not match STEP/BASE")


def _same_marker(term: Term, marker: Term) -> bool:
    return _shape(term, ()) == _shape(marker, ())


def _shape(term: Term, bound: tuple[str, ...]):
    """De Bruijn shape, so two alpha-equivalent markers compare equal."""
    if isinstance(term, Var):
        if term.name in bound:
            return ("bound", bound[::-1].index(term.name))
        return ("free", term.name)
    if isinstance(term, Lam):
        return ("lam", _shape(term.body, bound + (term.name,)))
    if isinstance(term, App):
        return ("app", _shape(term.fn, bound), _shape(term.arg, bound))
    return ("other",)


class _Stop(Exception):
    def __init__(self, status: str, steps: int, message: str = ""):
        self.status = status
        self.steps = steps
        self.message = message
