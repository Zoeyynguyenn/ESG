"""Version 6: query/field routing — retrieval strategy per field type."""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional

from extraction_v4 import DEFAULT_RETRIEVAL_MODE

CONFLICT_PRONE_IDS = {
    "ltifr_target_2026",
    "whistleblowing_response_sla",
    "board_committee_count",
    "primary_reporting_entity",
    "women_mid_management_target",
}

FIELD_CATEGORY = {
    "numeric": "numeric",
    "boolean": "boolean",
    "string": "policy",
    "enum": "policy",
}


@dataclass
class FieldRoute:
    field_id: str
    category: str
    primary_mode: str
    fallback_mode: str
    top_k: int
    pool: int
    source_bias: List[str]
    query_rewrites: List[str] = dc_field(default_factory=list)
    metadata_bias: bool = False


def classify_field(field: Dict[str, Any], priority_fields: Optional[List[str]] = None) -> str:
    fid = field.get("id", "")
    etype = field.get("expected_type", "string")
    if fid in CONFLICT_PRONE_IDS or (priority_fields and fid in priority_fields):
        return "conflict_prone"
    if etype == "number":
        return "numeric"
    if etype == "boolean":
        return "boolean"
    hint = (field.get("extraction_hint") or "").lower()
    if any(k in hint for k in ("bang", "table", "ty le", "%", "kpi", "chi tieu")):
        return "table"
    return FIELD_CATEGORY.get(etype, "policy")


def route_field(
    field: Dict[str, Any],
    default_mode: str = DEFAULT_RETRIEVAL_MODE,
    base_top_k: int = 4,
    base_pool: int = 24,
    priority_fields: Optional[List[str]] = None,
) -> FieldRoute:
    fid = field["id"]
    cat = classify_field(field, priority_fields)
    hint = field.get("extraction_hint", "")
    desc = field.get("description", "")

    source_bias_map = {
        "energy_reduction_target": ["environment_policy"],
        "wastewater_treatment_policy": ["environment_policy"],
        "water_reuse_target": ["environment_policy"],
        "waste_recycling_target_2026": ["environment_policy"],
        "third_party_audit_frequency": ["environment_policy"],
        "whistleblowing_response_sla": ["social_policy", "compliance_faq"],
        "overtime_limit": ["social_policy"],
        "ethics_policy_present": ["governance_policy"],
        "board_size": ["governance_policy"],
        "ltifr_target_2026": ["social_policy"],
    }
    source_bias = source_bias_map.get(fid, [])

    if cat == "numeric":
        primary, fallback = "bm25_lexical", default_mode
        top_k, pool = base_top_k + 2, base_pool + 8
    elif cat == "boolean":
        primary, fallback = default_mode, "bm25_lexical"
        top_k, pool = base_top_k + 2, base_pool + 12
    elif cat == "table":
        primary, fallback = "bm25_lexical", default_mode
        top_k, pool = base_top_k + 2, base_pool + 8
    elif cat == "conflict_prone":
        primary, fallback = default_mode, "hybrid_dense_bm25"
        top_k, pool = base_top_k + 4, base_pool + 16
    else:
        primary, fallback = default_mode, "bm25_lexical"
        top_k, pool = base_top_k, base_pool

    rewrites = [
        f"{desc}. {hint}",
        f"chi tiet {hint} trong chinh sach",
        f"metric {hint} bang so lieu",
    ]
    if cat == "boolean":
        rewrites.append(f"xac nhan co/khong: {hint}")

    return FieldRoute(
        field_id=fid,
        category=cat,
        primary_mode=primary,
        fallback_mode=fallback,
        top_k=top_k,
        pool=pool,
        source_bias=source_bias,
        query_rewrites=rewrites,
        metadata_bias=cat == "policy",
    )


def route_all_fields(
    fields: List[Dict[str, Any]],
    default_mode: str = DEFAULT_RETRIEVAL_MODE,
    base_top_k: int = 4,
    priority_fields: Optional[List[str]] = None,
) -> Dict[str, FieldRoute]:
    return {
        f["id"]: route_field(f, default_mode, base_top_k, 24, priority_fields)
        for f in fields
    }
