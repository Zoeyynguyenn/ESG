"""LangGraph handoff contract for enterprise internal-doc lane."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from enterprise_docs.readiness_model import assess_readiness
from enterprise_docs.registries import load_source_role_registry


HANDOFF_SCHEMA_VERSION = "1.0.0"

ALLOWED_HANDOFF_STATES = frozenset({
    "single_source_sufficient",
    "multi_source_sufficient",
    "aggregation_ready",
})

BLOCKED_HANDOFF_STATES = frozenset({
    "honest_abstain",
    "coverage_gap",
    "needs_sme_review",
    "not_ready_for_synthesis",
    "retrieval_ready",
    "extraction_ready",
})


@dataclass
class EvidenceBundleItem:
    logical_document_id: str
    unit_id: str
    metric_label: str
    value: str
    unit: str | None = None
    role: str | None = None
    snippet: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LangGraphHandoff:
    schema_version: str
    question_id: str
    company_id: str
    answer_mode: str
    kind: str
    readiness_state: str
    readiness_reason: str
    predicted_value: str | None
    predicted_unit: str | None
    evidence_bundle: list[EvidenceBundleItem]
    primary_doc: str | None
    supporting_docs: list[str]
    confidence: float
    needs_review_by: str | None
    handoff_allowed: bool
    handoff_block_reason: str | None = None
    sufficiency_status: str | None = None
    fail_stage: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["evidence_bundle"] = [e.to_dict() if isinstance(e, EvidenceBundleItem) else e for e in self.evidence_bundle]
        return d


def synthesis_gate_config() -> dict[str, Any]:
    reg = load_source_role_registry()
    return dict(reg.get("synthesis_gate") or {})


def handoff_allowed_for_state(readiness_state: str, *, kind: str) -> tuple[bool, str | None]:
    cfg = synthesis_gate_config()
    allowed = set(cfg.get("allowed_readiness_states") or ALLOWED_HANDOFF_STATES)

    if kind == "qualitative":
        return False, "qualitative_requires_synthesis_not_extractive_handoff"

    if readiness_state in allowed:
        return True, None
    if readiness_state in BLOCKED_HANDOFF_STATES:
        return False, f"blocked_state:{readiness_state}"
    return False, f"state_not_in_gate:{readiness_state}"


def needs_review_for(readiness_state: str, *, wrong_row_risk: bool = False) -> str | None:
    if wrong_row_risk or readiness_state == "needs_sme_review":
        return "sme"
    if readiness_state == "coverage_gap":
        return "dataset"
    if readiness_state == "honest_abstain":
        return "none"
    return None


def build_handoff(
    plan_row: dict[str, Any],
    ret,
    *,
    company_id: str = "demo_company",
    unit_lookup: dict[str, dict[str, Any]] | None = None,
    logical_to_corpus: dict[str, str] | None = None,
    aggregation_result: Any | None = None,
    extraction_result: Any | None = None,
) -> LangGraphHandoff:
    from enterprise_docs.evidence_aggregator import aggregate_cross_doc
    from enterprise_docs.structured_extractor import extract_from_retrieval

    unit_lookup = unit_lookup or {}
    logical_to_corpus = logical_to_corpus or {}
    readiness = assess_readiness(
        plan_row, ret, unit_lookup=unit_lookup, logical_to_corpus=logical_to_corpus
    )

    ext = extraction_result
    if ext is None:
        ext = extract_from_retrieval(
            plan_row, ret, unit_lookup=unit_lookup, retrieval_ready=readiness.get("retrieval_ok", False)
        )

    from enterprise_docs.confidence_policy import resolve_extraction_confidence

    company_id_str = str(company_id)
    resolved_conf, confidence_source = resolve_extraction_confidence(
        ext, company_id=company_id_str, unit_lookup=unit_lookup
    )

    agg = aggregation_result
    if agg is None and plan_row.get("answer_mode") == "cross_document_answer":
        agg = aggregate_cross_doc(plan_row, ret, unit_lookup=unit_lookup, logical_to_corpus=logical_to_corpus)

    evidence_bundle: list[EvidenceBundleItem] = []
    primary_doc: str | None = None
    supporting: list[str] = []
    predicted_value = readiness.get("resolved_value")
    predicted_unit = None
    sufficiency = readiness.get("sufficiency_status")
    confidence = resolved_conf

    if agg is not None:
        primary_doc = getattr(agg, "primary_doc_used", None)
        predicted_value = getattr(agg, "resolved_value", None) or predicted_value
        predicted_unit = getattr(agg, "predicted_unit", None)
        sufficiency = getattr(agg, "sufficiency_status", None) or sufficiency
        for c in getattr(agg, "aggregated_evidence_units", []) or []:
            evidence_bundle.append(
                EvidenceBundleItem(
                    logical_document_id=c.logical_document_id,
                    unit_id=c.unit_id,
                    metric_label=c.metric_label,
                    value=c.value,
                    unit=c.unit,
                    role=c.role,
                    snippet=(c.source_snippet or "")[:300],
                )
            )
            if c.logical_document_id and c.logical_document_id != primary_doc:
                if c.logical_document_id not in supporting:
                    supporting.append(c.logical_document_id)
    elif ext.success:
        primary_doc = ext.selected_doc
        predicted_value = ext.predicted_value
        predicted_unit = ext.predicted_unit
        confidence = max(confidence, resolved_conf)
        for uid in ext.selected_unit_ids or []:
            u = unit_lookup.get(uid, {})
            evidence_bundle.append(
                EvidenceBundleItem(
                    logical_document_id=ext.selected_doc or "",
                    unit_id=uid,
                    metric_label=ext.selected_row_label or "",
                    value=ext.predicted_value or "",
                    unit=ext.predicted_unit,
                    snippet=(ext.raw_snippet or "")[:300],
                )
            )

    state = str(readiness.get("readiness_state") or "")
    kind = str(plan_row.get("kind") or "")
    allowed, block_reason = handoff_allowed_for_state(state, kind=kind)
    review = needs_review_for(state, wrong_row_risk=bool(getattr(ext, "wrong_row_risk", False)))

    return LangGraphHandoff(
        schema_version=HANDOFF_SCHEMA_VERSION,
        question_id=str(plan_row.get("item_id") or ""),
        company_id=company_id,
        answer_mode=str(plan_row.get("answer_mode") or ""),
        kind=kind,
        readiness_state=state,
        readiness_reason=str(readiness.get("readiness_reason") or ""),
        predicted_value=predicted_value,
        predicted_unit=predicted_unit,
        evidence_bundle=evidence_bundle,
        primary_doc=primary_doc,
        supporting_docs=supporting,
        confidence=round(confidence, 4),
        needs_review_by=review,
        handoff_allowed=allowed,
        handoff_block_reason=block_reason,
        sufficiency_status=sufficiency,
        fail_stage=readiness.get("fail_stage"),
    )


def export_handoff_schema() -> dict[str, Any]:
    gate = synthesis_gate_config()
    return {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "description": "Handoff contract from enterprise internal-doc lane to LangGraph synthesis",
        "required_fields": [
            "question_id",
            "company_id",
            "answer_mode",
            "readiness_state",
            "predicted_value",
            "evidence_bundle",
            "handoff_allowed",
        ],
        "readiness_states": {
            "handoff_allowed": sorted(ALLOWED_HANDOFF_STATES),
            "handoff_blocked": sorted(BLOCKED_HANDOFF_STATES),
        },
        "synthesis_gate": gate,
        "evidence_bundle_item": {
            "logical_document_id": "string",
            "unit_id": "string",
            "metric_label": "string",
            "value": "string",
            "unit": "string|null",
            "role": "string|null",
            "snippet": "string",
        },
        "needs_review_by_values": ["sme", "dataset", "none", None],
    }
