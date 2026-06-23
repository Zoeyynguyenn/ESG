"""Version 3: multi-mode evidence retrieval (dense, BM25, hybrid, rerank)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from config import (
    BASE_DIR,
    BM25_INDEX_PATH,
    CANDIDATE_POOL_SIZE,
    CHROMA_DIR,
    EMBEDDING_MODEL,
    FINAL_TOP_K,
    HYBRID_ALPHA,
    RERANK_BACKEND,
    RERANK_MODEL,
    METADATA_AWARE_RETRIEVAL,
)
from evidence_rag import INSUFFICIENT_ANSWER, build_answer, is_insufficient_question
from rag_common import ChunkRecord, build_chunks, overlap_score, tokenize
from rag_stack import _chroma_store, stack_available

_bm25_index: Any = None
_corpus_chunks: Optional[List[ChunkRecord]] = None
_reranker: Any = None
_rerank_status: str = "not_loaded"
_rerank_effective_model: str = ""
_rerank_blend_alpha: float = float(os.getenv("RAG_RERANK_BLEND_ALPHA", "0.65"))


def _rerank_enabled() -> bool:
    return os.getenv("RAG_RERANK_ENABLED", "false").lower() in ("1", "true", "yes")


def _rerank_strict_enabled() -> bool:
    return os.getenv("RAG_RERANK_STRICT", "false").lower() in ("1", "true", "yes")


def _jina_rerank_max_docs() -> int:
    try:
        return max(4, int(os.getenv("RAG_JINA_RERANK_MAX_DOCS", "16")))
    except ValueError:
        return 16


def _is_transient_rerank_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(
        token in msg
        for token in ("429", "rate", "503", "502", "504", "timeout", "token rate limit")
    )


def _rerank_strict_should_raise(exc: Exception) -> bool:
    if not _rerank_strict_enabled():
        return False
    return not _is_transient_rerank_error(exc)


def _resolve_rerank_backend(model_name: str) -> str:
    backend = (os.getenv("RAG_RERANK_BACKEND", RERANK_BACKEND) or "auto").strip().lower()
    if backend in ("flashrank", "cross_encoder", "jina_api"):
        return backend
    if model_name.startswith("jina-") or model_name.startswith("jina_colbert"):
        return "jina_api"
    if model_name.startswith("ms-marco-") and "/" not in model_name:
        return "flashrank"
    return "cross_encoder"


def _ensure_flashrank_tmpdir() -> str:
    tmp_root = BASE_DIR / "artifacts" / "tmp" / "flashrank"
    tmp_root.mkdir(parents=True, exist_ok=True)
    tmp_str = str(tmp_root)
    os.environ["TMPDIR"] = tmp_str
    os.environ["TMP"] = tmp_str
    os.environ["TEMP"] = tmp_str
    return tmp_str


def _norm_source(source: str) -> str:
    return (source or "").replace("\\", "/").lower()


def _source_allowed_for_lane(source: str) -> bool:
    lane = os.getenv("RAG_BENCHMARK_LANE", "").strip()
    src = _norm_source(source)
    if lane == "company_public_dev":
        return src.startswith("data/rag_dataset/04_company_public_curated/")
    if lane.startswith("company_export_json"):
        pkg = os.getenv("RAG_COMPANY_FILTER", "").strip().strip("/").lower()
        if pkg:
            return src.startswith(f"data/rag_dataset/05_company_export_json/{pkg}/")
        return src.startswith("data/rag_dataset/05_company_export_json/")
    if lane.startswith("rtx_references"):
        lane_id = os.getenv("RAG_COMPANY_FILTER", "06_rtx_references_raw").strip().strip("/")
        if not lane_id:
            lane_id = "06_rtx_references_raw"
        return src.startswith(f"data/rag_dataset/{lane_id}/")
    return True


def _filter_hits_by_lane(hits: List[RankedChunk]) -> List[RankedChunk]:
    return [h for h in hits if _source_allowed_for_lane(h.source)]


def _infer_doc_group(question: str) -> Optional[str]:
    q = (question or "").lower()
    if any(k in q for k in ("governance", "board", "ethics", "compliance", "risk")):
        return "governance"
    if any(k in q for k in ("social", "labor", "human rights", "dei", "diversity", "safety")):
        return "social"
    if any(k in q for k in ("environment", "climate", "emission", "energy", "water", "waste")):
        return "environment"
    return None


def _infer_company(question: str) -> Optional[str]:
    q = (question or "").lower()
    company_map = {
        "microsoft": "microsoft",
        "google": "google",
        "apple": "apple",
        "unilever": "unilever",
        "nestle": "nestle",
        "toyota": "toyota",
        "vinamilk": "vinamilk",
        "fpt": "fpt",
    }
    for k, v in company_map.items():
        if k in q:
            return v
    return None


def _build_metadata_filter(question: str) -> Optional[Dict[str, str]]:
    if not METADATA_AWARE_RETRIEVAL:
        return None
    md: Dict[str, str] = {}
    company = _infer_company(question)
    if company:
        md["company"] = company
    doc_group = _infer_doc_group(question)
    if doc_group:
        md["doc_group"] = doc_group
    return md or None


def _chunk_matches_metadata(chunk: ChunkRecord, md_filter: Optional[Dict[str, str]]) -> bool:
    if not md_filter:
        return True
    src = _norm_source(chunk.source)
    company = md_filter.get("company")
    if company and company not in src:
        return False
    doc_group = md_filter.get("doc_group")
    if doc_group and doc_group not in src:
        # Fallback: doc_group may not exist in filename/path
        if doc_group == "environment" and not any(k in src for k in ("environment", "climate", "energy", "water", "waste", "emission")):
            return False
        if doc_group == "social" and not any(k in src for k in ("social", "labor", "human", "community", "dei", "diversity", "safety")):
            return False
        if doc_group == "governance" and not any(k in src for k in ("governance", "board", "ethic", "compliance", "risk")):
            return False
    return True


@dataclass
class RankedChunk:
    source: str
    text: str
    chunk_id: int
    score: float
    score_breakdown: Dict[str, Optional[float]]


def _chunk_key(c: ChunkRecord) -> str:
    return f"{c.source}::{c.chunk_id}"


def get_corpus_chunks(force_rebuild: bool = False) -> List[ChunkRecord]:
    global _corpus_chunks
    if _corpus_chunks is not None and not force_rebuild:
        return _corpus_chunks
    if BM25_INDEX_PATH.exists() and not force_rebuild:
        data = json.loads(BM25_INDEX_PATH.read_text(encoding="utf-8"))
        _corpus_chunks = [ChunkRecord(**x) for x in data.get("chunks", [])]
        _corpus_chunks = [c for c in _corpus_chunks if _source_allowed_for_lane(c.source)]
        if _corpus_chunks:
            return _corpus_chunks
    _corpus_chunks = build_chunks(BASE_DIR)
    _corpus_chunks = [c for c in _corpus_chunks if _source_allowed_for_lane(c.source)]
    BM25_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    BM25_INDEX_PATH.write_text(
        json.dumps(
            {"chunk_count": len(_corpus_chunks), "chunks": [c.__dict__ for c in _corpus_chunks]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return _corpus_chunks


def _normalize_scores(scores: List[float]) -> List[float]:
    if not scores:
        return []
    mn, mx = min(scores), max(scores)
    if mx - mn < 1e-9:
        return [1.0] * len(scores)
    return [(s - mn) / (mx - mn) for s in scores]


def _to_evidence(hit: RankedChunk) -> dict:
    return {
        "source": hit.source,
        "citation": hit.source,
        "score": round(hit.score, 4),
        "text": hit.text[:500],
        "score_breakdown": hit.score_breakdown,
    }


def _align_chunk_id(source: str, text: str, chunks: List[ChunkRecord]) -> int:
    prefix = text[:180]
    for c in chunks:
        if c.source == source and (c.text[:180] == prefix or prefix in c.text[:220]):
            return c.chunk_id
    for c in chunks:
        if c.source == source:
            return c.chunk_id
    return 0


def retrieve_semantic_dense(question: str, pool: int, top_k: int) -> Tuple[List[RankedChunk], str]:
    if not stack_available():
        raise FileNotFoundError("Chroma DB khong san sang cho semantic_dense")
    corpus = get_corpus_chunks()
    store = _chroma_store()
    md_filter = _build_metadata_filter(question)
    if md_filter:
        results = store.similarity_search_with_score(question, k=pool, filter=md_filter)
    else:
        results = store.similarity_search_with_score(question, k=pool)
    hits: List[RankedChunk] = []
    for doc, dist in results:
        sim = max(0.0, 1.0 - float(dist)) if dist is not None else 0.0
        src = doc.metadata.get("source", "unknown")
        cid = _align_chunk_id(src, doc.page_content, corpus)
        hits.append(
            RankedChunk(
                source=src,
                text=doc.page_content,
                chunk_id=cid,
                score=sim,
                score_breakdown={"dense": round(sim, 4), "bm25": None, "hybrid": round(sim, 4), "rerank": None},
            )
        )
    hits = _filter_hits_by_lane(hits)
    hits.sort(key=lambda x: x.score, reverse=True)
    note = "ok"
    if md_filter:
        note = f"ok;metadata_filter={md_filter}"
        if not hits:
            # metadata filter qua chat: fallback ve query khong filter de tranh miss toan bo
            results = store.similarity_search_with_score(question, k=pool)
            for doc, dist in results:
                sim = max(0.0, 1.0 - float(dist)) if dist is not None else 0.0
                src = doc.metadata.get("source", "unknown")
                cid = _align_chunk_id(src, doc.page_content, corpus)
                hits.append(
                    RankedChunk(
                        source=src,
                        text=doc.page_content,
                        chunk_id=cid,
                        score=sim,
                        score_breakdown={
                            "dense": round(sim, 4),
                            "bm25": None,
                            "hybrid": round(sim, 4),
                            "rerank": None,
                        },
                    )
                )
            hits = _filter_hits_by_lane(hits)
            hits.sort(key=lambda x: x.score, reverse=True)
            note = f"{note};no-hit-after-metadata-filter;fallback_no_filter"
    return hits[:top_k], note


def _get_bm25():
    global _bm25_index
    if _bm25_index is not None:
        return _bm25_index
    try:
        from rank_bm25 import BM25Okapi
    except ImportError as exc:
        raise ImportError("Can cai rank-bm25: pip install rank-bm25") from exc
    chunks = get_corpus_chunks()
    corpus = [tokenize(c.text) for c in chunks]
    _bm25_index = (BM25Okapi(corpus), chunks)
    return _bm25_index


def retrieve_bm25_lexical(question: str, pool: int, top_k: int) -> Tuple[List[RankedChunk], str]:
    bm25, chunks = _get_bm25()
    md_filter = _build_metadata_filter(question)
    q_tokens = tokenize(question)
    if not q_tokens:
        return [], "empty_query"
    scores = list(bm25.get_scores(q_tokens))
    indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:pool]
    norm = _normalize_scores([s for _, s in indexed])
    hits: List[RankedChunk] = []
    for (idx, raw), n in zip(indexed, norm):
        c = chunks[idx]
        if not _chunk_matches_metadata(c, md_filter):
            continue
        hits.append(
            RankedChunk(
                source=c.source,
                text=c.text,
                chunk_id=c.chunk_id,
                score=n,
                score_breakdown={"dense": None, "bm25": round(float(raw), 4), "hybrid": n, "rerank": None},
            )
        )
    hits = _filter_hits_by_lane(hits)
    hits.sort(key=lambda x: x.score, reverse=True)
    note = "ok"
    if md_filter:
        note = f"ok;metadata_filter={md_filter}"
        if not hits:
            # metadata filter qua chat: fallback khong filter de tranh no-hit toan bo
            hits = []
            for (idx, raw), n in zip(indexed, norm):
                c = chunks[idx]
                hits.append(
                    RankedChunk(
                        source=c.source,
                        text=c.text,
                        chunk_id=c.chunk_id,
                        score=n,
                        score_breakdown={
                            "dense": None,
                            "bm25": round(float(raw), 4),
                            "hybrid": n,
                            "rerank": None,
                        },
                    )
                )
            hits = _filter_hits_by_lane(hits)
            hits.sort(key=lambda x: x.score, reverse=True)
            note = f"{note};no-hit-after-metadata-filter;fallback_no_filter"
    return hits[:top_k], note


def _merge_candidate_maps(
    dense_hits: List[RankedChunk],
    bm25_hits: List[RankedChunk],
    alpha: float,
) -> List[RankedChunk]:
    merged: Dict[str, RankedChunk] = {}
    for h in dense_hits:
        key = f"{h.source}::{h.chunk_id}"
        d = h.score_breakdown.get("dense") or h.score
        merged[key] = RankedChunk(
            h.source, h.text, h.chunk_id, 0.0,
            {"dense": d, "bm25": None, "hybrid": None, "rerank": None},
        )
    for h in bm25_hits:
        key = f"{h.source}::{h.chunk_id}"
        b = h.score_breakdown.get("bm25") or h.score
        if key in merged:
            merged[key].score_breakdown["bm25"] = b
        else:
            merged[key] = RankedChunk(
                h.source, h.text, h.chunk_id, 0.0,
                {"dense": None, "bm25": b, "hybrid": None, "rerank": None},
            )
    dense_vals = [v.score_breakdown["dense"] for v in merged.values() if v.score_breakdown["dense"] is not None]
    bm25_vals = [v.score_breakdown["bm25"] for v in merged.values() if v.score_breakdown["bm25"] is not None]
    dense_norm_map = {}
    bm25_norm_map = {}
    if dense_vals:
        keys_d = [k for k, v in merged.items() if v.score_breakdown["dense"] is not None]
        norms = _normalize_scores([merged[k].score_breakdown["dense"] for k in keys_d])
        dense_norm_map = dict(zip(keys_d, norms))
    if bm25_vals:
        keys_b = [k for k, v in merged.items() if v.score_breakdown["bm25"] is not None]
        norms = _normalize_scores([merged[k].score_breakdown["bm25"] for k in keys_b])
        bm25_norm_map = dict(zip(keys_b, norms))

    out: List[RankedChunk] = []
    for key, v in merged.items():
        d = dense_norm_map.get(key, 0.0)
        b = bm25_norm_map.get(key, 0.0)
        if v.score_breakdown["dense"] is None:
            hybrid = b
        elif v.score_breakdown["bm25"] is None:
            hybrid = d
        else:
            hybrid = alpha * d + (1 - alpha) * b
        v.score = hybrid
        v.score_breakdown["hybrid"] = round(hybrid, 4)
        out.append(v)
    out.sort(key=lambda x: x.score, reverse=True)
    return out


def retrieve_hybrid_dense_bm25(
    question: str, pool: int, top_k: int, alpha: float = HYBRID_ALPHA
) -> Tuple[List[RankedChunk], str]:
    notes = []
    try:
        dense, _ = retrieve_semantic_dense(question, pool, pool)
    except Exception as exc:
        dense = []
        notes.append(f"dense_fail:{exc}")
    from export_json_retrieval_hints import (
        apply_field_boost,
        should_apply_export_json_boost,
    )
    from korean_metric_retrieval_hints import (
        apply_headcount_metric_boost,
        prepare_bm25_query,
    )

    bm25_question = prepare_bm25_query(
        question, lane_expand=should_apply_export_json_boost()
    )
    try:
        bm25, _ = retrieve_bm25_lexical(bm25_question, pool, pool)
    except Exception as exc:
        bm25 = []
        notes.append(f"bm25_fail:{exc}")
    if not dense and not bm25:
        return [], ";".join(notes) or "no_candidates"
    merged = _merge_candidate_maps(dense, bm25, alpha)
    if should_apply_export_json_boost():
        merged = apply_field_boost(question, merged)
    merged = apply_headcount_metric_boost(question, merged)
    return merged[:top_k], "ok" if not notes else "partial:" + ";".join(notes)


def _load_reranker() -> Tuple[Any, str]:
    global _reranker, _rerank_status, _rerank_effective_model
    if _reranker is not None:
        return _reranker, _rerank_status
    if not _rerank_enabled():
        _rerank_status = "disabled"
        _rerank_effective_model = "disabled"
        return None, _rerank_status
    model_name = os.getenv("RAG_RERANK_MODEL", RERANK_MODEL).strip() or RERANK_MODEL
    backend = _resolve_rerank_backend(model_name)
    try:
        if backend == "jina_api":
            from jina_rerank import jina_api_key

            if not jina_api_key():
                raise RuntimeError("jina_api_key_missing")
            _reranker = "jina_api"
            _rerank_status = "jina_api"
        elif backend == "flashrank":
            from flashrank import Ranker

            cache_dir = _ensure_flashrank_tmpdir()
            _reranker = Ranker(model_name=model_name, cache_dir=cache_dir)
            _rerank_status = "flashrank"
        elif backend == "cross_encoder":
            from sentence_transformers import CrossEncoder

            _reranker = CrossEncoder(model_name)
            _rerank_status = "cross_encoder"
        else:
            raise ValueError(f"unsupported_rerank_backend:{backend}")
        _rerank_effective_model = model_name
        return _reranker, _rerank_status
    except Exception as exc:
        _rerank_status = f"fallback_overlap:{exc}"
        _rerank_effective_model = f"fallback_overlap:{exc}"
        return None, _rerank_status


def _rerank_candidates(question: str, candidates: List[RankedChunk]) -> Tuple[List[RankedChunk], str]:
    if not candidates:
        return [], "empty"
    from korean_metric_retrieval_hints import (
        apply_headcount_metric_boost,
        headcount_rerank_blend_alpha,
        is_headcount_metric_query,
    )

    model, status = _load_reranker()
    # Giữ base score để tranh rerank "lat keo" qua manh
    base_scores = [float(c.score) for c in candidates]
    base_norm = _normalize_scores(base_scores)
    blend_alpha = _rerank_blend_alpha
    if is_headcount_metric_query(question):
        blend_alpha = headcount_rerank_blend_alpha(_rerank_blend_alpha)
    if model is not None:
        try:
            raw_scores: List[float] = []
            if status == "jina_api":
                from jina_rerank import jina_max_chars, rerank_scores

                max_docs = _jina_rerank_max_docs()
                head = list(candidates[:max_docs])
                tail = list(candidates[max_docs:])
                max_chars = jina_max_chars()
                raw_head = rerank_scores(
                    question,
                    [c.text[:max_chars] for c in head],
                    model=os.getenv("RAG_RERANK_MODEL", RERANK_MODEL),
                )
                head_base = base_scores[: len(head)]
                head_base_norm = _normalize_scores(head_base)
                rerank_norm = _normalize_scores(raw_head)
                alpha = max(0.0, min(1.0, blend_alpha))
                for i, (c, raw, rn) in enumerate(zip(head, raw_head, rerank_norm)):
                    final_score = alpha * rn + (1 - alpha) * head_base_norm[i]
                    c.score_breakdown["hybrid_pre_rerank"] = round(head_base[i], 4)
                    c.score_breakdown["rerank"] = round(raw, 4)
                    c.score_breakdown["rerank_norm"] = round(rn, 4)
                    c.score = final_score
                head.sort(key=lambda x: x.score, reverse=True)
                head = apply_headcount_metric_boost(question, head)
                return head + tail, f"{status};prefilter={len(head)};blend_alpha={alpha}"
            elif status == "flashrank":
                from flashrank import RerankRequest

                passages = [
                    {
                        "id": i,
                        "text": c.text[:512],
                        "meta": {"source": c.source, "chunk_id": c.chunk_id},
                    }
                    for i, c in enumerate(candidates)
                ]
                req = RerankRequest(query=question, passages=passages)
                ranked = model.rerank(req)
                score_by_id = {
                    int(item["id"]): float(item.get("score", 0.0))
                    for item in ranked
                    if item.get("id") is not None
                }
                raw_scores = [score_by_id.get(i, 0.0) for i in range(len(candidates))]
            else:
                pairs = [[question, c.text[:512]] for c in candidates]
                scores = model.predict(pairs)
                for s in scores:
                    if isinstance(s, (list, tuple)):
                        raw_scores.append(float(s[0]))
                    else:
                        raw_scores.append(float(s))
            rerank_norm = _normalize_scores(raw_scores)
            alpha = max(0.0, min(1.0, blend_alpha))
            for i, (c, raw, rn) in enumerate(zip(candidates, raw_scores, rerank_norm)):
                final_score = alpha * rn + (1 - alpha) * base_norm[i]
                c.score_breakdown["hybrid_pre_rerank"] = round(base_scores[i], 4)
                c.score_breakdown["rerank"] = round(raw, 4)
                c.score_breakdown["rerank_norm"] = round(rn, 4)
                c.score = final_score
            candidates.sort(key=lambda x: x.score, reverse=True)
            candidates = apply_headcount_metric_boost(question, candidates)
            return candidates, f"{status};blend_alpha={alpha}"
        except Exception as exc:
            if _rerank_strict_should_raise(exc):
                raise RuntimeError(f"fallback_overlap:{exc}") from exc
            return candidates, f"fallback_hybrid:{exc}"
    elif _rerank_strict_enabled():
        raise RuntimeError(f"reranker_unavailable:{status}")
    alpha = max(0.0, min(1.0, blend_alpha))
    overlap_scores = [overlap_score(question, c.text) for c in candidates]
    overlap_norm = _normalize_scores(overlap_scores)
    for i, c in enumerate(candidates):
        ov = overlap_scores[i]
        final_score = alpha * overlap_norm[i] + (1 - alpha) * base_norm[i]
        c.score_breakdown["hybrid_pre_rerank"] = round(base_scores[i], 4)
        c.score_breakdown["rerank"] = round(ov, 4)
        c.score_breakdown["rerank_norm"] = round(overlap_norm[i], 4)
        c.score = final_score
    candidates.sort(key=lambda x: x.score, reverse=True)
    candidates = apply_headcount_metric_boost(question, candidates)
    return candidates, f"{status};blend_alpha={alpha}"


def retrieve_hybrid_dense_bm25_rerank(
    question: str, pool: int, top_k: int, alpha: float = HYBRID_ALPHA
) -> Tuple[List[RankedChunk], str]:
    hybrid, note = retrieve_hybrid_dense_bm25(question, pool, pool, alpha)
    if not hybrid:
        return [], note
    reranked, rstatus = _rerank_candidates(question, hybrid)
    final_note = note if note == "ok" else note
    if rstatus.startswith("fallback"):
        final_note = f"{final_note};rerank_{rstatus}"
    else:
        final_note = f"{final_note};rerank_{rstatus}"
    return reranked[:top_k], final_note


def retrieve_semantic_dense_rerank(question: str, pool: int, top_k: int) -> Tuple[List[RankedChunk], str]:
    dense, note = retrieve_semantic_dense(question, pool, pool)
    if not dense:
        return [], note
    reranked, rstatus = _rerank_candidates(question, dense)
    return reranked[:top_k], f"{note};rerank_{rstatus}"


def retrieve(
    question: str,
    mode: str,
    pool: int = CANDIDATE_POOL_SIZE,
    top_k: int = FINAL_TOP_K,
) -> Tuple[List[RankedChunk], str]:
    if mode == "semantic_dense":
        return retrieve_semantic_dense(question, pool, top_k)
    if mode == "bm25_lexical":
        return retrieve_bm25_lexical(question, pool, top_k)
    if mode == "semantic_dense_rerank":
        return retrieve_semantic_dense_rerank(question, pool, top_k)
    if mode == "hybrid_dense_bm25":
        return retrieve_hybrid_dense_bm25(question, pool, top_k)
    if mode == "hybrid_dense_bm25_rerank":
        return retrieve_hybrid_dense_bm25_rerank(question, pool, top_k)
    raise ValueError(f"Retrieval mode khong ho tro: {mode}")


def _boost_record_hits(hits: List[Any], record_id: str) -> List[Any]:
    if not record_id or not hits:
        return hits
    needle = f"record_id: {record_id}"
    matched = [h for h in hits if needle in (h.text or "")]
    rest = [h for h in hits if needle not in (h.text or "")]
    return matched + rest if matched else hits


def query_v3(
    question: str,
    retrieval_mode: str = "semantic_dense",
    top_k: int = FINAL_TOP_K,
    pool: int = CANDIDATE_POOL_SIZE,
    answer_mode: str = "extractive",
    llm_runtime: Any = None,
    record_id_hint: str = "",
) -> Dict[str, Any]:
    if is_insufficient_question(question):
        return {
            "question": question,
            "answer": INSUFFICIENT_ANSWER,
            "confidence": "low",
            "insufficient": True,
            "evidence": [],
            "mode": f"v3_{retrieval_mode}_extractive",
            "retrieval_mode": retrieval_mode,
            "llm_mode": "extractive",
        }

    try:
        hits, retrieve_note = retrieve(question, retrieval_mode, pool, top_k)
        if record_id_hint:
            hits = _boost_record_hits(hits, record_id_hint.strip())
    except Exception as exc:
        return {
            "question": question,
            "answer": INSUFFICIENT_ANSWER,
            "confidence": "low",
            "insufficient": True,
            "evidence": [],
            "mode": f"v3_{retrieval_mode}_error",
            "retrieval_mode": retrieval_mode,
            "retrieve_error": str(exc),
        }

    top_chunks = [
        {"source": h.source, "citation": h.source, "score": h.score, "text": h.text}
        for h in hits
    ]
    if record_id_hint:
        needle = f"record_id: {record_id_hint}"
        matched = [c for c in top_chunks if needle in (c.get("text") or "")]
        if matched:
            rest = [c for c in top_chunks if c not in matched]
            top_chunks = matched + rest
    evidence = [_to_evidence(h) for h in hits]
    context = "\n\n".join(
        f"[{i}] source={c['source']}\n{c['text'][:1200]}" for i, c in enumerate(top_chunks, 1)
    )

    llm_mode_label = "extractive"
    answer = build_answer(question, top_chunks) if top_chunks else INSUFFICIENT_ANSWER

    if answer_mode == "generative" and llm_runtime is not None:
        from llm_runtime import generate_answer, normalize_answer

        if getattr(llm_runtime, "status", None) == "ready":
            try:
                raw, llm_mode_label = generate_answer(context, question, llm_runtime)
                answer, insufficient_flag = normalize_answer(raw)
            except Exception as exc:
                answer = INSUFFICIENT_ANSWER
                insufficient_flag = True
                retrieve_note = f"{retrieve_note};llm_error:{exc}"
        else:
            answer = INSUFFICIENT_ANSWER
            insufficient_flag = True
    else:
        insufficient_flag = INSUFFICIENT_ANSWER.lower() in answer.lower() or not hits

    insufficient = insufficient_flag if answer_mode == "generative" else (
        INSUFFICIENT_ANSWER.lower() in answer.lower() or not hits
    )

    scores = [e.get("score") for e in evidence if e.get("score") is not None]
    conf = "low"
    if scores:
        best = max(scores)
        conf = "high" if best >= 0.55 else ("medium" if best >= 0.35 else "low")

    return {
        "question": question,
        "answer": answer,
        "confidence": conf,
        "insufficient": insufficient,
        "evidence": evidence,
        "mode": f"v3_{retrieval_mode}_{answer_mode}",
        "retrieval_mode": retrieval_mode,
        "llm_mode": llm_mode_label,
        "retrieve_note": retrieve_note,
        "rerank_status": _rerank_status,
        "reranker_effective_model": _rerank_effective_model,
    }
