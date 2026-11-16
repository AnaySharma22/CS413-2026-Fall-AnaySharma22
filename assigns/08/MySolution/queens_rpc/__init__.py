"""JSON-RPC service for the animated N-Queens CPS solver."""

from .app import create_app
from .config import Limits

__all__ = ["create_app", "Limits"]
