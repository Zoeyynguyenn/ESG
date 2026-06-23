"""CLI wrapper for gold decision core round 4."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from golden_set.gold_decision_core_round4 import main

if __name__ == "__main__":
    raise SystemExit(main())
