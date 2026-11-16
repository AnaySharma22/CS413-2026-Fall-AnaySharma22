"""Limits and constants for the queens JSON-RPC service."""

from dataclasses import dataclass

API_VERSION = "1.0"
MIN_SIZE = 4
MAX_SIZE = 10
MIN_LIMIT = 1
MAX_LIMIT = 32


@dataclass(frozen=True)
class Limits:
    max_body_bytes: int = 1024 * 1024
    stream_idle_seconds: float = 600.0
    max_batch_items: int = 20
