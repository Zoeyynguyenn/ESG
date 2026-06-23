"""CLI wrapper for reference seed workbook v4 JSONL builder."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from golden_set.build_reference_seed_workbook_v4_jsonl import main

if __name__ == "__main__":
    raise SystemExit(main())
