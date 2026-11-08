# Testing

From `assigns/07`, with the virtual environment from `README.md`:

```text
MySolution\.venv\Scripts\python -m unittest discover -s MySolution/tests -v
```

67 tests passed in 33.0 seconds on Python 3.14.0. Every JSON answer is checked against `schema/jsonrpc.schema.json`, and every 200 response is checked for a traceback, a `.py` path, or a filesystem path.

The professor's suite, from `assigns/07`, with `MySolution/serve.py` already listening on port 8000:

```text
python -m unittest discover -s TEST -v
```

15 tests passed in 4.8 seconds. That suite talks to `http://127.0.0.1:8000/rpc` over real HTTP. It does not import this service.

Successful type-check, interpretation, and compilation tests call the provided LAMBDA3 implementation. Test doubles replace the worker only in `InjectedFailureTests`, where the failure is a crash, an unexpected exception, or an instant timeout. `RealDeadlineTests` does not use a double: it runs a slow Fibonacci in a worker with a one-second limit.

## Architecture

```text
HTTP client
    |
    |  POST /rpc, application/json
    v
lambda_rpc/app.py            Flask. Status 200 for any JSON-RPC answer,
                             204 when there is nothing to send, 4xx only
                             for a bad HTTP request.
    |
    v
lambda_rpc/jsonrpc.py        Envelope. Batches, notifications, ids, and
                             the five standard JSON-RPC errors.
    |
    v
lambda_rpc/service.py        Params, then one method. Maps a worker
                             outcome to -32010 .. -32014.
    |
    v
lambda_rpc/worker.py         A spawned process per source call. The parent
                             kills it when the time limit expires.
    |
    v
assigns/07/LAMBDA3/lambda3.py
                             d0exp_parse_and_typecheck, d0exp_evaluate,
                             format_type, d0val_format, d0exp_compile,
                             d0exp_compile_js. Not modified.
```

`lambda3_bridge.py` is the only module that imports LAMBDA3. The dispatcher does not. A library named in `libraries` is read from `LAMBDA3/mylib/`, parsed with `d0cls_parse`, and wrapped around the client expression with `D0Elets` before `d0exp_typecheck`.

## Item 1: health (`HealthTests`, `IdTests`)

| Test | What it checks |
| --- | --- |
| `test_health_reports_status_and_version` | `{"status": "ok", "version": "1.0"}`, id `"health-1"` kept |
| `test_health_accepts_absent_params` | `params` may be omitted |
| `test_health_rejects_unknown_params` | Any member is `-32602` |
| `test_ids_are_copied_unchanged` | String, empty string, number, float, and null ids come back with the same type |
| `test_error_responses_keep_the_id` | A failing call keeps `"keep-me"` |

## Item 2: type-checking (`TypecheckTests`)

| Test | What it checks |
| --- | --- |
| `test_types_are_formatted_by_lambda3` | `sint`, `bool`, `(sint, bool)`, `sint -> (sint, bool)`, `List[sint]`, `unit` |
| `test_typecheck_does_not_evaluate` | `print(7)` and `10 / 0` type-check. Nothing is printed and nothing is divided |

## Item 3: interpretation (`InterpretTests`, `LibraryTests`)

| Test | What it checks |
| --- | --- |
| `test_arithmetic` | `20 + 22` is `"42"`. `(7 - 10) * 3` is `"-9"` |
| `test_factorial` | `fact(6)` is `"720"`. `fact(30)` is the full decimal, not an approximation |
| `test_tuple` | `(1, true)` has type `(sint, bool)` and value `(1, true)` |
| `test_list` | `list_cons(1, list_cons(2, list_nil()))` is `[1, 2]` |
| `test_each_library_can_be_used` | `list`, `optn`, `a1sz`, and `strm`, alone and together |
| `test_printed_text_is_returned_as_output` | `print(1234567890)` returns `output` and does not print on the server |
| `test_printed_text_is_truncated_at_the_output_limit` | A 4-character cap returns `"1234"` and `output_truncated: true` |
| `test_deepest_source_that_fits_the_size_limit` | 65,535 characters of nested parentheses evaluate to `1` |

## Item 4: compilation (`CompileTests`)

| Test | What it checks |
| --- | --- |
| `test_code_is_exactly_what_lambda3_generates` | Python and JavaScript for `fact(5)` equal direct `d0exp_compile` and `d0exp_compile_js` |
| `test_compiled_code_is_returned_not_run` | `print(424242)` comes back as text. The result has only `target` and `code` |
| `test_service_never_executes_generated_code` | No service module calls `exec`, `eval`, `compile`, `__import__`, `subprocess`, `os.system`, or Node |
| `test_oversized_generated_code_is_rejected` | A 50-character cap on `1 + 2` is `-32014` |

## Item 5: distinct language errors (`LambdaErrorTests`)

| Test | What it checks |
| --- | --- |
| `test_syntax_and_type_errors_have_distinct_codes` | `if then` is `-32010`. `1 + true` is `-32011` |
| `test_syntax_error_reports_position` | `if then` is line 1, column 4, source line `if then` |
| `test_each_source_method_checks_before_running` | Type-check, interpret, and compile all reject both programs |
| `test_ill_typed_program_is_never_evaluated` | `print(5)` inside an ill-typed `let` produces no `output` |
| `test_runtime_errors` | Empty `list_head`, division by zero, and a bad array index are `-32013` |
| `test_recursion_too_deep_for_the_interpreter` | A lowered recursion limit reports `kind: "recursion_depth"` |

## Item 6: malformed input (`EnvelopeTests`, `ParamsTests`)

| Test | What it checks |
| --- | --- |
| `test_malformed_json` | Truncated JSON, empty body, single quotes, non-UTF-8, and a trailing comma are `-32700` with `id: null` |
| `test_non_json_constants_are_parse_errors` | `NaN`, `Infinity`, and `-Infinity` are `-32700` |
| `test_deeply_nested_json_is_a_parse_error` | 200,000 nested arrays are `-32700` with `reason: "nesting_too_deep"`, not a crash |
| `test_invalid_envelopes_answer_with_null_id` | Wrong `jsonrpc`, missing members, bad id types, and an unknown member are `-32600` with `id: null`, even when the body carried an id |
| `test_unknown_method_keeps_the_id` | An unknown name, `rpc.discover`, a case change, and an empty name are `-32601` |
| `test_positional_params_are_invalid_params` | An array `params` is `-32602` |
| `test_absent_source` | `{}` and a missing `params` are `reason: "missing"` |
| `test_source_of_the_wrong_type` | Number, null, boolean, array, and object |
| `test_blank_source` | `""`, spaces, and whitespace |
| `test_oversized_source` | 65,537 bytes, including a string whose UTF-8 size exceeds the character count |
| `test_source_at_the_size_limit_is_accepted` | 65,536 bytes type-checks |
| `test_unknown_param` | `src` instead of `source`, and `target` on type-check |
| `test_compile_target` | Missing target, and `ruby`, `Python`, `""`, a number, and null |
| `test_libraries` | A string, an unknown name, a duplicate, a non-string, an object, and null |

## Item 7: function formatting (`InterpretTests`)

| Test | What it checks |
| --- | --- |
| `test_functions_are_formatted_without_their_closure` | A lambda is `<lam>`, a fix is `<fix>`, and a captured `12345` does not appear |

## Item 8: injected failure and a real deadline (`InjectedFailureTests`, `RealDeadlineTests`)

| Test | What it checks |
| --- | --- |
| `test_unexpected_exception_preserves_id_without_traceback` | A raising runner returns `-32603` with id `"req-17"` and only a `reference`. The traceback is in the server log |
| `test_worker_crash_preserves_id` | `WorkerFailure` is the same shape, id `17` |
| `test_worker_internal_outcome_is_logged_not_returned` | An `internal` outcome from the worker is logged, id null kept, and the planted path is not in the response |
| `test_injected_timeout_preserves_id` | An instant timeout is `-32012` with the configured 2.5 seconds, for a string id, `0`, and null |
| `test_failure_in_one_batch_item_does_not_affect_the_others` | One item is `-32603` and the health item still succeeds |
| `test_invalid_params_never_reach_lambda3` | Blank, missing, mistyped, and unknown params never call the runner |
| `test_slow_program_is_stopped_and_service_keeps_working` | `fib(27)` at a one-second limit is `-32012` with id `"slow"`, and the next call, `fib(10)`, returns `55` |

## Item 9: unbound variables (`LambdaErrorTests`)

| Test | What it checks |
| --- | --- |
| `test_unbound_variable_is_rejected` | `y + 1` is `-32011` with `unbound variable 'y'` on type-check, interpret, and compile |
| `test_library_names_are_unbound_without_the_library` | `list_range` is a type error until `libraries` names `list` |

## Item 10: batches and notifications (`BatchTests`)

| Test | What it checks |
| --- | --- |
| `test_mixed_batch_is_answered_per_item_and_omits_notifications` | Calls answered by id, both notifications omitted, a syntax error and a non-object kept |
| `test_malformed_members_each_get_a_null_id_error` | A string and an object with no method are `-32600` with `id: null` |
| `test_notification_only_batch_returns_204` | Status 204 and an empty body, including a notification that would have failed |
| `test_single_notification_returns_204_even_when_it_fails` | One notification is 204 for health, an unknown method, and a blank source |
| `test_null_id_is_a_call_not_a_notification` | `"id": null` gets a response |
| `test_empty_batch_is_one_invalid_request` | `[]` is one object, `-32600`, `reason: "empty_batch"` |
| `test_batch_size_limit` | 20 items succeed. 21 is one `-32600` with `batch_too_large` |
| `test_nested_batch_is_an_invalid_item` | An array inside a batch is `not_an_object` |

## Transport, contract, and schema

| Test | What it checks |
| --- | --- |
| `test_rpc_errors_use_http_200` | Unknown method and malformed JSON are HTTP 200 with `application/json` |
| `test_charset_parameter_is_accepted` | `application/json; charset=utf-8` |
| `test_other_media_types_are_415` | Plain text, form data, a latin-1 charset, and a missing type |
| `test_oversized_body_is_413` | Past `max_body_bytes` is HTTP 413, plain text |
| `test_other_http_methods_are_405` | GET, PUT, and DELETE, with `Allow: POST` |
| `test_other_paths_are_404` | `/`, `/rpc/health`, `/typecheck` |
| `test_syntax_error_positions_refer_to_the_client_source` | With `libraries: ["list"]`, a fault on line 2 is still line 2 of the client source |
| `test_every_documented_example_matches_the_service` | All 12 HTTP examples in `RPC.md` section 7, byte for byte except the generated-code placeholder |
| `test_well_formed_example_requests_match_the_schema` | The well-formed examples validate |
| `test_schema_rejects_what_the_service_rejects` | Wrong version, boolean id, extra member, blank source, bad target, unknown library, empty batch |
