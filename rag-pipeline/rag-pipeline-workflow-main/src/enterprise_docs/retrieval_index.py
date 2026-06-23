"""BM25 index for enterprise evidence units (separate from dataset_excel)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from rag_common import overlap_score, tokenize

try:
    from rank_bm25 import BM25Okapi
except ImportError:  # pragma: no cover
    BM25Okapi = None


def unit_search_text(unit: dict[str, Any]) -> str:
    return str(unit.get("search_text") or unit.get("text") or "")


def build_corpus_index(units: list[dict[str, Any]]) -> dict[str, Any]:
    by_company: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in units:
        by_company[str(unit.get("company_id") or "default")].append(unit)

    indexes: dict[str, Any] = {}
    for company_id, company_units in by_company.items():
        tokenized = [tokenize(unit_search_text(u)) for u in company_units]
        bm25 = BM25Okapi(tokenized) if BM25Okapi is not None else None
        indexes[company_id] = {
            "units": company_units,
            "bm25": bm25,
            "tokenized": tokenized,
        }
    return indexes


def score_units(
    question: str,
    index: dict[str, Any],
    *,
    pool: int = 48,
) -> list[tuple[dict[str, Any], float]]:
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
        scores[i] = 0.6 * scores[i] + 0.4 * lexical

    ranked = sorted(zip(units, scores), key=lambda x: x[1], reverse=True)
    return ranked[:pool]
