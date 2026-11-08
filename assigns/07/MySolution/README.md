# Assignment 7: a JSON-RPC service for LAMBDA3

One endpoint, `POST /rpc`, speaks JSON-RPC 2.0. A client names a method and passes LAMBDA3 source as text. The service parses and type-checks that source with the provided LAMBDA3 implementation, then returns the type, the interpreted value, or generated code. It does not run generated code.

Developed and tested with Python 3.14.0, Flask 3.1.3, Werkzeug 3.1.9, and jsonschema 4.26.0 on Windows. Python 3.12 or later is required. `requirements.txt` asks for Flask 3 and jsonschema 4.

## Setup

From `assigns/07/MySolution`:

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

On a POSIX shell the interpreter is `.venv/bin/python`. The virtual environment stays local. Do not commit it.

## Commands

Own tests, from `assigns/07`. 67 tests, all passing:

```text
MySolution\.venv\Scripts\python -m unittest discover -s MySolution/tests -v
```

Start the service, from `assigns/07`:

```text
MySolution\.venv\Scripts\python MySolution\serve.py
```

It prints `LAMBDA3 JSON-RPC service on http://127.0.0.1:8000/rpc` and listens until stopped. `--port` changes the port and `--time-limit` changes the seconds allowed for each source call (default 5).

The professor's black-box suite does not use Flask. With the service already running, from `assigns/07`:

```text
python -m unittest discover -s TEST -v
```

That run was 15 tests, all passing, against `http://127.0.0.1:8000/rpc`. `LAMBDA_RPC_URL` selects another endpoint.

## Modules

| Module | Role |
| --- | --- |
| `lambda_rpc/app.py` | Flask transport. `POST /rpc` only |
| `lambda_rpc/jsonrpc.py` | JSON-RPC envelope, batches, notifications, error objects |
| `lambda_rpc/service.py` | Parameter checks and the four methods. No HTTP |
| `lambda_rpc/worker.py` | One spawned process per source call, killed at the deadline |
| `lambda_rpc/lambda3_bridge.py` | Imports the provided `assigns/07/LAMBDA3/lambda3.py` |
| `lambda_rpc/errors.py` | Error codes and messages |
| `lambda_rpc/config.py` | Limits |
| `serve.py` | Process entry point |
| `tests/` | HTTP tests through Flask's test client |

The handler validates the envelope, dispatches to the service, and serializes the answer. It does not reimplement the parser, type-checker, interpreter, or compilers. The contract, including every limit, is `RPC.md`. Shapes are in `schema/jsonrpc.schema.json`.

## Calling the service

The endpoint is `http://127.0.0.1:8000/rpc`. These examples use `curl.exe` so PowerShell does not substitute `Invoke-WebRequest`. The same text works as `curl` in a POSIX shell. Single quotes keep the JSON intact in both.

Health:

```text
curl.exe -s -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"service.health","params":{},"id":"h1"}' http://127.0.0.1:8000/rpc
```

```json
{"jsonrpc": "2.0", "id": "h1", "result": {"status": "ok", "version": "1.0"}}
```

Type-check:

```text
curl.exe -s -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"lambda.typecheck","params":{"source":"lam (x: sint) => (x, x <= 1)"},"id":1}' http://127.0.0.1:8000/rpc
```

```json
{"jsonrpc": "2.0", "id": 1, "result": {"type": "sint -> (sint, bool)"}}
```

Factorial. The source is the program from the assignment, on one line:

```text
curl.exe -s -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"lambda.interpret","params":{"source":"let fact : sint -> sint = fix fact(n: sint): sint => if n <= 1 then 1 else n * fact(n - 1) in fact(6) end"},"id":2}' http://127.0.0.1:8000/rpc
```

```json
{"jsonrpc": "2.0", "id": 2, "result": {"type": "sint", "value": "720"}}
```

An unbound variable is a type error, not a crash. The HTTP status is still 200:

```text
curl.exe -s -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"lambda.interpret","params":{"source":"y + 1"},"id":6}' http://127.0.0.1:8000/rpc
```

```json
{"jsonrpc": "2.0", "id": 6, "error": {"code": -32011, "message": "LAMBDA type error", "data": {"message": "unbound variable 'y'"}}}
```

Compile to JavaScript. The response is one JSON object. `code` is the full program from `d0exp_compile_js`, several kilobytes, beginning `const _lambda_some_tag = Symbol("some");`. Use `"target": "python"` for `d0exp_compile` instead.

```text
curl.exe -s -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"lambda.compile","params":{"source":"1 + 2","target":"javascript"},"id":4}' http://127.0.0.1:8000/rpc
```

Generated code is returned and not run. `lambda.compile` never calls `exec`, never starts Node, and never imports the string it returns. The service has no method that executes a submitted Python or JavaScript program. `CompileTests.test_service_never_executes_generated_code` reads the service source and rejects those calls.

`libraries` is optional and is the only parameter beyond the assignment table. `"libraries": ["list"]` puts `LAMBDA3/mylib/list.lam` in scope, so `list_reverse(list_range(1, 5))` evaluates to `[4, 3, 2, 1]`. The names are `list`, `optn`, `a1sz`, and `strm`.

More request and response pairs, including batches, notifications, and the error table, are in `RPC.md`. `tests/test_contract_examples.py` replays every example in section 7.

## Documents

- `RPC.md`: the contract. Written before the dispatcher.
- `schema/jsonrpc.schema.json`: JSON Schema (draft 2020-12) for request and response bodies.
- `TESTING.md`: which test covers which required behavior, and the architecture.
- `AI-TRANSCRIPT.md`: how AI was used and how the result was checked.
