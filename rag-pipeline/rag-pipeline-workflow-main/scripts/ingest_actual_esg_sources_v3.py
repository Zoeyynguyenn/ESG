"""CLI wrapper for actual ESG source ingest v3."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from golden_set.ingest_actual_esg_sources_v3 import main

if __name__ == "__main__":
    raise SystemExit(main())
