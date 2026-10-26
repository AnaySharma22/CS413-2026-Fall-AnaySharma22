# Testing

From `assigns/06`:

```text
python -m unittest discover -s MySolution/tests -v
python MySolution/demo.py
```

40 tests passed on Python 3.14.0. The demo reported `14 of 14 programs match the expected column.`

Test classes are named for the seven testing items in `Assign06.md`. Every expected answer is written in the test. Answers are not recomputed in Python. Tests that run a program also check the source-side answer from the same evaluator.

## Item 1: substitution, shadowing, capture (`T1Substitution`)

| Test | What it checks | ACC |
| --- | --- | --- |
| `test_capture_is_avoided_and_y_stays_free` | `(lam y. x)[x := y]` is `(lam y_1. y)`, and `y` stays free | ACC-01 |
| `test_shadowing_binder_stops_substitution` | `(lam x. ...)[x := y]` is the same object | ACC-01 |
| `test_nested_shadow_and_an_existing_fresh_name` | Nested `y` binders; an existing `y_1` forces `y_2` | ACC-01 |
| `test_replacement_is_inserted_once_and_inputs_are_kept` | Replacement inserted as the same object; term and replacement unchanged | ACC-01 |
| `test_open_terms_can_be_substituted` | Substitution on an open term | ACC-01 |
| `test_printer_formats` | `x`, `(lam x. body)`, `(fn arg)`, nested | ACC-13 |

## Item 2: call-by-value reduction (`T2Reduction`)

| Test | What it checks | ACC |
| --- | --- | --- |
| `test_no_reduction_under_a_lambda` | `lam x. ((lam y. y) x)` is a value in zero steps | ACC-02 |
| `test_budget_boundaries` | `I` at 0, `I I` at 0, `I I` at 1 | ACC-03 |
| `test_left_then_right_then_contract` | Trace of `(I I) (I I)` | ACC-02 |
| `test_argument_is_a_value_before_substitution` | The argument is reduced before the outer beta | ACC-02 |
| `test_deterministic_and_input_preserved` | Same outcome twice; input unchanged | ACC-04 |
| `test_diverging_term_exhausts` | Omega exhausts at its budget, twice | ACC-03 |
| `test_open_terms_and_bad_budgets_are_rejected` | Open term rejected in zero steps; `None`, `-1`, and `1.5` budgets refused | RED-02, RED-03 |
| `test_one_evaluator_for_both_languages` | A source `(lam x. x) 3` and a target `I I` give the same trace through the same visitor | QLT-02 |
| `test_target_run_uses_only_the_shared_methods` | All ten source-only visit methods stubbed to fail; compiled `2 + 3` still runs and decodes 5 | RED-05, ACC-14 |
| `test_reducer_does_not_shortcut_church_numerals` | `evaluate.py` does not mention numerals, Church encodings, or the observer, and does not import the compiler | ENC-04, RED-05 |

## Item 3: every constructor and operator (`T3ConstructorsAndOperators`)

| Test | What it checks | ACC |
| --- | --- | --- |
| `test_literals_zero_and_both_booleans` | `0`, `7`, `true`, `false` | ACC-05 |
| `test_arithmetic_including_predecessor_of_zero` | Eight `+`, `-`, `*` cases, including `0 - 1 = 0`, `2 - 5 = 0`, and multiplication by zero | ACC-05 |
| `test_both_outcomes_of_every_comparison` | Eighteen cases: each comparison true, false, and with equal operands | ACC-05 |
| `test_source_boolean_truth_tables` | Source `not`, `and`, and `or`, every input pair | ACC-05 |
| `test_remaining_constructors` | `if`, `let`, application, `fst`, `snd`, `pair`, `fix` | ACC-05 |
| `test_library_combinators_directly` | `SUCC`, `PRED` (0, 1, 4), `ADD`, `SUB`, `MUL`, `NOT`, value `AND` and `OR` | ACC-05 |

## Item 4: scope and names (`T4Scope`)

| Test | What it checks | ACC |
| --- | --- | --- |
| `test_free_variables_are_preserved_on_open_terms` | Eleven open terms, including `let x = x in x` and free `s`, `t`, `f`, `x`, `v`, `w`, `k_1`; `FV(C[e]) = FV(e)`; output is pure | ACC-06 |
| `test_source_and_repeated_output_are_unchanged` | Source AST identity snapshot unchanged; the same output twice | ACC-06, ACC-10 |
| `test_nested_lets_and_initializer_scope` | `let x = 5 in let x = x * 2 in x` is 10; an inner `let x` does not affect `y` | ACC-06 |
| `test_nested_lambdas_shadow` | `((lam x. lam x. x) 1) 2` is 2 | ACC-06 |
| `test_source_names_that_match_encoding_and_thunk_names` | Source `s`, `z`, `t`, `f`, `w`, and `k_1` all keep their meaning | ACC-06 |
| `test_both_fix_binders_including_z_names` | `(fix f(f). f) 3` is 3; a function named `g`, a parameter named `v`, and a `fix s(z)` around a free `n` | ACC-07 |

## Item 5: divergence (`T5Divergence`)

| Test | What it checks | ACC |
| --- | --- | --- |
| `test_unselected_divergence_is_skipped` | `LOOP` in an unchosen `if` branch, or after `false and` or `true or`, is not run | ACC-08 |
| `test_forced_divergence_exhausts` | Argument, let initializer, either pair component, chosen branch, `true and LOOP`, `false or LOOP`, an arithmetic operand, and `LOOP` itself | ACC-08 |

## Item 6: demonstrations and rejection (`T6DemonstrationsAndRejection`)

| Test | What it checks | ACC |
| --- | --- | --- |
| `test_required_demonstrations` | All fourteen programs; target and source agree | DEMO-01 to DEMO-14 |
| `test_nested_pair` | `pair (pair 2 true) 3` decodes to `((2, True), 3)` | ACC-12 |
| `test_recursion_counts_are_stable` | Factorial and Fibonacci step counts repeat and stay under the budget | ACC-07 |
| `test_rejection_names_the_bad_input_even_in_dead_code` | `-1`, `/`, `%`, `neg` in live code, dead branches, unapplied lambdas, and an unapplied `fix`; the message names the input | ACC-09 |

## Item 7: structure, isolation, and observers (`T7StructureAndObservation`)

| Test | What it checks | ACC |
| --- | --- | --- |
| `test_combinators_and_contexts_are_closed_pure_terms` | Every combinator and every observation context is closed and pure | ACC-05 |
| `test_every_demonstration_compiles_to_pure_terms` | Only `Var`, `Lam`, `App` in each output | ACC-10 |
| `test_compilation_never_enters_the_evaluator` | `evaluate` and `EvaluateVisitor.run` stubbed to fail; arithmetic, `LOOP`, and factorial still compile; `compile.py` has no evaluator import | ACC-10 |
| `test_alpha_renamed_and_computed_values_decode` | `lam a. lam b. a (a b)` is 2; `lam p. lam q. q` is false; `2 + 2` decodes to 4 while its body still has work in it | ACC-11 |
| `test_zero_by_kind` | Church zero is `0` as a natural and `false` as a boolean | ACC-11 |
| `test_malformed_differs_from_exhausted` | `TRUE` read as a natural and `NUM(2)` read as a boolean are malformed; budget 0 is exhausted; a pair at budget 4 is exhausted | ACC-11 |

## Checked by review, not by a test

- ACC-14: `lambda1_vp.py` is unchanged (`git diff` against upstream shows nothing). Both commands above were run from `assigns/06`.
- ACC-15: the slides cover the required topics. The recording has to be checked for length, face, slides, audio, and access after it is made.
