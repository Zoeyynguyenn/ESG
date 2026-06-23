"""Formal review-owner resolution for LangGraph handoff preparation."""

from __future__ import annotations

from typing import Any

REVIEW_OWNER_POLICY_VERSION = "1.1.0"

# Canonical owner labels (downstream contract)
OWNER_RAG = "RAG"
OWNER_SME = "SME"
OWNER_DATASET = "Dataset"
OWNER_NONE = "None"

# Readiness states that always block handoff (no owner — blocked path)
_BLOCKED_STATES = frozenset({
    "not_ready_for_synthesis",
    "honest_abstain",
})


def export_review_owner_rules() -> dict[str, Any]:
    return {
        "version": REVIEW_OWNER_POLICY_VERSION,
        "description": "Review owner assignment for LangGraph handoff preparation (not runtime trial)",
        "owners": [OWNER_RAG, OWNER_SME, OWNER_DATASET, OWNER_NONE],
        "priority_order": [
            "terminal_readiness_state",
            "kind_qualitative",
            "coverage_gap",
            "needs_sme_review",
            "wrong_row_risk",
            "confidence_calibration",
            "promoted_clean",
        ],
        "rules": [
            {
                "id": "qualitative_blocked",
                "condition": "kind == qualitative",
                "owner": None,
                "prep_status": "handoff_blocked",
                "reason": "qualitative_requires_synthesis_not_extractive_handoff",
            },
            {
                "id": "not_ready_for_synthesis",
                "condition": "readiness_state == not_ready_for_synthesis",
                "owner": None,
                "prep_status": "handoff_blocked",
                "reason": "synthesis_blocker",
            },
            {
                "id": "coverage_gap",
                "condition": "readiness_state == coverage_gap OR blocker coverage",
                "owner": OWNER_DATASET,
                "prep_status": "needs_manual_review_before_handoff",
                "reason": "corpus_or_logical_doc_gap",
            },
            {
                "id": "needs_sme_review",
                "condition": "readiness_state == needs_sme_review OR wrong_row_risk",
                "owner": OWNER_SME,
                "prep_status": "needs_manual_review_before_handoff",
                "reason": "sme_validation_required",
            },
            {
                "id": "confidence_below_family_min",
                "condition": "promoted AND confidence < family_min AND NOT wrong_row_risk",
                "owner": OWNER_RAG,
                "prep_status": "needs_manual_review_before_handoff",
                "reason": "confidence_policy_calibration",
            },
            {
                "id": "retrieval_or_extraction_not_promoted",
                "condition": "readiness_state in (retrieval_ready, extraction_ready) AND NOT promoted",
                "owner": OWNER_RAG,
                "prep_status": "handoff_blocked",
                "reason": "extraction_or_retrieval_incomplete",
            },
            {
                "id": "promoted_adequate_confidence",
                "condition": "promoted AND single_source_sufficient AND confidence >= family_min",
                "owner": OWNER_NONE,
                "prep_status": "handoff_allowed_for_preparation",
                "reason": "family_contract_met",
            },
            {
                "id": "promoted_multi_source",
                "condition": "promoted AND multi_source_sufficient",
                "owner": OWNER_NONE,
                "prep_status": "handoff_allowed_for_preparation",
                "reason": "multi_source_contract_met",
            },
            {
                "id": "default_blocked",
                "condition": "fallback",
                "owner": OWNER_RAG,
                "prep_status": "handoff_blocked",
                "reason": "prep_conditions_not_met",
            },
        ],
        "family_overrides": {
            "governance": {
                "narrative_promoted_borderline_conf": OWNER_SME,
                "note": "Governance narrative metrics default SME when confidence < 0.35 on holdout",
            },
            "environment_ghg": {
                "unresolved_conflict": OWNER_SME,
            },
            "employee_headcount": {
                "wrong_row_risk": OWNER_SME,
            },
        },
        "metric_types": {
            "exact": ["needs_review_by when rule matches"],
            "heuristic": ["governance borderline SME override"],
        },
    }


def resolve_review_owner(
    *,
    readiness_state: str,
    kind: str,
    promoted: bool,
    confidence: float,
    family_min_confidence: float,
    blockers: list[str] | None = None,
    wrong_row_risk: bool = False,
    family_id: str | None = None,
    company_role: str = "dev",
) -> dict[str, Any]:
    """Return needs_review_by, prep_status, and rule_id."""
    blockers = list(blockers or [])
    state = str(readiness_state or "")
    kind_s = str(kind or "")

    if kind_s == "qualitative":
        return _result(None, "handoff_blocked", "qualitative_blocked", "qualitative_requires_synthesis")

    if state in _BLOCKED_STATES:
        return _result(None, "handoff_blocked", "not_ready_for_synthesis", "synthesis_blocker")

    if state == "coverage_gap" or any("coverage" in b for b in blockers):
        return _result(OWNER_DATASET, "needs_manual_review_before_handoff", "coverage_gap", "corpus_gap")

    if state == "needs_sme_review" or wrong_row_risk or "wrong_row_risk" in blockers:
        return _result(OWNER_SME, "needs_manual_review_before_handoff", "needs_sme_review", "sme_validation")

    if promoted and state in ("single_source_sufficient", "multi_source_sufficient"):
        gov_borderline = (
            family_id == "governance"
            and company_role == "holdout"
            and confidence < 0.35
            and confidence >= family_min_confidence
        )
        if gov_borderline:
            return _result(
                OWNER_SME,
                "needs_manual_review_before_handoff",
                "governance_holdout_borderline",
                "governance_narrative_borderline_confidence",
            )
        if confidence < family_min_confidence:
            return _result(
                OWNER_RAG,
                "needs_manual_review_before_handoff",
                "confidence_below_family_min",
                "confidence_calibration",
            )
        return _result(OWNER_NONE, "handoff_allowed_for_preparation", "promoted_clean", "family_contract_met")

    if state in ("retrieval_ready", "extraction_ready") and not promoted:
        return _result(OWNER_RAG, "handoff_blocked", "retrieval_or_extraction_not_promoted", "pipeline_incomplete")

    if "confidence_below_min" in blockers:
        return _result(OWNER_RAG, "handoff_blocked", "confidence_blocker", "confidence_below_min")

    if "missing_predicted_value" in blockers or "evidence_bundle_insufficient" in blockers:
        return _result(OWNER_RAG, "handoff_blocked", "package_incomplete", "evidence_package_gap")

    return _result(OWNER_RAG, "handoff_blocked", "default_blocked", "prep_conditions_not_met")


def _result(
    owner: str | None,
    prep_status: str,
    rule_id: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "needs_review_by": owner,
        "prep_status": prep_status,
        "review_owner_rule_id": rule_id,
        "review_owner_reason": reason,
    }
