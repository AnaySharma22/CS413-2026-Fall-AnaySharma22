"""JSON-RPC 2.0 envelope handling, independent of the web framework and of LAMBDA3.

`Dispatcher.handle_body` takes the raw request body and returns either a
JSON-serializable response (an object or a list) or None when nothing must
be sent back (a notification, or a batch of only notifications).
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .config import Limits
from .errors import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    RpcError,
)

log = logging.getLogger("lambda_rpc")

REQUEST_MEMBERS = {"jsonrpc", "method", "params", "id"}
_NO_ID = object()


@dataclass(frozen=True)
class Request:
    method: str
    params: dict | list
    id: Any

    @property
    def is_notification(self) -> bool:
        return self.id is _NO_ID


class _InvalidRequest(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class Dispatcher:
    def __init__(self, methods: Mapping[str, Callable[[dict], Any]], limits: Limits):
        self.methods = dict(methods)
        self.limits = limits

    def handle_body(self, body: bytes) -> dict | list | None:
        try:
            payload = json.loads(body.decode("utf-8"), parse_constant=_reject_constant)
        except RecursionError:
            return error_response(None, RpcError(PARSE_ERROR, {"reason": "nesting_too_deep"}))
        except (UnicodeDecodeError, ValueError):
            return error_response(None, RpcError(PARSE_ERROR, {"reason": "invalid_json"}))

        if not isinstance(payload, list):
            return self.handle_one(payload)
        if not payload:
            return _invalid(None, "empty_batch")
        if len(payload) > self.limits.max_batch_items:
            return _invalid(None, "batch_too_large", limit=self.limits.max_batch_items)
        responses = [response for item in payload if (response := self.handle_one(item)) is not None]
        return responses or None

    def handle_one(self, item: Any) -> dict | None:
        try:
            request = parse_request(item)
        except _InvalidRequest as invalid:
            return _invalid(None, invalid.reason)

        try:
            result = self.call(request)
        except RpcError as error:
            response = error_response(request.id, error)
        else:
            response = {"jsonrpc": "2.0", "id": request.id, "result": result}
        return None if request.is_notification else response

    def call(self, request: Request) -> Any:
        handler = self.methods.get(request.method)
        if handler is None:
            raise RpcError(METHOD_NOT_FOUND, {"method": request.method})
        if not isinstance(request.params, dict):
            raise RpcError(INVALID_PARAMS, {"param": None, "reason": "params_not_object"})
        try:
            return handler(request.params)
        except RpcError:
            raise
        except Exception as error:
            reference = uuid.uuid4().hex[:12]
            detail = getattr(error, "detail", "")
            log.exception(
                "internal error reference=%s method=%s %s", reference, request.method, detail
            )
            raise RpcError(INTERNAL_ERROR, {"reference": reference}) from None


def parse_request(item: Any) -> Request:
    if not isinstance(item, dict):
        raise _InvalidRequest("not_an_object")
    unknown = set(item) - REQUEST_MEMBERS
    if unknown:
        raise _InvalidRequest("unknown_member")
    if item.get("jsonrpc") != "2.0":
        raise _InvalidRequest("jsonrpc_must_be_2.0")
    if not isinstance(item.get("method"), str):
        raise _InvalidRequest("method_must_be_string")
    params = item.get("params", {})
    if not isinstance(params, (dict, list)):
        raise _InvalidRequest("params_must_be_object_or_array")
    request_id = item.get("id", _NO_ID)
    if request_id is not _NO_ID and not _valid_id(request_id):
        raise _InvalidRequest("invalid_id")
    return Request(item["method"], params, request_id)


def error_response(request_id: Any, error: RpcError) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": error.to_object()}


def _invalid(request_id: Any, reason: str, **extra) -> dict:
    return error_response(request_id, RpcError(INVALID_REQUEST, {"reason": reason, **extra}))


def _valid_id(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    return value is None or isinstance(value, (str, int, float))


def _reject_constant(name: str):
    raise ValueError(f"{name} is not valid JSON")
