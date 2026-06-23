"""UTF-8 safe JSON output for benchmark subprocess (tranh loi charmap Windows)."""

from __future__ import annotations

import json
import sys
from typing import Any, Dict


def emit_case_json(payload: Dict[str, Any]) -> None:
    """Ghi JSON ra stdout bang UTF-8 bytes — khong dung print() tren Windows cp1252."""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.write(b"\n")
    sys.stdout.buffer.flush()
