"""Run one LAMBDA3 operation in a child process that is killed at a deadline.

The LAMBDA3 interpreter is recursive and has no step budget, so the only way
to stop a long computation is to stop the process running it. Each call gets
a fresh spawned process. The parent waits for a "ready" message (sent after
LAMBDA3 is imported), then waits at most the time limit for the outcome, and
terminates the process if it is still running.

The child reports its outcome as plain data:

    {"ok": result}
    {"error": "syntax", "message", "line", "column", "source_line"}
    {"error": "type", "message"}
    {"error": "runtime", "kind", "message"}
    {"error": "too_large", "limit_chars"}
    {"internal": traceback_text}        # logged by the server, never returned

Only the service layer turns these into JSON-RPC errors.
"""

from __future__ import annotations

import io
import multiprocessing
import sys
import threading
import traceback
from contextlib import redirect_stdout
from dataclasses import dataclass

from . import lambda3_bridge
from .config import Limits

RUNTIME_ERRORS = (ArithmeticError, IndexError, ValueError)


@dataclass(frozen=True)
class Job:
    operation: str
    source: str
    libraries: tuple[str, ...] = ()
    target: str | None = None


class WorkerTimeout(Exception):
    pass


class WorkerFailure(Exception):
    """The worker could not report an outcome (failed to start or crashed)."""


class ProcessRunner:
    def __init__(self, limits: Limits):
        self.limits = limits
        self._context = multiprocessing.get_context("spawn")

    def run(self, job: Job) -> dict:
        reader, writer = self._context.Pipe(duplex=False)
        process = self._context.Process(
            target=child_main, args=(writer, job, self.limits), daemon=True
        )
        process.start()
        writer.close()
        try:
            if not reader.poll(self.limits.worker_start_seconds):
                raise WorkerFailure("worker did not start in time")
            reader.recv()
            if not reader.poll(self.limits.time_limit_seconds):
                raise WorkerTimeout()
            return reader.recv()
        except EOFError as error:
            raise WorkerFailure(
                f"worker exited without an outcome (exit code {process.exitcode})"
            ) from error
        finally:
            if process.is_alive():
                process.terminate()
                process.join(2)
                if process.is_alive():
                    process.kill()
            process.join()
            reader.close()


def child_main(conn, job: Job, limits: Limits) -> None:
    try:
        lambda3 = lambda3_bridge.load()
        sys.set_int_max_str_digits(0)
        conn.send(("ready", None))
        conn.send(_in_large_stack(lambda: execute(lambda3, job, limits), limits))
    except BaseException:
        try:
            conn.send({"internal": traceback.format_exc()})
        except BaseException:
            pass
    finally:
        conn.close()


def _in_large_stack(work, limits: Limits) -> dict:
    box: dict = {}

    def target():
        sys.setrecursionlimit(limits.recursion_limit)
        try:
            box["outcome"] = work()
        except BaseException:
            box["outcome"] = {"internal": traceback.format_exc()}

    threading.stack_size(limits.stack_bytes)
    thread = threading.Thread(target=target, name="lambda3-job")
    thread.start()
    thread.join()
    return box.get("outcome", {"internal": "worker thread produced no outcome"})


def execute(L, job: Job, limits: Limits) -> dict:
    try:
        expression, typ = analyze(L, job)
    except L.LambdaSyntaxError as error:
        return {
            "error": "syntax",
            "message": error.msg,
            "line": error.lineno,
            "column": error.offset,
            "source_line": error.text,
        }
    except L.TypeCheckError as error:
        return {"error": "type", "message": str(error)}
    except RecursionError:
        return _recursion("the source is nested too deeply to analyze")

    type_text = L.format_type(typ)
    if job.operation == "typecheck":
        return {"ok": {"type": type_text}}

    if job.operation == "compile":
        compiler = L.d0exp_compile if job.target == "python" else L.d0exp_compile_js
        try:
            code = compiler(expression)
        except RecursionError:
            return _recursion("the source is nested too deeply to compile")
        if len(code) > limits.max_result_chars:
            return {"error": "too_large", "limit_chars": limits.max_result_chars}
        return {"ok": {"target": job.target, "code": code}}

    if job.operation == "interpret":
        printed = _BoundedText(limits.max_output_chars)
        try:
            with redirect_stdout(printed):
                value = L.d0exp_evaluate(expression)
            value_text = L.d0val_format(value)
        except RecursionError:
            return _recursion("maximum recursion depth exceeded during evaluation")
        except RUNTIME_ERRORS as error:
            return {"error": "runtime", "kind": "runtime", "message": str(error)}
        if len(value_text) > limits.max_result_chars:
            return {"error": "too_large", "limit_chars": limits.max_result_chars}
        result = {"type": type_text, "value": value_text}
        if printed.text:
            result["output"] = printed.text
            if printed.truncated:
                result["output_truncated"] = True
        return {"ok": result}

    raise ValueError(f"unknown operation {job.operation!r}")


def analyze(L, job: Job):
    if not job.libraries:
        return L.d0exp_parse_and_typecheck(job.source)
    declarations = [_library_declarations(L, name) for name in job.libraries]
    expression = L.d0exp_parse(job.source)
    for block in reversed(declarations):
        expression = L.D0Elets(block, expression)
    return expression, L.d0exp_typecheck(expression)


def _library_declarations(L, name: str):
    text = (lambda3_bridge.LIBRARY_DIR / f"{name}.lam").read_text(encoding="utf-8")
    try:
        return L.d0cls_parse(text)
    except L.LambdaSyntaxError as error:
        raise RuntimeError(f"library {name} failed to parse") from error


def _recursion(message: str) -> dict:
    return {"error": "runtime", "kind": "recursion_depth", "message": message}


class _BoundedText(io.TextIOBase):
    def __init__(self, limit: int):
        self.limit = limit
        self.parts: list[str] = []
        self.size = 0
        self.truncated = False

    def writable(self) -> bool:
        return True

    def write(self, text: str) -> int:
        room = self.limit - self.size
        if len(text) > room:
            self.truncated = True
            text = text[:max(room, 0)]
        self.parts.append(text)
        self.size += len(text)
        return len(text)

    @property
    def text(self) -> str:
        return "".join(self.parts)
