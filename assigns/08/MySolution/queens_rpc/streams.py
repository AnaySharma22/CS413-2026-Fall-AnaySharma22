"""Process-local table of open lazy streams."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field

from .config import Limits
from .errors import UNKNOWN_STREAM, RpcError
from .solver import QueensSolver


@dataclass
class StreamEntry:
    size: int
    stream: object
    exhausted: bool = False
    last_used: float = field(default_factory=time.monotonic)


class StreamTable:
    def __init__(self, solver: QueensSolver | None = None, limits: Limits | None = None,
                 clock=time.monotonic):
        self.solver = solver or QueensSolver()
        self.limits = limits or Limits()
        self.clock = clock
        self._lock = threading.Lock()
        self._streams: dict[str, StreamEntry] = {}

    def open(self, size: int) -> tuple[str, int]:
        stream = self.solver.open_stream(size)
        stream_id = uuid.uuid4().hex
        with self._lock:
            self._expire_locked()
            self._streams[stream_id] = StreamEntry(
                size=size, stream=stream, last_used=self.clock()
            )
        return stream_id, size

    def next_events(self, stream_id: str, limit: int) -> tuple[list[dict], bool]:
        with self._lock:
            entry = self._get_locked(stream_id)
            entry.last_used = self.clock()
            if entry.exhausted:
                return [], True

            events: list[dict] = []
            finished = False
            for _ in range(limit):
                event, tail, finished = self.solver.next_event(entry.stream)
                entry.stream = tail
                if event is None:
                    finished = True
                    break
                events.append(event)
                if finished:
                    break
            entry.exhausted = finished
            entry.last_used = self.clock()
            return events, finished

    def close(self, stream_id: str) -> bool:
        with self._lock:
            self._expire_locked()
            if stream_id not in self._streams:
                raise RpcError(UNKNOWN_STREAM, {"stream_id": stream_id, "reason": "unknown"})
            del self._streams[stream_id]
            return True

    def get(self, stream_id: str) -> StreamEntry:
        with self._lock:
            return self._get_locked(stream_id)

    def _get_locked(self, stream_id: str) -> StreamEntry:
        self._expire_locked()
        entry = self._streams.get(stream_id)
        if entry is None:
            raise RpcError(UNKNOWN_STREAM, {"stream_id": stream_id, "reason": "unknown"})
        return entry

    def _expire_locked(self) -> None:
        now = self.clock()
        expired = [
            stream_id
            for stream_id, entry in self._streams.items()
            if now - entry.last_used > self.limits.stream_idle_seconds
        ]
        for stream_id in expired:
            del self._streams[stream_id]
