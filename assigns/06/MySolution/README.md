# Midterm 1: compiling extended LAMBDA into pure lambda calculus

Python 3.12 or later is required. Developed and tested with Python 3.14.0 on Windows.

## Dependencies and setup

The compiler, encodings, evaluator, decoders, demo, and tests use only the Python standard library, so there is nothing to install. They import two files from Assignment 5 and change neither:

- `assigns/05/lambda1_vp.py`, the supplied source AST and `D0ExpVisitor`.
- `assigns/05/MySolution/visitors.py`, my Assignment 5 pretty printer and capture-avoiding source substitution.

`boot.py` adds those folders to `sys.path`, so the commands below work from a clean checkout.

## Commands

From `assigns/06`:

```text
python -m unittest discover -s MySolution/tests -v
python MySolution/demo.py
```

The first command runs the unittest suite: 40 tests, all passing. The second compiles the fourteen required programs, runs each pure term, decodes the result, and prints the source, the target term (inline when it is short), the saved-file path, execution status and beta-value steps, observation status and steps, the decoded answer, the source-side answer, and the expected answer. It ends with `14 of 14 programs match the expected column.` The pure terms are saved in `MySolution/demo-out/01.lam` through `14.lam`. The demo regenerates them identically on every run.

## Modules

| Module | Role |
| --- | --- |
| `target.py` | Target AST `Var`, `Lam`, `App`; printer; free names; capture-avoiding substitution |
| `church.py` | Closed Church encodings, including predecessor and `Z` |
| `compile.py` | `compile_expr`, a `D0ExpVisitor`. It does not import or call the evaluator |
| `evaluate.py` | The one evaluator, `EvaluateVisitor`, for source ASTs and target terms. It does not import the compiler |
| `observe.py` | Natural, boolean, and pair observers, with their own step budget |
| `examples.py` | The required source programs, built as ASTs |
| `demo.py` | The command-line demonstration |
| `boot.py` | Import paths for Assignment 5 |
| `tests/test_midterm.py` | The unittest suite |

`church.py` has that name because Python already uses the module name `encodings`.

## Budgets

| Run | Budget | Largest count used |
| --- | --- | --- |
| Execution, terminating programs | 20,000 beta-value steps | 3,080 (Fibonacci of 5) |
| Observation | 5,000 beta-value steps | 333 (factorial of 4) |
| Execution, `LOOP` and `(lam x. 0) LOOP` | 200 beta-value steps | exhausted at 200 |

Factorial of 4 uses 471 execution steps and 333 observation steps. Exhaustion means the budget ran out. It is not a proof that the program diverges. Source-side evaluation is not budgeted.

## Documents

- `DESIGN.md`: interfaces, representations, predecessor, fresh names, evaluation, correctness argument, decisions, and translation rules.
- `TESTING.md`: each test mapped to the seven testing items in `Assign06.md` and to the ACC checks in `REQUIREMENTS.md`.
- `AI-TRANSCRIPT.md`: how AI was used and how the results were checked.

## Slides and recording

- Slides: `MySolution/midterm-slides.pdf`. The editable deck is `MySolution/midterm-slides.pptx`, and its speaker notes are the talk outline.
- Recording: [CS413 Midterm (Google Drive)](https://drive.google.com/file/d/1MLx_cJhKMqBhv3op_ZoI98yfSLhvUYJz/view?usp=sharing). 16 minutes 54 seconds, presenter's webcam in the lower-right corner, including the live factorial run from `demo.py`. Anyone with the link can view it without requesting access.

## Limitations

- No parser, no type checker, and no web page.
- Negative literals and unsupported operators are compile errors everywhere, including dead code. Other ill-typed programs are outside the checked language.
- Decoders cover naturals, booleans, and finite pairs.
- Target execution rejects open terms. Compilation and substitution still accept them.
- Substitution-based reduction is slow on large numerals, and a very deep term can exceed the Python stack.

## Attribution

The boolean, numeral, pair, and `Z` shapes are the ones given in `Assign06.md`. The pair-shift predecessor is the standard construction in Church-encoding references, for example Pierce, *Types and Programming Languages*, chapter 5. Capture-avoiding substitution follows my Assignment 5 policy. The source side calls that Assignment 5 code directly, and `target.py` reimplements it for target terms.
