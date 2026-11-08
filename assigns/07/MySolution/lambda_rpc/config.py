"""Limits and constants shared by the transport, dispatcher, and service."""

from dataclasses import dataclass

API_VERSION = "1.0"
LIBRARIES = ("list", "optn", "a1sz", "strm")
TARGETS = ("python", "javascript")


@dataclass(frozen=True)
class Limits:
    max_body_bytes: int = 1024 * 1024
    max_source_bytes: int = 65_536
    max_batch_items: int = 20
    time_limit_seconds: float = 5.0
    # Process start and the LAMBDA3 import are not charged to the time limit.
    worker_start_seconds: float = 30.0
    recursion_limit: int = 1_000_000
    # CPython on Windows only accepts thread stacks below 256 MiB.
    stack_bytes: int = 255 * 1024 * 1024
    max_result_chars: int = 1_000_000
    max_output_chars: int = 65_536
