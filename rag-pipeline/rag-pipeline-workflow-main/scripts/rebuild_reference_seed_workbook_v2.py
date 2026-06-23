"""CLI wrapper for reference seed workbook rebuild v2."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from golden_set.rebuild_reference_seed_workbook_v2 import main

if __name__ == "__main__":
    raise SystemExit(main())
