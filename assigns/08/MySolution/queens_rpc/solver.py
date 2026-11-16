"""Load the LAMBDA3 CPS solver and force lazy event cells one at a time.

This module knows LAMBDA3 values. It does not know HTTP or JSON-RPC.
"""

from __future__ import annotations

import sys
from pathlib import Path

KIND_NAMES = ("try", "place", "reject", "backtrack", "solution", "done")

LAMBDA3_DIR = Path(__file__).resolve().parents[2] / "LAMBDA3"
SOLVER_PATH = Path(__file__).resolve().parents[1] / "queens_cps.lam"
LIST_PATH = LAMBDA3_DIR / "mylib" / "list.lam"


class ForceCounter:
    """Counts first-time evaluations of D0Vlazy cells."""

    def __init__(self):
        self.forces = 0

    def reset(self) -> None:
        self.forces = 0


class QueensSolver:
    def __init__(self):
        if str(LAMBDA3_DIR) not in sys.path:
            sys.path.insert(0, str(LAMBDA3_DIR))
        import lambda3 as L
        from basics0 import fnlist_cons, fnlist_nil

        self.L = L
        self.fnlist_cons = fnlist_cons
        self.fnlist_nil = fnlist_nil
        list_src = LIST_PATH.read_text(encoding="utf-8")
        solver_src = SOLVER_PATH.read_text(encoding="utf-8")
        self.declarations = L.d0cls_parse(list_src + "\n" + solver_src)
        L.d0cls_typecheck(self.declarations)
        self.counter = ForceCounter()
        # Deep CPS + lazy tails need more than the default recursion limit.
        sys.setrecursionlimit(max(sys.getrecursionlimit(), 100_000))

    def open_stream(self, size: int):
        """Return an unforced Strm[Event] for an N-queens search."""
        expression = self.L.D0Elets(
            self.declarations, self.L.d0exp_parse(f"queens_stream({size})")
        )
        stream = self.L.d0exp_evaluate(expression)
        if not isinstance(stream, self.L.D0Vlazy):
            raise TypeError("queens_stream must return a lazy stream")
        if stream.evaluated:
            raise RuntimeError("opening the stream must not force it")
        return stream

    def next_event(self, stream):
        """Force one cell. Return (event_dict_or_None, tail_stream, finished)."""
        node = self._force(stream)
        if not node.is_cons:
            return None, stream, True
        event = self._decode(node.head)
        tail = node.tail
        finished = event["event"] == "done"
        return event, tail, finished

    def is_unevaluated(self, stream) -> bool:
        return isinstance(stream, self.L.D0Vlazy) and not stream.evaluated

    def _force(self, lazy):
        if not isinstance(lazy, self.L.D0Vlazy):
            raise TypeError("expected a lazy stream cell")
        if not lazy.evaluated:
            self.counter.forces += 1
            lazy.value = self.L._d0val_apply(lazy.arg1, self.L.D0Vtupl(()))
            lazy.evaluated = True
        return lazy.value

    def _decode(self, value) -> dict:
        if not isinstance(value, self.L.D0Vtupl) or len(value.arg1) != 4:
            raise TypeError("event must be a 4-tuple")
        kind_v, column_v, row_v, board_v = value.arg1
        kind = int(kind_v.arg1)
        if kind < 0 or kind >= len(KIND_NAMES):
            raise ValueError(f"unknown event kind {kind}")
        name = KIND_NAMES[kind]
        if name == "done":
            return {"event": "done"}
        board = self._board(board_v)
        if name == "solution":
            return {"event": "solution", "board": board}
        return {
            "event": name,
            "column": int(column_v.arg1),
            "row": int(row_v.arg1),
            "board": board,
        }

    def _board(self, value) -> list[int]:
        if not isinstance(value, self.L.D0Vlist):
            raise TypeError("board must be a list")
        columns: list[int] = []
        items = value.arg1
        while isinstance(items, self.fnlist_cons):
            columns.append(int(items.arg1.arg1))
            items = items.arg2
        if not isinstance(items, self.fnlist_nil):
            raise TypeError("malformed board list")
        columns.reverse()
        return columns
