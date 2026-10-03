# LAMBDA workbench

A one-user MVC page for the supplied LAMBDA interpreter in `assigns/04/lambda1.py`. Tested with Python 3.14.0 on Windows. The same code requires Python 3.12 or later. There are no third-party packages.

```text
cd assigns/04/MySolution
python -m unittest discover -s tests -v
python app.py
```

`python app.py --port 8765` chooses another port. The default is 8000. Open http://127.0.0.1:8000. Stop the server with Ctrl+C. The process binds to 127.0.0.1 only. State is in memory, shared by tabs, and discarded on restart. Uploaded files are not modified.

`requirements.txt` records that nothing needs to be installed.

## Demonstration

1. Load source, choose Factorial (canned), then Interpret. The result is `D0Vint(arg1=120)`, action `interpret`, outcome `success`, revision of that load.
2. Load Fibonacci (canned) and Interpret. The result is `D0Vint(arg1=55)`.
3. Choose Manual input. The editor becomes blank and the tool buttons disable. Enter `D0Evar("x")`, Apply changes, and Lint. The outcome is `language_error` and the text lists `x`. Replace the editor with `D0Elam("x", D0Evar("x"))`, Apply changes, and Lint again. The outcome is `success`: no free variables were found.
4. Apply `D0Eop2("/", D0Eint(1), D0Eint(0))`. Lint succeeds because the expression is closed. Interpret then reports `ZeroDivisionError`. Lint does not mean evaluation will succeed.
5. Type-check reports “Type checking is not yet implemented.” Compile reports “Compilation is not yet implemented.” Neither outcome is success, and no artifact is stored. Execute stays disabled. The page states that Execute is for generated code and is unavailable until compilation produces an artifact.

Editing the textarea enables Apply changes and Discard changes. Until one of those is used, the load menu and the tool buttons stay disabled. A rejected apply leaves the previous revision in place and leaves the rejected text in the editor. Each accepted load or apply shows a new revision and clears the previous result.

## Input, bounds, and limitations

Source is one Python constructor expression of type `d0exp`: positional arguments, string, integer, and Boolean literals, a leading minus on an integer, nested constructors, comments, and more than one line. It is not a script. Imports, operators, calls other than the `D0E` constructors, keyword arguments, and `D0E000` are rejected. Sample files are in `examples/`: Factorial, Fibonacci, Arithmetic (`D0Eop2("+", D0Eint(20), D0Eint(22))`), Undeclared, Runtime-error, and Markup.

Source may be at most 65,536 UTF-8 bytes. Each Lint, Interpret, Type-check, or Compile call runs in a subprocess that is killed after 3 seconds. Python may raise `RecursionError` before that limit. There is no separate memory cap. Type checking, compilation, generated-code execution, accounts, saved test collections, and persistence across restarts are not implemented. Use one tab; a second tab shares the same applied source.

## Reflection

MVC kept the applied program separate from the text sitting in the textarea. That split is what makes Apply and Discard meaningful: the model can reject an empty edit without forgetting the previous revision, and a test can check that rule without opening a browser. The controller is also the only place that turns a crashed or timed-out worker back into an idle model, so the view never has to guess whether a button is safe to press.

The hard boundary was the draft. Sending every keystroke to the server would make the model the editor, and it would also make “unapplied edits” a second copy of the same string. Leaving the draft in the page avoids that, but then the server cannot see the draft unless the action request includes it. Tool calls therefore send the editor text and fail when it does not match. Source replacement is still refused in the page by disabling the menu. A refresh throws the draft away. That is acceptable for one local user and a poor fit for several tabs.

The other split that earned its keep is the constructor reader. Lint and Interpret both use it, and Lint stops after `d0exp_fvset`, so a closed division by zero is not executed during checking. The reader never calls `exec` on the upload. A later compiler can replace the Compile branch, return an artifact tied to the revision, and leave Execute to consume that artifact. The model already drops the artifact when source changes or compilation starts, so that hook does not require a new page.
