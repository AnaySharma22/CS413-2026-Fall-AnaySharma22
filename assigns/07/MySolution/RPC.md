# LAMBDA3 JSON-RPC contract

This document is the contract for the service. It was written before the
dispatcher, and `tests/test_contract_examples.py` replays every example in
section 7 against the running application, so the examples are checked
output, not illustrations.

## 1. Overview

The service makes four operations available over JSON-RPC 2.0:

| Method | Params | Result | What it does |
| --- | --- | --- | --- |
| `service.health` | `{}` | `{"status": "ok", "version": "1.0"}` | Reports that the service is up and which API version it speaks. Does not touch LAMBDA3. |
| `lambda.typecheck` | `{"source": string, "libraries"?: [name]}` | `{"type": string}` | Parses and type-checks the source with LAMBDA3. Returns the type formatted by `format_type`. |
| `lambda.interpret` | `{"source": string, "libraries"?: [name]}` | `{"type": string, "value": string}` and, only if the program printed, `"output": string` | Parses and type-checks, then evaluates with `d0exp_evaluate` under a hard time limit. The value is formatted by `d0val_format`, so a function is `<lam>` or `<fix>`. |
| `lambda.compile` | `{"source": string, "target": "python" \| "javascript", "libraries"?: [name]}` | `{"target": string, "code": string}` | Parses and type-checks, then returns `d0exp_compile` or `d0exp_compile_js` output unchanged. **The service never runs the generated code.** |

Method names are case-sensitive. Names starting with `rpc.` are reserved by
JSON-RPC and are reported as unknown methods.

Every source method parses and type-checks before it interprets or compiles.
A program that fails either step is never evaluated or compiled.

### The optional `libraries` parameter

`LAMBDA3/mylib/` contains four declaration libraries: `list`, `optn`, `a1sz`,
and `strm`. A source method may name any of them, for example
`"libraries": ["list"]`. Their declarations are parsed with `d0cls_parse` and
placed in scope around the source expression, which is then type-checked as
one program. Line and column numbers in a syntax error always refer to the
client's own source. When `libraries` is absent or empty, the source is
handled by `d0exp_parse_and_typecheck` exactly as the assignment specifies.
This parameter is the only addition to the required contract.

## 2. Transport

There is one endpoint: `POST /rpc`. Operations are not separate URLs.

| Situation | HTTP status | Body |
| --- | --- | --- |
| Any JSON-RPC response object or batch array, **including** parse errors, invalid requests, unknown methods, and LAMBDA errors | `200 OK` | JSON-RPC response, `Content-Type: application/json` |
| A single notification, or a batch that contains only notifications | `204 No Content` | empty |
| `Content-Type` is not `application/json` (a `charset=utf-8` parameter is allowed) | `415 Unsupported Media Type` | short plain-text message |
| Request body larger than 1 MiB | `413` | short plain-text message (`Request Entity Too Large` on this Flask and Werkzeug version) |
| Any method other than `POST` on `/rpc` | `405 Method Not Allowed` | short plain-text message |
| Any other path | `404 Not Found` | short plain-text message |

**HTTP status describes the transport. The RPC outcome is inside the body.**
If the server received a well-formed HTTP request with a JSON body and
produced a JSON-RPC answer, the HTTP exchange succeeded and the status is 200,
even when the answer is an error such as `-32700` or `-32011`. A client reads
`result` or `error` to learn what happened to the call. The 4xx statuses are
used only when the HTTP request itself cannot be accepted, before any
JSON-RPC processing; their bodies are not JSON-RPC objects.

## 3. Envelope

### Request object

| Member | Rule |
| --- | --- |
| `jsonrpc` | Required. Exactly the string `"2.0"`. |
| `method` | Required. A string. |
| `params` | Optional. If present it must be an object or an array (JSON-RPC structured value). These methods need an object; an array is answered with `-32602`. If absent, it is treated as `{}`. |
| `id` | Optional. A string, a number, or `null`. Booleans, objects, and arrays are not valid IDs. |

Any other top-level member makes the request invalid. A request that breaks
any rule above is answered with `-32600 Invalid Request` and `id: null`: the
object is not a valid request, so its `id` is not used, whether or not one was
supplied.

### Notifications

A valid request object with **no** `id` member is a notification. The server
runs it and sends nothing back, even if the call fails. `"id": null` is not a
notification; it is a call whose ID is null, and it gets a response.

### Response object

| Member | Rule |
| --- | --- |
| `jsonrpc` | Always `"2.0"`. |
| `id` | The request's `id`, copied unchanged (same type and value). `null` for parse errors and invalid requests. |
| `result` | Present only on success. |
| `error` | Present only on failure: `{"code": integer, "message": string, "data"?: object}`. |

A response never contains both `result` and `error`.

### Batches

The body may be a JSON array of request objects.

- An empty array is an invalid request. The answer is **one** error object
  (not an array) with code `-32600` and `id: null`.
- More than 20 items is also answered with a single `-32600` object, with
  `data.reason` set to `"batch_too_large"`.
- Otherwise each item is handled on its own. The answer is an array with one
  response for every call and every invalid item. Invalid items, such as a
  string or an object missing `method`, get `-32600` with `id: null`.
  Notifications get no entry.
- If no entries remain because every item was a valid notification, the
  answer is `204` with an empty body.
- Items run one after another, and the response array happens to follow the
  request order, but clients must match responses to calls by `id`, not by
  position.

## 4. Methods

### `service.health`

Params: `{}` or absent. Any member is rejected with `-32602`.
Result: `{"status": "ok", "version": "1.0"}`. `version` is the API version of
this contract.

### `lambda.typecheck`

Params: `source` (required), `libraries` (optional).
Calls `d0exp_parse_and_typecheck(source)` and returns
`{"type": format_type(type)}`.

### `lambda.interpret`

Params: `source` (required), `libraries` (optional).
Parses and type-checks, then calls `d0exp_evaluate` in a worker process that is
killed when the time limit expires. Returns
`{"type": format_type(type), "value": d0val_format(value)}`. Values are
formatted as text; closures and environments are never serialized. If the
program called `print`, the printed text is returned in `output` (and
`output_truncated: true` is added if it passed the output limit). Printed text
never reaches the server's own console.

### `lambda.compile`

Params: `source` (required), `target` (required, `"python"` or
`"javascript"`), `libraries` (optional).
Parses and type-checks, then returns
`{"target": target, "code": d0exp_compile(...)}` or `d0exp_compile_js(...)`.
The code string is returned exactly as LAMBDA3 produced it. The service does
not execute it, import it, or pass it to `exec`, Node, or any other runtime.

### Parameter rules (all source methods)

| Problem | Code | `data.param` | `data.reason` |
| --- | --- | --- | --- |
| `params` is an array | `-32602` | `null` | `params_not_object` |
| An unrecognized member, such as `{"src": ...}` | `-32602` | that name | `unknown_param` |
| `source` absent | `-32602` | `source` | `missing` |
| `source` not a string | `-32602` | `source` | `not_a_string` |
| `source` empty or only whitespace | `-32602` | `source` | `blank` |
| `source` over 65,536 UTF-8 bytes | `-32602` | `source` | `too_large` (with `limit_bytes`) |
| `target` absent (compile only) | `-32602` | `target` | `missing` |
| `target` not `"python"` or `"javascript"` | `-32602` | `target` | `unsupported` (with `allowed`) |
| `libraries` not an array of known, distinct names | `-32602` | `libraries` | `invalid` (with `allowed`) |

## 5. Errors

| Code | Message | When | `data` |
| --- | --- | --- | --- |
| `-32700` | Parse error | The body is not valid UTF-8 JSON. `NaN` and `Infinity` are not JSON and are rejected here. | `{"reason": string}` |
| `-32600` | Invalid Request | The body or a batch item is not a valid request object; empty or oversized batch. | `{"reason": string}` |
| `-32601` | Method not found | `method` is not one of the four above. | `{"method": string}` |
| `-32602` | Invalid params | See the parameter table. | `{"param": string or null, "reason": string, ...}` |
| `-32603` | Internal error | An unexpected failure in the service or the worker. Details are logged on the server only. | `{"reference": string}`, which matches the server log line |
| `-32010` | LAMBDA syntax error | `LambdaSyntaxError` from the LAMBDA3 parser. | `{"message": string, "line": int, "column": int, "source_line": string}` |
| `-32011` | LAMBDA type error | `TypeCheckError` from the LAMBDA3 checker, including unbound variables. | `{"message": string}` |
| `-32012` | Execution timeout | The time limit passed before the operation finished. | `{"limit_seconds": number}` |
| `-32013` | LAMBDA runtime error | A well-typed program failed while running, for example `list_head(list_nil())`, division by zero, an array index out of range, or recursion too deep for the interpreter. | `{"message": string, "kind": "runtime" or "recursion_depth"}` |
| `-32014` | Result too large | The formatted value or generated code is longer than 1,000,000 characters. | `{"limit_chars": int}` |

A LAMBDA syntax error is an application error, not `-32700`: the JSON was
fine, and only the program text inside it was wrong.

No error contains a Python traceback, exception class name, or filesystem
path. LAMBDA3's own diagnostic message is passed through for syntax, type,
and runtime errors, because those messages describe the client's program.

A timeout means only that the operation did not finish in time. It does not
prove the program never terminates.

## 6. Limits

| Limit | Value | Where it is enforced |
| --- | --- | --- |
| Request body | 1 MiB | HTTP status `413` |
| `source` | 65,536 UTF-8 bytes | `-32602`, before any LAMBDA3 call |
| Batch size | 20 items | `-32600` |
| Time per source call | 5 seconds by default; `--time-limit` changes it | `-32012`. The clock starts after the worker has started and imported LAMBDA3, and covers parsing, type-checking, and evaluating or compiling. |
| Interpreter recursion | Python recursion limit of 1,000,000 frames in a 255 MiB thread stack (LAMBDA3 uses several Python frames per LAMBDA call, so roughly 50,000 nested LAMBDA calls fit in the time limit) | `-32013` with `kind: "recursion_depth"` |
| Formatted value or generated code | 1,000,000 characters | `-32014` |
| Printed output | 65,536 characters | truncated, with `output_truncated: true` |

Each source call runs in its own worker process. The server terminates the
process when the time limit expires, so a runaway program cannot keep running
in the background or exhaust the server's own stack.

## 7. Examples

Each pair below is an HTTP request and the exact response the service returns.
Where a response says `"<generated code>"`, the real response contains the
full generated program (several kilobytes), and the replay test checks only
that it is a nonempty string.

### Health

```http
POST /rpc HTTP/1.1
Content-Type: application/json

{"jsonrpc": "2.0", "method": "service.health", "params": {}, "id": "h1"}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"jsonrpc": "2.0", "id": "h1", "result": {"status": "ok", "version": "1.0"}}
```

### Successful type-check

```http
POST /rpc HTTP/1.1
Content-Type: application/json

{"jsonrpc": "2.0", "method": "lambda.typecheck", "params": {"source": "lam (x: sint) => (x, x <= 1)"}, "id": 1}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"jsonrpc": "2.0", "id": 1, "result": {"type": "sint -> (sint, bool)"}}
```

### Successful interpretation (factorial)

```http
POST /rpc HTTP/1.1
Content-Type: application/json

{"jsonrpc": "2.0", "method": "lambda.interpret", "params": {"source": "let fact : sint -> sint = fix fact(n: sint): sint => if n <= 1 then 1 else n * fact(n - 1) in fact(6) end"}, "id": 2}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"jsonrpc": "2.0", "id": 2, "result": {"type": "sint", "value": "720"}}
```

### Interpretation using a library

```http
POST /rpc HTTP/1.1
Content-Type: application/json

{"jsonrpc": "2.0", "method": "lambda.interpret", "params": {"source": "list_reverse(list_range(1, 5))", "libraries": ["list"]}, "id": 3}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"jsonrpc": "2.0", "id": 3, "result": {"type": "List[sint]", "value": "[4, 3, 2, 1]"}}
```

### Compilation

```http
POST /rpc HTTP/1.1
Content-Type: application/json

{"jsonrpc": "2.0", "method": "lambda.compile", "params": {"source": "1 + 2", "target": "javascript"}, "id": 4}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"jsonrpc": "2.0", "id": 4, "result": {"target": "javascript", "code": "<generated code>"}}
```

### LAMBDA syntax error

```http
POST /rpc HTTP/1.1
Content-Type: application/json

{"jsonrpc": "2.0", "method": "lambda.typecheck", "params": {"source": "if then"}, "id": 5}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"jsonrpc": "2.0", "id": 5, "error": {"code": -32010, "message": "LAMBDA syntax error", "data": {"message": "Expected an expression", "line": 1, "column": 4, "source_line": "if then"}}}
```

### LAMBDA type error (unbound variable)

```http
POST /rpc HTTP/1.1
Content-Type: application/json

{"jsonrpc": "2.0", "method": "lambda.interpret", "params": {"source": "y + 1"}, "id": 6}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"jsonrpc": "2.0", "id": 6, "error": {"code": -32011, "message": "LAMBDA type error", "data": {"message": "unbound variable 'y'"}}}
```

### Invalid params

```http
POST /rpc HTTP/1.1
Content-Type: application/json

{"jsonrpc": "2.0", "method": "lambda.compile", "params": {"source": "1", "target": "ruby"}, "id": 7}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"jsonrpc": "2.0", "id": 7, "error": {"code": -32602, "message": "Invalid params", "data": {"param": "target", "reason": "unsupported", "allowed": ["python", "javascript"]}}}
```

### Batch with calls, a notification, and an invalid item

The second item has no `id`, so it is a notification and gets no response.

```http
POST /rpc HTTP/1.1
Content-Type: application/json

[{"jsonrpc": "2.0", "method": "lambda.interpret", "params": {"source": "6 * 7"}, "id": "answer"}, {"jsonrpc": "2.0", "method": "service.health", "params": {}}, {"jsonrpc": "2.0", "method": "lambda.typecheck", "params": {"source": "(1, true)"}, "id": 8}, 42]
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

[{"jsonrpc": "2.0", "id": "answer", "result": {"type": "sint", "value": "42"}}, {"jsonrpc": "2.0", "id": 8, "result": {"type": "(sint, bool)"}}, {"jsonrpc": "2.0", "id": null, "error": {"code": -32600, "message": "Invalid Request", "data": {"reason": "not_an_object"}}}]
```

### Notification-only batch

```http
POST /rpc HTTP/1.1
Content-Type: application/json

[{"jsonrpc": "2.0", "method": "service.health", "params": {}}, {"jsonrpc": "2.0", "method": "lambda.typecheck", "params": {"source": "1 + 2"}}]
```

```http
HTTP/1.1 204 No Content
```

### Empty batch

```http
POST /rpc HTTP/1.1
Content-Type: application/json

[]
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"jsonrpc": "2.0", "id": null, "error": {"code": -32600, "message": "Invalid Request", "data": {"reason": "empty_batch"}}}
```

### Malformed JSON

```http
POST /rpc HTTP/1.1
Content-Type: application/json

{"jsonrpc":
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"jsonrpc": "2.0", "id": null, "error": {"code": -32700, "message": "Parse error", "data": {"reason": "invalid_json"}}}
```

## 8. Schema

`schema/jsonrpc.schema.json` is a JSON Schema (draft 2020-12) for the request
body (a single request or a batch), the response body, each method's `params`
and `result`, and the error object. The schema describes shape only. Rules
that depend on context, such as "invalid requests answer with `id: null`" or
"the source must fit in 65,536 bytes", are stated in this document and checked
by the tests.
