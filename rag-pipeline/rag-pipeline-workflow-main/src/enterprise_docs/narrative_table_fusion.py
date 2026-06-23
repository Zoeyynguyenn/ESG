"""Narrative <-> table candidate alignment for cross-document fusion."""

from __future__ import annotations

import re
from typing import Any

from enterprise_docs.fusion_equivalence import canonical_metric_label_key, normalize_numeric_value
from enterprise_docs.structured_extractor import RowMatchCandidate, score_row_match


def _item_relevant(label: str, plan_row: dict[str, Any], min_score: float = 0.35) -> bool:
    item = str(plan_row.get("item") or "")
    if not item:
        return True
    score, _ = score_row_match(label, plan_row)
    if score >= min_score:
        return True
    label_l = label.lower()
    item_l = item.lower()
    return item_l in label_l or any(tok in label_l for tok in item_l.split() if len(tok) >= 2)


def filter_candidates_for_plan_item(
    candidates: list[RowMatchCandidate],
    plan_row: dict[str, Any],
    *,
    min_score: float = 0.35,
) -> list[RowMatchCandidate]:
    """Drop spurious cross-metric hits (e.g. Scope 1 from Scope 1+2 when item is total GHG)."""
    item = str(plan_row.get("item") or "")
    if not item:
        return candidates
    kept: list[RowMatchCandidate] = []
    for c in candidates:
        label = str(c.label or "")
        val = str(c.value or "")
        if re.search(r"scope\s*1\+2|scope\s*1\s*\+\s*2", label, re.I):
            if "총" in item or "total" in item.lower() or "온실가스" in item:
                continue
        if re.fullmatch(r"[0123]", val) and ("scope" in label.lower() or "스코프" in label or "ghg" in label.lower()):
            if "총" in item or "total" in item.lower() or "온실가스" in item:
                continue
        if _item_relevant(label, plan_row, min_score=min_score):
            kept.append(c)
        elif _item_relevant(val, plan_row, min_score=min_score * 0.8):
            kept.append(c)
        elif normalize_numeric_value(val) and score_row_match(item, plan_row)[0] >= 0.85:
            kept.append(c)

    if item and ("총" in item or "온실가스" in item):
        large = []
        for c in kept:
            nv = normalize_numeric_value(c.value)
            try:
                if nv and float(nv) >= 10:
                    large.append(c)
            except ValueError:
                large.append(c)
        if large:
            kept = large
        else:
            kept = [c for c in kept if not re.fullmatch(r"[0123]", str(c.value or ""))]

    return kept if kept else candidates


def best_candidate_per_logical_doc(
    candidates: list[RowMatchCandidate],
    plan_row: dict[str, Any],
) -> list[RowMatchCandidate]:
    """Keep highest-scoring candidate per logical doc for fusion comparison."""
    by_doc: dict[str, RowMatchCandidate] = {}
    for c in candidates:
        lid = str(c.logical_doc or "")
        if not lid:
            continue
        prev = by_doc.get(lid)
        if prev is None or c.row_match_score > prev.row_match_score:
            by_doc[lid] = c
    return list(by_doc.values())


def narrative_table_fusion_preview(
    candidates: list[RowMatchCandidate],
    plan_row: dict[str, Any],
) -> dict[str, Any]:
    filtered = filter_candidates_for_plan_item(candidates, plan_row)
    per_doc = best_candidate_per_logical_doc(filtered, plan_row)
    groups: dict[str, list[str]] = {}
    for c in per_doc:
        gk = canonical_metric_label_key(c.label, plan_row)
        groups.setdefault(gk, []).append(str(c.logical_doc or ""))
    return {
        "filtered_count": len(filtered),
        "per_doc_count": len(per_doc),
        "metric_groups": groups,
        "values_by_doc": {str(c.logical_doc): c.value for c in per_doc},
    }
