"""Version 5: product-oriented workflow report (Markdown)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _top_fields_to_action(gap: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for p in gap.get("priority_risk", []):
        if p.get("risk_level") == "high":
            items.append({**p, "action_type": "priority_risk"})
    for c in gap.get("conflict_fields", []):
        items.append({**c, "action_type": "conflict"})
    for m in gap.get("missing_fields", []):
        if m["field"] not in {x.get("field") for x in items}:
            items.append({**m, "action_type": "missing"})
    for l in gap.get("low_confidence_fields", []):
        if l["field"] not in {x.get("field") for x in items}:
            items.append({**l, "action_type": "low_confidence"})
    return items[:limit]


def _recommendations(gap: Dict[str, Any], workflow_metrics: Dict[str, Any]) -> List[str]:
    recs: List[str] = []
    if gap.get("summary", {}).get("missing_count", 0) > 0:
        recs.append(
            "Bo sung tai lieu hoac cai thien retrieval cho field insufficient (dac biet boolean/table trong environment_policy)."
        )
    if gap.get("summary", {}).get("conflict_count", 0) > 0:
        recs.append(
            "Rà soát conflict thủ công — ưu tiên chọn chunk từ policy chính thức thay vì FAQ/guidelines."
        )
    if gap.get("summary", {}).get("priority_risk_high", 0) > 0:
        recs.append(
            "Xử lý ngay priority_fields có risk high trước khi export báo cáo nghiệp vụ."
        )
    if workflow_metrics.get("priority_field_completion_rate", 1) < 0.7:
        recs.append(
            "Nâng rule parser V4 cho priority_fields (water_reuse, wastewater, third_party_audit, ethics_policy)."
        )
    if not recs:
        recs.append("Duy trì pipeline; cân nhắc mở rộng intake required_fields theo framework mới.")
    return recs


def write_workflow_report(
    path: Path,
    intake: Dict[str, Any],
    workflow_log: Dict[str, Any],
    profile: Dict[str, Any],
    gap: Dict[str, Any],
    workflow_metrics: Dict[str, Any],
) -> Path:
    ts = datetime.now().isoformat(timespec="seconds")
    top_action = _top_fields_to_action(gap, 10)
    recs = _recommendations(gap, workflow_metrics)
    ext = workflow_metrics

    lines = [
        "# V5 Workflow Report",
        "",
        f"Ngay: {ts}",
        f"Run ID: `{intake.get('run_id', 'n/a')}`",
        "",
        "## 1. Intake summary",
        "",
        "```json",
        json.dumps(
            {
                "entity_name": intake.get("entity_name"),
                "target_framework": intake.get("target_framework"),
                "retrieval_mode": intake.get("retrieval_mode"),
                "top_k": intake.get("top_k"),
                "required_fields_count": len(intake.get("required_fields") or []),
                "priority_fields_count": len(intake.get("priority_fields") or []),
                "notes": intake.get("notes"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## 2. Workflow execution summary",
        "",
        "| Stage | Status | Duration (s) | Records |",
        "|---|---|---:|---:|",
    ]
    for st in workflow_log.get("stages", []):
        lines.append(
            f"| {st.get('name')} | {st.get('status')} | {st.get('duration_sec', 0):.3f} | {st.get('record_count', '-')} |"
        )
    lines.extend(
        [
            "",
            f"- **execution_success:** {workflow_log.get('execution_success')}",
            f"- **end_to_end_duration_sec:** {workflow_log.get('end_to_end_duration_sec')}",
            "",
            "## 3. Extraction summary",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| extraction_coverage_rate | {ext.get('extraction_coverage_rate')} |",
            f"| verified_rate | {ext.get('verified_rate')} |",
            f"| insufficient_rate | {ext.get('insufficient_rate')} |",
            f"| conflict_rate | {ext.get('conflict_rate')} |",
            f"| evidence_presence_rate | {ext.get('evidence_presence_rate')} |",
            f"| priority_field_completion_rate | {ext.get('priority_field_completion_rate')} |",
            "",
            "## 4. Gap analysis summary",
            "",
            "```json",
            json.dumps(gap.get("summary", {}), ensure_ascii=False, indent=2),
            "```",
            "",
            "### Coverage by group",
            "",
            "| Group | Coverage % | Verified % |",
            "|---|---:|---:|",
        ]
    )
    for grp, cov in gap.get("coverage_by_group", {}).items():
        lines.append(
            f"| {grp} | {cov.get('coverage_pct')} | {cov.get('verified_pct')} |"
        )

    lines.extend(["", "## 5. Top 10 field can xu ly tiep", "", "| field | action | status | confidence | risk/reason |", "|---|---|---|---|---|"])
    for item in top_action:
        reason = item.get("reasons") or item.get("reason") or item.get("action_type", "")
        if isinstance(reason, list):
            reason = ", ".join(reason)
        lines.append(
            f"| {item.get('field')} | {item.get('action_type')} | {item.get('status')} | {item.get('confidence')} | {reason} |"
        )

    lines.extend(["", "## 6. Recommendation next action", ""])
    for i, r in enumerate(recs, 1):
        lines.append(f"{i}. {r}")

    lines.extend(
        [
            "",
            "## Workflow metrics",
            "",
            "```json",
            json.dumps(workflow_metrics, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
