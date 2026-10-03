"""Restricted constructor reader and the replaceable language-tool adapter."""

import ast
import json
import subprocess
import sys
from pathlib import Path

ASSIGN_DIR = Path(__file__).resolve().parent.parent
if str(ASSIGN_DIR) not in sys.path:
    sys.path.insert(0, str(ASSIGN_DIR))

import lambda1 as lang

MAX_BYTES = 65536
TIMEOUT_SECONDS = 3

SCHEMA = {
    "D0Eint": (int,),
    "D0Ebtf": (bool,),
    "D0Evar": (str,),
    "D0Eop1": (str, "expr"),
    "D0Eop2": (str, "expr", "expr"),
    "D0Elam": (str, "expr"),
    "D0Efix": (str, str, "expr"),
    "D0Eapp": ("expr", "expr"),
    "D0Eif0": ("expr", "expr", "expr"),
    "D0Elet": (str, "expr", "expr"),
    "D0Epair": ("expr", "expr"),
    "D0Epfst": ("expr",),
    "D0Epsnd": ("expr",),
}


def read_source(source):
    """Build one d0exp from a constructor expression. Do not run the source."""
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Source cannot be empty or whitespace.")
    if len(source.encode("utf-8")) > MAX_BYTES:
        raise ValueError("Source exceeds the 65,536-byte limit.")
    tree = ast.parse(source, mode="eval")
    return _read(tree.body, "expr")


def _read(node, expected):
    if expected != "expr":
        return _literal(node, expected)
    if (
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id not in SCHEMA
        or node.keywords
    ):
        raise ValueError(
            "Use one supported D0E constructor call. "
            "Imports, operators, and other Python are not allowed."
        )
    schema = SCHEMA[node.func.id]
    if len(node.args) != len(schema):
        raise ValueError(
            f"{node.func.id} expects {len(schema)} positional arguments."
        )
    args = [_read(arg, kind) for arg, kind in zip(node.args, schema)]
    return getattr(lang, node.func.id)(*args)


def _literal(node, expected):
    if (
        expected is int
        and isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and type(node.operand.value) is int
    ):
        return -node.operand.value
    if isinstance(node, ast.Constant) and type(node.value) is expected:
        return node.value
    raise ValueError(f"Expected a {expected.__name__} literal.")


def _contains_error_sentinel(value):
    if type(value) is lang.D0V000:
        return True
    if isinstance(value, lang.D0Vpair):
        return _contains_error_sentinel(value.arg1) or _contains_error_sentinel(value.arg2)
    return False


def perform(operation, source):
    """Run one language operation in this process. Outcomes are never implied."""
    if operation == "typecheck":
        return {
            "outcome": "not_implemented",
            "text": "Type checking is not yet implemented.",
        }
    if operation == "compile":
        return {
            "outcome": "not_implemented",
            "text": "Compilation is not yet implemented.",
        }
    if operation == "execute":
        return {
            "outcome": "not_implemented",
            "text": (
                "Execute is for generated code and is unavailable until "
                "compilation is implemented and produces an artifact."
            ),
        }
    try:
        expr = read_source(source)
    except (ValueError, SyntaxError, RecursionError) as error:
        return {"outcome": "input_error", "text": str(error)}
    try:
        if operation == "lint":
            names = sorted(lang.d0exp_fvset(expr))
            if names:
                return {
                    "outcome": "language_error",
                    "text": "Undeclared variables: " + ", ".join(names),
                }
            return {
                "outcome": "success",
                "text": "No free variables were found.",
            }
        if operation != "interpret":
            raise ValueError("Unknown operation.")
        value = lang.d0exp_evaluate(expr, lang.ENVnil())
        if _contains_error_sentinel(value):
            return {
                "outcome": "runtime_error",
                "text": "Evaluation returned an undefined value (D0V000).",
            }
        return {"outcome": "success", "text": repr(value)}
    except Exception as error:
        return {
            "outcome": "runtime_error",
            "text": f"{type(error).__name__}: {error}",
        }


def run_bounded(command, source, timeout):
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        stdout, _stderr = process.communicate(source.encode("utf-8"), timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        return {
            "outcome": "backend_error",
            "text": (
                f"Stopped after the {TIMEOUT_SECONDS:g}-second limit. "
                "The applied source is unchanged; edit the program or retry."
            ),
        }
    if process.returncode != 0:
        return {
            "outcome": "backend_error",
            "text": "The language worker failed. The applied source is unchanged; retry.",
        }
    try:
        payload = json.loads(stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return {
            "outcome": "backend_error",
            "text": "The language worker returned an unreadable result. Retry.",
        }
    if not isinstance(payload, dict) or "outcome" not in payload or "text" not in payload:
        return {
            "outcome": "backend_error",
            "text": "The language worker returned an incomplete result. Retry.",
        }
    return {"outcome": payload["outcome"], "text": payload["text"]}


class Backend:
    """Adapter the controller calls. A test can pass bounded=False."""

    def __init__(self, timeout=TIMEOUT_SECONDS, bounded=True):
        self.timeout = timeout
        self.bounded = bounded

    def run(self, operation, source):
        if not self.bounded:
            return perform(operation, source)
        return run_bounded(
            [sys.executable, str(Path(__file__).resolve()), operation],
            source,
            self.timeout,
        )


if __name__ == "__main__":
    operation = sys.argv[1]
    source = sys.stdin.buffer.read().decode("utf-8")
    print(json.dumps(perform(operation, source)))
