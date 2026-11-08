# AI transcript

AI system: Cursor, in this repository.

I worked through Assignment 7 in pieces: the contract, the split between envelope and service, the deadline, the Windows limits, the tests, and the documents. Each section is the part of the discussion that changed the code, followed by what I kept. `assigns/07/LAMBDA3/` and `assigns/07/TEST/` stay untouched throughout.

## 1. The contract before the dispatcher

**Me:** The brief says `RPC.md` comes before the dispatcher. I want the method table, the envelope rules, the error codes, the limits, and full HTTP examples written down first, plus a JSON Schema. The professor's `TEST/test_rpc_api.py` is the floor: health, `1 + 2`, `20 + 22`, a tuple, a list, `<lam>`, both compile targets, `-32010` for `if then`, `-32011` for `1 + true`, `-32602` for blank, a number, a missing source, and `ruby`, `-32601`, `-32700` for a truncated body, batches that drop notifications, 204 for a notification, and `-32600` with `id: null` for `jsonrpc: "1.0"` and for `[]`.

**Assistant:** One endpoint, `POST /rpc`. HTTP status describes the transport. A JSON-RPC error, including a parse error, is still HTTP 200. The schema can describe shapes. Rules that depend on context, such as "an invalid request answers with `id: null`", belong in `RPC.md` and in tests.

**Me:** `libraries` is the only addition. `mylib/` is part of the provided system, and the brief says it should be available. Absent or empty means `d0exp_parse_and_typecheck`, exactly as specified. Do not invent a second way to pass source. Also, the examples in section 7 have to be replayed by a test, so they are checked output and not illustrations.

**What I kept:** `RPC.md` and `schema/jsonrpc.schema.json`, including the optional `libraries` parameter.

## 2. Envelope separate from LAMBDA3

**Me:** Four layers, and each one does one job. Flask accepts the HTTP request. A dispatcher owns JSON-RPC and does not import LAMBDA3. A service owns the four methods and the parameter rules. A worker owns the process. The handler must not grow its own parser.

**Assistant:** `Dispatcher.handle_body` takes bytes and returns a response object, a list, or `None` when nothing should be sent. The service methods take a params object and return a result or raise `RpcError`.

**Me:** An invalid request always answers with `id: null`, even when the body had an id. The professor's suite sends `jsonrpc: "1.0"` with `id: 1` and expects null. Unknown top-level members are invalid requests, not ignored. `params` as an array is legal JSON-RPC but not legal for these methods, so that is `-32602`, not `-32600`. Health rejects every member. A notification is a missing `id`, not `"id": null`.

**What I kept:** `lambda_rpc/jsonrpc.py`, `lambda_rpc/service.py`, and `lambda_rpc/app.py`.

## 3. A deadline that can stop the interpreter

**Me:** LAMBDA3 recurses and has no step budget. A timeout has to kill the computation, and it does not prove the program diverges. Say that in the contract. The clock should start after LAMBDA3 has been imported, or a cold import eats the budget.

**Assistant:** Each source call can run in a spawned process. The child sends `ready` after the import. The parent waits the time limit, then terminates and kills the process. Parsing and type-checking run in that process too, so a pathological source cannot stall the server either.

**Me:** Good. Map `LambdaSyntaxError` to `-32010` with line, column, and the source line, and `TypeCheckError` to `-32011`. An unbound variable is a type error. Add `-32013` for a runtime failure such as `list_head` of an empty list, and `-32014` when the formatted value or the generated code is too big. Both are in the server-error range the brief allows. An unexpected failure is `-32603` with a reference, and the traceback stays in the server log. No paths in the response. `print` is captured into `output` and must not reach the server console.

**What I kept:** `lambda_rpc/worker.py` and the error table in `RPC.md`.

## 4. What Windows actually accepted

**Me:** The first run failed every source call. Do not paper over it. Find the real limit and write that into the contract.

**Assistant:** `threading.stack_size` rejected 512 MiB and then exactly 256 MiB. 255 MiB is accepted. With that stack, a recursion limit of 50,000 died inside LAMBDA3 after a few thousand source calls, because one LAMBDA call uses several Python frames. `sum(20000)` finishes at a limit of 1,000,000 and takes about two seconds. A deeper call runs into the five-second deadline and comes back as `-32012`, which is the right outcome. `fib(27)` at a one-second limit comes back as `-32012` in about a second and a half, and the next call still works.

**Me:** Put the measured numbers in `RPC.md`. Python recursion limit 1,000,000, thread stack 255 MiB, and say plainly that this is about 50,000 nested LAMBDA calls inside the time limit. A `RecursionError` is still `-32013` with `kind: "recursion_depth"`, for the case where the limit is hit before the clock.

**What I kept:** those two limits in `lambda_rpc/config.py`, and the corrected row in `RPC.md`.

## 5. Tests against the contract, then the professor's suite

**Me:** HTTP tests through Flask's test client, not by calling the service methods directly. Cover the ten items in the brief. Doubles only for failures LAMBDA3 will not produce on demand. A real slow program has to be in the suite as well, or the deadline is untested. Replay section 7 of `RPC.md`. Then start `serve.py` and run `TEST/`.

**Assistant:** The compile test can call `d0exp_compile` and `d0exp_compile_js` itself and require the response to be identical. A scan of the service source can reject `exec`, `eval`, and Node.

**Me:** The first full run was 67 tests with three failures. Two were my leak check matching a colon inside a comment of the generated Python. Check the decoded string, and ignore that false positive. The third called `optn_none`, which does not exist. The library's empty option is `optn_nil()`. Fix the test, not the library.

**Me:** Also check the 413 body. The contract said "Content Too Large". Werkzeug 3.1.9 sends `Request Entity Too Large`. Change the contract to the status code and the text this stack sends.

**What I kept:** `tests/`, the replay test, and the corrected 413 row. After that, 67 tests passed, and the professor's 15 tests passed against the live server on port 8000.

## 6. Documents

**Me:** `README.md` needs the versions I actually ran, the venv command, both test commands, the URL, and a curl for every method. Show factorial, the unbound `y + 1`, and a JavaScript compile. Say in the README, not only in a comment, that the generated code is returned and not run. `TESTING.md` maps the ten items to test names and has the layer diagram.

**What I kept:** `README.md`, `TESTING.md`, and this file.
