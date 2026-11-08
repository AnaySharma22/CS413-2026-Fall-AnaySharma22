"""Shared helpers for the HTTP tests.

Every test talks to the Flask application through its test client, so each
request goes through the same transport, envelope, and service code as a
real server. Every JSON answer is also validated against the JSON Schema.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SOLUTION_DIR = Path(__file__).resolve().parents[1]
if str(SOLUTION_DIR) not in sys.path:
    sys.path.insert(0, str(SOLUTION_DIR))

from jsonschema import Draft202012Validator  # noqa: E402

from lambda_rpc import Limits, create_app  # noqa: E402
from lambda_rpc.service import LambdaService  # noqa: E402

SCHEMA = json.loads((SOLUTION_DIR / "schema" / "jsonrpc.schema.json").read_text("utf-8"))
Draft202012Validator.check_schema(SCHEMA)


def schema_validator(definition: str) -> Draft202012Validator:
    return Draft202012Validator({**SCHEMA, "oneOf": [{"$ref": f"#/$defs/{definition}"}]})


RESPONSE_BODY = schema_validator("responseBody")
REQUEST_BODY = schema_validator("requestBody")

LEAK_PATTERNS = [
    re.compile(pattern)
    for pattern in (r"Traceback", r'File "', r"\.py\b", r"/home/", r"/Users/",
                    r"lambda_rpc", r"site-packages")
]

_DRIVE_LETTER = re.compile(r"[A-Za-z]:\\")


def assert_no_leak(payload: dict | list) -> None:
    text = json.dumps(payload)
    for pattern in LEAK_PATTERNS:
        assert not pattern.search(text), f"response leaks {pattern.pattern!r}: {text[:300]}"
    # Generated Python comments contain a colon, so drive letters are checked
    # against the decoded strings rather than the JSON text.
    for value in _strings(payload):
        assert not _DRIVE_LETTER.search(value), f"response leaks a path: {value[:300]}"


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        yield from _strings(list(value.values()))
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def build_app(limits: Limits | None = None, runner=None):
    limits = limits or Limits()
    return create_app(LambdaService(runner=runner, limits=limits))


class Client:
    def __init__(self, app):
        self.http = app.test_client()

    def post(self, payload=None, *, raw: bytes | None = None,
             content_type: str = "application/json"):
        data = raw if raw is not None else json.dumps(payload)
        response = self.http.post("/rpc", data=data, content_type=content_type)
        if response.status_code == 200:
            assert response.mimetype == "application/json", response.mimetype
            RESPONSE_BODY.validate(response.get_json())
            assert_no_leak(response.get_json())
        return response

    def answer(self, payload=None, *, raw: bytes | None = None):
        response = self.post(payload, raw=raw)
        assert response.status_code == 200, response.status_code
        return response.get_json()

    def call(self, method: str, params=None, id=1):
        request = {"jsonrpc": "2.0", "method": method, "id": id}
        if params is not None:
            request["params"] = params
        return self.answer(request)
