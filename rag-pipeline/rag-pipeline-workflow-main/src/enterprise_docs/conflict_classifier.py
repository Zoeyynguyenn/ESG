"""Cross-document conflict status classification for structured ESG output."""

from __future__ import annotations

import re
from typing import Any

from enterprise_docs.diagnostics import NOT_DISCLOSED_RE

CONFLICT_STATUS_VALUES = frozenset({
    "metric_absent",
    "not_disclosed",
    "conflict_numeric",
    "conflict_semantic",
    "single_source_sufficient",
    "multi_source_confirmed",
    "insufficient_cross_doc_support",
    "none",
})


def classify_conflict_status(
    *,
    aggregation: Any | None = None,
    sufficiency_status: str | None = None,
    conflict_flags: list[str] | None = None,
    roles_with_metric: list[str] | None = None,
    resolved_value: str | None = None,
    answer_mode: str = "single_document_answer",
    multi_source_confirmed: bool = False,
    confirming_logical_docs: list[str] | None = None,
) -> tuple[str, str]:
    """Return (conflict_status, reason)."""
    conflict_flags = list(conflict_flags or [])
    roles_with_metric = list(roles_with_metric or [])
    confirming_logical_docs = list(confirming_logical_docs or [])
    suff = sufficiency_status or (getattr(aggregation, "sufficiency_status", None) if aggregation else None)
    resolved = resolved_value or (getattr(aggregation, "resolved_value", None) if aggregation else None)
    flags = conflict_flags or (getattr(aggregation, "conflict_flags", None) or [] if aggregation else [])

    if aggregation is not None:
        multi_source_confirmed = multi_source_confirmed or bool(
            getattr(aggregation, "multi_source_confirmed", False)
        )
        if not confirming_logical_docs:
            confirming_logical_docs = list(getattr(aggregation, "confirming_logical_docs", None) or [])

    if resolved and NOT_DISCLOSED_RE.search(str(resolved)):
        return "not_disclosed", "resolved_value_marked_not_disclosed"

    if flags:
        numeric = any("numeric_mismatch" in f for f in flags)
        if numeric:
            res_status = getattr(aggregation, "resolution_status", None) if aggregation else None
            if res_status == "resolved_with_preference_rule":
                return "conflict_numeric", "numeric_conflict_resolved_with_source_priority"
            return "conflict_numeric", "unresolved_or_flagged_numeric_mismatch"

    if suff == "conflict_unresolved":
        return "conflict_numeric", "aggregation_conflict_unresolved"

    # Multi-source confirmation before single-source downgrade
    confirm_count = len(confirming_logical_docs) if confirming_logical_docs else len(roles_with_metric)
    if multi_source_confirmed or (confirm_count >= 2 and resolved and not flags):
        return "multi_source_confirmed", "multiple_logical_docs_agree_on_value"

    if suff in ("partial_metric_absent_in_role",) or (
        aggregation and getattr(aggregation, "roles_absent_by_design", None)
        and not resolved
    ):
        return "metric_absent", "metric_absent_in_role_or_corpus"

    if suff == "resolved_single_source_sufficient":
        return "single_source_sufficient", "single_authoritative_source"

    if answer_mode == "cross_document_answer":
        missing_roles = list(
            getattr(aggregation, "missing_numeric_roles", None) or [] if aggregation else []
        )
        if resolved and missing_roles and len(roles_with_metric) >= 1 and not flags:
            return "conflict_numeric", "numeric_in_one_role_other_missing_or_undisclosed"
        if len(roles_with_metric) >= 2 and resolved and not flags:
            return "multi_source_confirmed", "multiple_roles_same_metric_no_conflict"
        if len(roles_with_metric) < 2 and suff in ("partial_missing_numeric_role", "failed"):
            return "insufficient_cross_doc_support", "cross_doc_roles_incomplete"

    if resolved and not flags:
        if len(roles_with_metric) >= 2:
            return "multi_source_confirmed", "multi_source_agreement"
        return "single_source_sufficient", "single_source_resolved"

    if not resolved:
        if aggregation and getattr(aggregation, "aggregation_reason", "") == "all_candidates_not_disclosed":
            return "not_disclosed", "all_sources_not_disclosed"
        return "metric_absent", "no_resolved_value"

    return "none", "unclassified"


def export_conflict_taxonomy() -> dict[str, Any]:
    return {
        "version": "1.1.0",
        "statuses": sorted(CONFLICT_STATUS_VALUES),
        "definitions": {
            "metric_absent": "Corpus/role has no parseable metric candidate",
            "not_disclosed": "Explicit not-disclosed or all candidates withheld",
            "conflict_numeric": "Numeric mismatch across sources (may be resolved with priority)",
            "conflict_semantic": "Same slot different semantic interpretation (future)",
            "single_source_sufficient": "One authoritative source sufficient",
            "multi_source_confirmed": "Multiple docs agree or complementary without conflict",
            "insufficient_cross_doc_support": "Cross-doc question lacks required multi-role support",
            "none": "Fallback / unclassified",
        },
        "resolution_rules": [
            "primary_doc numeric preferred over conflicting supporting",
            "not_disclosed candidates filtered before resolve",
            "year alignment before value compare",
            "5% numeric tolerance in _values_conflict",
        ],
    }
