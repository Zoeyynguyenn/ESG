"""CLI wrapper for freeze gold core v1."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from golden_set.freeze_gold_core_v1 import main

if __name__ == "__main__":
    raise SystemExit(main())
