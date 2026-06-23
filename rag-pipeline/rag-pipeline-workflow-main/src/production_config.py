"""Load frozen production RAG stack config and apply runtime env."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

DEFAULT_PRODUCTION_CONFIG = "configs/production_openai_hybrid_qdrant_jina.yaml"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_production_config(path: Optional[str | Path] = None) -> Dict[str, Any]:
    cfg_path = repo_root() / (path or DEFAULT_PRODUCTION_CONFIG)
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8"))


def production_cache_key(cfg: Dict[str, Any]) -> str:
    stack = cfg["stack"]
    chunk_key = f"{stack['chunking_profile']}_{stack['chunk_size']}_{stack['chunk_overlap']}"
    emb_key = stack["embedding_model"].replace("/", "_").replace(":", "_")
    key = (
        f"p={stack['parser_version']}__c={chunk_key}__e={emb_key}"
        f"__d={stack['corpus_version']}__lane={stack['lane']}__vs={stack['vector_store']}"
    )
    company = (stack.get("company_filter") or "").strip()
    if company:
        key += f"__company={hashlib.md5(company.encode()).hexdigest()[:10]}"
    return key


def index_dir(cfg: Dict[str, Any]) -> Path:
    cache_root = repo_root() / cfg.get("cache_root", "artifacts/benchmark_cache")
    return cache_root / "index_cache" / production_cache_key(cfg)


def apply_production_env(cfg: Dict[str, Any], *, base_dir: Optional[Path] = None) -> Path:
    """Set os.environ for frozen stack; return corpus manifest path."""
    base = base_dir or repo_root()
    stack = cfg["stack"]
    cache_root = base / cfg.get("cache_root", "artifacts/benchmark_cache")
    idx = index_dir(cfg)
    cache_key = production_cache_key(cfg)

    os.environ["RAG_BENCHMARK_LANE"] = stack["lane"]
    os.environ["RAG_COMPANY_FILTER"] = stack.get("company_filter", "")
    os.environ["RAG_CHUNKING_PROFILE"] = stack["chunking_profile"]
    os.environ["RAG_CHUNK_SIZE"] = str(stack["chunk_size"])
    os.environ["RAG_CHUNK_OVERLAP"] = str(stack["chunk_overlap"])
    os.environ["RAG_EMBEDDING_MODEL"] = stack["embedding_model"]
    os.environ["RAG_RETRIEVAL_MODE"] = stack["retrieval_mode"]
    os.environ["RAG_VECTOR_STORE"] = stack["vector_store"]
    os.environ["RAG_TOP_K"] = str(stack.get("top_k", 4))
    os.environ["RAG_FINAL_TOP_K"] = str(stack.get("top_k", 4))
    os.environ["RAG_CANDIDATE_POOL_SIZE"] = str(stack.get("candidate_pool", 64))
    reranker = (stack.get("reranker") or "none").strip().lower()
    rerank_backend = (stack.get("reranker_backend") or "").strip().lower()
    if reranker not in ("none", ""):
        os.environ["RAG_RERANK_ENABLED"] = "true"
        os.environ["RAG_RERANK_STRICT"] = "true"
        if rerank_backend:
            os.environ["RAG_RERANK_BACKEND"] = rerank_backend
        if stack.get("reranker_model"):
            os.environ["RAG_RERANK_MODEL"] = str(stack["reranker_model"])
        if stack.get("rerank_blend_alpha") is not None:
            os.environ["RAG_RERANK_BLEND_ALPHA"] = str(stack["rerank_blend_alpha"])
        if reranker == "jina_api" or rerank_backend == "jina_api":
            os.environ.setdefault(
                "RAG_JINA_RERANK_MAX_DOCS", str(stack.get("jina_rerank_max_docs", 16))
            )
            os.environ.setdefault("RAG_JINA_MAX_CHARS", str(stack.get("jina_max_chars", 400)))
            os.environ.setdefault(
                "JINA_RERANK_MIN_INTERVAL_SEC", str(stack.get("jina_min_interval_sec", 2))
            )
            os.environ.setdefault("JINA_RERANK_MAX_RETRIES", str(stack.get("jina_max_retries", 3)))
    else:
        os.environ["RAG_RERANK_ENABLED"] = "false"
        os.environ["RAG_RERANK_STRICT"] = "false"
    os.environ["RAG_BENCHMARK_LANGUAGE"] = stack.get("benchmark_language", "ko")
    os.environ["RAG_BM25_INDEX_PATH"] = str(idx / "bm25_corpus.json")
    os.environ["RAG_CHROMA_COLLECTION"] = f"bench_{hashlib.md5(cache_key.encode('utf-8')).hexdigest()[:16]}"
    os.environ["RAG_OPENAI_EMBED_BATCH"] = str(stack.get("openai_embed_batch", 32))
    os.environ["RAG_BENCHMARK_LLM_PROVIDER"] = stack.get("llm_provider", "openai_api")
    if stack.get("llm_model"):
        os.environ["OPENAI_MODEL"] = str(stack["llm_model"])
    llm_url_env = stack.get("llm_base_url_env")
    if llm_url_env:
        url = os.getenv(llm_url_env, "").strip()
        if url:
            os.environ["OPENAI_BASE_URL"] = url

    if stack["vector_store"] == "qdrant":
        os.environ["RAG_QDRANT_PATH"] = str(idx / "qdrant_db")
    else:
        os.environ["RAG_CHROMA_DIR"] = str(idx / "chroma_db")

    from run_benchmark_case import _prepare_corpus_manifest

    manifest = _prepare_corpus_manifest(
        base,
        stack["lane"],
        float(stack.get("corpus_ratio", 1.0)),
        cache_root,
        company_filter=stack.get("company_filter", ""),
    )
    os.environ["RAG_BENCHMARK_CORPUS_MANIFEST"] = str(manifest)
    sync_runtime_config_paths()
    return manifest


def sync_runtime_config_paths() -> None:
    """Re-bind cached config module paths after os.environ stack switch (multi-company API)."""
    import sys

    import config as cfg

    base = cfg.BASE_DIR
    cfg.BM25_INDEX_PATH = Path(
        os.getenv("RAG_BM25_INDEX_PATH", str(base / "artifacts" / "bm25_corpus.json"))
    )
    cfg.CHROMA_DIR = Path(os.getenv("RAG_CHROMA_DIR", str(base / "artifacts" / "chroma_db")))
    cfg.QDRANT_PATH = Path(os.getenv("RAG_QDRANT_PATH", str(base / "artifacts" / "qdrant_db")))
    cfg.VECTOR_STORE = os.getenv("RAG_VECTOR_STORE", "chroma").strip().lower()

    for name in ("rag_stack", "retrieval_v3"):
        mod = sys.modules.get(name)
        if mod is None:
            continue
        for attr in ("BM25_INDEX_PATH", "CHROMA_DIR", "QDRANT_PATH", "VECTOR_STORE"):
            if hasattr(mod, attr) and hasattr(cfg, attr):
                setattr(mod, attr, getattr(cfg, attr))
        if name == "retrieval_v3" and hasattr(mod, "_rerank_blend_alpha"):
            try:
                mod._rerank_blend_alpha = float(os.getenv("RAG_RERANK_BLEND_ALPHA", "0.65"))
            except ValueError:
                pass


def cached_bm25_chunk_count(cfg: Dict[str, Any]) -> int:
    bm25 = index_dir(cfg) / "bm25_corpus.json"
    if not bm25.exists():
        return 0
    data = json.loads(bm25.read_text(encoding="utf-8"))
    chunks = data.get("chunks", []) if isinstance(data, dict) else data
    return len(chunks)


def expected_bm25_chunk_count(*, base_dir: Optional[Path] = None) -> int:
    """Chunk count from build_chunks under current os.environ lane/manifest."""
    from rag_common import build_chunks

    base = base_dir or repo_root()
    return len(build_chunks(base))


def index_chunk_parity_mismatch(cfg: Dict[str, Any], *, base_dir: Optional[Path] = None) -> Optional[str]:
    """Return reason string when cached BM25 chunk count != build_chunks (export-json lane)."""
    lane = (cfg.get("stack") or {}).get("lane", "")
    if not (lane.startswith("company_export_json") or lane.startswith("rtx_references")):
        return None
    if not index_ready(cfg):
        return "index_not_ready"
    base = base_dir or repo_root()
    cached = cached_bm25_chunk_count(cfg)
    expected = expected_bm25_chunk_count(base_dir=base)
    if cached != expected:
        return f"chunk_count_mismatch:cached={cached},expected={expected}"
    return None


def index_ready(cfg: Dict[str, Any]) -> bool:
    idx = index_dir(cfg)
    marker = idx / ".index_complete"
    bm25 = idx / "bm25_corpus.json"
    store = idx / ("qdrant_db" if cfg["stack"]["vector_store"] == "qdrant" else "chroma_db")
    return marker.exists() and bm25.exists() and store.exists() and any(store.rglob("*"))


def smoke_question_ids(cfg: Dict[str, Any]) -> List[str]:
    smoke = cfg.get("smoke_ci") or {}
    return list(smoke.get("question_ids") or [])


def monitoring_thresholds(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return dict((cfg.get("monitoring") or {}).get("thresholds") or {})
