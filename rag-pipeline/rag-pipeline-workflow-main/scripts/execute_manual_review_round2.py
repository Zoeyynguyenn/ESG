"""CLI wrapper for manual review round 2 execution."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from golden_set.execute_manual_review_round2 import main

if __name__ == "__main__":
    raise SystemExit(main())
