"""unittest suite. From assigns/06:

python -m unittest discover -s MySolution/tests -v

Classes follow the seven testing items in Assign06.md. TESTING.md maps each
test to those items and to the ACC checks in REQUIREMENTS.md.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import boot  # noqa: E402,F401

import compile as compile_mod  # noqa: E402
import evaluate as evaluate_mod  # noqa: E402
from church import (  # noqa: E402
    ADD,
    AND,
    FALSE,
    MUL,
    NOT,
    OR,
    PRED,
    SUB,
    SUCC,
    TRUE,
    combinators,
    numeral,
)
from compile import CompileError, compile_expr  # noqa: E402
from demo import EXEC_BUDGET, EXHAUST_BUDGET, OBS_BUDGET, run_example  # noqa: E402
from evaluate import evaluate, source_data  # noqa: E402
from examples import LOOP, b, demonstrations, factorial, fibonacci, n, op, v  # noqa: E402
from lambda1_vp import (  # noqa: E402
    D0Eapp,
    D0Efix,
    D0Eif0,
    D0Eint,
    D0Elam,
    D0Elet,
    D0Eop1,
    D0Epair,
    D0Epfst,
    D0Epsnd,
    d0exp_fvset,
)
from observe import BASE, MARK_FALSE, MARK_TRUE, STEP, observe  # noqa: E402
from target import App, Lam, Var, only_target, pretty, substitute  # noqa: E402


def _source_ids(expr):
    rows = []

    def walk(node):
        rows.append((id(node), node.ctag))
        for field in ("arg1", "arg2", "arg3"):
            child = getattr(node, field, None)
            if hasattr(child, "accept"):
                walk(child)

    walk(expr)
    return tuple(rows)


def _term_ids(term):
    rows = []

    def walk(node):
        rows.append((id(node), type(node).__name__))
        if isinstance(node, Lam):
            walk(node.body)
        elif isinstance(node, App):
            walk(node.fn)
            walk(node.arg)

    walk(term)
    return tuple(rows)


I = Lam("x", Var("x"))  # noqa: E741


class Pipeline(unittest.TestCase):
    """Helpers: compile, run, observe, and compare with the source side."""

    def finishes(self, expr, kind, expected, budget=EXEC_BUDGET):
        _term, reduced, seen = run_example(expr, kind, budget, OBS_BUDGET)
        self.assertEqual(reduced.status, "value", reduced.message)
        self.assertEqual(seen.status, "value", seen.message)
        self.assertEqual(seen.value, expected)
        self.assertEqual(source_data(evaluate(expr)), expected)

    def exhausts(self, expr):
        _term, reduced, seen = run_example(expr, None, EXHAUST_BUDGET, OBS_BUDGET)
        self.assertEqual(reduced.status, "exhausted")
        self.assertEqual(reduced.steps, EXHAUST_BUDGET)
        self.assertIsNone(seen)


class T1Substitution(unittest.TestCase):
    """Testing item 1: target substitution, shadowing, and capture."""

    def test_capture_is_avoided_and_y_stays_free(self):
        result = substitute(Lam("y", Var("x")), "x", Var("y"))
        self.assertEqual(pretty(result), "(lam y_1. y)")
        self.assertEqual(result.fv(), frozenset({"y"}))

    def test_shadowing_binder_stops_substitution(self):
        shadowed = Lam("x", App(Var("x"), Var("z")))
        self.assertIs(substitute(shadowed, "x", Var("y")), shadowed)

    def test_nested_shadow_and_an_existing_fresh_name(self):
        nested = Lam("y", Lam("y", Var("x")))
        self.assertEqual(pretty(substitute(nested, "x", Var("y"))), "(lam y_1. (lam y_1. y))")
        taken = Lam("y", App(Var("x"), Var("y_1")))
        self.assertEqual(pretty(substitute(taken, "x", Var("y"))), "(lam y_2. (y y_1))")

    def test_replacement_is_inserted_once_and_inputs_are_kept(self):
        replacement = App(Var("x"), Var("x"))
        self.assertIs(substitute(Var("x"), "x", replacement), replacement)
        term = App(Lam("y", Var("x")), Var("x"))
        before, before_r = _term_ids(term), _term_ids(replacement)
        substitute(term, "x", replacement)
        self.assertEqual(_term_ids(term), before)
        self.assertEqual(_term_ids(replacement), before_r)

    def test_open_terms_can_be_substituted(self):
        result = substitute(App(Var("f"), Var("x")), "x", Var("free"))
        self.assertEqual(pretty(result), "(f free)")

    def test_printer_formats(self):
        self.assertEqual(pretty(Var("x")), "x")
        self.assertEqual(pretty(Lam("x", Var("x"))), "(lam x. x)")
        self.assertEqual(pretty(App(Var("f"), Var("x"))), "(f x)")
        nested = App(App(Var("f"), Var("x")), Lam("y", App(Var("y"), Var("y"))))
        self.assertEqual(pretty(nested), "((f x) (lam y. (y y)))")


class T2Reduction(unittest.TestCase):
    """Testing item 2: call-by-value order, values, budgets, divergence."""

    def test_no_reduction_under_a_lambda(self):
        inner = Lam("x", App(Lam("y", Var("y")), Var("x")))
        done = evaluate(inner, 0)
        self.assertEqual((done.status, done.steps), ("value", 0))
        self.assertIs(done.value, inner)

    def test_budget_boundaries(self):
        self.assertEqual(_status(evaluate(I, 0)), ("value", 0))
        self.assertEqual(_status(evaluate(App(I, I), 0)), ("exhausted", 0))
        once = evaluate(App(I, I), 1)
        self.assertEqual(_status(once), ("value", 1))
        self.assertEqual(pretty(once.value), "(lam x. x)")

    def test_left_then_right_then_contract(self):
        trace = []
        outcome = evaluate(App(App(I, I), App(I, I)), 5, trace)
        self.assertEqual(_status(outcome), ("value", 3))
        self.assertEqual(trace, [
            "function", "function", "argument", "beta",
            "argument", "function", "argument", "beta",
            "beta",
        ])

    def test_argument_is_a_value_before_substitution(self):
        trace = []
        evaluate(App(Lam("x", Lam("y", Var("x"))), App(I, I)), 5, trace)
        self.assertEqual(trace, ["function", "argument", "function", "argument", "beta", "beta"])

    def test_deterministic_and_input_preserved(self):
        term = App(App(Lam("a", Lam("b", Var("a"))), I), Lam("z", Var("z")))
        before = _term_ids(term)
        first, second = evaluate(term, 10), evaluate(term, 10)
        self.assertEqual(_status(first), _status(second))
        self.assertEqual(pretty(first.value), pretty(second.value))
        self.assertEqual(_term_ids(term), before)

    def test_diverging_term_exhausts(self):
        omega = App(Lam("x", App(Var("x"), Var("x"))), Lam("x", App(Var("x"), Var("x"))))
        self.assertEqual(_status(evaluate(omega, 30)), ("exhausted", 30))
        self.assertEqual(_status(evaluate(omega, 30)), ("exhausted", 30))

    def test_open_terms_and_bad_budgets_are_rejected(self):
        opened = evaluate(App(I, Var("y")), 5)
        self.assertEqual(_status(opened), ("rejected", 0))
        self.assertIn("y", opened.message)
        for budget in (None, -1, 1.5):
            with self.assertRaises(evaluate_mod.EvalError):
                evaluate(I, budget)

    def test_one_evaluator_for_both_languages(self):
        source_trace, target_trace = [], []
        source = evaluate(D0Eapp(D0Elam("x", v("x")), n(3)), trace=source_trace)
        target = evaluate(App(I, I), 5, target_trace)
        self.assertEqual(source_data(source), 3)
        self.assertEqual(source.steps, 1)
        self.assertEqual(source_trace, target_trace)
        self.assertEqual(source_trace, ["function", "argument", "beta"])
        self.assertEqual(_status(evaluate(D0Eapp(D0Elam("x", v("x")), n(3)), 0)), ("exhausted", 0))
        self.assertEqual(_status(evaluate(v("free"))), ("rejected", 0))

    def test_target_run_uses_only_the_shared_methods(self):
        source_only = [
            "visit_int", "visit_btf", "visit_op1", "visit_op2", "visit_if0",
            "visit_let", "visit_pair", "visit_pfst", "visit_psnd", "visit_fix",
        ]
        visitor = evaluate_mod.EvaluateVisitor
        patches = [
            patch.object(visitor, name, side_effect=AssertionError(name)) for name in source_only
        ]
        for active in patches:
            active.start()
        try:
            result = evaluate(compile_expr(op("+", n(2), n(3))), EXEC_BUDGET)
        finally:
            for active in patches:
                active.stop()
        self.assertEqual(result.status, "value")
        self.assertEqual(observe(result.value, "nat", OBS_BUDGET).value, 5)

    def test_reducer_does_not_shortcut_church_numerals(self):
        text = Path(evaluate_mod.__file__).read_text(encoding="utf-8")
        for marker in ("numeral", "church", "observe", "import compile", "from compile"):
            self.assertNotIn(marker, text)


def _status(outcome):
    return (outcome.status, outcome.steps)


class T3ConstructorsAndOperators(Pipeline):
    """Testing item 3: every constructor and operator, with explicit answers."""

    ARITHMETIC = [
        ("+", 0, 0, 0), ("+", 2, 3, 5),
        ("-", 5, 0, 5), ("-", 3, 3, 0), ("-", 2, 5, 0), ("-", 0, 1, 0),
        ("*", 0, 5, 0), ("*", 3, 4, 12),
    ]
    COMPARISONS = [
        ("<", 2, 3, True), ("<", 3, 2, False), ("<", 3, 3, False),
        ("<=", 2, 3, True), ("<=", 3, 2, False), ("<=", 3, 3, True),
        (">", 3, 2, True), (">", 2, 3, False), (">", 3, 3, False),
        (">=", 3, 2, True), (">=", 2, 3, False), (">=", 3, 3, True),
        ("==", 3, 3, True), ("==", 2, 3, False), ("==", 0, 0, True),
        ("!=", 2, 3, True), ("!=", 3, 3, False), ("!=", 0, 1, True),
    ]

    def test_literals_zero_and_both_booleans(self):
        self.finishes(n(0), "nat", 0)
        self.finishes(n(7), "nat", 7)
        self.finishes(b(True), "bool", True)
        self.finishes(b(False), "bool", False)

    def test_arithmetic_including_predecessor_of_zero(self):
        for name, left, right, expected in self.ARITHMETIC:
            with self.subTest(op=f"{left} {name} {right}"):
                self.finishes(op(name, n(left), n(right)), "nat", expected)

    def test_both_outcomes_of_every_comparison(self):
        for name, left, right, expected in self.COMPARISONS:
            with self.subTest(op=f"{left} {name} {right}"):
                self.finishes(op(name, n(left), n(right)), "bool", expected)

    def test_source_boolean_truth_tables(self):
        for left in (True, False):
            with self.subTest(op=f"not {left}"):
                self.finishes(D0Eop1("not", b(left)), "bool", not left)
            for right in (True, False):
                with self.subTest(op=f"{left} and {right}"):
                    self.finishes(op("and", b(left), b(right)), "bool", left and right)
                with self.subTest(op=f"{left} or {right}"):
                    self.finishes(op("or", b(left), b(right)), "bool", left or right)

    def test_remaining_constructors(self):
        self.finishes(D0Eif0(b(False), n(1), n(2)), "nat", 2)
        self.finishes(D0Elet("x", n(4), op("*", v("x"), v("x"))), "nat", 16)
        self.finishes(D0Eapp(D0Elam("x", op("+", v("x"), n(1))), n(1)), "nat", 2)
        self.finishes(D0Epfst(D0Epair(n(1), n(2))), "nat", 1)
        self.finishes(D0Epsnd(D0Epair(n(1), n(2))), "nat", 2)
        self.finishes(D0Epair(n(1), b(False)), ("pair", "nat", "bool"), (1, False))
        countdown = D0Efix("f", "x", D0Eif0(op("==", v("x"), n(0)), n(9), D0Eapp(v("f"), op("-", v("x"), n(1)))))
        self.finishes(D0Eapp(countdown, n(3)), "nat", 9)

    def test_library_combinators_directly(self):
        def nat(term):
            outcome = evaluate(term, EXEC_BUDGET)
            return observe(outcome.value, "nat", OBS_BUDGET).value

        def boolean(term):
            outcome = evaluate(term, EXEC_BUDGET)
            return observe(outcome.value, "bool", OBS_BUDGET).value

        self.assertEqual(nat(App(SUCC(), numeral(2))), 3)
        self.assertEqual(nat(App(PRED(), numeral(0))), 0)
        self.assertEqual(nat(App(PRED(), numeral(1))), 0)
        self.assertEqual(nat(App(PRED(), numeral(4))), 3)
        self.assertEqual(nat(App(App(ADD(), numeral(2)), numeral(3))), 5)
        self.assertEqual(nat(App(App(SUB(), numeral(2)), numeral(5))), 0)
        self.assertEqual(nat(App(App(MUL(), numeral(3)), numeral(4))), 12)
        self.assertFalse(boolean(App(NOT(), TRUE())))
        self.assertTrue(boolean(App(NOT(), FALSE())))
        for left, right in ((True, True), (True, False), (False, True), (False, False)):
            lterm, rterm = (TRUE() if left else FALSE()), (TRUE() if right else FALSE())
            self.assertEqual(boolean(App(App(AND(), lterm), rterm)), left and right)
            self.assertEqual(boolean(App(App(OR(), lterm), rterm)), left or right)


class T4Scope(Pipeline):
    """Testing item 4: nesting, let scope, fix binders, open terms, names."""

    OPEN = [
        v("s"),
        D0Elet("x", v("x"), v("x")),
        D0Elet("y", v("z"), op("+", v("y"), v("t"))),
        D0Elam("y", D0Elam("y", v("x"))),
        D0Efix("f", "n", v("s")),
        D0Efix("f", "f", v("f")),
        D0Efix("g", "x", op("+", v("v"), v("x"))),
        D0Eif0(v("k_1"), v("k_2"), v("w")),
        op("and", v("t"), v("f")),
        D0Eapp(D0Elam("z", v("z")), v("t")),
        D0Epfst(D0Epair(v("a"), v("p"))),
    ]

    def test_free_variables_are_preserved_on_open_terms(self):
        for expr in self.OPEN:
            with self.subTest(expr=type(expr).__name__):
                term = compile_expr(expr)
                self.assertEqual(term.fv(), d0exp_fvset(expr))
                self.assertTrue(only_target(term))

    def test_source_and_repeated_output_are_unchanged(self):
        for expr in self.OPEN + [factorial(), fibonacci()]:
            with self.subTest(expr=type(expr).__name__):
                before = _source_ids(expr)
                first = pretty(compile_expr(expr))
                self.assertEqual(_source_ids(expr), before)
                self.assertEqual(pretty(compile_expr(expr)), first)

    def test_nested_lets_and_initializer_scope(self):
        self.finishes(D0Elet("x", n(5), D0Elet("x", op("*", v("x"), n(2)), v("x"))), "nat", 10)
        inner = D0Elet("y", op("+", v("x"), n(1)), D0Elet("x", n(10), v("y")))
        self.finishes(D0Elet("x", n(1), inner), "nat", 2)

    def test_nested_lambdas_shadow(self):
        expr = D0Eapp(D0Eapp(D0Elam("x", D0Elam("x", v("x"))), n(1)), n(2))
        self.finishes(expr, "nat", 2)

    def test_source_names_that_match_encoding_and_thunk_names(self):
        self.finishes(D0Elet("s", n(2), D0Elet("z", n(3), op("+", v("s"), v("z")))), "nat", 5)
        self.finishes(D0Eapp(D0Eapp(D0Elam("t", D0Elam("f", v("t"))), n(1)), n(2)), "nat", 1)
        thunk_names = D0Elet("k_1", n(4), D0Eif0(b(True), op("+", v("k_1"), n(6)), v("k_1")))
        self.finishes(thunk_names, "nat", 10)
        self.finishes(D0Elet("w", n(3), op("and", b(True), op("==", v("w"), n(3)))), "bool", True)

    def test_both_fix_binders_including_z_names(self):
        same = D0Eapp(D0Efix("f", "f", v("f")), n(3))
        self.finishes(same, "nat", 3)
        function_g = D0Efix("g", "x", D0Eif0(op("==", v("x"), n(0)), n(0), D0Eapp(v("g"), op("-", v("x"), n(1)))))
        self.finishes(D0Eapp(function_g, n(3)), "nat", 0)
        parameter_v = D0Efix("x", "v", D0Eif0(op("==", v("v"), n(0)), n(1), op("*", v("v"), D0Eapp(v("x"), op("-", v("v"), n(1))))))
        self.finishes(D0Eapp(parameter_v, n(3)), "nat", 6)
        outer = D0Elet("n", n(7), D0Eapp(D0Efix("s", "z", v("n")), n(0)))
        self.finishes(outer, "nat", 7)


class T5Divergence(Pipeline):
    """Testing item 5: skipped and forced divergence."""

    def test_unselected_divergence_is_skipped(self):
        self.finishes(D0Eif0(b(True), n(1), LOOP()), "nat", 1)
        self.finishes(D0Eif0(b(False), LOOP(), n(1)), "nat", 1)
        self.finishes(op("and", b(False), op("==", LOOP(), n(0))), "bool", False)
        self.finishes(op("or", b(True), op("==", LOOP(), n(0))), "bool", True)

    def test_forced_divergence_exhausts(self):
        cases = [
            D0Eapp(D0Elam("x", n(0)), LOOP()),
            D0Elet("x", LOOP(), n(2)),
            D0Epfst(D0Epair(n(2), LOOP())),
            D0Epsnd(D0Epair(LOOP(), b(True))),
            D0Eif0(b(True), LOOP(), n(1)),
            op("and", b(True), op("==", LOOP(), n(0))),
            op("or", b(False), op("==", LOOP(), n(0))),
            op("+", n(1), LOOP()),
            LOOP(),
        ]
        for expr in cases:
            with self.subTest(expr=type(expr).__name__):
                self.exhausts(expr)


class T6DemonstrationsAndRejection(Pipeline):
    """Testing item 6: the required table, nested pairs, and rejection."""

    def test_required_demonstrations(self):
        self.assertEqual(len(demonstrations()), 14)
        for title, expr, kind, expected in demonstrations():
            with self.subTest(title=title):
                if kind is None:
                    self.assertEqual(expected, "exhausted")
                    self.exhausts(expr)
                else:
                    self.finishes(expr, kind, expected)

    def test_nested_pair(self):
        expr = D0Epair(D0Epair(n(2), b(True)), n(3))
        self.finishes(expr, ("pair", ("pair", "nat", "bool"), "nat"), ((2, True), 3))

    def test_recursion_counts_are_stable(self):
        for expr in (factorial(), fibonacci()):
            _t1, first, seen1 = run_example(expr, "nat", EXEC_BUDGET, OBS_BUDGET)
            _t2, second, seen2 = run_example(expr, "nat", EXEC_BUDGET, OBS_BUDGET)
            self.assertEqual((first.steps, seen1.steps), (second.steps, seen2.steps))
            self.assertLess(first.steps, EXEC_BUDGET)

    def test_rejection_names_the_bad_input_even_in_dead_code(self):
        cases = [
            (n(-1), "-1"),
            (D0Eif0(b(True), n(1), n(-2)), "-2"),
            (D0Elam("x", n(-3)), "-3"),
            (D0Efix("f", "x", op("+", v("x"), n(-4))), "-4"),
            (op("/", n(1), n(0)), "/"),
            (D0Eif0(b(True), n(1), op("/", n(1), n(1))), "/"),
            (op("and", b(False), op("%", n(1), n(2))), "%"),
            (D0Eop1("neg", b(True)), "neg"),
            (D0Elam("x", D0Eop1("neg", v("x"))), "neg"),
        ]
        for expr, token in cases:
            with self.subTest(token=token):
                with self.assertRaises(CompileError) as caught:
                    compile_expr(expr)
                self.assertIn(token, str(caught.exception))


class T7StructureAndObservation(unittest.TestCase):
    """Testing item 7, plus the observer checks in Task 4."""

    def test_combinators_and_contexts_are_closed_pure_terms(self):
        extra = {"STEP": STEP(), "BASE": BASE(), "MARK_TRUE": MARK_TRUE(), "MARK_FALSE": MARK_FALSE()}
        for name, term in {**combinators(), **extra}.items():
            with self.subTest(name=name):
                self.assertEqual(term.fv(), frozenset())
                self.assertTrue(only_target(term))

    def test_every_demonstration_compiles_to_pure_terms(self):
        for title, expr, _kind, _expected in demonstrations():
            with self.subTest(title=title):
                self.assertTrue(only_target(compile_expr(expr)))

    def test_compilation_never_enters_the_evaluator(self):
        fail = AssertionError("compilation called the evaluator")
        with patch.object(evaluate_mod, "evaluate", side_effect=fail), \
                patch.object(evaluate_mod.EvaluateVisitor, "run", side_effect=fail):
            for expr in (op("+", n(2), op("*", n(3), n(4))), LOOP(), factorial()):
                self.assertTrue(only_target(compile_expr(expr)))
        text = Path(compile_mod.__file__).read_text(encoding="utf-8")
        self.assertNotIn("import evaluate", text)
        self.assertNotIn("from evaluate", text)

    def test_alpha_renamed_and_computed_values_decode(self):
        renamed_two = Lam("a", Lam("b", App(Var("a"), App(Var("a"), Var("b")))))
        self.assertEqual(observe(renamed_two, "nat", 50).value, 2)
        renamed_false = Lam("p", Lam("q", Var("q")))
        self.assertIs(observe(renamed_false, "bool", 50).value, False)
        computed = evaluate(App(App(ADD(), numeral(2)), numeral(2)), EXEC_BUDGET)
        self.assertIsInstance(computed.value.body, Lam)
        self.assertEqual(observe(computed.value, "nat", OBS_BUDGET).value, 4)

    def test_zero_by_kind(self):
        zero = numeral(0)
        self.assertEqual(observe(zero, "nat", 10).value, 0)
        self.assertIs(observe(zero, "bool", 10).value, False)

    def test_malformed_differs_from_exhausted(self):
        self.assertEqual(observe(TRUE(), "nat", 50).status, "malformed")
        self.assertEqual(observe(numeral(2), "bool", 50).status, "malformed")
        starved = observe(numeral(2), "nat", 0)
        self.assertEqual((starved.status, starved.steps), ("exhausted", 0))
        pair = evaluate(compile_expr(D0Epair(n(2), n(3))), EXEC_BUDGET).value
        partial = observe(pair, ("pair", "nat", "nat"), 4)
        self.assertEqual(partial.status, "exhausted")


if __name__ == "__main__":
    unittest.main()
