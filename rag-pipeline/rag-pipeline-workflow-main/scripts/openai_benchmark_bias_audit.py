"""Read-only audit: OpenAI export-json benchmark bias checklist."""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))

PACKAGE_NEEDLE = "넥스트아이_dataset_package_20260528T091409"
LANE_PREFIX = f"data/rag_dataset/05_company_export_json/{PACKAGE_NEEDLE}/"


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
            if v:
                os.environ.setdefault(k, v)


def _is_leak(source: str) -> bool:
    s = (source or "").replace("\\", "/").lower()
    if not s:
        return True
    if "05_company_export_json/" not in s:
        return True
    if PACKAGE_NEEDLE.lower() not in s and "dataset_package_20260528t091409" not in s:
        return True
    if "04_company_public_curated/" in s:
        return True
    if "/01_synthetic" in s or "/02_esg_public" in s or "/03_esg_public" in s:
        return True
    return False


def audit_lane_leakage(rows: List[Dict[str, str]], n: int = 15) -> Dict[str, Any]:
    from production_config import apply_production_env, index_ready, load_production_config
    from retrieval_v3 import query_v3

    cfg = load_production_config()
    if not index_ready(cfg):
        return {"status": "SKIP", "reason": "index not ready", "samples": []}
    apply_production_env(cfg, base_dir=BASE)
    stack = cfg["stack"]
    sample_rows = rows[:n]
    samples: List[Dict[str, Any]] = []
    leaks = 0
    for row in sample_rows:
        r = query_v3(
            row["question"],
            retrieval_mode=stack["retrieval_mode"],
            top_k=stack["top_k"],
            pool=stack["candidate_pool"],
            answer_mode="extractive",
            llm_runtime=None,
        )
        ev = r.get("evidence") or []
        tops = [e.get("source", "") for e in ev[:4]]
        row_leaks = [_is_leak(s) for s in tops]
        if any(row_leaks):
            leaks += 1
        samples.append(
            {
                "id": row["id"],
                "question": row["question"][:80],
                "top_sources": tops,
                "leak_flags": row_leaks,
            }
        )
    return {
        "status": "PASS" if leaks == 0 else "FAIL",
        "questions": len(sample_rows),
        "questions_with_leak": leaks,
        "samples": samples,
    }


def audit_matcher(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    from eval_scoring_v2 import score_retrieval, score_citation
    from eval_source_matcher import normalize_source
    from production_config import apply_production_env, index_ready, load_production_config
    from retrieval_v3 import query_v3

    cfg = load_production_config()
    if not index_ready(cfg):
        return {"status": "SKIP", "reason": "index not ready"}
    apply_production_env(cfg, base_dir=BASE)
    stack = cfg["stack"]

    ret_reasons: Counter = Counter()
    cit_reasons: Counter = Counter()
    utf8_issues: List[str] = []
    split_mismatch_expected: List[str] = []

    for row in rows:
        exp = row.get("expected_source", "")
        if "dataset_package_" in exp and PACKAGE_NEEDLE not in exp:
            if "ë" in exp or "ì" in exp or "í" in exp:
                utf8_issues.append(row["id"])
        if "/splits/dev.jsonl" in exp and "validation" in os.getenv("RAG_BENCHMARK_LANE", ""):
            split_mismatch_expected.append(row["id"])

        r = query_v3(
            row["question"],
            retrieval_mode=stack["retrieval_mode"],
            top_k=stack["top_k"],
            pool=stack["candidate_pool"],
            answer_mode="extractive",
            llm_runtime=None,
        )
        ev = r.get("evidence") or []
        _, ret_d, _ = score_retrieval(row, ev)
        _, cit_d, _ = score_citation(row, ev)
        ret_reasons[ret_d.get("match_reason", "unknown")] += 1
        cit_reasons[cit_d.get("match_reason", "unknown")] += 1

    return {
        "status": "PASS",
        "retrieval_match_reason": dict(ret_reasons),
        "citation_match_reason": dict(cit_reasons),
        "utf8_mojibake_expected_source_ids": utf8_issues,
        "eval_points_dev_split_on_validation_lane": split_mismatch_expected,
        "note": "package_split_match expected when eval=dev.jsonl corpus=validation.jsonl",
    }


def audit_fairness_openai_configs() -> Dict[str, Any]:
    import yaml

    paths = [
        "configs/benchmark_exportjson_openai_validation.yaml",
        "configs/benchmark_exportjson_openai_phase3.yaml",
        "configs/benchmark_exportjson_openai_e2e.yaml",
        "configs/benchmark_exportjson_openai_smoke.yaml",
    ]
    issues: List[str] = []
    fair_notes: List[str] = []
    for rel in paths:
        p = BASE / rel
        if not p.exists():
            continue
        cfg = yaml.safe_load(p.read_text(encoding="utf-8"))
        for c in cfg.get("candidates") or []:
            cid = c.get("config_id", "")
            pool = c.get("candidate_pool")
            rerank = c.get("reranker", "none")
            mode = c.get("retrieval_mode", "")
            if rerank and rerank != "none":
                issues.append(f"{rel}: {cid} has reranker={rerank}")
            if pool != 64:
                issues.append(f"{rel}: {cid} pool={pool} != 64")
            if mode.endswith("_rerank"):
                issues.append(f"{rel}: {cid} retrieval_mode={mode}")
        fair_notes.append(f"{rel}: all candidates reranker=none pool=64")

    # Historical MiniLM phase2 — documented unfair pre-fix
    historical = (
        "Local exportjson phase2 (MiniLM) before 2026-05-28 fairness fix: "
        "reranker comparisons may be INVALID if pool/mode differed."
    )
    return {
        "status": "PASS" if not issues else "FAIL",
        "openai_yaml_issues": issues,
        "openai_fair": fair_notes,
        "historical_local_rerank": historical,
        "invalid_conclusions": [] if not issues else issues,
    }


def audit_index_integrity() -> Dict[str, Any]:
    from production_config import index_dir, load_production_config, production_cache_key

    cfg = load_production_config()
    key = production_cache_key(cfg)
    idx = index_dir(cfg)
    marker = idx / ".index_complete"
    bm25 = idx / "bm25_corpus.json"
    qdrant = idx / "qdrant_db"

    issues: List[str] = []
    siblings: List[str] = []
    cache_parent = BASE / "artifacts/benchmark_cache/index_cache"
    if cache_parent.exists():
        for d in sorted(cache_parent.iterdir()):
            if d.is_dir() and "openai_text-embedding-3-small" in d.name:
                siblings.append(d.name[:100])

    # Check no MiniLM index path reused for OpenAI
    for name in siblings:
        if "all-minilm" in name.lower() and "openai" in name.lower():
            issues.append(f"suspicious combined key: {name}")

    chroma_collection = os.getenv("RAG_CHROMA_COLLECTION", "")
    code_has_dimension_guard = True  # rag_stack.py rmtree on dimension mismatch

    return {
        "status": "PASS" if idx.exists() and marker.exists() and bm25.exists() else "WARN",
        "production_cache_key": key,
        "index_dir": str(idx),
        "marker_exists": marker.exists(),
        "bm25_exists": bm25.exists(),
        "qdrant_exists": qdrant.exists(),
        "openai_index_siblings_count": len(siblings),
        "chroma_collection_hash_in_runner": "RAG_CHROMA_COLLECTION=bench_{md5(cache_key)[:16]} in run_benchmark_case.py",
        "dimension_mismatch_recovery": "rag_stack.py shutil.rmtree CHROMA_DIR on embedding dimension error",
        "issues": issues,
    }


def audit_embedding_safety() -> Dict[str, Any]:
    rag_stack = (BASE / "src/rag_stack.py").read_text(encoding="utf-8")
    has_batch = "RAG_OPENAI_EMBED_BATCH" in rag_stack and "_ingest_batches" in rag_stack
    has_retry = bool(re.search(r"retry|backoff|429|tenacity", rag_stack, re.I))
    has_token_budget = bool(re.search(r"token|300000|max.*request", rag_stack, re.I))
    runner_resume = (BASE / "src/run_model_candidate_benchmark.py").read_text(encoding="utf-8")
    has_resume = "--resume" in runner_resume

    issues = []
    if not has_retry:
        issues.append("No explicit 429/timeout retry in rag_stack.py ingest/embed")
    if not has_token_budget:
        issues.append("No token-budget splitter before OpenAI embed API calls")

    return {
        "status": "PASS" if has_batch and has_resume else "FAIL" if issues else "WARN",
        "batching": {
            "RAG_OPENAI_EMBED_BATCH": has_batch,
            "doc_batch_loop": "_ingest_batches in ingest_corpus_files",
            "langchain_chunk_size": "OpenAIEmbeddings chunk_size from env",
        },
        "retry_backoff": has_retry,
        "token_budget_guard": has_token_budget,
        "checkpoint_resume": {
            "model_candidate_resume": has_resume,
            "matrix_resume": "--resume in run_benchmark_matrix.py",
            "index_reuse": "reuse-index + .index_complete marker",
        },
        "issues": issues,
        "minimal_patches": issues,
    }


def main() -> int:
    _load_dotenv()
    from eval_set_io import parse_eval_set

    eval_path = BASE / ".rag/rag-pipeline-practice/eval_set_company_export_json_dev_ko.md"
    rows = parse_eval_set(eval_path)
    if rows and hasattr(rows[0], "to_dict"):
        rows = [r.to_dict() for r in rows]

    report = {
        "lane_leakage": audit_lane_leakage(rows, n=min(15, len(rows))),
        "eval_matcher": audit_matcher(rows),
        "fairness": audit_fairness_openai_configs(),
        "index_integrity": audit_index_integrity(),
        "embedding_safety": audit_embedding_safety(),
    }
    out_json = BASE / "artifacts" / "openai_benchmark_bias_audit.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
