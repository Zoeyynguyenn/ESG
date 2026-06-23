"""Version 5: gap analysis tren structured profile V4."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _record_by_id(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {r["field"]: r for r in records if r.get("field")}


def analyze_gaps(
    profile: Dict[str, Any],
    intake: Dict[str, Any],
    extraction_metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    records = profile.get("records", [])
    by_id = _record_by_id(records)
    required = intake.get("required_fields") or []
    priority = intake.get("priority_fields") or []

    missing_fields: List[Dict[str, Any]] = []
    low_confidence_fields: List[Dict[str, Any]] = []
    conflict_fields: List[Dict[str, Any]] = []

    for r in records:
        fid = r.get("field")
        entry = {
            "field": fid,
            "group": r.get("group"),
            "status": r.get("status"),
            "confidence": r.get("confidence"),
            "value": r.get("value"),
            "source": r.get("source"),
        }
        if r.get("value") is None or r.get("status") == "insufficient":
            missing_fields.append(entry)
        if r.get("confidence") == "low":
            low_confidence_fields.append(entry)
        if r.get("status") == "conflict":
            conflict_fields.append(entry)

    coverage_by_group: Dict[str, Dict[str, Any]] = {}
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        groups.setdefault(r.get("group", "Other"), []).append(r)

    for group, items in groups.items():
        n = len(items) or 1
        with_value = sum(1 for x in items if x.get("value") is not None)
        verified = sum(1 for x in items if x.get("status") == "verified")
        coverage_by_group[group] = {
            "total": len(items),
            "with_value": with_value,
            "verified": verified,
            "coverage_pct": round(100 * with_value / n, 1),
            "verified_pct": round(100 * verified / n, 1),
        }

    priority_risk: List[Dict[str, Any]] = []
    for fid in priority:
        r = by_id.get(fid)
        if not r:
            priority_risk.append(
                {"field": fid, "risk_level": "high", "reason": "field_not_in_profile"}
            )
            continue
        reasons = []
        risk = "low"
        if r.get("value") is None or r.get("status") == "insufficient":
            reasons.append("missing_or_insufficient")
            risk = "high"
        if r.get("status") == "conflict":
            reasons.append("conflict")
            risk = "high"
        if r.get("confidence") == "low" and risk != "high":
            reasons.append("low_confidence")
            risk = "medium"
        if fid in required and risk == "low" and r.get("status") != "verified":
            reasons.append("required_not_verified")
            risk = "medium"
        if reasons:
            priority_risk.append(
                {
                    "field": fid,
                    "risk_level": risk,
                    "reasons": reasons,
                    "status": r.get("status"),
                    "confidence": r.get("confidence"),
                    "value": r.get("value"),
                }
            )

    required_missing = [f for f in required if f in {m["field"] for m in missing_fields}]
    priority_ok = 0
    for fid in priority:
        r = by_id.get(fid)
        if r and r.get("value") is not None and r.get("status") not in ("insufficient", "conflict"):
            priority_ok += 1
    priority_total = len(priority) or 1

    return {
        "run_id": intake.get("run_id"),
        "entity_name": intake.get("entity_name") or profile.get("entity"),
        "target_framework": intake.get("target_framework"),
        "missing_fields": missing_fields,
        "low_confidence_fields": low_confidence_fields,
        "conflict_fields": conflict_fields,
        "coverage_by_group": coverage_by_group,
        "priority_risk": priority_risk,
        "required_field_missing": required_missing,
        "summary": {
            "total_fields": len(records),
            "missing_count": len(missing_fields),
            "low_confidence_count": len(low_confidence_fields),
            "conflict_count": len(conflict_fields),
            "priority_risk_high": sum(1 for p in priority_risk if p.get("risk_level") == "high"),
            "required_missing_count": len(required_missing),
            "priority_field_completion_rate": round(priority_ok / priority_total, 4),
            "extraction_metrics": extraction_metrics or {},
        },
    }
