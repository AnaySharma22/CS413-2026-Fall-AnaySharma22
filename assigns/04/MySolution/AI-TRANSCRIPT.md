# AI transcript

AI system: Cursor, in this repository.

I worked through Assignment 4 one piece at a time: the MVC split, the language adapter, the page, then the tests. Unrelated earlier assignments are left out.

## 1. MVC boundaries

**Me:** The assignment wants a web front-end, but the grade is the architecture, not a fancy page. If Lint and Interpret live in the button handlers, that fails the MVC objective even if the page looks right.

**Assistant:** Put applied source, revision, the latest result, the artifact, and the busy flag in a model that does not import HTTP or HTML. The page only renders and posts events. A controller is the only module that calls the language adapter.

**Me:** I do not want a framework just so I can name three folders. The standard library is enough, and the boundaries should be obvious in the files: `model.py`, `controller.py`, `backend.py`, `app.py`, and `static/`.

**Assistant:** `app.py` can be a loopback HTTP server that decodes requests and serves the page. It should not call `d0exp_evaluate`.

**Me:** The view must not know how the interpreter is started. Tests of the model should run with no browser. A controller test should be able to pass a fake backend without editing the HTML.

**What I kept:** that file split, a model with no web imports, and `Controller` taking an optional backend.

## 2. Reading source and Lint

**Me:** Input is one constructor expression, like `D0Eop2("+", D0Eint(20), D0Eint(22))`. I am not writing a LAMBDA parser. I also refuse to `exec` an upload. Someone will paste `import os`.

**Assistant:** Parse with `ast` in eval mode. Allow only the `D0E` constructors, positional arguments, and int, bool, and string literals, including a leading minus. Reject keywords, operators, lists, and `D0E000`.

**Me:** Lint has to use `d0exp_fvset` from the supplied `assigns/04/lambda1.py` and return a `frozenset`. A nonempty set is an error, names in sorted order. An empty set passes. Do not evaluate during lint. A closed `1/0` must still pass Lint.

**Me:** Scope has to match the assignment, not “every name that appears.” A lambda binds its parameter. `fix` binds its own name and its parameter in the body. `let` binds the name only in the body, not in the initializer. An unused binding is not an error. Both branches of `if` count.

**What I kept:** `read_source`, Lint outcomes `success` and `language_error`, and the scope rules already implemented in `d0exp_fvset`.

## 3. Interpret, placeholders, and Execute

**Me:** Interpret should call `d0exp_evaluate` with the empty environment and show the value as text, such as `D0Vint(arg1=120)`. Lint passing does not mean evaluation will succeed. I want a bad constructor reported as an input error, and division by zero or a type error reported as a runtime error. Those are different outcomes.

**Assistant:** Also treat `D0V000()` as a runtime error when it is the whole result or nested inside a pair. Do not print that sentinel as a successful value.

**Me:** Type-check and Compile get buttons and backend entry points, but they must say they are not implemented. Do not fake a successful analysis or invent an artifact. Execute is only for generated code. While Compile is a placeholder, disable Execute and say why on the page. Do not run the interpreter when someone hits Execute.

**What I kept:** outcomes `input_error`, `runtime_error`, and `not_implemented`. Execute is rejected in the model before the backend runs, and the button stays disabled.

## 4. The page

**Me:** The load menu is Choose File, Manual input, Factorial (canned), and Fibonacci (canned), in an editor the user can change. Show the source name and revision. Apply changes updates the app’s copy, not the file on disk. Discard puts the editor back. While there are unapplied edits, block the tools and block loading a different source.

**Assistant:** Keep the draft in the browser. Send the editor text with each tool request. If it does not match the applied source, the controller rejects the call, so the rule is not only a disabled button.

**Me:** Reject empty or whitespace-only source, invalid UTF-8, and anything over 65,536 bytes. A rejection must leave the previous applied source alone and leave the bad text in the editor so I can fix it. Every accepted load or apply gets a new revision and clears the old result.

**Me:** Button order is Lint, Interpret, Type-check, Compile, Execute. Results need the action, the revision, and the outcome, with line breaks preserved. If the source contains something that looks like HTML, show it as text. Status has to be words, not color alone, and the controls have to be keyboard buttons. Show a busy status and refuse a second action until the first one finishes. After a backend failure, keep the source and allow retry.

**What I kept:** that menu and button order, Apply/Discard, literal `<pre>` output, and the busy flag on the model.

## 5. Bounds and tests

**Me:** A nonterminating program cannot leave the server busy forever. I want a real time limit, not a comment. This machine is Windows, so do not depend on Unix `resource` limits. Kill the worker when the time is up. Bind only to 127.0.0.1.

**Assistant:** Run Lint and Interpret in a subprocess with a 3-second wall-clock timeout, and kill the child if it expires. Document that there is no separate memory cap.

**Me:** Tests I want, and they have to hit the real Lint and Interpret, not only mocks: every constructor’s free variables, duplicate names, nested bindings, `fix`, and `let` initializer scope; Lint on a closed program and on an open one; Lint must not evaluate `1/0`; Interpret of arithmetic, factorial, and Fibonacci including base cases; malformed input and runtime failure; manual apply, replacement, and rejection without losing the previous source; placeholders must not look like success and Execute must stay unavailable; busy state, a backend failure, and a retry.

**What I kept:** `tests/test_language.py`, `tests/test_state.py`, and `tests/test_http.py`. Mocks are only for dispatch and injected failures.

## 6. What I checked

**Me:** I ran `python -m unittest discover -s tests -v`. All 16 tests passed. Then I opened the page and walked the demo myself: Factorial interprets to `D0Vint(arg1=120)`, Fibonacci to `D0Vint(arg1=55)`, `D0Evar("x")` fails Lint, editing it into a lambda passes Lint, `1/0` passes Lint and then fails Interpret, Type-check and Compile say they are not implemented, and Execute stays disabled. HTML-like text stayed text. Those steps are in `TESTING.md`.

**Assistant:** The architecture write-up should match those files: diagram, responsibility table, Load → Lint → Interpret trace, the draft-versus-applied decision, the subprocess timeout, and how a later compiler would return an artifact for Execute without the page calling the interpreter instead.

**What I kept:** `ARCHITECTURE.md`, `README.md`, and `TESTING.md` aligned with the code that the tests and the browser pass actually exercised.
