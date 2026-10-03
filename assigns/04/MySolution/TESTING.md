# Testing

Automated tests: `python -m unittest discover -s tests -v` from `assigns/04/MySolution`. 16 tests passed on Python 3.14.0.

| Check | Where | F-IDs |
| --- | --- | --- |
| Free variables for every constructor, duplicates, nested lambdas, fix, and let initializer scope; result is a `frozenset` | `tests/test_language.py` `FreeVariableTests` | F5 |
| Lint success on a closed program; sorted names on an open program; lint does not evaluate division by zero | `LintAndInterpretTests` | F5, F6 |
| Interpret arithmetic (42), factorial (120) and Fibonacci (55), including base cases; malformed input; `D0V000` inside a pair | `LintAndInterpretTests` | F6 |
| Manual apply, replacement, empty and oversized rejection without losing the previous source | `tests/test_state.py` `ModelTests` | F2, F3, F8 |
| Tool call rejected when editor text is unapplied; source kept | `ControllerTests` | F2 |
| Type-check and Compile are `not_implemented`; Execute does not call the backend and stays unavailable | `ControllerTests` and `perform` | F4, F7 |
| Busy state rejects another apply or tool call; backend exception becomes `backend_error`; retry succeeds | `ControllerTests` | F10 |
| Subprocess interpret of arithmetic; a sleeping child is killed and reported as a backend error | `test_worker_and_timeout` | F10 |
| HTTP manual apply, empty rejection, invalid UTF-8 upload, lint outcome, Execute rejected | `tests/test_http.py` | F1, F3, F4, F5 |

## Browser smoke test

Page: http://127.0.0.1:8765. Observed on 3 October 2026.

| Step | Expected | Observed |
| --- | --- | --- |
| Open the page | Load menu has Choose File, Manual input, Factorial (canned), and Fibonacci (canned). Tool buttons disabled. Execute disabled. Status is text. | Menu options matched. Status: “Idle. Apply source before running tools.” Execute disabled, with the generated-code explanation on the page. |
| Factorial, then Interpret | Revision advances, result `D0Vint(arg1=120)`, busy text while it runs | Status “Working: interpret.” Then “Action: interpret. Revision: 1. Outcome: success.” and `D0Vint(arg1=120)`. |
| Fibonacci, then Interpret | New revision, previous result cleared, value 55 | Revision 2, “No result.” until Interpret finished, then `D0Vint(arg1=55)`. |
| Manual input | Editor clears. Tools and the load menu disable until Apply or Discard. | Status: “Unapplied edits…” Lint through Compile disabled. Source name shown as Manual input. |
| Enter `D0Evar("x")`, Apply, Lint | Language error naming `x`. New revision. | Revision 3. “Undeclared variables: x”. Outcome `language_error`. |
| Change to `D0Elam("x", D0Evar("x"))`, Apply, Lint | Success. Tools disabled until Apply. | Revision 4. “No free variables were found.” Outcome `success`. |
| Apply `D0Eop2("/", D0Eint(1), D0Eint(0))`, Lint, then Interpret | Lint succeeds. Interpret is a runtime error. Source remains. | Revision 5. Lint success, then “ZeroDivisionError: division by zero”, outcome `runtime_error`. Editor text unchanged. |
| Type-check, Compile, Execute | Placeholder text. Execute stays disabled. | Type-check: “Type checking is not yet implemented.” Compile: “Compilation is not yet implemented.” Both outcomes `not_implemented`. Execute remained disabled. |
| Apply `D0Evar("<b>literal</b>")` and Lint | The tag is visible as text, not markup. | Result text: `Undeclared variables: <b>literal</b>`. The result node is a text node. No `b` element was created. |
| After the runtime error, run Type-check | Controls work again. | Type-check ran on the same revision. |

Choose File is in the load menu. The browser session did not open the system file dialog. Invalid UTF-8 and empty-source rejection were checked by `tests/test_http.py` and `ModelTests`.
