"""Generate Phase 2/3 configs from prior phase benchmark results."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, List

import yaml


def _safe_float(value: Any) -> float:
    try:
        if value in (None, ""):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def _load_ranked(path: Path, top_n: int) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("status") == "success"]
    rows.sort(key=lambda r: _safe_float(r.get("composite_score")), reverse=True)
    return rows[:top_n]


def _base_config(benchmark_id: str, lane: str, corpus_version: str, description: str) -> Dict[str, Any]:
    return {
        "benchmark_id": benchmark_id,
        "description": description,
        "lane": lane,
        "eval_set_path": ".rag/rag-pipeline-practice/eval_set_company_export_json_dev_ko.md",
        "corpus_version": corpus_version,
        "parser_version": "jsonl_v1",
        "cache_root": "artifacts/benchmark_cache",
        "lane_config": {
            "corpus_ratio": 1.0,
            "company_filter": "넥스트아이_dataset_package_20260528T091409",
            "pdf_parser": "pypdf",
            "eval_questions": 20,
            "chunking_profile": "recursive_800_120",
            "chunk_size": 800,
            "chunk_overlap": 120,
            "top_k": 4,
        },
        "timeouts": {
            "default_sec": 1200,
            "embedding_heavy_sec": 1800,
        },
        "scoring": {
            "retrieval_hit_rate": 0.30,
            "citation_correctness": 0.20,
            "answer_correctness": 0.15,
            "insufficient_information_handling": 0.10,
            "groundedness": 0.10,
            "latency_normalized": 0.10,
            "stability_penalty": 0.05,
        },
        "candidates": [],
    }


def _candidate_from_row(
    row: Dict[str, str],
    config_id: str,
    *,
    rerank: bool,
    vector_store: str,
    fair_pool: int = 64,
) -> Dict[str, Any]:
    chunking = row.get("chunking") or "recursive_800_120"
    chunk_size = 512 if "512" in chunking else 800
    chunk_overlap = 80 if "512" in chunking else 120
    retrieval_mode = row.get("retrieval_mode") or "hybrid_dense_bm25"
    if rerank:
        if retrieval_mode == "semantic_dense":
            retrieval_mode = "semantic_dense_rerank"
        elif retrieval_mode == "hybrid_dense_bm25":
            retrieval_mode = "hybrid_dense_bm25_rerank"
        elif retrieval_mode.endswith("_rerank"):
            pass
        else:
            retrieval_mode = "hybrid_dense_bm25_rerank"
    embedding_model = row.get("embedding_model") or "sentence-transformers/all-MiniLM-L6-v2"
    candidate = {
        "config_id": config_id,
        "chunking_profile": chunking,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "embedding_model": embedding_model,
        "retrieval_mode": retrieval_mode,
        "reranker": "cross_encoder_minilm" if rerank else "none",
        "vector_store": vector_store,
        "candidate_pool": fair_pool,
    }
    if rerank:
        candidate["reranker_model"] = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    if embedding_model != "sentence-transformers/all-MiniLM-L6-v2":
        candidate["embedding_heavy"] = True
    return candidate


def build_phase2(phase1_csv: Path, out: Path, top_n: int) -> None:
    rows = _load_ranked(phase1_csv, top_n)
    cfg = _base_config(
        "benchmark_exportjson_phase2",
        "company_export_json_validation",
        "nexteye_esg_v1_1_1_validation",
        "Phase 2 - compare reranker on top retrieval configs from Phase 1.",
    )
    for idx, row in enumerate(rows, 1):
        base_id = row["config_id"].replace("p1_", f"p2_top{idx}_")
        cfg["candidates"].append(
            _candidate_from_row(row, base_id + "_none", rerank=False, vector_store="chroma", fair_pool=64)
        )
        cfg["candidates"].append(
            _candidate_from_row(row, base_id + "_rerank", rerank=True, vector_store="chroma", fair_pool=64)
        )
    out.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")


def build_phase3(phase2_csv: Path, out: Path, top_n: int) -> None:
    rows = _load_ranked(phase2_csv, top_n)
    cfg = _base_config(
        "benchmark_exportjson_phase3",
        "company_export_json_full",
        "nexteye_esg_v1_1_1_full",
        "Phase 3 - compare Chroma and Qdrant on top configs from Phase 2.",
    )
    for idx, row in enumerate(rows, 1):
        rerank = (row.get("reranker") or "") != "none" or row.get("retrieval_mode") == "hybrid_dense_bm25_rerank"
        base_id = row["config_id"].replace("p2_", f"p3_top{idx}_")
        cfg["candidates"].append(_candidate_from_row(row, base_id + "_chroma", rerank=rerank, vector_store="chroma"))
        cfg["candidates"].append(_candidate_from_row(row, base_id + "_qdrant", rerank=rerank, vector_store="qdrant"))
    out.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["phase2", "phase3"], required=True)
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-config", required=True)
    parser.add_argument("--top-n", type=int, default=3)
    args = parser.parse_args()

    src = Path(args.input_csv)
    out = Path(args.output_config)
    if args.phase == "phase2":
        build_phase2(src, out, args.top_n)
    else:
        build_phase3(src, out, args.top_n)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
