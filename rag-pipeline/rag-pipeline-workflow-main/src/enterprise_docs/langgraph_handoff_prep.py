"""LangGraph handoff preparation layer (contract + payload + prep gate, no runtime trial)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from enterprise_docs.handoff_readiness import (
    _min_confidence,
    load_family_handoff_registry,
    run_case_handoff,
    run_handoff_readiness_matrix,
)
from enterprise_docs.langgraph_handoff import HANDOFF_SCHEMA_VERSION, export_handoff_schema
from enterprise_docs.registries import company_config
from enterprise_docs.review_owner_policy import (
    OWNER_NONE,
    export_review_owner_rules,
    resolve_review_owner,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "data/enterprise_docs/langgraph_handoff_contract.json"
PREP_SCHEMA_VERSION = "1.0.0"
PILOT_FAMILIES = frozenset({"employee_headcount", "environment_ghg", "governance"})

PREP_ALLOWED_STATES = frozenset({"single_source_sufficient", "multi_source_sufficient"})
PREP_BLOCKED_STATES = frozenset({
    "coverage_gap",
    "needs_sme_review",
    "honest_abstain",
    "not_ready_for_synthesis",
    "retrieval_ready",
    "extraction_ready",
})


@lru_cache(maxsize=1)
def load_langgraph_handoff_contract() -> dict[str, Any]:
    if CONTRACT_PATH.exists():
        return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    return build_langgraph_handoff_contract()


def build_langgraph_handoff_contract() -> dict[str, Any]:
    """Harden family-level handoff contract from registry + prep gates."""
    reg = load_family_handoff_registry()
    families_out: dict[str, Any] = {}

    for fid, spec in (reg.get("families") or {}).items():
        conf_rule = spec.get("confidence_rule") or {}
        blockers = list(spec.get("handoff_blockers") or [])
        review_rule = spec.get("review_owner_rule") or {}

        families_out[fid] = {
            "family_id": fid,
            "question_type": spec.get("question_type"),
            "pilot_order": spec.get("pilot_order"),
            "handoff_minimum": {
                "readiness_states_allowed": sorted(PREP_ALLOWED_STATES),
                "readiness_states_blocked": sorted(PREP_BLOCKED_STATES),
                "kind_required": "quantitative",
                "required_fields": list(spec.get("required_fields") or []),
                "optional_fields": list(spec.get("optional_fields") or []),
                "min_evidence_count": int(spec.get("required_evidence_count") or 1),
                "min_confidence_table": float(conf_rule.get("min_table_extraction") or 0.85),
                "min_confidence_narrative": float(conf_rule.get("min_narrative_extraction") or 0.25),
                "unit_required": bool(spec.get("unit_required")),
                "narrative_single_source_ok": bool(spec.get("narrative_single_source_ok")),
            },
            "prep_gate_outcomes": {
                "handoff_allowed_for_preparation": (
                    "promoted quant case in single/multi_source_sufficient with complete payload, "
                    "confidence >= family min, needs_review_by=None"
                ),
                "handoff_blocked": (
                    "terminal blocker, qualitative, synthesis gate, incomplete package, "
                    "or retrieval/extraction not promoted"
                ),
                "needs_manual_review_before_handoff": (
                    "promoted or near-ready but needs_review_by in (RAG, SME, Dataset)"
                ),
            },
            "handoff_blockers": blockers,
            "review_owner_defaults": {
                "needs_sme_review": review_rule.get("needs_sme_review", "SME"),
                "coverage_gap": review_rule.get("coverage_gap", "Dataset"),
                "default": review_rule.get("default"),
            },
            "primary_doc_rule": spec.get("primary_doc_rule"),
            "supporting_doc_rule": spec.get("supporting_doc_rule"),
            "notes": spec.get("notes"),
        }

    return {
        "version": "1.0.0",
        "schema_version": PREP_SCHEMA_VERSION,
        "description": (
            "Family-level LangGraph handoff contract — preparation gate only, not runtime integration"
        ),
        "global_constraints": {
            "no_synthesis": True,
            "no_langgraph_runtime_trial": True,
            "no_case_tuning": True,
            "no_loosening_promotion_rules": True,
        },
        "promotion_rules_inherited_from": "data/enterprise_docs/family_handoff_registry.json",
        "families": families_out,
        "review_owner_policy": export_review_owner_rules(),
    }


def export_handoff_payload_schema() -> dict[str, Any]:
    base = export_handoff_schema()
    return {
        "prep_schema_version": PREP_SCHEMA_VERSION,
        "handoff_schema_version": HANDOFF_SCHEMA_VERSION,
        "description": "Standardized downstream payload for LangGraph handoff (preparation contract)",
        "field_groups": {
            "identity": {
                "question_id": {"type": "string", "required": True},
                "company_id": {"type": "string", "required": True},
                "family_id": {"type": "string", "required": True},
                "question_type": {"type": "string", "required": True},
                "kind": {"type": "string", "required": True, "enum": ["quantitative", "qualitative"]},
                "answer_mode": {"type": "string", "required": True},
            },
            "readiness": {
                "readiness_state": {"type": "string", "required": True},
                "handoff_allowed": {"type": "boolean", "required": True},
                "handoff_allowed_for_preparation": {"type": "boolean", "required": True},
                "prep_status": {
                    "type": "string",
                    "required": True,
                    "enum": [
                        "handoff_allowed_for_preparation",
                        "handoff_blocked",
                        "needs_manual_review_before_handoff",
                    ],
                },
                "handoff_blockers": {"type": "array[string]", "required": True},
                "needs_review_by": {"type": "string|null", "enum": ["RAG", "SME", "Dataset", "None", None]},
            },
            "answer": {
                "predicted_value": {"type": "string|null", "required": True},
                "predicted_unit": {"type": "string|null", "required": False},
                "confidence": {"type": "number", "required": True},
                "confidence_source": {"type": "string", "required": True},
            },
            "evidence": {
                "primary_doc": {"type": "string|null", "required": False},
                "supporting_docs": {"type": "array[string]", "required": True},
                "evidence_bundle": {"type": "array[object]", "required": True},
                "logical_document_ids": {"type": "array[string]", "required": True},
            },
            "review_control": {
                "review_owner_rule": {"type": "object", "required": True},
                "review_owner_rule_id": {"type": "string", "required": True},
                "review_owner_reason": {"type": "string", "required": True},
                "sufficiency_reason": {"type": "string|null", "required": False},
                "coverage_or_abstain_flag": {"type": "boolean", "required": True},
            },
        },
        "inherited_handoff_schema": base,
    }


def standardize_handoff_payload(
    case_row: dict[str, Any],
    *,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build downstream-ready payload from handoff readiness case row."""
    contract = contract or load_langgraph_handoff_contract()
    fid = str(case_row.get("family_id") or "")
    fam_contract = (contract.get("families") or {}).get(fid) or {}
    min_spec = fam_contract.get("handoff_minimum") or {}

    bundle_raw = case_row.get("handoff_package") or {}
    if isinstance(bundle_raw, dict):
        evidence_bundle = bundle_raw.get("evidence_bundle") or []
    else:
        evidence_bundle = []
    logical_ids: list[str] = []
    primary = case_row.get("primary_doc")
    if primary:
        logical_ids.append(str(primary))
    for doc in case_row.get("supporting_docs") or []:
        if doc and doc not in logical_ids:
            logical_ids.append(str(doc))

    state = str(case_row.get("readiness_state_after") or case_row.get("readiness_state_before") or "")
    kind = str(case_row.get("kind") or "")
    promoted = bool(case_row.get("promoted"))
    conf = float(case_row.get("confidence") or 0.0)
    blockers = list(case_row.get("handoff_blockers") or [])

    narrative = "narrative" in str(case_row.get("confidence_source") or "")
    fam_min = float(
        min_spec.get("min_confidence_narrative" if narrative else "min_confidence_table") or 0.25
    )

    company_id = str(case_row.get("company_id") or "")
    role = str(company_config(company_id).get("role") or "dev")

    owner_res = resolve_review_owner(
        readiness_state=state,
        kind=kind,
        promoted=promoted,
        confidence=conf,
        family_min_confidence=fam_min,
        blockers=blockers,
        wrong_row_risk="wrong_row_risk" in blockers,
        family_id=fid or None,
        company_role=role,
    )

    prep_status = owner_res["prep_status"]
    needs_review = owner_res["needs_review_by"]

    # Prep gate: only None owner + promoted + sufficient state → allowed
    prep_allowed = (
        prep_status == "handoff_allowed_for_preparation"
        and promoted
        and state in PREP_ALLOWED_STATES
        and needs_review == OWNER_NONE
        and kind == "quantitative"
        and not blockers
    )

    if prep_status == "handoff_allowed_for_preparation" and not prep_allowed:
        prep_status = "needs_manual_review_before_handoff"

    coverage_flag = state == "coverage_gap" or any("coverage" in b for b in blockers)

    return {
        "schema_version": PREP_SCHEMA_VERSION,
        "identity": {
            "question_id": case_row.get("question_id") or case_row.get("probe_id"),
            "company_id": company_id,
            "family_id": fid,
            "question_type": fam_contract.get("question_type"),
            "kind": kind,
            "answer_mode": case_row.get("answer_mode"),
        },
        "readiness": {
            "readiness_state": state,
            "readiness_state_before": case_row.get("readiness_state_before"),
            "handoff_allowed": bool(case_row.get("handoff_allowed")),
            "handoff_allowed_for_preparation": prep_allowed,
            "prep_status": prep_status,
            "handoff_blockers": blockers,
            "needs_review_by": needs_review,
        },
        "answer": {
            "predicted_value": case_row.get("predicted_value"),
            "predicted_unit": case_row.get("predicted_unit"),
            "confidence": conf,
            "confidence_source": case_row.get("confidence_source"),
        },
        "evidence": {
            "primary_doc": primary,
            "supporting_docs": list(case_row.get("supporting_docs") or []),
            "evidence_bundle": evidence_bundle,
            "logical_document_ids": logical_ids,
            "evidence_bundle_quality": case_row.get("evidence_bundle_quality"),
            "evidence_bundle_count": len(evidence_bundle),
        },
        "review_control": {
            "review_owner_rule": fam_contract.get("review_owner_defaults") or {},
            "review_owner_rule_id": owner_res["review_owner_rule_id"],
            "review_owner_reason": owner_res["review_owner_reason"],
            "sufficiency_reason": case_row.get("promotion", {}).get("promotion_reason"),
            "coverage_or_abstain_flag": coverage_flag,
        },
        "promoted": promoted,
        "handoff_candidate": bool(case_row.get("handoff_candidate")),
    }


def assess_prep_case(case_row: dict[str, Any]) -> dict[str, Any]:
    payload = standardize_handoff_payload(case_row)
    return {
        **case_row,
        "prep_status": payload["readiness"]["prep_status"],
        "handoff_allowed_for_preparation": payload["readiness"]["handoff_allowed_for_preparation"],
        "needs_review_by": payload["readiness"]["needs_review_by"],
        "standardized_payload": payload,
    }


def run_handoff_prep_matrix(
    *,
    include_demo: bool = True,
) -> dict[str, Any]:
    """Run preparation-only gate on demo + holdout."""
    base = run_handoff_readiness_matrix(include_demo=include_demo, demo_family_filter=True)
    matrix = base.get("matrix") or []
    contract = build_langgraph_handoff_contract()

    prep_rows: list[dict[str, Any]] = []
    for row in matrix:
        prep_rows.append(assess_prep_case(row))

    return summarize_prep_matrix(prep_rows, contract=contract, base_result=base)


def summarize_prep_matrix(
    prep_rows: list[dict[str, Any]],
    *,
    contract: dict[str, Any],
    base_result: dict[str, Any],
) -> dict[str, Any]:
    from collections import Counter, defaultdict

    by_company: dict[str, Any] = {}
    by_family: dict[str, Any] = {}
    by_blocker: Counter[str] = Counter()
    by_prep_status: Counter[str] = Counter()

    for company_id in sorted({r["company_id"] for r in prep_rows}):
        rows = [r for r in prep_rows if r["company_id"] == company_id]
        by_company[company_id] = {
            "total_cases": len(rows),
            "promoted_count": sum(1 for r in rows if r.get("promoted")),
            "handoff_allowed_for_preparation": sum(
                1 for r in rows if r.get("handoff_allowed_for_preparation")
            ),
            "blocked_count": sum(1 for r in rows if r.get("prep_status") == "handoff_blocked"),
            "review_required_count": sum(
                1 for r in rows if r.get("prep_status") == "needs_manual_review_before_handoff"
            ),
            "prep_status_distribution": dict(Counter(r.get("prep_status") for r in rows)),
            "review_owner_distribution": dict(
                Counter(
                    (r.get("needs_review_by") if r.get("needs_review_by") is not None else "None")
                    if r.get("prep_status") != "handoff_blocked" or r.get("promoted")
                    else "blocked_no_owner"
                    for r in rows
                )
            ),
        }

    for fid in sorted({r.get("family_id") for r in prep_rows if r.get("family_id")}):
        rows = [r for r in prep_rows if r.get("family_id") == fid]
        blockers = Counter(b for r in rows for b in (r.get("handoff_blockers") or []))
        owners = Counter(r.get("needs_review_by") or "unset" for r in rows)
        dominant_blocker = blockers.most_common(1)[0][0] if blockers else None
        dominant_owner = owners.most_common(1)[0][0] if owners else None
        by_family[fid] = {
            "preparation_ready_count": sum(1 for r in rows if r.get("handoff_allowed_for_preparation")),
            "blocked_count": sum(1 for r in rows if r.get("prep_status") == "handoff_blocked"),
            "review_required_count": sum(
                1 for r in rows if r.get("prep_status") == "needs_manual_review_before_handoff"
            ),
            "promoted_count": sum(1 for r in rows if r.get("promoted")),
            "dominant_blocker": dominant_blocker,
            "dominant_review_owner": dominant_owner,
            "blocker_breakdown": dict(blockers),
            "review_owner_breakdown": dict(owners),
        }

    for r in prep_rows:
        by_prep_status[r.get("prep_status") or "unknown"] += 1
        for b in r.get("handoff_blockers") or []:
            if "confidence" in b:
                by_blocker["confidence_blocker"] += 1
            elif "coverage" in b:
                by_blocker["coverage_blocker"] += 1
            elif "synthesis" in b or "qualitative" in b:
                by_blocker["synthesis_blocker"] += 1
            elif "review" in b or "sme" in b:
                by_blocker["review_blocker"] += 1
            else:
                by_blocker["package_blocker"] += 1

    holdout_rows = [r for r in prep_rows if r["company_id"] in ("hanssem", "musinsa")]
    holdout_prep_rows = [
        r for r in holdout_rows if r.get("handoff_allowed_for_preparation")
    ]
    holdout_prep = len(holdout_prep_rows)
    holdout_families_prep = sorted(
        {
            r.get("family_id")
            for r in holdout_prep_rows
            if r.get("family_id") in PILOT_FAMILIES
        }
    )

    system_decision = {
        "phase": "langgraph_handoff_preparation",
        "gate_type": "preparation_gate_not_integration_gate_not_runtime_trial",
        "ready_for_limited_langgraph_handoff_preparation": True,
        "ready_for_limited_langgraph_handoff_trial": False,
        "not_ready_for_synthesis": True,
        "holdout_prep_allowed_count": holdout_prep,
        "holdout_prep_allowed_families": holdout_families_prep,
        "total_prep_allowed": sum(1 for r in prep_rows if r.get("handoff_allowed_for_preparation")),
        "total_blocked": sum(1 for r in prep_rows if r.get("prep_status") == "handoff_blocked"),
        "total_review_required": sum(
            1 for r in prep_rows if r.get("prep_status") == "needs_manual_review_before_handoff"
        ),
        "dominant_blocker_category": by_blocker.most_common(1)[0][0] if by_blocker else None,
        "recommend_trial": False,
        "trial_blockers": [
            "preparation_contract_signoff_pending",
            "confidence_policy_calibration",
            "holdout_review_owner_clearance",
            "no_runtime_integration_yet",
        ],
    }

    if holdout_prep >= 5 and len(holdout_families_prep) >= 2:
        system_decision["recommend_trial"] = False
        system_decision["trial_readiness_note"] = (
            "Prep payload contract sufficient for limited trial design review; "
            "runtime trial still blocked until explicit sign-off"
        )

    samples = build_payload_samples(prep_rows)

    return {
        "matrix": prep_rows,
        "by_company": by_company,
        "by_family": by_family,
        "by_blocker_category": dict(by_blocker),
        "by_prep_status": dict(by_prep_status),
        "system_decision": system_decision,
        "family_handoff_contract": contract,
        "payload_schema": export_handoff_payload_schema(),
        "review_owner_rules": export_review_owner_rules(),
        "base_readiness": {
            "by_company": base_result.get("by_company"),
            "by_family": base_result.get("by_family"),
        },
        "payload_samples": samples,
    }


def build_payload_samples(prep_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """One sample per prep_status category if available."""
    samples: dict[str, Any] = {}
    for status in (
        "handoff_allowed_for_preparation",
        "handoff_blocked",
        "needs_manual_review_before_handoff",
    ):
        for row in prep_rows:
            if row.get("prep_status") == status:
                samples[status] = row.get("standardized_payload")
                break
    # Per review owner
    for owner in ("RAG", "SME", "Dataset", "None"):
        for row in prep_rows:
            if row.get("needs_review_by") == owner:
                samples[f"owner_{owner}"] = row.get("standardized_payload")
                break
    return samples
