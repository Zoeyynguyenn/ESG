#!/usr/bin/env python3
"""Smoke Jina Rerank API before benchmark gate."""

from __future__ import annotations

import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    for name in (".env.local", ".env"):
        p = BASE / name
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v:
                os.environ.setdefault(k, v)
        break


def main() -> int:
    _load_dotenv()
    sys.path.insert(0, str(BASE / "src"))
    from jina_rerank import DEFAULT_JINA_RERANK_MODEL, jina_api_key, rerank_scores

    key = jina_api_key()
    model = os.getenv("JINA_RERANK_MODEL", DEFAULT_JINA_RERANK_MODEL)
    print("JINA_API_KEY_set:", bool(key))
    print("JINA_RERANK_MODEL:", model)
    if not key:
        print("PREFLIGHT_FAIL: set JINA_API_KEY in .env (do not commit)")
        return 1

    scores = rerank_scores(
        "한샘 ESG governance ticker",
        [
            "ticker는 009240이다",
            "무관한 스킨케어 제품 광고",
            "manifest record_count 1161",
        ],
        model=model,
        top_n=3,
    )
    print("scores:", [round(s, 4) for s in scores])
    if max(scores) <= 0:
        print("PREFLIGHT_FAIL: empty or zero scores")
        return 1
    print("PREFLIGHT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
