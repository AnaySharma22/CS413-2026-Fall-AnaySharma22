# Design

## Correctness claim

For a closed, well-typed program in this call-by-value source language, if the program produces a natural number, a boolean, or a finite pair of those, then observing the compiled term yields the same data whenever the execution budget and the observation budget are large enough. The compiler does not run the program and encode the answer. It builds a pure term whose call-by-value reduction has that answer.

## Interfaces

| Module | Entry point | Contract |
| --- | --- | --- |
| `compile.py` | `compile_expr(expr) -> Term` | `CompileVisitor` over the supplied `D0ExpVisitor`. Raises `CompileError` naming a negative literal or an unsupported operator. Never calls `evaluate`. |
| `target.py` | `Var`, `Lam`, `App`, `pretty`, `substitute`, `only_target` | Target syntax only. `Term.fv()` and `Term.names()` are cached per node. |
| `church.py` | `TRUE()`, `numeral(n)`, `ADD()`, `PRED()`, `Z()`, ... | Each builder returns a fresh closed term. |
| `evaluate.py` | `evaluate(expr, budget=None) -> Outcome` | One `EvaluateVisitor` for both languages. `Outcome.status` is `value`, `exhausted`, or `rejected`, with a beta-value step count. A target term needs a budget. |
| `observe.py` | `observe(value, kind, budget) -> Observation` | `kind` is `"nat"`, `"bool"`, or `("pair", k1, k2)`. Status is `value`, `exhausted`, or `malformed`. |
| `demo.py` | `python MySolution/demo.py` | Runs the fourteen required programs and writes `demo-out/NN.lam`. |

## Representations

Booleans, numerals, and pairs are the terms required by the assignment. `TRUE` is `lam t. lam f. t`. `FALSE` is `lam t. lam f. f`. `NUM(n)` is `lam s. lam z.` followed by `s` applied `n` times to `z`. `PAIR` is `lam a. lam b. lam p. p a b`. Each is a closed `Var`/`Lam`/`App` tree. The names `TRUE` and `NUM` exist only in Python. The operator terms are listed after the translation rules.

`NUM(0)` and `FALSE` are the same lambda, so the decoder is told which kind it is reading. A natural is observed by evaluating `v STEP BASE`, where `STEP = lam tail. lam c. lam z. c tail` and `BASE = lam c. lam z. z`. The value is a spine of `c tail` nodes ending in `z`, and Python counts the nodes without caring about binder names. A boolean is observed by evaluating `v MARK_TRUE MARK_FALSE`, with markers `lam a. lam b. lam c. a` and `lam a. lam b. lam c. b`. The value has to be one of the two markers up to alpha-renaming. An identity marker would let `NUM(2)` pass as a boolean; these markers make it malformed. Running out of observation steps is a separate status.

Predecessor has to send zero to zero, and it has to be ordinary beta reduction. The term iterates a pair. The start value is `(0, 0)`. One step replaces `(previous, current)` with `(current, succ current)`. After `n` steps the first component is `n - 1` when `n > 0`, and it is still `0` when `n` is `0` because the step is never applied. `pred` returns that first component. Subtraction applies `pred` as many times as the second numeral says, so `2 - 5` becomes `0`. Comparisons are built on that: `m <= n` is `iszero (m - n)`, and the other five follow from it, `not`, and `and`.

The library also has value-level `and` and `or`, which `==` uses on two booleans it has already computed. Source `and` and `or` are not compiled to them. They wrap the right side in a thunk, like `if`, and force it only when it can change the answer. That keeps `false and LOOP` from running `LOOP`.

Recursion uses `Z`, not `Y`. Under call-by-value, `Z g` reduces to a lambda. The recursive copy waits inside `lam v. x x v` until an argument arrives. Ordinary `Y` keeps unfolding before it is ever a value, so a step budget would always run out.

## Fresh names

A binder introduced by the compiler is `k_1`, `k_2`, and so on. The first candidate that is not already a name in the terms being wrapped is used. The reserved set includes binders and occurrences, so a source variable named `k_1` is skipped. Source binders are copied unchanged. The names `s`, `z`, `t`, `f`, and `x` are not reserved for the compiler. They appear as binders inside closed encodings, and a source program may still use them. The dummy value `I` is `lam w. w`, a closed term, so its `w` never meets a source variable.

Target substitution uses the Assignment 5 policy. A binder is renamed only when it would capture a free name of the replacement, and the new name is `stem_1`, `stem_2`, ... chosen against every name in the term and the replacement. `(lam y. x)[x := y]` becomes `(lam y_1. y)`.

## Evaluation

`EvaluateVisitor` is the only evaluator. Target `Var`, `Lam`, and `App` accept the same `visit_var`, `visit_lam`, and `visit_app` calls as source `D0Evar`, `D0Elam`, and `D0Eapp`, so there is one case for each of those forms. `visit_app` evaluates the function, then the argument, then performs a beta-value step. That step substitutes with the target substitution for a target lambda and with the Assignment 5 source substitution for a source lambda or `fix`. Nothing reduces under a lambda, and nothing is eta-reduced. The other visit methods are source-only rules, and a target term never reaches them. A test replaces all ten of them with failing stubs and still runs a compiled `2 + 3`.

Source evaluation also substitutes values: `let` evaluates the initializer, then substitutes it into the body. `fix` applied to `v` substitutes the fix itself for the function name and then `v` for the parameter. When the two names match, only the parameter substitution happens, so the parameter wins. Python arithmetic exists only in the source operator cases.

A lambda finishes in zero steps, even at budget zero. Spending the last allowed step still counts as completion. Needing one more step is exhaustion, which means the budget ended, not that the term diverges. Open terms are rejected before the first step and the free names are reported. Inputs are never mutated. The beta chain is a loop rather than a Python call per step, so a diverging term reports exhaustion instead of overflowing the stack.

Execution and observation have separate budgets and counts. Execution stops when the term becomes a lambda. A numeral built by arithmetic still has work under that lambda, so observation spends its own steps. A pair is observed by evaluating `FST v` and `SND v`, then decoding each component by its kind.

## Why the translation preserves meaning

Application is unchanged: `C[e1 e2] = C[e1] C[e2]`. Target call-by-value evaluates the function, then the argument, then substitutes, which is the source order. A diverging argument still diverges, including under a function that ignores it, in a let initializer, and in either component of a pair.

A conditional is a boolean applied to two thunks, and the chosen thunk is applied to `I`. Both thunks are lambdas, so call-by-value builds them without entering them. Only the application to `I` enters the chosen branch. `and` and `or` use the same shape. The unchosen branch is still compiled, so a negative literal in a dead branch is a compile error, but it is never reduced.

`let x = e1 in e2` is `(lam x. C[e2]) C[e1]`. The initializer is the argument, so it is evaluated before the body, and the binder does not cover it. A name free in `e1` stays free.

`fix f(x). e` is `Z (lam f. lam x. C[e])`. `Z` produces a lambda, and the body sees `f` as the recursive function and `x` as the parameter. When the names match, the inner lambda shadows the outer one, which is the source rule. Encodings are closed, so a source function named `s` or `g`, or a parameter named `v`, is not captured by the binders inside a numeral or `Z`. The tests run each case.

Free variables are preserved because variables and source binders are copied, literals and combinators are closed, and every fresh binder is chosen outside the names of the term it wraps. So `FV(C[e]) = FV(e)`.

Delayed branches matter because the target has no primitive `if`. If both branches were ordinary arguments, call-by-value would evaluate `LOOP` in `if true then 1 else LOOP`. The thunk makes that branch a lambda, which is already a value. Call-by-value recursion matters for the same reason: the recursive copy has to wait until an argument is supplied.

Testing does not prove the claim. The suite checks every constructor and operator, the demonstrations, capture, short-circuiting, and divergence at a budget. It cannot cover every well-typed program, and exhaustion is not a divergence proof. The argument above is why the translation should agree with the source rules. It is not a formal proof.

## Decisions

**Decision 1.** One visitor evaluates both languages, and the compiler cannot call it. The gain is that source and target call-by-value share one application rule, so they cannot drift apart, and a test can show that compiling `LOOP` never enters the evaluator. The cost is that the visitor holds two substitution functions, one per syntax, and the target nodes carry `arg1`/`arg2` aliases so the shared methods read both.

**Decision 2.** Decoding is a second reduction with its own budget, not a reducer that understands numerals. The gain is that the reducer stays a pure beta engine and cannot replace Church arithmetic with Python. The cost is two step counts to explain, because a lambda result can still hide work.

## Limitations

There is no parser, no type checker, and no web page. Negative literals and unknown operators are rejected. Other type errors are not. Only naturals, booleans, and finite pairs are decoded. A very deep term can exceed the Python stack. The diverging demonstrations stop at budget 200, which is not a divergence proof.

## Translation rules

`C[e]` is the translation of `e`. `I` is `lam w. w`. `u` and `v` are fresh `k_i` binders. Every abbreviation is expanded into pure terms in the output.

```text
C[x]                  = x
C[lam x. e]           = lam x. C[e]
C[e1 e2]              = C[e1] C[e2]
C[let x = e1 in e2]   = (lam x. C[e2]) C[e1]
C[if c then t else f] = (C[c] (lam u. C[t]) (lam v. C[f])) I
C[fix f(x). e]        = Z (lam f. lam x. C[e])
C[n]                  = NUM(n)                         n >= 0
C[true]               = TRUE
C[false]              = FALSE
C[not e]              = NOT C[e]
C[e1 and e2]          = (C[e1] (lam u. C[e2]) (lam v. FALSE)) I
C[e1 or e2]           = (C[e1] (lam u. TRUE) (lam v. C[e2])) I
C[e1 + e2]            = ADD C[e1] C[e2]
C[e1 - e2]            = SUB C[e1] C[e2]
C[e1 * e2]            = MUL C[e1] C[e2]
C[e1 < e2]            = LT C[e1] C[e2]
C[e1 <= e2]           = LEQ C[e1] C[e2]
C[e1 > e2]            = GT C[e1] C[e2]
C[e1 >= e2]           = GEQ C[e1] C[e2]
C[e1 == e2]           = EQ C[e1] C[e2]
C[e1 != e2]           = NEQ C[e1] C[e2]
C[pair e1 e2]         = PAIR C[e1] C[e2]
C[fst e]              = FST C[e]
C[snd e]              = SND C[e]
C[n] with n < 0, or an operator not listed  = compile error
```

Library terms, all closed:

```text
TRUE   = lam t. lam f. t
FALSE  = lam t. lam f. f
NUM(n) = lam s. lam z. s (s ... (s z))
PAIR   = lam a. lam b. lam p. p a b
FST    = lam p. p (lam a. lam b. a)
SND    = lam p. p (lam a. lam b. b)
SUCC   = lam n. lam s. lam z. s (n s z)
SHIFT  = lam p. PAIR (SND p) (SUCC (SND p))
PRED   = lam n. FST (n SHIFT (PAIR NUM(0) NUM(0)))
ISZERO = lam n. n (lam x. FALSE) TRUE
ADD    = lam m. lam n. lam s. lam z. m s (n s z)
MUL    = lam m. lam n. lam s. lam z. m (n s) z
SUB    = lam m. lam n. n PRED m
LEQ    = lam m. lam n. ISZERO (SUB m n)
GEQ    = lam m. lam n. LEQ n m
LT     = lam m. lam n. NOT (LEQ n m)
GT     = lam m. lam n. NOT (LEQ m n)
EQ     = lam m. lam n. AND (LEQ m n) (LEQ n m)
NEQ    = lam m. lam n. NOT (EQ m n)
NOT    = lam b. b FALSE TRUE
AND    = lam a. lam b. a b FALSE        values only, used by EQ
OR     = lam a. lam b. a TRUE b         values only
Z      = lam g. (lam x. g (lam v. x x v)) (lam x. g (lam v. x x v))
I      = lam w. w
```

Observation contexts:

```text
STEP       = lam tail. lam c. lam z. c tail
BASE       = lam c. lam z. z
MARK_TRUE  = lam a. lam b. lam c. a
MARK_FALSE = lam a. lam b. lam c. b
```
