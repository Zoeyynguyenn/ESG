"""Diagnostic metrics and fail taxonomy for enterprise internal-doc lane."""

from __future__ import annotations

import re
from typing import Any, Literal

from enterprise_docs.cross_doc_retriever import RetrievalResult

FailStage = Literal[
    "parser_gap",
    "retrieval_gap",
    "aggregation_gap",
    "synthesis_gap",
    "coverage_gap",
    "semantic_ambiguity",
    "ready",
]

NOT_DISCLOSED_RE = re.compile(r"not disclosed|미공시|공시.*없", re.I)


def detect_conflict(units: list[dict[str, Any]]) -> bool:
    """Approximation: 'Not disclosed' in one unit while numeric signal in another."""
    has_not_disclosed = False
    has_numeric = False
    for u in units:
        text = str(u.get("evidence_text") or u.get("text") or "")
        if NOT_DISCLOSED_RE.search(text):
            has_not_disclosed = True
        if re.search(r"\d{2,}", text):
            has_numeric = True
    return has_not_disclosed and has_numeric


def unit_has_signal(text: str, question: str) -> bool:
    """Approximation: overlap between question tokens and evidence text."""
    from rag_common import tokenize

    q = set(tokenize(question))
    c = set(tokenize(text))
    if not q:
        return bool(text.strip())
    return len(q.intersection(c)) >= max(1, len(q) // 4)


def classify_fail_stage(
    plan_row: dict[str, Any],
    result: RetrievalResult,
    *,
    aggregation_readiness: float,
    logical_to_corpus: dict[str, str] | None = None,
) -> tuple[FailStage, str]:
    logical_to_corpus = logical_to_corpus or {}
    company_id = str(plan_row.get("company_id") or "demo_company")

    if result.parser_fail:
        return "parser_gap", "empty_or_unparseable_evidence_units"

    primary_logical = list(plan_row.get("primary_document_ids") or [])
    supporting_logical = list(plan_row.get("supporting_document_ids") or [])
    all_planned = primary_logical + supporting_logical

    from enterprise_docs.registries import holdout_routing_profile, is_holdout_company

    holdout = holdout_routing_profile(company_id)
    if is_holdout_company(company_id) and holdout.get("require_primary_logical_map_only"):
        unmapped = [lid for lid in primary_logical if lid not in logical_to_corpus]
    else:
        unmapped = [lid for lid in all_planned if lid not in logical_to_corpus]
    if unmapped:
        return "coverage_gap", f"planned_doc_not_in_corpus:{','.join(unmapped)}"

    if result.evidence_plan_coverage < 0.5 or result.required_doc_hit_rate < 0.5:
        return "retrieval_gap", (
            f"coverage={result.evidence_plan_coverage},doc_hit={result.required_doc_hit_rate}"
        )

    if plan_row.get("needs_merge") and aggregation_readiness < 0.5:
        return "aggregation_gap", f"aggregation_readiness={aggregation_readiness}"

    if plan_row.get("kind") == "qualitative" and result.evidence_plan_coverage < 1.0:
        return "synthesis_gap", "qualitative_needs_full_doc_coverage_before_synthesis"

    if result.missing_roles or result.missing_docs:
        return "retrieval_gap", (
            f"missing_docs:{','.join(result.missing_docs)};"
            f"missing_roles:{','.join(result.missing_roles)}"
        )

    return "ready", "retrieval_sufficient_for_next_stage"


def evaluate_single_doc(
    plan_row: dict[str, Any],
    result: RetrievalResult,
    *,
    logical_to_corpus: dict[str, str] | None = None,
) -> dict[str, Any]:
    primary_logical = (plan_row.get("primary_document_ids") or [None])[0]
    primary_corpus = result.top_docs[0].corpus_document_id if result.top_docs else None

    doc_hit_at_1 = False
    if result.top_docs and primary_logical:
        doc_hit_at_1 = result.top_docs[0].logical_document_id == primary_logical
    elif result.top_docs and not primary_logical:
        doc_hit_at_1 = True

    required = list(plan_row.get("primary_document_ids") or [])
    top_doc_logical = [d.logical_document_id for d in result.top_docs[:3]]
    doc_hit_at_k = any(r in top_doc_logical for r in required) if required else bool(result.top_docs)

    unit_hit_at_k = any(
        unit_has_signal(u.evidence_text, result.question) for u in result.top_units
    )

    aggregation_readiness = 1.0 if not plan_row.get("needs_merge") else (
        1.0 if len({u.corpus_document_id for u in result.top_units}) >= 2 else 0.0
    )

    fail_stage, fail_reason = classify_fail_stage(
        plan_row,
        result,
        aggregation_readiness=aggregation_readiness,
        logical_to_corpus=logical_to_corpus,
    )
    single_ready = (
        not result.parser_fail
        and doc_hit_at_k
        and unit_hit_at_k
        and result.evidence_plan_coverage >= 0.99
        and fail_stage == "ready"
    )

    return {
        "doc_hit_at_1": doc_hit_at_1,
        "doc_hit_at_k": doc_hit_at_k,
        "unit_hit_at_k": unit_hit_at_k,
        "parser_fail": result.parser_fail,
        "parser_fail_rate": 1.0 if result.parser_fail else 0.0,
        "aggregation_readiness": aggregation_readiness,
        "single_doc_ready": single_ready,
        "fail_stage": fail_stage,
        "fail_reason": fail_reason,
        "primary_corpus_document_id": primary_corpus,
    }


def evaluate_cross_doc(
    plan_row: dict[str, Any],
    result: RetrievalResult,
    *,
    logical_to_corpus: dict[str, str] | None = None,
) -> dict[str, Any]:
    required_logical = list(
        dict.fromkeys(
            list(plan_row.get("primary_document_ids") or [])
            + list(plan_row.get("supporting_document_ids") or [])
        )
    )
    hit_logical = {u.logical_document_id for u in result.top_units}
    hit_docs = {d.logical_document_id for d in result.top_docs}

    multi_doc_recall = (
        sum(1 for r in required_logical if r in hit_logical) / max(1, len(required_logical))
    )
    required_doc_hit_rate = result.required_doc_hit_rate
    evidence_plan_coverage = result.evidence_plan_coverage

    unique_docs_in_units = len({u.corpus_document_id for u in result.top_units})
    needs_n = max(2, min(len(required_logical), 2))
    aggregation_readiness = (
        1.0
        if not plan_row.get("needs_merge")
        else min(1.0, unique_docs_in_units / needs_n)
    )

    unit_texts = [{"evidence_text": u.evidence_text} for u in result.top_units]
    conflict_detected = detect_conflict(unit_texts) if plan_row.get("needs_conflict_resolution") else detect_conflict(unit_texts)

    missing_role_rate = (
        len(result.missing_roles) / max(1, len(plan_row.get("roles") or {}))
    )

    fail_stage, fail_reason = classify_fail_stage(
        plan_row,
        result,
        aggregation_readiness=aggregation_readiness,
        logical_to_corpus=logical_to_corpus,
    )

    cross_ready = (
        not result.parser_fail
        and multi_doc_recall >= 0.5
        and evidence_plan_coverage >= 0.5
        and (not plan_row.get("needs_merge") or aggregation_readiness >= 0.5)
        and fail_stage in ("ready", "synthesis_gap")
    )

    return {
        "multi_doc_recall": round(multi_doc_recall, 4),
        "evidence_plan_coverage": evidence_plan_coverage,
        "required_doc_hit_rate": required_doc_hit_rate,
        "aggregation_readiness": round(aggregation_readiness, 4),
        "missing_role_rate": round(missing_role_rate, 4),
        "conflict_detected": conflict_detected,
        "conflict_detected_rate": 1.0 if conflict_detected else 0.0,
        "parser_fail": result.parser_fail,
        "parser_fail_rate": 1.0 if result.parser_fail else 0.0,
        "cross_doc_ready": cross_ready,
        "fail_stage": fail_stage,
        "fail_reason": fail_reason,
        "unique_docs_in_units": unique_docs_in_units,
        "hit_logical_docs": sorted(hit_logical),
        "hit_top_docs": sorted(hit_docs),
    }


def aggregate_metrics(rows: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    if not rows:
        return {}
    n = len(rows)

    def rate(key: str) -> float:
        return round(sum(1 for r in rows if r.get(key)) / n, 4)

    def mean(key: str) -> float:
        vals = [float(r.get(key) or 0) for r in rows]
        return round(sum(vals) / max(1, len(vals)), 4)

    if mode == "single_document_answer":
        return {
            "count": n,
            "doc_hit_at_1": rate("doc_hit_at_1"),
            "doc_hit_at_k": rate("doc_hit_at_k"),
            "unit_hit_at_k": rate("unit_hit_at_k"),
            "parser_fail_rate": mean("parser_fail_rate"),
            "single_doc_ready_rate": rate("single_doc_ready"),
            "fail_stage_counts": _count_fail_stages(rows),
        }

    return {
        "count": n,
        "multi_doc_recall": mean("multi_doc_recall"),
        "evidence_plan_coverage": mean("evidence_plan_coverage"),
        "required_doc_hit_rate": mean("required_doc_hit_rate"),
        "aggregation_readiness": mean("aggregation_readiness"),
        "missing_role_rate": mean("missing_role_rate"),
        "conflict_detected_rate": mean("conflict_detected_rate"),
        "parser_fail_rate": mean("parser_fail_rate"),
        "cross_doc_ready_rate": rate("cross_doc_ready"),
        "fail_stage_counts": _count_fail_stages(rows),
    }


def _count_fail_stages(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        stage = str(r.get("fail_stage") or "unknown")
        counts[stage] = counts.get(stage, 0) + 1
    return counts
