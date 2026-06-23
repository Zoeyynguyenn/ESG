#!/usr/bin/env python3
"""Pre-download FlashRank ONNX model into artifacts/tmp/flashrank (offline rerank)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pre-seed FlashRank model cache")
    parser.add_argument(
        "--model",
        default=os.getenv("RAG_RERANK_MODEL", "ms-marco-MultiBERT-L-12"),
        help="FlashRank model name (default: ms-marco-MultiBERT-L-12)",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    cache_dir = root / "artifacts" / "tmp" / "flashrank"
    cache_dir.mkdir(parents=True, exist_ok=True)
    tmp_str = str(cache_dir)
    os.environ["TMPDIR"] = tmp_str
    os.environ["TMP"] = tmp_str
    os.environ["TEMP"] = tmp_str

    sys.path.insert(0, str(root / "src"))
    try:
        from flashrank import Ranker
    except ImportError:
        print("ERROR: pip install flashrank>=0.2.10", file=sys.stderr)
        return 1

    print(f"Downloading FlashRank model={args.model} cache_dir={cache_dir}")
    try:
        from flashrank import RerankRequest

        ranker = Ranker(model_name=args.model, cache_dir=tmp_str)
        probe = ranker.rerank(
            RerankRequest(
                query="테스트",
                passages=[{"id": 0, "text": "한샘 ESG governance policy"}],
            )
        )
        status = "flashrank"
        if not probe:
            print("WARN: rerank probe returned empty", file=sys.stderr)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    files = list(cache_dir.rglob("*"))
    print(f"OK: {status} model={args.model} cache_files={len(files)} dir={cache_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
