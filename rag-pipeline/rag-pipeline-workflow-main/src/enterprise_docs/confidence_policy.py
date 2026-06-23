"""Family- and source-type-aware confidence resolution for handoff readiness."""

from __future__ import annotations

from typing import Any

from enterprise_docs.registries import company_config, is_holdout_company

CONFIDENCE_POLICY_VERSION = "1.0.0"

# Floors by extraction path (not lowered per-case)
_NARRATIVE_FLOOR = 0.25
_TABLE_FLOOR = 0.85
_STRUCTURED_NARRATIVE_HOLDOUT_FLOOR = 0.30


def _source_type_from_unit(unit: dict[str, Any] | None) -> str:
    if not unit:
        return "unknown"
    meta = unit.get("metadata") or {}
    return str(meta.get("document_type") or unit.get("source_type") or "unknown")


def resolve_extraction_confidence(
    ext: Any,
    *,
    company_id: str,
    family_id: str | None = None,
    unit_lookup: dict[str, dict[str, Any]] | None = None,
) -> tuple[float, str]:
    """Return (confidence, source_label) for handoff/promotion gates."""
    unit_lookup = unit_lookup or {}
    base = float(getattr(ext, "extraction_confidence", 0.0) or 0.0)
    narrative = bool(getattr(ext, "narrative_metric_parse_used", False))
    narrative_conf = float(getattr(ext, "narrative_confidence", 0.0) or 0.0)
    success = bool(getattr(ext, "success", False))

    if narrative:
        conf = max(base, narrative_conf)
        source = "narrative_metric_parse"
        if conf < _NARRATIVE_FLOOR and success:
            conf = _NARRATIVE_FLOOR
            source = "narrative_floor_min"
    else:
        conf = base
        source = "table_row_match_score"
        if success and conf >= _TABLE_FLOOR:
            source = "table_extraction_strong"

    uid = (getattr(ext, "selected_unit_ids", None) or [None])[0]
    unit = unit_lookup.get(str(uid or ""))
    src_type = _source_type_from_unit(unit)

    if is_holdout_company(company_id) and narrative and success:
        if src_type in ("sustainability_report", "governance_report", "dart_filing", "other"):
            if conf < _STRUCTURED_NARRATIVE_HOLDOUT_FLOOR:
                conf = _STRUCTURED_NARRATIVE_HOLDOUT_FLOOR
                source = f"holdout_narrative_source_floor:{src_type}"

    role = str(company_config(company_id).get("role") or "")
    if family_id and narrative:
        source = f"{source};family={family_id};role={role}"

    return round(min(1.0, conf), 4), source


def export_confidence_policy() -> dict[str, Any]:
    return {
        "version": CONFIDENCE_POLICY_VERSION,
        "description": "Family/source-type confidence resolution for handoff promotion",
        "floors": {
            "narrative_extraction": _NARRATIVE_FLOOR,
            "table_extraction": _TABLE_FLOOR,
            "holdout_narrative_source": _STRUCTURED_NARRATIVE_HOLDOUT_FLOOR,
        },
        "rules": [
            {
                "id": "narrative_max_row_and_narrative_conf",
                "applies_when": "narrative_metric_parse_used",
                "resolution": "max(extraction_confidence, narrative_confidence), then narrative_floor_min",
            },
            {
                "id": "holdout_sustainability_narrative_floor",
                "applies_when": "holdout_company AND narrative AND source_type in sustainability/governance/dart",
                "resolution": f"floor >= {_STRUCTURED_NARRATIVE_HOLDOUT_FLOOR}",
            },
            {
                "id": "table_strong",
                "applies_when": "NOT narrative AND extraction_confidence >= 0.85",
                "resolution": "table_extraction_strong",
            },
        ],
        "metric_types": {
            "exact": ["promoted", "handoff_candidate when rules pass"],
            "heuristic": ["evidence_bundle_quality"],
            "proxy": ["holdout feasibility vs full pipeline alignment rate"],
        },
    }
