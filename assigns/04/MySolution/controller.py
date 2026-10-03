"""Coordinate the model and a replaceable backend. The view is not imported here."""

from threading import Lock

from backend import Backend
from model import Model


class Controller:
    def __init__(self, backend=None):
        self.model = Model()
        self.backend = backend if backend is not None else Backend()
        self._lock = Lock()

    def state(self):
        with self._lock:
            return self._snapshot()

    def apply(self, source, name):
        with self._lock:
            self.model.apply(source, name)
            return self._snapshot()

    def run(self, operation, editor):
        with self._lock:
            if editor != self.model.source:
                raise ValueError(
                    "Apply or discard unapplied edits before running a tool."
                )
            self.model.begin(operation)
            source = self.model.source
        try:
            result = self.backend.run(operation, source)
        except Exception:
            result = {
                "outcome": "backend_error",
                "text": "The backend failed. The applied source is unchanged; retry.",
            }
        if not isinstance(result, dict) or "outcome" not in result or "text" not in result:
            result = {
                "outcome": "backend_error",
                "text": "The backend returned an incomplete result. Retry.",
            }
        with self._lock:
            self.model.finish(operation, result)
            return self._snapshot()

    def _snapshot(self):
        return {
            "name": self.model.name,
            "source": self.model.source,
            "revision": self.model.revision,
            "busy": self.model.busy,
            "artifact": self.model.artifact,
            "result": self.model.result,
            "execute_available": self.model.artifact is not None,
        }
