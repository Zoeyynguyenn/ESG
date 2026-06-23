"""Run mot benchmark case don le (stage-wise, lane-aware, cache-aware)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from benchmark_io import emit_case_json

INDEX_COMPLETE_MARKER = ".index_complete"


def _index_cache_ready(store_dir: Path, bm25_path: Path) -> bool:
    marker = store_dir.parent / INDEX_COMPLETE_MARKER
    has_store = store_dir.exists() and any(store_dir.rglob("*"))
    has_bm25 = bm25_path.exists()
    if not (has_store and has_bm25):
        return False
    # Backward-compatible: cache tao truoc khi co marker van duoc reuse.
    if marker.exists():
        return True
    return True


def _model_available_local(model_name: str) -> tuple[bool, str]:
    from embedding_providers import api_embedding_available, is_api_embedding_model

    if is_api_embedding_model(model_name):
        return api_embedding_available(model_name)
    try:
        from sentence_transformers import SentenceTransformer

        SentenceTransformer(model_name, local_files_only=True)
        return True, "cached_local"
    except Exception as exc:
        return False, f"model_not_cached_local:{exc}"


def _deterministic_pick(items: List[str], ratio: float) -> List[str]:
    if ratio >= 1.0:
        return items
    count = max(1, int(len(items) * ratio))
    sorted_items = sorted(items, key=lambda x: hashlib.md5(x.encode("utf-8")).hexdigest())
    return sorted(sorted_items[:count])


def _prepare_corpus_manifest(
    base_dir: Path,
    lane: str,
    ratio: float,
    cache_root: Path,
    company_filter: str = "",
) -> Path:
    from rag_common import iter_corpus_files

    all_files = [str(p.relative_to(base_dir)).replace("\\", "/") for p in iter_corpus_files()]
    if company_filter:
        if lane.startswith("company_export_json"):
            package = company_filter.strip("/")
            split_name = "dev"
            if lane.endswith("_validation"):
                split_name = "validation"
            elif lane.endswith("_full"):
                split_name = "full"
            split_path = f"data/rag_dataset/05_company_export_json/{package}/splits/{split_name}.jsonl"
            if split_path in all_files:
                picked_base = [split_path]
            else:
                needle = f"data/rag_dataset/05_company_export_json/{package}/"
                picked_base = [p for p in all_files if p.startswith(needle)]
            extras = [
                f"data/rag_dataset/05_company_export_json/{package}/manifest.json",
                f"data/rag_dataset/05_company_export_json/{package}/README.md",
            ]
            all_files = list(picked_base)
            for ep in extras:
                if (base_dir / ep).exists() and ep not in all_files:
                    all_files.append(ep)
        elif lane.startswith("rtx_references"):
            lane_id = company_filter.strip("/") or "06_rtx_references_raw"
            chunk_path = f"data/rag_dataset/{lane_id}/chunks/rtx_chunked_corpus.jsonl"
            all_files = [chunk_path] if (base_dir / chunk_path).exists() else []
        else:
            needle = f"data/rag_dataset/04_company_public_curated/{company_filter.strip('/')}/"
            all_files = [p for p in all_files if p.startswith(needle)]
    picked = _deterministic_pick(all_files, ratio)
    manifest_name = f"corpus_{lane}"
    if company_filter:
        company_hash = hashlib.md5(company_filter.encode("utf-8")).hexdigest()[:10]
        manifest_name += f"_company_{company_hash}"
    manifest = cache_root / "manifests" / f"{manifest_name}.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {"lane": lane, "company_filter": company_filter, "files": picked},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest


def _load_eval_rows(eval_max_questions: int, eval_path: Path | None = None) -> List[Dict[str, str]]:
    from eval_set_io import parse_eval_set

    rows = parse_eval_set(eval_path) if eval_path else parse_eval_set()
    rows = sorted(rows, key=lambda r: r["id"])
    if eval_max_questions <= 0 or eval_max_questions >= len(rows):
        return rows
    return rows[:eval_max_questions]


def _run_retrieval_eval(
    rows: List[Dict[str, str]],
    retrieval_mode: str,
    top_k: int,
    pool: int,
    *,
    answer_mode: str = "extractive",
    llm_runtime: Any = None,
    collect_audit: bool = False,
) -> Dict[str, Any]:
    from eval_scoring_v2 import aggregate_metrics_v2, score_result_v2
    from retrieval_v3 import query_v3

    evaluated: List[Dict[str, Any]] = []
    audit_samples: List[Dict[str, Any]] = []
    query_times: List[float] = []
    reranker_effective_model = ""

    for row in rows:
        t0 = time.perf_counter()
        record_hint = (row.get("extracted_field") or "").strip()
        if not record_hint.startswith("rec_"):
            record_hint = ""
        result = query_v3(
            row["question"],
            retrieval_mode=retrieval_mode,
            top_k=top_k,
            pool=pool,
            answer_mode=answer_mode,
            llm_runtime=llm_runtime,
            record_id_hint=record_hint,
        )
        query_times.append(time.perf_counter() - t0)
        metrics = score_result_v2(row, result)
        reranker_effective_model = result.get("reranker_effective_model", "") or reranker_effective_model
        evaluated.append({"metrics": metrics, "result": result, "row": row})
        if collect_audit and len(audit_samples) < 12:
            ev = result.get("evidence") or []
            ret_d = (metrics.get("details") or {}).get("retrieval") or {}
            cit_d = (metrics.get("details") or {}).get("citation") or {}
            audit_samples.append(
                {
                    "question_id": row.get("id", ""),
                    "question": row.get("question", "")[:120],
                    "expected_source": row.get("expected_source", ""),
                    "retrieval_hit": metrics.get("retrieval_hit"),
                    "citation_correct": metrics.get("citation_correct"),
                    "top_sources": [e.get("source", "") for e in ev[:5]],
                    "normalized_expected_source": ret_d.get("normalized_expected_source", ""),
                    "normalized_top_sources": ret_d.get("normalized_top_sources", []),
                    "expected_record_id": ret_d.get("expected_record_id", ""),
                    "expected_doc_id": ret_d.get("expected_doc_id", ""),
                    "match_reason": ret_d.get("match_reason", cit_d.get("match_reason", "")),
                    "fail_kind": ret_d.get("fail_kind", ""),
                    "retrieval_mode": retrieval_mode,
                    "pool": pool,
                }
            )

    agg = aggregate_metrics_v2([x["metrics"] for x in evaluated])
    out = {
        "retrieval_hit_rate": agg["retrieval_hit_rate"],
        "citation_correctness": agg["citation_correctness"],
        "groundedness": agg["groundedness"],
        "answer_correctness": agg["answer_correctness"],
        "insufficient_information_handling": agg["insufficient_information_handling"],
        "pass_rate": agg["pass_rate"],
        "partial_rate": agg["partial_rate"],
        "fail_rate": agg["fail_rate"],
        "query_time_avg": round(sum(query_times) / max(1, len(query_times)), 3),
        "reranker_effective_model": reranker_effective_model,
    }
    if collect_audit:
        out["failure_audit_samples"] = audit_samples
    out["_evaluated"] = evaluated  # internal — stripped before JSON emit
    return out


def _ragas_metrics(
    enable_ragas: bool,
    benchmark_mode: str,
    evaluated: Optional[List[Dict[str, Any]]] = None,
    *,
    max_questions: int = 10,
) -> Dict[str, Any]:
    from config import OPENAI_MODEL

    base = {
        "faithfulness": None,
        "answer_relevancy": None,
        "context_precision": None,
        "context_recall": None,
        "model_judge": "",
    }
    if not enable_ragas:
        return {
            **base,
            "ragas_status": "skipped",
            "ragas_reason": "stagewise_dev_internal_metrics_only",
            "model_judge": "",
        }
    if not os.getenv("OPENAI_API_KEY", "").strip():
        return {
            **base,
            "ragas_status": "disabled",
            "ragas_reason": "OPENAI_API_KEY_missing",
            "model_judge": "",
        }
    if not evaluated:
        return {
            **base,
            "ragas_status": "skipped",
            "ragas_reason": "no_evaluated_rows",
            "model_judge": OPENAI_MODEL,
        }
    from ragas_eval import run_ragas_on_evaluated

    return run_ragas_on_evaluated(
        evaluated,
        max_questions=max_questions,
        model_judge=OPENAI_MODEL,
    )


def _run_full_pipeline_eval(retrieval_mode: str, top_k: int, pool: int) -> Dict[str, Any]:
    from config import BASE_DIR
    from hardening_config import HardeningConfig
    from hardening_orchestrator import run_hardening_profile
    from workflow_v5 import load_intake

    intake = load_intake(BASE_DIR / "data" / "rag_dataset" / "v5_intake_template.json")
    cfg = HardeningConfig(
        config_id="benchmark_case",
        label="benchmark_case",
        retrieval_mode=retrieval_mode,
        enable_policy_boost=True,
        corpus_scope="mixed",
        strict_conflict=False,
        top_k=top_k,
        pool=pool,
        verification_max_attempts=3,
    )
    out = run_hardening_profile(cfg, intake, run_id="benchmark_case_tmp")
    m = out["metrics"]
    return {
        "field_coverage": m.get("extraction_coverage_rate"),
        "verified_rate": m.get("verified_rate"),
        "insufficient_rate": m.get("insufficient_rate"),
        "conflict_rate": m.get("conflict_rate"),
        "priority_field_completion": m.get("priority_field_completion_rate"),
        "latency": m.get("end_to_end_duration_sec"),
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--config-id", required=True)
    parser.add_argument(
        "--dataset-lane",
        required=True,
        choices=[
            "dev",
            "validation",
            "full",
            "company_public_dev",
            "company_export_json_dev",
            "company_export_json_validation",
            "company_export_json_full",
        ],
    )
    parser.add_argument("--benchmark-lane", default="")
    parser.add_argument("--eval-set-path", default="")
    parser.add_argument("--benchmark-mode", required=True, choices=["retrieval_only", "full_pipeline"])
    parser.add_argument("--chunking-profile", required=True)
    parser.add_argument("--chunk-size", type=int, required=True)
    parser.add_argument("--chunk-overlap", type=int, required=True)
    parser.add_argument("--embedding-model", required=True)
    parser.add_argument("--retrieval-mode", required=True)
    parser.add_argument("--reranker", required=True)
    parser.add_argument("--reranker-backend", default="")
    parser.add_argument("--reranker-model", default="")
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--pool", type=int, default=24)
    parser.add_argument("--index-key", required=True)
    parser.add_argument("--parser-version", default="v1")
    parser.add_argument("--corpus-version", default="esg_core_v1")
    parser.add_argument("--corpus-ratio", type=float, default=1.0)
    parser.add_argument("--eval-max-questions", type=int, default=50)
    parser.add_argument("--reuse-index", default="true")
    parser.add_argument("--cache-root", default="artifacts/benchmark_cache")
    parser.add_argument("--enable-ragas", action="store_true")
    parser.add_argument("--ragas-max-questions", type=int, default=10)
    parser.add_argument(
        "--answer-mode",
        default="extractive",
        choices=["extractive", "generative"],
        help="extractive=rule chunk answer; generative=OpenAI/Ollama LLM",
    )
    parser.add_argument("--vector-store", default="chroma", choices=["chroma", "qdrant"])
    parser.add_argument("--collect-failure-audit", action="store_true")
    parser.add_argument("--metadata-aware", default="auto", choices=["auto", "true", "false"])
    parser.add_argument("--embed-local-only", default="auto", choices=["auto", "true", "false"])
    parser.add_argument("--pdf-parser", default="auto", choices=["auto", "pypdf", "docling"])
    parser.add_argument("--company-filter", default="")
    args = parser.parse_args(argv)

    from benchmark_utils import normalize_error_code
    from evidence_api.env_bootstrap import load_repo_dotenv

    base_dir = Path(__file__).resolve().parent.parent
    load_repo_dotenv()
    bench_lane = (args.benchmark_lane or args.dataset_lane).strip()
    os.environ["RAG_BENCHMARK_LANE"] = bench_lane
    eval_path = Path(args.eval_set_path) if args.eval_set_path else None
    if eval_path and not eval_path.is_absolute():
        eval_path = base_dir / eval_path
    started_at = datetime.now().isoformat(timespec="seconds")
    cache_root = base_dir / args.cache_root
    cache_root.mkdir(parents=True, exist_ok=True)
    parser_key = args.parser_version
    chunk_key = f"{args.chunking_profile}_{args.chunk_size}_{args.chunk_overlap}"
    emb_key = (
        args.embedding_model.replace("/", "_")
        .replace(":", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )
    corpus_key = args.corpus_version
    vs = (args.vector_store or "chroma").strip().lower()
    company_filter = args.company_filter.strip()
    cache_key = (
        f"p={parser_key}__c={chunk_key}__e={emb_key}__d={corpus_key}"
        f"__lane={args.dataset_lane}__vs={vs}"
    )
    if company_filter:
        company_hash = hashlib.md5(company_filter.encode("utf-8")).hexdigest()[:10]
        cache_key += f"__company={company_hash}"

    chroma_dir = cache_root / "index_cache" / cache_key / "chroma_db"
    qdrant_dir = cache_root / "index_cache" / cache_key / "qdrant_db"
    bm25_path = cache_root / "index_cache" / cache_key / "bm25_corpus.json"
    lexical_path = cache_root / "chunks_cache" / cache_key / "lexical_index.json"

    # Dat env truoc khi import rag_common/config (tranh cache RERANK_ENABLED=false).
    os.environ["RAG_CHUNKING_PROFILE"] = args.chunking_profile
    os.environ["RAG_CHUNK_SIZE"] = str(args.chunk_size)
    os.environ["RAG_CHUNK_OVERLAP"] = str(args.chunk_overlap)
    os.environ["RAG_EMBEDDING_MODEL"] = args.embedding_model
    os.environ["RAG_CHROMA_DIR"] = str(chroma_dir)
    os.environ["RAG_BM25_INDEX_PATH"] = str(bm25_path)
    os.environ["RAG_LEXICAL_INDEX_PATH"] = str(lexical_path)
    os.environ["RAG_TOP_K"] = str(args.top_k)
    os.environ["RAG_FINAL_TOP_K"] = str(args.top_k)
    os.environ["RAG_CANDIDATE_POOL_SIZE"] = str(args.pool)
    os.environ.setdefault("RAG_BENCHMARK_LANGUAGE", "ko")
    os.environ["RAG_RERANK_ENABLED"] = "true" if args.reranker != "none" else "false"
    # Neu da bat reranker, benchmark nen strict de tranh fallback ngam lam lech so sanh
    os.environ["RAG_RERANK_STRICT"] = "true" if args.reranker != "none" else "false"
    if company_filter:
        os.environ["RAG_COMPANY_FILTER"] = company_filter
    if args.embed_local_only == "true":
        os.environ["RAG_EMBED_LOCAL_ONLY"] = "true"
    elif args.embed_local_only == "false":
        os.environ["RAG_EMBED_LOCAL_ONLY"] = "false"
    else:
        os.environ["RAG_EMBED_LOCAL_ONLY"] = os.getenv("RAG_EMBED_LOCAL_ONLY", "false")
    if args.pdf_parser != "auto":
        os.environ["RAG_PDF_PARSER"] = args.pdf_parser
    if args.metadata_aware == "true":
        os.environ["RAG_METADATA_AWARE_RETRIEVAL"] = "true"
    elif args.metadata_aware == "false":
        os.environ["RAG_METADATA_AWARE_RETRIEVAL"] = "false"
    else:
        # auto: uu tien bat metadata-aware cho lane company public
        os.environ["RAG_METADATA_AWARE_RETRIEVAL"] = (
            "true" if "company_public" in args.dataset_lane or "company_export_json" in args.dataset_lane else "false"
        )
    if args.reranker_model:
        os.environ["RAG_RERANK_MODEL"] = args.reranker_model
    if args.reranker_backend:
        os.environ["RAG_RERANK_BACKEND"] = args.reranker_backend.strip().lower()
    if args.reranker == "jina_api" or (args.reranker_backend or "").strip().lower() == "jina_api":
        os.environ.setdefault("RAG_JINA_RERANK_MAX_DOCS", "16")
        os.environ.setdefault("RAG_JINA_MAX_CHARS", "400")
        os.environ.setdefault("JINA_RERANK_MIN_INTERVAL_SEC", "2")
        os.environ.setdefault("JINA_RERANK_MAX_RETRIES", "3")
        os.environ.setdefault("RAG_RERANK_BLEND_ALPHA", "0.40")
    os.environ["RAG_VECTOR_STORE"] = vs
    collection_hash = f"bench_{hashlib.md5(cache_key.encode('utf-8')).hexdigest()[:16]}"
    os.environ["RAG_CHROMA_COLLECTION"] = collection_hash
    os.environ["RAG_QDRANT_COLLECTION"] = collection_hash
    if vs == "qdrant":
        os.environ["RAG_QDRANT_PATH"] = str(qdrant_dir)

    parsed_manifest = _prepare_corpus_manifest(
        base_dir,
        args.dataset_lane,
        args.corpus_ratio,
        cache_root,
        company_filter=company_filter,
    )
    os.environ["RAG_BENCHMARK_CORPUS_MANIFEST"] = str(parsed_manifest)

    started = time.perf_counter()

    model_ok, model_reason = _model_available_local(args.embedding_model)
    if not model_ok:
        effective_embedding = os.getenv("RAG_EFFECTIVE_EMBEDDING_MODEL", "").strip() or args.embedding_model
        out = {
            "run_id": args.run_id,
            "config_id": args.config_id,
            "dataset_lane": args.dataset_lane,
            "benchmark_mode": args.benchmark_mode,
            "status": "failed",
            "error_reason": model_reason,
            "error_code": normalize_error_code(model_reason),
            "latency": round(time.perf_counter() - started, 3),
            "started_at": started_at,
            "ended_at": datetime.now().isoformat(timespec="seconds"),
            "embedding_model_effective": effective_embedding,
            "retrieval_mode_effective": args.retrieval_mode,
            "reranker_effective": "true" if args.reranker != "none" else "false",
        }
        emit_case_json(out)
        return 0

    index_build_time = 0.0
    try:
        from ingest import ingest_lexical_fallback
        from rag_stack import ingest_corpus_files

        reuse_index = str(args.reuse_index).lower() in ("1", "true", "yes")
        store_dir = qdrant_dir if vs == "qdrant" else chroma_dir
        has_index = _index_cache_ready(store_dir, bm25_path)
        if reuse_index and has_index:
            ingest_status = "reused_index_cache"
        else:
            t_ingest = time.perf_counter()
            ingest_corpus_files()
            index_build_time = round(time.perf_counter() - t_ingest, 3)
            ingest_status = "fresh_index_build"
        from rag_stack import _embeddings

        _embeddings()
        effective_embedding = os.getenv("RAG_EFFECTIVE_EMBEDDING_MODEL", "").strip() or args.embedding_model
        if effective_embedding != args.embedding_model:
            out = {
                "run_id": args.run_id,
                "config_id": args.config_id,
                "dataset_lane": args.dataset_lane,
                "status": "failed",
                "error_reason": f"embedding_runtime_mismatch:expected={args.embedding_model};effective={effective_embedding}",
                "error_code": "embedding_runtime_mismatch",
                "latency": round(time.perf_counter() - started, 3),
                "started_at": started_at,
                "ended_at": datetime.now().isoformat(timespec="seconds"),
                "embedding_model_effective": effective_embedding,
            }
            emit_case_json(out)
            return 0
    except Exception as exc:
        try:
            ingest_lexical_fallback()
        except Exception:
            pass
        out = {
            "run_id": args.run_id,
            "config_id": args.config_id,
            "dataset_lane": args.dataset_lane,
            "status": "failed",
            "error_reason": f"ingest_failed:{exc}",
            "latency": round(time.perf_counter() - started, 3),
        }
        emit_case_json(out)
        return 0

    try:
        rows = _load_eval_rows(args.eval_max_questions, eval_path)
        answer_mode = args.answer_mode
        llm_runtime = None
        llm_provider = ""
        if answer_mode == "generative":
            from llm_runtime import detect_llm_runtime

            llm_runtime = detect_llm_runtime()
            if llm_runtime.status != "ready":
                out = {
                    "run_id": args.run_id,
                    "config_id": args.config_id,
                    "dataset_lane": args.dataset_lane,
                    "status": "failed",
                    "error_code": "generative_llm_blocked",
                    "error_reason": llm_runtime.blocker_reason or "generative_llm_blocked",
                    "latency": round(time.perf_counter() - started, 3),
                }
                emit_case_json(out)
                return 0
            llm_provider = llm_runtime.provider or ""

        retrieval_metrics = _run_retrieval_eval(
            rows,
            args.retrieval_mode,
            args.top_k,
            args.pool,
            answer_mode=answer_mode,
            llm_runtime=llm_runtime,
            collect_audit=args.collect_failure_audit,
        )
        evaluated = retrieval_metrics.pop("_evaluated", [])
        failure_audit_samples = retrieval_metrics.pop("failure_audit_samples", None)
        if args.benchmark_mode == "full_pipeline":
            pipeline_metrics = _run_full_pipeline_eval(args.retrieval_mode, args.top_k, args.pool)
        else:
            pipeline_metrics = {
                "field_coverage": None,
                "verified_rate": None,
                "insufficient_rate": None,
                "conflict_rate": None,
                "priority_field_completion": None,
            }
        ragas = _ragas_metrics(
            args.enable_ragas,
            args.benchmark_mode,
            evaluated,
            max_questions=args.ragas_max_questions,
        )
        total_latency = round(time.perf_counter() - started, 3)

        out = {
            "run_id": args.run_id,
            "config_id": args.config_id,
            "dataset_lane": args.dataset_lane,
            "status": "success",
            "error_reason": "",
            "error_code": "",
            "ingest_status": ingest_status,
            "cache_key": cache_key,
            "chunking": args.chunking_profile,
            "embedding_model": args.embedding_model,
            "retrieval_mode": args.retrieval_mode,
            "reranker": args.reranker,
            "extraction_mode": "heuristic_v4",
            "verification_mode": "v6_loop_mixed_policy_boost",
            "benchmark_mode": args.benchmark_mode,
            "benchmark_kind": args.benchmark_mode,
            "answer_mode": answer_mode,
            "llm_provider": llm_provider,
            "embedding_model_effective": os.getenv("RAG_EFFECTIVE_EMBEDDING_MODEL", effective_embedding),
            "retrieval_mode_effective": args.retrieval_mode,
            "reranker_effective": "true" if args.reranker != "none" else "false",
            "candidate_pool": args.pool,
            "vector_store": vs,
            "company_filter": company_filter,
            "qdrant_status": "enabled" if vs == "qdrant" else "",
            "index_build_time": index_build_time,
            "query_time_avg": retrieval_metrics.get("query_time_avg"),
            "reranker_latency": "",
            "latency": total_latency,
            "started_at": started_at,
            "ended_at": datetime.now().isoformat(timespec="seconds"),
        }
        if failure_audit_samples is not None:
            out["failure_audit_samples"] = failure_audit_samples
        out.update(retrieval_metrics)
        out.update(pipeline_metrics)
        out.update(ragas)
        emit_case_json(out)
        return 0
    except Exception as exc:
        out = {
            "run_id": args.run_id,
            "config_id": args.config_id,
            "dataset_lane": args.dataset_lane,
            "status": "failed",
            "error_reason": f"benchmark_eval_failed:{exc}",
            "error_code": "benchmark_eval_failed",
            "latency": round(time.perf_counter() - started, 3),
        }
        emit_case_json(out)
        return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.exit(main())
