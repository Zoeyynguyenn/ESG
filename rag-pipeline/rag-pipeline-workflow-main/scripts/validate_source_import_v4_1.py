"""CLI wrapper for source import validation v4.1."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from golden_set.validate_source_import_v4_1 import main

if __name__ == "__main__":
    raise SystemExit(main())
