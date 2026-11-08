"""The service layer: validate method params, run LAMBDA3, map outcomes to RPC errors.

It knows nothing about HTTP or the JSON-RPC envelope. Each method takes the
params object and returns a result object or raises RpcError.
"""

from __future__ import annotations

from collections.abc import Callable

from .config import API_VERSION, LIBRARIES, TARGETS, Limits
from .errors import (
    EXECUTION_TIMEOUT,
    LAMBDA_RUNTIME_ERROR,
    LAMBDA_SYNTAX_ERROR,
    LAMBDA_TYPE_ERROR,
    RESULT_TOO_LARGE,
    RpcError,
    invalid_params,
)
from .worker import Job, ProcessRunner, WorkerTimeout


class ServiceFault(Exception):
    """The worker reported an unexpected failure. The detail is for the server log."""

    def __init__(self, detail: str):
        super().__init__("LAMBDA3 worker failed unexpectedly")
        self.detail = detail


class LambdaService:
    def __init__(self, runner=None, limits: Limits | None = None):
        self.limits = limits or Limits()
        self.runner = runner or ProcessRunner(self.limits)

    def methods(self) -> dict[str, Callable[[dict], dict]]:
        return {
            "service.health": self.health,
            "lambda.typecheck": self.typecheck,
            "lambda.interpret": self.interpret,
            "lambda.compile": self.compile,
        }

    def health(self, params: dict) -> dict:
        _reject_unknown(params, set())
        return {"status": "ok", "version": API_VERSION}

    def typecheck(self, params: dict) -> dict:
        return self._run(self._job("typecheck", params, {"source", "libraries"}))

    def interpret(self, params: dict) -> dict:
        return self._run(self._job("interpret", params, {"source", "libraries"}))

    def compile(self, params: dict) -> dict:
        job = self._job("compile", params, {"source", "target", "libraries"})
        return self._run(job)

    def _job(self, operation: str, params: dict, allowed: set[str]) -> Job:
        _reject_unknown(params, allowed)
        source = self._source(params)
        libraries = _libraries(params)
        target = _target(params) if "target" in allowed else None
        return Job(operation, source, libraries, target)

    def _source(self, params: dict) -> str:
        if "source" not in params:
            raise invalid_params("source", "missing")
        source = params["source"]
        if not isinstance(source, str):
            raise invalid_params("source", "not_a_string")
        if not source.strip():
            raise invalid_params("source", "blank")
        limit = self.limits.max_source_bytes
        if len(source.encode("utf-8", "surrogatepass")) > limit:
            raise invalid_params("source", "too_large", limit_bytes=limit)
        return source

    def _run(self, job: Job) -> dict:
        try:
            outcome = self.runner.run(job)
        except WorkerTimeout:
            raise RpcError(
                EXECUTION_TIMEOUT, {"limit_seconds": self.limits.time_limit_seconds}
            ) from None
        if "ok" in outcome:
            return outcome["ok"]
        if "internal" in outcome:
            raise ServiceFault(outcome["internal"])
        kind = outcome["error"]
        if kind == "syntax":
            return _raise(LAMBDA_SYNTAX_ERROR, {
                "message": outcome["message"],
                "line": outcome["line"],
                "column": outcome["column"],
                "source_line": outcome["source_line"],
            })
        if kind == "type":
            return _raise(LAMBDA_TYPE_ERROR, {"message": outcome["message"]})
        if kind == "runtime":
            return _raise(LAMBDA_RUNTIME_ERROR, {
                "message": outcome["message"],
                "kind": outcome["kind"],
            })
        if kind == "too_large":
            return _raise(RESULT_TOO_LARGE, {"limit_chars": outcome["limit_chars"]})
        raise ServiceFault(f"unrecognized worker outcome {outcome!r}")


def _raise(code: int, data: dict):
    raise RpcError(code, data)


def _reject_unknown(params: dict, allowed: set[str]) -> None:
    for name in params:
        if name not in allowed:
            raise invalid_params(name, "unknown_param")


def _target(params: dict) -> str:
    if "target" not in params:
        raise invalid_params("target", "missing", allowed=list(TARGETS))
    target = params["target"]
    if target not in TARGETS:
        raise invalid_params("target", "unsupported", allowed=list(TARGETS))
    return target


def _libraries(params: dict) -> tuple[str, ...]:
    names = params.get("libraries", [])
    valid = (
        isinstance(names, list)
        and all(isinstance(name, str) and name in LIBRARIES for name in names)
        and len(set(names)) == len(names)
    )
    if not valid:
        raise invalid_params("libraries", "invalid", allowed=list(LIBRARIES))
    return tuple(names)
