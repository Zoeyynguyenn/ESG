"""System-level readiness model for enterprise internal-doc lane."""

from __future__ import annotations

from typing import Any, Literal

from enterprise_docs.diagnostics import evaluate_cross_doc, evaluate_single_doc
from enterprise_docs.evidence_aggregator import aggregate_cross_doc
from enterprise_docs.structured_extractor import extract_from_retrieval

ReadinessState = Literal[
    "retrieval_ready",
    "extraction_ready",
    "aggregation_ready",
    "single_source_sufficient",
    "multi_source_sufficient",
    "honest_abstain",
    "coverage_gap",
    "needs_sme_review",
    "not_ready_for_synthesis",
]


def assess_readiness(
    plan_row: dict[str, Any],
    ret,
    *,
    unit_lookup: dict[str, dict[str, Any]] | None = None,
    logical_to_corpus: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Derive canonical readiness state from retrieval + extraction + aggregation."""
    unit_lookup = unit_lookup or {}
    logical_to_corpus = logical_to_corpus or {}
    kind = str(plan_row.get("kind") or "")
    answer_mode = str(plan_row.get("answer_mode") or "")

    if answer_mode == "single_document_answer":
        diag = evaluate_single_doc(plan_row, ret, logical_to_corpus=logical_to_corpus)
        ext = extract_from_retrieval(
            plan_row, ret, unit_lookup=unit_lookup, retrieval_ready=bool(diag.get("single_doc_ready"))
        )
        agg = None
    else:
        diag = evaluate_cross_doc(plan_row, ret, logical_to_corpus=logical_to_corpus)
        ext = extract_from_retrieval(plan_row, ret, unit_lookup=unit_lookup, retrieval_ready=True)
        agg = aggregate_cross_doc(plan_row, ret, unit_lookup=unit_lookup, logical_to_corpus=logical_to_corpus)

    fail_stage = str(diag.get("fail_stage") or "")
    readiness: ReadinessState
    reason = fail_stage

    if fail_stage == "coverage_gap":
        readiness = "coverage_gap"
    elif kind == "qualitative":
        readiness = "not_ready_for_synthesis"
        reason = "qualitative_requires_synthesis_gate"
    elif ext.extraction_reason == "source_not_disclosed_for_metric":
        readiness = "honest_abstain"
        reason = ext.extraction_reason
    elif agg and agg.sufficiency_status == "resolved_single_source_sufficient":
        readiness = "single_source_sufficient"
        reason = agg.sufficiency_reason or agg.sufficiency_status
    elif agg and agg.aggregation_status == "success" and agg.sufficiency_status == "resolved":
        readiness = "multi_source_sufficient"
        reason = agg.sufficiency_reason or "multi_role_resolved"
    elif agg and agg.aggregation_status == "success":
        readiness = "aggregation_ready"
        reason = agg.aggregation_reason
    elif ext.success and not plan_row.get("needs_merge"):
        readiness = "extraction_ready"
        reason = ext.extraction_reason
    elif diag.get("single_doc_ready") or diag.get("cross_doc_ready"):
        if ext.success:
            readiness = "extraction_ready"
            reason = ext.extraction_reason
        elif ext.wrong_row_risk:
            readiness = "needs_sme_review"
            reason = ext.wrong_row_risk_reason or "wrong_row_risk"
        else:
            readiness = "retrieval_ready"
            reason = diag.get("fail_reason") or "retrieval_ok_extraction_pending"
    elif fail_stage == "retrieval_gap":
        readiness = "retrieval_ready"
        reason = diag.get("fail_reason") or fail_stage
        # retrieval NOT ready — downgrade label
        readiness = "coverage_gap" if "planned_doc_not_in_corpus" in str(diag.get("fail_reason")) else "retrieval_ready"
        if readiness == "retrieval_ready" and not ret.top_units:
            readiness = "coverage_gap"
            reason = "no_units_retrieved"
    elif fail_stage == "aggregation_gap":
        readiness = "aggregation_ready" if ext.success else "extraction_ready"
        reason = diag.get("fail_reason") or fail_stage
    elif ext.wrong_row_risk:
        readiness = "needs_sme_review"
        reason = ext.wrong_row_risk_reason or "wrong_row_risk"
    else:
        readiness = "not_ready_for_synthesis" if kind == "qualitative" else "retrieval_ready"
        reason = fail_stage or "unknown"

    # Fix mis-label: retrieval_ready should mean retrieval layer OK
    retrieval_ok = bool(ret.top_units) and not ret.parser_fail and fail_stage not in ("parser_gap", "coverage_gap")
    if readiness == "retrieval_ready" and not retrieval_ok:
        readiness = "coverage_gap"
        reason = diag.get("fail_reason") or "retrieval_not_sufficient"

    return {
        "item_id": plan_row.get("item_id"),
        "kind": kind,
        "answer_mode": answer_mode,
        "readiness_state": readiness,
        "readiness_reason": reason,
        "retrieval_ok": retrieval_ok,
        "extraction_success": ext.success,
        "aggregation_status": agg.aggregation_status if agg else None,
        "sufficiency_status": agg.sufficiency_status if agg else None,
        "resolved_value": agg.resolved_value if agg else ext.predicted_value,
        "fail_stage": fail_stage,
        "open_synthesis_allowed": readiness in (
            "multi_source_sufficient",
            "single_source_sufficient",
            "aggregation_ready",
        )
        and kind == "quantitative",
    }


def summarize_readiness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    by_kind: dict[str, dict[str, int]] = {}
    by_mode: dict[str, dict[str, int]] = {}

    for r in rows:
        state = str(r.get("readiness_state") or "unknown")
        kind = str(r.get("kind") or "unknown")
        mode = str(r.get("answer_mode") or "unknown")
        counts[state] = counts.get(state, 0) + 1
        by_kind.setdefault(kind, {})
        by_kind[kind][state] = by_kind[kind].get(state, 0) + 1
        by_mode.setdefault(mode, {})
        by_mode[mode][state] = by_mode[mode].get(state, 0) + 1

    n = max(1, len(rows))
    quant = [r for r in rows if r.get("kind") == "quantitative"]
    qual = [r for r in rows if r.get("kind") == "qualitative"]
    synthesis_allowed = sum(1 for r in rows if r.get("open_synthesis_allowed"))

    return {
        "total": len(rows),
        "readiness_counts": counts,
        "readiness_rates": {k: round(v / n, 4) for k, v in counts.items()},
        "by_kind": by_kind,
        "by_answer_mode": by_mode,
        "quantitative_count": len(quant),
        "qualitative_count": len(qual),
        "synthesis_gate_allowed_count": synthesis_allowed,
        "synthesis_gate_allowed_rate_quant": round(
            sum(1 for r in quant if r.get("open_synthesis_allowed")) / max(1, len(quant)), 4
        ),
    }
