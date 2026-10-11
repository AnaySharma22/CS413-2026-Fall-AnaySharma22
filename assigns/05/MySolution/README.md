# Assignment 5: pretty printing and capture-avoiding substitution

Python 3.12 or later is required. This solution was developed and tested with Python 3.14.0. The visitors import the supplied `assigns/05/lambda1_vp.py` and do not modify it. Java and JavaScript copies in this assignment are references only.

## Setup

From `assigns/05`:

```text
python -m pip install -r MySolution/requirements.txt
python -m unittest discover -s MySolution/tests -v
python -m pytest MySolution/tests/test_pytest.py -q
```

The first command installs pytest. The second command runs the standard-library `unittest` suite (`MySolution/tests/test_unittest.py`). The third command runs the pytest functions in `MySolution/tests/test_pytest.py`. Those functions are not `unittest.TestCase` classes, so discovering the tests directory with pytest is not a substitute for the third command. Shared inputs live in `MySolution/tests/samples.py`.

On this machine both commands were run from `assigns/05`: 6 unittest tests passed, and 7 pytest tests passed.

## Examples

```text
d0exp_pretty(D0Eapp(D0Elam("x", D0Eop2("+", D0Evar("x"), D0Eint(1))), D0Eint(4)))
  -> ((lam x. (x + 1)) 4)

d0exp_pretty(D0Eop2("/", D0Eint(1), D0Eint(0)))
  -> (1 / 0)
```

Printing does not evaluate, so the division is only text. Booleans print as `true` and `false`. Integers use Python `str`, including negatives and values larger than 64 bits.

Substitution `e[x := r]` is `d0exp_substitute(e, x, r)`. With the fresh-name policy below:

| Expression | Substitution | Result |
| --- | --- | --- |
| `(x + z)` | `x := 3` | `(3 + z)` |
| `(lam x. (x + y))` | `x := 3` | `(lam x. (x + y))` |
| `(lam y. (x + y))` | `x := y` | `(lam y_1. (y + y_1))` |
| `(let x = x in (x + y))` | `x := 3` | `(let x = 3 in (x + y))` |
| `(let y = x in (x + y))` | `x := y` | `(let y_1 = y in (y + y_1))` |
| `(fix f(n). (x + (f n)))` | `x := f` | `(fix f_1(n). (f + (f_1 n)))` |
| `x` | `x := (x + 1)` | `(x + 1)` |

The last result is the replacement object itself. The inserted `(x + 1)` is not walked again, so the `x` inside it stays.

## Fresh-name policy

A binder is renamed only when the substitution target is free in that binder's scope and the binder's name is free in the replacement. The fresh name is `{stem}_{k}` for `k = 1, 2, ...`, using the first candidate that is not reserved. The reserved set for one call is every name that occurs or is bound in the original expression, every name that occurs or is bound in the replacement, the substitution target, and every name allocated earlier in that call. `NameCollector` gathers occurrences and binders. Free-variable names alone are not enough: an unused binder, or a name that is bound rather than free, must still block a fresh choice.

When a `fix` function name and parameter are the same string, and that name is free in the replacement, both binders are renamed to the same fresh name. That keeps the parameter shadowing the function name. When the two binders differ, the function name is renamed first and the parameter second, so a replacement that mentions both receives two different fresh names (`f_1` and `n_1` in the usual case).

## Limitations

There is no parser and no web page. Variable names are not validated. There is no separate alpha-equivalence checker; the tests expect the exact strings produced by this policy. The operation does not simplify or evaluate. It does not copy the replacement: the matching variable node is replaced by the caller's replacement object, and unchanged subtrees are returned as the same objects. A later mutation of an inserted or reused node would be visible to the caller. Fresh-name search is unbounded in theory if every `{stem}_{k}` is already reserved; course-sized terms do not hit that.

## Design

Pretty printing and substitution are two operations on one fixed set of expression classes. `D0ExpVisitor` is generic in its result, so each operation is its own class and the nodes stay unchanged. `PrettyPrintVisitor` produces strings. Each method sends its children through `accept` and places the text in the required parentheses and spaces. Integers use Python `str`, so negatives and large integers have no suffix. Booleans print as `true` and `false`. The visitor never calls the evaluator, so `(1 / 0)` is a string.

`SubstitutionVisitor` produces expressions. Its context is the variable being replaced, the replacement, and one `FreshNames` generator shared by every rename in that call. The target and the replacement stay fixed as the walk descends. What changes is whether the target is still free. A lambda, a `fix`, or a `let` decides that from its own binders before entering a region. Forms that bind nothing rebuild a node only when a child object changes. Otherwise they return the original node, so an untouched subtree keeps its identity and neither input is rewritten in place.

A variable occurrence is the only place the replacement is inserted, and it is inserted as that same object. The walk stops there, so a replacement that still contains the target is not substituted again. Renaming is another substitution, not a scan of printed text. At a lambda, the parameter is in scope only in the body. If the parameter is the target, or the target is not free in the body, the lambda is returned unchanged. If the parameter is free in the replacement, the body is first substituted with that parameter mapped to a fresh variable. Only occurrences free under that binder change. An inner binder of the same name stops the rename, so a nested shadow stays nested and fresh names are chosen outside-in. The original substitution then runs on the renamed body.

`let` always substitutes the initializer, even when the let name equals the target, because that name is not in scope there. Renaming the let name changes the body only. `fix` binds both the function name and the parameter in the body. When those strings differ, each is renamed only if it is free in the replacement, function name first and parameter second. When they are the same string, the parameter shadows the function name, as in the supplied evaluator, and a conflicting replacement renames both binders to one fresh name.

Adding an operation means writing another visitor. Pretty printing and substitution did not require an edit to `lambda1_vp.py`, because every expression already implements `accept`. Adding a constructor goes the other way: the visitor interface grows a method, and every existing visitor, including free-variable collection and evaluation, must handle the new node. Each operation therefore mentions every constructor, which the tests cover, and a new analysis sits beside the interpreter instead of being threaded through it.
