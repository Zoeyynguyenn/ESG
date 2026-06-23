from __future__ import annotations

from typing import Any, Dict, Optional

from evidence_api.record_catalog import TRUSTED_SOURCE_TYPES
from evidence_api.schemas import ConfidenceLevel


def compute_confidence(score: float, record: Optional[Dict[str, Any]]) -> ConfidenceLevel:
    points = 0.0
    if score >= 0.7:
        points += 2.0
    elif score >= 0.45:
        points += 1.0
    elif score >= 0.25:
        points += 0.5

    if not record:
        return "low" if points < 1.0 else "medium"

    if record.get("page") is not None:
        points += 1.0
    if record.get("section_path"):
        points += 0.5
    metric = record.get("metric")
    if isinstance(metric, dict) and metric.get("metric_name"):
        points += 2.0
    if record.get("is_raw_text") is True:
        points += 0.5
    if str(record.get("source_type") or "") in TRUSTED_SOURCE_TYPES:
        points += 1.0

    if points >= 4.5:
        return "high"
    if points >= 2.5:
        return "medium"
    return "low"
