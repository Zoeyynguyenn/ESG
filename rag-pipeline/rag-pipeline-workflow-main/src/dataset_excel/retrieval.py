"""BM25 + heuristic retrieval for dataset-excel eval."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from dataset_excel.extractor_utils import unit_evidence_text, unit_search_text
from dataset_excel.family_router import heuristic_boost
from dataset_excel.profile import QuestionProfile
from rag_common import overlap_score, tokenize

try:
    from rank_bm25 import BM25Okapi
except ImportError:  # pragma: no cover
    BM25Okapi = None


def build_index(units: list[dict[str, Any]]) -> dict[str, Any]:
    by_company: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in units:
        by_company[unit["company_id"]].append(unit)

    indexes: dict[str, Any] = {}
    for company_id, company_units in by_company.items():
        tokenized = [tokenize(unit_search_text(u)) for u in company_units]
        bm25 = BM25Okapi(tokenized) if BM25Okapi is not None else None
        indexes[company_id] = {"units": company_units, "bm25": bm25, "tokenized": tokenized}
    return indexes


def retrieve(
    question: str,
    company_id: str,
    index: dict[str, Any],
    profile: QuestionProfile,
    *,
    top_k: int = 5,
    pool: int = 32,
) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = index["units"]
    if not units:
        return []

    bm25 = index.get("bm25")
    q_tokens = tokenize(question)
    if bm25 is not None and q_tokens:
        scores = list(bm25.get_scores(q_tokens))
    else:
        scores = [overlap_score(question, unit_search_text(unit)) for unit in units]

    for i, unit in enumerate(units):
        lexical = overlap_score(question, unit_search_text(unit))
        scores[i] = 0.55 * scores[i] + 0.25 * lexical + heuristic_boost(profile, unit)

    ranked = sorted(zip(units, scores), key=lambda x: x[1], reverse=True)[:pool]
    hits: list[dict[str, Any]] = []
    for unit, score in ranked[:top_k]:
        meta = unit.get("metadata") if isinstance(unit.get("metadata"), dict) else {}
        hits.append(
            {
                "chunk_id": unit["chunk_id"],
                "source": unit.get("source_path") or unit.get("doc_title") or "",
                "score": round(float(score), 4),
                "search_text": unit_search_text(unit)[:1200],
                "evidence_text": unit_evidence_text(unit)[:1200],
                "metadata": {
                    "company_id": unit.get("company_id"),
                    "doc_title": unit.get("doc_title"),
                    "source_url": unit.get("source_url"),
                    "file_url": unit.get("file_url"),
                    "source_kind": unit.get("source_kind"),
                    "year": unit.get("year"),
                    "schema": unit.get("schema"),
                    "sanction_lane": unit.get("sanction_lane") or meta.get("sanction_lane"),
                },
            }
        )
    return hits
