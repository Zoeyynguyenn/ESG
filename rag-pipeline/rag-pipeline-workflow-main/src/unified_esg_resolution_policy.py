"""Resolution policy for unified ESG answer layer — dataset + internal-doc."""

from __future__ import annotations

import re
from typing import Any

POLICY_VERSION = "unified_esg_resolution_v1"

RESOLUTION_STATUSES = (
    "MATCH_CONFIRMED",
    "BACKFILL_FROM_INTERNAL",
    "BACKFILL_FROM_DATASET",
    "CONFLICT_REVIEW_REQUIRED",
    "NO_ANSWER_FOUND",
    "INSUFFICIENT_EVIDENCE",
)

AUTO_CONFIRM_STATUSES = frozenset({"MATCH_CONFIRMED", "BACKFILL_FROM_DATASET"})
REVIEW_REQUIRED_STATUSES = frozenset({"CONFLICT_REVIEW_REQUIRED", "INSUFFICIENT_EVIDENCE"})

# Dataset question_family -> internal-doc family_id (pilot alignment)
FAMILY_ALIASES: dict[str, str] = {
    "employee_status": "employee_headcount",
    "employee_headcount": "employee_headcount",
    "environment_ghg": "environment_ghg",
    "climate": "environment_ghg",
    "governance": "governance",
    "financial": "governance",
    "financial_tax": "governance",
    "board_director": "governance",
}

DEFAULT_POLICY: dict[str, Any] = {
    "version": POLICY_VERSION,
    "identity": {
        "primary_key": "question_id",
        "fallback_business_key": ["company_id", "family_id", "metric_name", "year"],
        "metric_name_normalize": "strip_lower_collapse_ws",
    },
    "answer_presence": {
        "dataset_has_answer": "predicted_answer not null and not predicted_abstain",
        "internal_has_answer": "extraction_success and value not null and sufficiency not failed",
    },
    "value_equivalence": {
        "numeric_tolerance": 0.01,
        "strip_commas": True,
        "case_insensitive_text": True,
        "treat_abstain_as_no_answer": True,
    },
    "resolution_rules": [
        {
            "order": 1,
            "when": "neither_source_has_answer",
            "status": "NO_ANSWER_FOUND",
            "best_answer_origin": None,
            "auto_confirm": False,
            "review_required": False,
        },
        {
            "order": 2,
            "when": "only_dataset_has_answer",
            "status": "BACKFILL_FROM_DATASET",
            "best_answer_origin": "dataset",
            "auto_confirm": True,
            "review_required": False,
            "note": "Public/source-based RAG answer when internal-doc absent",
        },
        {
            "order": 3,
            "when": "only_internal_has_answer",
            "status": "BACKFILL_FROM_INTERNAL",
            "best_answer_origin": "internal_doc",
            "auto_confirm_if": "internal_confidence >= 0.85 and sufficiency_resolved",
            "candidate_only_if": "internal_confidence < 0.85 or not extraction_success",
            "review_required_if": "not auto_confirm",
        },
        {
            "order": 4,
            "when": "both_have_answer_and_values_match",
            "status": "MATCH_CONFIRMED",
            "best_answer_origin": "both_confirmed",
            "prefer_evidence_from": "internal_doc",
            "prefer_canonical_from": "dataset",
            "auto_confirm": True,
            "review_required": False,
        },
        {
            "order": 5,
            "when": "both_have_answer_and_values_conflict",
            "status": "CONFLICT_REVIEW_REQUIRED",
            "best_answer_origin": "unresolved",
            "auto_confirm": False,
            "review_required": True,
            "review_owner_hint": "SME",
            "tie_break_guidance": (
                "Company SR/internal-doc wins for company-specific narrative metrics "
                "when multi_source_confirmed; dataset/public source wins for regulatory filings"
            ),
        },
        {
            "order": 6,
            "when": "partial_signal_below_threshold",
            "status": "INSUFFICIENT_EVIDENCE",
            "best_answer_origin": "candidate",
            "auto_confirm": False,
            "review_required": True,
            "review_owner_hint": "RAG",
        },
    ],
    "business_decisions": {
        "prefer_internal_doc_when": [
            "multi_source_confirmed on internal record",
            "company-specific SR metric with primary_evidence from sustainability_report",
            "dataset absent or abstained",
        ],
        "prefer_dataset_when": [
            "regulatory/public filing source (DART, government)",
            "internal-doc extraction_success false",
            "MATCH_CONFIRMED — dataset provides canonical gold alignment",
        ],
        "sme_review_when": [
            "CONFLICT_REVIEW_REQUIRED",
            "semantic_ambiguity on dataset row",
            "internal conflict_status in conflict_numeric, conflict_text",
        ],
        "auto_confirm_when": [
            "MATCH_CONFIRMED",
            "BACKFILL_FROM_DATASET with answer_correct",
            "BACKFILL_FROM_INTERNAL with confidence >= 0.85 and sufficiency resolved",
        ],
        "do_not_auto_confirm_when": [
            "CONFLICT_REVIEW_REQUIRED",
            "INSUFFICIENT_EVIDENCE",
            "internal readiness_state not_ready_for_synthesis with only candidate value",
        ],
    },
    "thresholds": {
        "internal_auto_confirm_confidence": 0.85,
        "internal_min_candidate_confidence": 0.5,
        "dataset_trust_answer_correct": True,
    },
}


def normalize_metric_name(name: str | None) -> str:
    if not name:
        return ""
    text = str(name).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_year(year: Any) -> str:
    if year is None or year == "":
        return ""
    try:
        return str(int(year))
    except (TypeError, ValueError):
        return str(year).strip()


def map_dataset_family(question_family: str | None) -> str:
    fam = str(question_family or "").strip()
    return FAMILY_ALIASES.get(fam, fam or "unknown")


def normalize_value(value: Any, *, policy: dict[str, Any] | None = None) -> str:
    if value is None:
        return ""
    policy = policy or DEFAULT_POLICY
    equiv = policy.get("value_equivalence") or {}
    text = str(value).strip()
    if equiv.get("strip_commas"):
        text = text.replace(",", "")
    if equiv.get("case_insensitive_text"):
        text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


def values_equivalent(
    a: Any,
    b: Any,
    *,
    policy: dict[str, Any] | None = None,
) -> bool:
    policy = policy or DEFAULT_POLICY
    na, nb = normalize_value(a, policy=policy), normalize_value(b, policy=policy)
    if not na and not nb:
        return True
    if not na or not nb:
        return False
    if na == nb:
        return True
    tol = float((policy.get("value_equivalence") or {}).get("numeric_tolerance", 0.01))
    try:
        fa, fb = float(na), float(nb)
        return abs(fa - fb) <= tol
    except ValueError:
        return False


def dataset_has_answer(row: dict[str, Any], *, policy: dict[str, Any] | None = None) -> bool:
    policy = policy or DEFAULT_POLICY
    if row.get("predicted_abstain"):
        return False
    pred = row.get("predicted_answer")
    if pred is None or str(pred).strip() == "":
        return False
    return True


def internal_has_answer(row: dict[str, Any], *, policy: dict[str, Any] | None = None) -> bool:
    if not row.get("extraction_success"):
        return False
    val = row.get("value")
    if val is None or str(val).strip() == "":
        return False
    if row.get("sufficiency_status") == "failed":
        return False
    if row.get("value_type") == "not_disclosed":
        return False
    return True


def internal_sufficiency_resolved(row: dict[str, Any]) -> bool:
    suff = str(row.get("sufficiency_status") or "")
    if suff in ("resolved", "resolved_single_source_sufficient"):
        return True
    conflict = str(row.get("conflict_status") or "")
    return conflict in ("single_source_sufficient", "resolved")


def resolve_pair(
    dataset_row: dict[str, Any] | None,
    internal_row: dict[str, Any] | None,
    *,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply resolution policy to a matched pair (either side may be None)."""
    policy = policy or DEFAULT_POLICY
    thresholds = policy.get("thresholds") or {}

    ds_present = dataset_row is not None and dataset_has_answer(dataset_row, policy=policy)
    in_present = internal_row is not None and internal_has_answer(internal_row, policy=policy)

    ds_val = (dataset_row or {}).get("predicted_answer") or (dataset_row or {}).get("gold_answer_raw")
    in_val = (internal_row or {}).get("value")
    in_conf = float((internal_row or {}).get("confidence") or 0)
    auto_conf_thresh = float(thresholds.get("internal_auto_confirm_confidence", 0.85))

    status: str
    best_answer: Any = None
    best_origin: str | None = None
    auto_confirm = False
    review_required = False
    review_owner = None
    resolution_note = ""

    if not ds_present and not in_present:
        # Check insufficient evidence (partial signals)
        ds_partial = dataset_row is not None and not dataset_row.get("predicted_abstain") and dataset_row.get("retrieval_hit_top1")
        in_partial = internal_row is not None and in_conf >= float(thresholds.get("internal_min_candidate_confidence", 0.5))
        if ds_partial or in_partial:
            status = "INSUFFICIENT_EVIDENCE"
            best_answer = ds_val or in_val
            best_origin = "candidate"
            review_required = True
            review_owner = "RAG"
            resolution_note = "Partial retrieval/extraction signal without resolved answer"
        else:
            status = "NO_ANSWER_FOUND"
            resolution_note = "Neither dataset nor internal-doc produced a resolved answer"

    elif ds_present and not in_present:
        status = "BACKFILL_FROM_DATASET"
        best_answer = ds_val
        best_origin = "dataset"
        auto_confirm = bool((dataset_row or {}).get("answer_correct", True))
        resolution_note = "Dataset/public source only"

    elif in_present and not ds_present:
        status = "BACKFILL_FROM_INTERNAL"
        best_answer = in_val
        best_origin = "internal_doc"
        suff_ok = internal_sufficiency_resolved(internal_row or {})
        auto_confirm = in_conf >= auto_conf_thresh and suff_ok
        review_required = not auto_confirm
        review_owner = (internal_row or {}).get("review_owner") or ("None" if auto_confirm else "SME")
        resolution_note = "Internal-doc backfill" + (" (auto-confirm)" if auto_confirm else " (candidate — review)")

    elif values_equivalent(ds_val, in_val, policy=policy):
        status = "MATCH_CONFIRMED"
        best_answer = ds_val
        best_origin = "both_confirmed"
        auto_confirm = True
        resolution_note = "Dataset and internal-doc values align"

    else:
        status = "CONFLICT_REVIEW_REQUIRED"
        best_answer = None
        best_origin = "unresolved"
        review_required = True
        review_owner = "SME"
        resolution_note = f"Conflict: dataset={ds_val!r} vs internal={in_val!r}"

    return {
        "resolution_status": status,
        "best_answer": best_answer,
        "best_answer_origin": best_origin,
        "auto_confirm": auto_confirm,
        "review_required": review_required,
        "review_owner": review_owner,
        "resolution_note": resolution_note,
        "dataset_answer": ds_val if ds_present else None,
        "internal_answer": in_val if in_present else None,
        "dataset_present": ds_present,
        "internal_present": in_present,
    }
