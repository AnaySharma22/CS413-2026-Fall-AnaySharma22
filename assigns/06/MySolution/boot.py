"""Put this folder and Assignment 5 on the import path.

assigns/05 holds the supplied lambda1_vp.py. assigns/05/MySolution holds the
Assignment 5 pretty printer and source substitution reused here.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSIGN05 = ROOT.parent.parent / "05"
for folder in (ROOT, ASSIGN05, ASSIGN05 / "MySolution"):
    entry = str(folder)
    if entry not in sys.path:
        sys.path.insert(0, entry)
