"""Queens RPC methods: validate params, talk to the stream table."""

from __future__ import annotations

from collections.abc import Callable

from .config import API_VERSION, MAX_LIMIT, MAX_SIZE, MIN_LIMIT, MIN_SIZE, Limits
from .errors import invalid_params
from .streams import StreamTable


class QueensService:
    def __init__(self, table: StreamTable | None = None, limits: Limits | None = None):
        self.limits = limits or Limits()
        self.table = table or StreamTable(limits=self.limits)

    def methods(self) -> dict[str, Callable[[dict], dict]]:
        return {
            "service.health": self.health,
            "queens.open": self.open,
            "queens.next": self.next,
            "queens.close": self.close,
        }

    def health(self, params: dict) -> dict:
        _reject_unknown(params, set())
        return {"status": "ok", "version": API_VERSION}

    def open(self, params: dict) -> dict:
        _reject_unknown(params, {"size"})
        size = _int_param(params, "size", MIN_SIZE, MAX_SIZE)
        stream_id, size = self.table.open(size)
        return {"stream_id": stream_id, "size": size}

    def next(self, params: dict) -> dict:
        _reject_unknown(params, {"stream_id", "limit"})
        stream_id = _stream_id(params)
        limit = _int_param(params, "limit", MIN_LIMIT, MAX_LIMIT)
        events, done = self.table.next_events(stream_id, limit)
        return {"events": events, "done": done}

    def close(self, params: dict) -> dict:
        _reject_unknown(params, {"stream_id"})
        stream_id = _stream_id(params)
        self.table.close(stream_id)
        return {"closed": True}


def _reject_unknown(params: dict, allowed: set[str]) -> None:
    for name in params:
        if name not in allowed:
            raise invalid_params(name, "unknown_param")


def _stream_id(params: dict) -> str:
    if "stream_id" not in params:
        raise invalid_params("stream_id", "missing")
    value = params["stream_id"]
    if not isinstance(value, str) or not value:
        raise invalid_params("stream_id", "not_a_string")
    return value


def _int_param(params: dict, name: str, low: int, high: int) -> int:
    if name not in params:
        raise invalid_params(name, "missing")
    value = params[name]
    if isinstance(value, bool) or not isinstance(value, int):
        raise invalid_params(name, "not_an_integer")
    if value < low or value > high:
        raise invalid_params(name, "out_of_range", minimum=low, maximum=high)
    return value
