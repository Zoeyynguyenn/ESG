"""CLI wrapper for RTX lane chunking."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rtx_chunking.build_rtx_chunked_corpus import main

if __name__ == "__main__":
    raise SystemExit(main())
