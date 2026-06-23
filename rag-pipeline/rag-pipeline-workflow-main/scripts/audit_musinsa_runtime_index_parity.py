#!/usr/bin/env python3
"""Runtime vs expected index parity audit for Musinsa (no retrieve API for GT conclusions)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

GT_RECORD = "rec_27e2235c5c45f84a"
GT_ANCHOR = "1891명"


def _scan_chunks(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    texts = [c.get("text", "") if isinstance(c, dict) else str(c) for c in chunks]
    return {
        "chunk_count": len(chunks),
        "has_1891": any("1891" in t for t in texts),
        "has_1891myeong": any(GT_ANCHOR in t for t in texts),
        "has_gt_record_id": any(GT_RECORD in t for t in texts),
        "anchor_snippet": next(
            (t[max(0, t.find(GT_ANCHOR) - 60) : t.find(GT_ANCHOR) + 60] for t in texts if GT_ANCHOR in t),
            "",
        ),
    }


def _runtime_snapshot(company_id: str = "musinsa") -> Dict[str, Any]:
    from evidence_api.env_bootstrap import load_repo_dotenv
    from evidence_api.staging_config import apply_company_env, company_cfg, company_registry, load_staging_config
    from production_config import cached_bm25_chunk_count, expected_bm25_chunk_count, index_dir, production_cache_key

    load_repo_dotenv()
    cfg = load_staging_config()
    entry = company_registry(cfg)[company_id]
    ccfg = company_cfg(cfg, company_id)
    apply_company_env(cfg, company_id, base_dir=ROOT)
    idx = index_dir(ccfg)
    bm25_path = idx / "bm25_corpus.json"
    chunks: List[Dict[str, Any]] = []
    if bm25_path.exists():
        data = json.loads(bm25_path.read_text(encoding="utf-8"))
        chunks = data.get("chunks", []) if isinstance(data, dict) else data

    pkg = entry["package"]
    return {
        "company_id": company_id,
        "package": pkg,
        "package_full_jsonl": str(
            ROOT / "data/rag_dataset/05_company_export_json" / pkg / "splits/full.jsonl"
        ),
        "manifest_path": os.getenv("RAG_BENCHMARK_CORPUS_MANIFEST", ""),
        "cache_key": production_cache_key(ccfg),
        "index_dir": str(idx),
        "bm25_path": str(bm25_path),
        "qdrant_path": str(idx / "qdrant_db"),
        "index_marker": (idx / ".index_complete").read_text(encoding="utf-8").strip()
        if (idx / ".index_complete").exists()
        else "",
        "cached_bm25": _scan_chunks(chunks),
        "expected_build_chunks": {
            "chunk_count": expected_bm25_chunk_count(base_dir=ROOT),
            **_scan_chunks(
                [{"text": c.text} for c in __import__("rag_common", fromlist=["build_chunks"]).build_chunks(ROOT)]
            ),
        },
        "cached_bm25_chunk_count_fn": cached_bm25_chunk_count(ccfg),
    }


def main() -> int:
    snap = _runtime_snapshot()
    out_json = ROOT / "reports" / "musinsa_runtime_index_parity.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    c = snap["cached_bm25"]
    e = snap["expected_build_chunks"]
    print("cached chunks", c["chunk_count"], "expected", e["chunk_count"])
    print("cached 1891명", c["has_1891myeong"], "expected 1891명", e["has_1891myeong"])
    print(f"Wrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
