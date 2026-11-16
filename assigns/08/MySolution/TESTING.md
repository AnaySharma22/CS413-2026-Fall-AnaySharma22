# Testing

From `assigns/08`:

```text
MySolution\.venv\Scripts\python -m unittest discover -s MySolution/tests -v
```

Observed result: 18 tests passed in about 39 seconds on Python 3.14.0.

## Architecture

```text
Browser  --POST /rpc-->  Flask (app.py)
                            |
                            v
                       JSON-RPC dispatcher (jsonrpc.py)
                            |
                            v
                       QueensService (service.py)
                            |
                            v
                       StreamTable (streams.py)
                            |
                            v
                       QueensSolver (solver.py) --> LAMBDA3 queens_cps.lam
```

## Required items

| # | Requirement | Tests |
| --- | --- | --- |
| 1 | Safety: same column, both diagonals, safe placement | `SolverTests.test_safety_same_column_and_both_diagonals` |
| 2 | CPS success/failure and resume at next candidate | `SolverTests.test_cps_resumes_at_the_next_candidate_after_reject_and_backtrack` |
| 3 | 8×8: 92 distinct solutions, deterministic order | `SolverTests.test_eight_queens_has_ninety_two_distinct_solutions`, `SolverTests.test_four_queens_solutions_are_exact_and_ordered` |
| 4 | Every event kind with board/coordinates | `SolverTests.test_each_required_event_kind_appears`, `RpcTests.test_event_json_shapes` |
| 5 | Lazy construction and bounded force | `SolverTests.test_opening_does_not_force_the_stream`, `test_forcing_one_cell_does_not_force_its_tail`, `test_bounded_prefix_leaves_later_work_unforced` |
| 6 | Exhaustion, close, unknown ID, expiration | `RpcTests.test_close_unknown_and_repeated_next_after_done`, `test_expired_stream_is_unknown` |
| 7 | JSON-RPC envelopes, methods, params, notifications | `RpcTests.test_health_preserves_id`, `test_unknown_method_and_invalid_params`, `test_malformed_envelope_and_notification` |
| 8 | `queens.next` limits 1 and 32 | `RpcTests.test_open_does_not_force_and_next_respects_limits` |
| 9 | HTTP open through all 92 solutions to completion | `ClientFlowTests.test_http_flow_finds_all_eight_queens_solutions` |
| 10 | Browser controls and RPC failure handling | `ClientFlowTests.test_static_page_exposes_required_controls`, checklist below |

Successful solver tests call the real LAMBDA3 program. Expiration uses a fake
clock. Laziness is observed with a force counter and the `D0Vlazy.evaluated`
flag, not only by reading a `<lazy>` printout.

## Browser checklist

Run `serve.py`, open `http://127.0.0.1:8000/`, then:

1. **Start** — board empty, status says the stream is open, Step/Play enabled.
2. **Step** — one event applied; try/place/reject highlights appear; log grows.
3. **Play** — events advance on the timer; changing Speed changes the pace.
4. **Pause** — advancement stops; Step works again.
5. **Next solution** — playback continues until a solution row appears in the
   log and the solution counter increases, or until `done`.
6. **Reset** — stream closes, board clears, Start works again.
7. **RPC failure** — stop the server and press Step: the red error box shows a
   failure message; Start/Reset still recover after restarting the server.
8. **Completion** — after `done`, status reports search complete and the
   solution count; Play/Step stay disabled until Reset.

`ClientFlowTests.test_browser_checklist_is_documented` checks that this section
exists. The static-page test checks that the HTML and JS expose the controls and
call `queens.open` / `queens.next` / `queens.close` with a small batch limit.
