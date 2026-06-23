"""Version 6: conflict resolution by source quality ranking."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from extraction_v4 import (
    extract_value_from_text,
    _assign_status_confidence,
    _best_snippet,
)
from retrieval_v3 import RankedChunk

SOURCE_RANK_RULES: List[Tuple[str, int]] = [
    ("environment_policy", 100),
    ("social_policy", 95),
    ("governance_policy", 95),
    ("company_overview", 80),
    ("compliance_faq", 65),
    ("product_internal_faq", 55),
    ("sources.md", 50),
    ("dataset_readme", 40),
    ("esg_eval_guidelines", 5),
]


def source_rank(source: str, strict: bool = False) -> int:
    s = source.lower().replace("\\", "/")
    best = 0
    for key, score in SOURCE_RANK_RULES:
        if key in s:
            best = max(best, score)
    if "01_synthetic_controlled" in s:
        best = max(best, 70 if not strict else 55)
    if "02_esg_public" in s or "03_esg_public" in s:
        best = max(best, 75 if strict else 68)
    if strict and "esg_eval_guidelines" in s:
        best = min(best, 1)
    if strict and "dataset_readme" in s:
        best = min(best, 15)
    return best


def rank_hits(
    hits: List[RankedChunk],
    source_bias: Optional[List[str]] = None,
    strict: bool = False,
) -> List[RankedChunk]:
    bias = source_bias or []

    def key(h: RankedChunk) -> Tuple[int, float]:
        rank = source_rank(h.source, strict=strict)
        if any(b in h.source.lower() for b in bias):
            rank += 25 if not strict else 35
        return (rank, h.score)

    return sorted(hits, key=key, reverse=True)


def resolve_from_hits(
    field: Dict[str, Any],
    hits: List[RankedChunk],
    query: str,
    source_bias: Optional[List[str]] = None,
    strict: bool = False,
) -> Dict[str, Any]:
    """Chon value tu hit co source tot nhat; ghi trace + reason code."""
    ranked = rank_hits(hits, source_bias, strict=strict)
    candidates: List[Dict[str, Any]] = []
    for h in ranked[:8]:
        val = extract_value_from_text(field, h.text)
        if val is not None:
            candidates.append(
                {
                    "value": val,
                    "source": h.source,
                    "score": round(h.score, 4),
                    "source_rank": source_rank(h.source, strict=strict),
                    "snippet": h.text[:200],
                }
            )

    trace = {
        "resolver": "source_quality_ranking_strict" if strict else "source_quality_ranking",
        "candidates": candidates,
        "rule": "policy > social/governance > public > overview > faq >> guidelines",
        "strict_mode": strict,
    }

    if not candidates:
        return {"resolved": False, "trace": trace, "resolve_reason": "no_candidates"}

    best = max(candidates, key=lambda c: (c["source_rank"], c["score"]))
    runners = [c for c in candidates if c["value"] != best["value"]]
    if runners:
        reason = "source_rank_winner_over_alternate_values"
    elif best["source_rank"] >= (85 if strict else 80):
        reason = "high_trust_policy_source"
    else:
        reason = "best_available_retrieval_score"

    status, confidence = _assign_status_confidence(
        best["value"], best["score"], False, field, best["source"]
    )
    min_rank = 85 if strict else 80
    if best["source_rank"] >= min_rank:
        status = "verified"
        confidence = "high" if confidence != "low" else "medium"

    return {
        "resolved": True,
        "value": best["value"],
        "source": best["source"],
        "citation": best["source"],
        "evidence_text": _best_snippet(
            next(h.text for h in ranked if h.source == best["source"]),
            query,
        ),
        "confidence": confidence,
        "status": status,
        "selected_source_rank": best["source_rank"],
        "resolve_reason": reason,
        "trace": trace,
    }
