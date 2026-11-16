# Design: animated N-Queens with CPS and lazy streams

This document was written before the implementation. The solver lives in
LAMBDA3, the RPC layer only forces stream cells and translates events, and the
browser only consumes events one batch at a time.

## 1. Solver state and board invariant

A **partial board** is a `List[sint]`. The head is the most recently placed
column (the queen in the highest filled row). The length of the list is the
number of placed queens, which equals the next row index when a placement
succeeds. Rows and columns are numbered from 0. For an N×N board, every column
value is in `0 .. N-1`, and no two entries share a column or a diagonal.

A **complete board** has length `N`. The JSON encoding reverses the list so
index `i` is the column of the queen in row `i`. Internally the newest-first
order matches the safety walk: distance 1 is the previous row, distance 2 the
one before that, and so on.

Search fills **one row at a time**, trying columns from left to right
(0, 1, …, N−1). That order is deterministic. The 8×8 stream contains exactly
92 distinct solutions and then a single `done` event.

## 2. Continuation conventions

Every search helper returns a `Strm[Event]` as its answer. It never returns a
board or a Boolean for direct-style code to inspect.

| Continuation | Type (conceptual) | Role |
| --- | --- | --- |
| Success (`on_solution`) | `(Board, unit -> Strm[Event]) -> Strm[Event]` | Emit `solution`, then resume the remaining search via the failure continuation that was passed in. |
| Exhaustion / failure | `unit -> Strm[Event]` | Resume the next candidate in this row, or emit `backtrack` and try the next column of the enclosing row, or emit `done` at the root. |
| Safe | `unit -> Strm[Event]` | The candidate passed every conflict check; emit `place` and search the next row. |
| Conflict | `unit -> Strm[Event]` | A conflict was found; emit `reject` and try the next column. |

Trying a candidate (pseudocode, matching the assignment sketch):

```text
try_column(row, column, board, on_solution, on_exhausted):
  if column == size:
    on_exhausted()
  else
    emit(try(column, row, board), λ():
      check_safe(column, 1, board,
        λ():  # safe
          next = cons(column, board)
          emit(place(column, row, next), λ():
            search(row + 1, next, on_solution,
              λ(): emit(backtrack(column, row, board), λ():
                     try_column(row, column + 1, board,
                       on_solution, on_exhausted)))),
        λ():  # conflict
          emit(reject(column, row, board), λ():
            try_column(row, column + 1, board,
              on_solution, on_exhausted))))
```

`check_safe` is itself CPS: it calls `on_safe` only after every earlier queen
is clear, and calls `on_conflict` as soon as one conflicts. It does not return
a Boolean.

`emit(event, cont)` builds a stream cell whose head is `event` and whose tail
is a fresh lazy thunk that runs `cont` only when that tail is forced:

```text
emit(event, cont) =
  lazy_make(λ_. stcn_cons(event, lazy_make(λ_. lazy_eval(cont()))))
```

So constructing a stream does no search. Forcing one cell produces one event
and installs the next lazy cell; it does not force that next cell.

## 3. From CPS search to a lazy event stream

`queens_stream(size)` returns

```text
search(0, nil, on_solution, root_exhausted)
```

where `on_solution(board, resume) = emit(solution(board), resume)` and
`root_exhausted() = emit(done, λ_. strm_nil())`.

Work happens only inside a forced thunk: a safety walk for the current
candidate, construction of the next `emit`, or a call to the next
continuation. Unforced tails remain `D0Vlazy` values with `evaluated = false`.
The Python adapter counts first-time forces of those lazy cells so tests can
observe that a bounded prefix leaves later work untouched.

The supplied `eight_queens_stream.lam` is a reference for lazy backtracking,
but it is direct-style, column-oriented, and yields only solution boards. This
solver is rewritten in CPS, row-oriented, and yields the full event trace.
Safety geometry (same column, both diagonals) is the same idea as that file.

## 4. Event schema

| `event` | Fields | Board meaning |
| --- | --- | --- |
| `try` | `column`, `row`, `board` | Candidate under consideration; board is the partial board before placement. |
| `place` | `column`, `row`, `board` | Candidate is safe; board includes the new queen. |
| `reject` | `column`, `row`, `board` | Candidate conflicts; board unchanged. |
| `backtrack` | `column`, `row`, `board` | Subtree failed; board restored to the state before that place. |
| `solution` | `board` | Complete arrangement, row order. |
| `done` | (none) | Final event; appears exactly once. |

Internal LAMBDA encoding of an event is
`(kind, column, row, board)` with
`kind ∈ {0=try, 1=place, 2=reject, 3=backtrack, 4=solution, 5=done}`.
The adapter maps that tuple to the JSON objects above. Closures are never
serialized.

## 5. RPC exchange examples

Endpoint: `POST /rpc`, `Content-Type: application/json`. HTTP 200 for every
JSON-RPC response; HTTP 204 for a valid notification.

### `service.health`

```json
--> {"jsonrpc":"2.0","method":"service.health","params":{},"id":1}
<-- {"jsonrpc":"2.0","id":1,"result":{"status":"ok","version":"1.0"}}
```

### `queens.open`

Creates a stream. Does not force the first event.

```json
--> {"jsonrpc":"2.0","method":"queens.open","params":{"size":8},"id":2}
<-- {"jsonrpc":"2.0","id":2,"result":{"stream_id":"…uuid…","size":8}}
```

### `queens.next`

Forces at most `limit` events (`1..32`).

```json
--> {"jsonrpc":"2.0","method":"queens.next","params":{"stream_id":"…","limit":1},"id":3}
<-- {"jsonrpc":"2.0","id":3,"result":{"events":[{"event":"try","column":0,"row":0,"board":[]}],"done":false}}
```

When the batch includes `done`, `done` is `true`. Later `queens.next` calls
return `{"events":[],"done":true}`.

### `queens.close`

```json
--> {"jsonrpc":"2.0","method":"queens.close","params":{"stream_id":"…"},"id":4}
<-- {"jsonrpc":"2.0","id":4,"result":{"closed":true}}
```

## 6. Stream lifetime, cleanup, limits, errors

| Rule | Value |
| --- | --- |
| Board size | Integer 4 through 10 |
| `limit` | Integer 1 through 32 |
| Inactivity lifetime | 10 minutes since last successful open/next; then the ID is removed |
| Stream IDs | `uuid4` hex strings, unguessable within the process |
| Storage | Process-local dict; a restart forgets every ID |
| Close | Removes the stream immediately |
| Exhaustion | After `done` is delivered, the entry is kept until close or expiry so repeated `next` can return empty + `done: true` |

Application error **`-32020`** (`Unknown stream`) covers unknown, closed, and
expired IDs. Standard JSON-RPC codes cover parse/envelope/params/internal
failures. Responses never include tracebacks, filesystem paths, or closure
objects.

Batch requests are not implemented. A notification for a queens method still
mutates stream state and returns HTTP 204.

## 7. Architecture

```text
Browser (static HTML/CSS/JS)
    |  fetch POST /rpc  (open, next, close)
    v
Flask transport          app.py — one route, media-type checks
    |
    v
JSON-RPC dispatcher      jsonrpc.py — envelope, ids, notifications
    |
    v
Queens service           service.py — validate params, open/next/close
    |
    +-- stream table     streams.py — id -> {size, strm value, last_used}
    |
    v
LAMBDA3 adapter          solver.py — load queens_cps.lam, force one cell,
                         decode event tuples, count lazy forces
    |
    v
assigns/08/LAMBDA3       lambda3.py + mylib/list.lam
                         CPS search + lazy Strm[Event]
```

The browser never receives a full trace up front. Playback calls `queens.next`
with a small limit as the animation needs more events. **Next solution** keeps
requesting until a `solution` or `done` arrives. **Reset** closes the stream
and clears the board.
