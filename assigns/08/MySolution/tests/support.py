"""Shared helpers for Assignment 8 tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SOLUTION_DIR = Path(__file__).resolve().parents[1]
if str(SOLUTION_DIR) not in sys.path:
    sys.path.insert(0, str(SOLUTION_DIR))

from queens_rpc import Limits, create_app  # noqa: E402
from queens_rpc.service import QueensService  # noqa: E402
from queens_rpc.solver import QueensSolver  # noqa: E402
from queens_rpc.streams import StreamTable  # noqa: E402


def build_app(limits: Limits | None = None, table: StreamTable | None = None):
    limits = limits or Limits()
    table = table or StreamTable(limits=limits)
    return create_app(QueensService(table=table, limits=limits), limits=limits)


class Client:
    def __init__(self, app):
        self.http = app.test_client()

    def call(self, method, params=None, id=1):
        payload = {"jsonrpc": "2.0", "method": method, "id": id}
        if params is not None:
            payload["params"] = params
        response = self.http.post(
            "/rpc", data=json.dumps(payload), content_type="application/json"
        )
        assert response.status_code == 200, response.status_code
        return response.get_json()

    def raw(self, body, content_type="application/json"):
        return self.http.post("/rpc", data=body, content_type=content_type)
