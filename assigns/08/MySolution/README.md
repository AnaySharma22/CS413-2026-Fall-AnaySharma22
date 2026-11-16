# Assignment 8: animated N-Queens with CPS and lazy streams

A LAMBDA3 continuation-passing search emits a lazy stream of board events.
A small JSON-RPC service forces those events on demand. A browser page plays
them as an animation. Generated search state stays in the server process; the
page never downloads the full trace up front.

Developed and tested with Python 3.14.0 and Flask 3.1.3 on Windows. Python 3.12
or later is required.

## Setup

From `assigns/08/MySolution`:

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

On POSIX use `.venv/bin/python`. Do not commit the virtual environment.

## Run the animation demo

From `assigns/08`, after the setup above:

```text
MySolution\.venv\Scripts\python MySolution\serve.py
```

Leave that terminal running. In a browser, open:

[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

That page is the N-Queens animation (`static/index.html`). Press **Start**, then
**Step** or **Play**. The JSON-RPC endpoint used by the page is
[http://127.0.0.1:8000/rpc](http://127.0.0.1:8000/rpc).

`--port` changes the port. `--idle-seconds` changes the inactivity lifetime for
open streams (default 600).

## Run the tests

From `assigns/08`:

```text
MySolution\.venv\Scripts\python -m unittest discover -s MySolution/tests -v
```

## Controls

| Control | Behavior |
| --- | --- |
| Start | `queens.open` for the selected size (4–10). Does not force events. |
| Step | Fetch a small batch if needed, then apply one event. |
| Play / Pause | Advance on a timer; speed slider sets the delay. |
| Next solution | Play until the next `solution` or `done`. |
| Reset | `queens.close`, clear the board, allow Start again. |

The status line and event log distinguish a `solution` from search completion
(`done`). Rejected candidates, placements, and backtracks use different cell
highlights. Network or RPC failures surface in the red error box; Reset starts
a fresh search.

## RPC examples

```text
curl.exe -s -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"service.health\",\"params\":{},\"id\":1}" http://127.0.0.1:8000/rpc
curl.exe -s -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"queens.open\",\"params\":{\"size\":8},\"id\":2}" http://127.0.0.1:8000/rpc
curl.exe -s -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"queens.next\",\"params\":{\"stream_id\":\"REPLACE\",\"limit\":1},\"id\":3}" http://127.0.0.1:8000/rpc
curl.exe -s -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"queens.close\",\"params\":{\"stream_id\":\"REPLACE\"},\"id\":4}" http://127.0.0.1:8000/rpc
```

## Layout

| Path | Role |
| --- | --- |
| `queens_cps.lam` | CPS search and lazy event stream in LAMBDA3 |
| `queens_rpc/` | Flask app, JSON-RPC dispatcher, stream table, solver adapter |
| `static/` | Animation page |
| `DESIGN.md` | Continuations, events, RPC, architecture |
| `TESTING.md` | Requirement-to-test map and browser checklist |

## Limitations

- Stream IDs are process-local. A restart forgets them. Idle streams expire
  after ten minutes.
- Batches are not supported; a batch body is an invalid request.
- Board sizes outside 4–10 are rejected. `limit` must be 1–32.
- The service only runs the reviewed queens solver. It does not evaluate
  client-supplied LAMBDA source.
