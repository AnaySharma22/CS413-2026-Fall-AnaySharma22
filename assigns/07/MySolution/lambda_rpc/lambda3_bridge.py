"""Locate and import the provided LAMBDA3 implementation without modifying it."""

import sys
from pathlib import Path
from types import ModuleType

LAMBDA3_DIR = Path(__file__).resolve().parents[2] / "LAMBDA3"
LIBRARY_DIR = LAMBDA3_DIR / "mylib"


def load() -> ModuleType:
    if str(LAMBDA3_DIR) not in sys.path:
        sys.path.insert(0, str(LAMBDA3_DIR))
    import lambda3

    return lambda3
