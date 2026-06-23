"""Enrich holdout probes with evidence plans (registry-driven routing)."""

from __future__ import annotations

from typing import Any

from enterprise_docs.doc_router import build_evidence_plan
from enterprise_docs.registries import holdout_routing_profile, is_holdout_company


def holdout_cross_doc_pattern_families(company_id: str) -> frozenset[str]:
    fams = holdout_routing_profile(company_id).get("cross_doc_quant_probe_pattern_families") or []
    return frozenset(str(f) for f in fams)


def enrich_holdout_probe(probe: dict[str, Any], *, company_id: str) -> dict[str, Any]:
    """Apply evidence plan fields for structured ESG pipeline."""
    plan = dict(probe)
    plan.setdefault("company_id", company_id)
    plan.setdefault("item_id", probe.get("probe_id") or probe.get("item_id"))
    if plan.get("answer_mode") and plan.get("roles"):
        return plan
    ev = build_evidence_plan(plan, company_id=company_id)
    plan.update(
        {
            "answer_mode": ev.answer_mode,
            "primary_document_ids": ev.primary_document_ids,
            "supporting_document_ids": ev.supporting_document_ids,
            "roles": ev.roles,
            "needs_merge": ev.needs_merge,
            "needs_conflict_resolution": ev.needs_conflict_resolution,
            "notes": ev.notes,
        }
    )
    return plan


def cross_doc_holdout_enabled(probe: dict[str, Any], *, company_id: str) -> bool:
    if not is_holdout_company(company_id):
        return False
    pf = str(probe.get("pattern_family") or "")
    return pf in holdout_cross_doc_pattern_families(company_id)
