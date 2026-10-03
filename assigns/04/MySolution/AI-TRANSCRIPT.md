# AI transcript

AI system: Cursor, in this repository.

## Prompt

Get assignment 4 done.

## What was used

The assistant read `assigns/04/Assign04.md` and the supplied `assigns/04/lambda1.py` (`d0exp_fvset` and `d0exp_evaluate`). It added an MVC workbench under `assigns/04/MySolution/`: `model.py`, `controller.py`, `backend.py`, `app.py`, `static/`, `examples/`, and `tests/`. The page uses the Python standard library and binds to 127.0.0.1. Lint calls `d0exp_fvset`. Interpret calls `d0exp_evaluate`. Type-check and Compile return not-implemented results. Execute stays disabled because no generated artifact exists.

Suggestions I kept: a restricted constructor reader instead of `exec`; a subprocess time limit so a nonterminating program cannot leave the server busy; unapplied editor text checked by the controller before a tool runs; outcomes named `success`, `input_error`, `language_error`, `runtime_error`, `backend_error`, and `not_implemented`.

## Review

I required the tests in `tests/` to pass, including free-variable scope, lint on division by zero without evaluation, factorial and Fibonacci, placeholder outcomes, busy-state failure and retry, and HTTP rejection of empty source and invalid UTF-8. I then ran the page in a browser and checked the load menu, manual editing, all five controls, a runtime error after a successful lint, and literal display of HTML-like text. The steps and observed results are in `TESTING.md`.
