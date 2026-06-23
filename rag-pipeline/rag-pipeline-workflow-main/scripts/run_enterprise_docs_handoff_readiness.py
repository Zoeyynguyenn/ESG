#!/usr/bin/env python3
"""Handoff readiness round: extraction_ready → single_source_sufficient (preparation only)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.handoff_readiness import (  # noqa: E402
    export_family_handoff_schema,
    export_readiness_promotion_doc,
    run_handoff_readiness_matrix,
)

PRIOR_STRENGTHENING = ROOT / "reports/enterprise_docs_family_strengthening_20260618-164132/summary.json"
PILOT_FAMILIES = ("employee_headcount", "environment_ghg", "governance")


def _system_decision(result: dict[str, Any], prior: dict[str, Any] | None) -> dict[str, Any]:
    by_family = result.get("by_family") or {}
    pilot_rows = {
        fid: by_family.get(fid) or {}
        for fid in PILOT_FAMILIES
    }

    promoted_families = [
        fid
        for fid, spec in pilot_rows.items()
        if spec.get("single_source_count", 0) > 0 or spec.get("multi_source_count", 0) > 0
    ]
    handoff_prep = [
        fid
        for fid, spec in pilot_rows.items()
        if spec.get("handoff_candidate_count", 0) > 0
        and spec.get("companies")
        and "hanssem" in spec.get("companies", []) or "musinsa" in spec.get("companies", [])
    ]
    # holdout gate: need at least one promoted quant case on holdout per family
    holdout_promoted: dict[str, int] = {}
    for row in result.get("matrix") or []:
        if row.get("company_id") not in ("hanssem", "musinsa"):
            continue
        fid = row.get("family_id")
        if fid in PILOT_FAMILIES and row.get("promoted"):
            holdout_promoted[fid] = holdout_promoted.get(fid, 0) + 1

    holdout_ready_families = [fid for fid in PILOT_FAMILIES if holdout_promoted.get(fid, 0) > 0]
    extraction_only = [
        fid
        for fid, spec in pilot_rows.items()
        if spec.get("still_extraction_ready", 0) > 0 and fid not in holdout_ready_families
    ]
    not_handoff = [
        fid
        for fid in PILOT_FAMILIES
        if (pilot_rows.get(fid) or {}).get("handoff_candidate_count", 0) == 0
    ]

    prior_gate = (prior or {}).get("system_decision_gate") or {}
    prior_ext = prior_gate.get("holdout_extraction_avg")

    holdout_cases = [r for r in (result.get("matrix") or []) if r.get("company_id") in ("hanssem", "musinsa")]
    holdout_promoted_n = sum(1 for r in holdout_cases if r.get("promoted"))
    holdout_n = max(1, len(holdout_cases))

    limited_prep_ok = (
        len(holdout_ready_families) >= 1
        and all(
            (pilot_rows.get(fid) or {}).get("handoff_candidate_count", 0) > 0
            for fid in holdout_ready_families
        )
    )

    return {
        "phase": "handoff_preparation",
        "ready_for_limited_langgraph_handoff": False,
        "ready_for_limited_langgraph_handoff_preparation": limited_prep_ok,
        "not_ready_for_synthesis": True,
        "not_ready_for_langgraph_trial": True,
        "single_source_sufficient_families": promoted_families,
        "extraction_ready_only_families": extraction_only,
        "handoff_prep_candidate_families": [
            fid for fid in PILOT_FAMILIES if fid in holdout_ready_families
        ],
        "not_handoff_ready_families": not_handoff,
        "holdout_promotion_rate": round(holdout_promoted_n / holdout_n, 4),
        "holdout_promoted_by_family": holdout_promoted,
        "prior_holdout_extraction_avg": prior_ext,
        "gaps_before_trial": [
            "evidence_packaging_on_holdout",
            "confidence_policy_calibration",
            "review_owner_rule_enforcement",
            "formal_single_source_sufficient_on_holdout",
        ],
    }


def _family_pilot_summary(schema: dict[str, Any]) -> str:
    lines = ["## Family pilot summary", ""]
    families = schema.get("families") or {}
    for fid in PILOT_FAMILIES:
        spec = families.get(fid) or {}
        lines.append(f"### `{fid}` (pilot #{spec.get('pilot_order', '?')})")
        lines.append(f"- question_type: `{spec.get('question_type')}`")
        lines.append(f"- required_readiness_state: `{spec.get('required_readiness_state')}`")
        lines.append(f"- required_evidence_count: {spec.get('required_evidence_count')}")
        lines.append(f"- primary_doc_rule: {spec.get('primary_doc_rule')}")
        lines.append(f"- handoff_blockers: {', '.join(spec.get('handoff_blockers') or [])}")
        lines.append(f"- notes: {spec.get('notes', '')}")
        lines.append("")
    return "\n".join(lines)


def write_artifacts(out_dir: Path, result: dict[str, Any], *, prior: dict[str, Any] | None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    schema = export_family_handoff_schema()
    promotion = result.get("readiness_promotion") or export_readiness_promotion_doc()
    system = _system_decision(result, prior)

    summary = {
        "artifact": "enterprise_docs_handoff_readiness",
        "timestamp": out_dir.name.split("_")[-1],
        "pilot_families": list(PILOT_FAMILIES),
        "by_company": result.get("by_company"),
        "by_family": result.get("by_family"),
        "by_promotion": result.get("by_promotion"),
        "system_decision": system,
        "constraints": {
            "no_synthesis": True,
            "no_langgraph_trial": True,
            "no_case_tuning": True,
            "demo_company_role": "dev",
            "holdout_role": "gate",
        },
    }

    matrix_payload = {
        "by_company": result.get("by_company"),
        "by_family": result.get("by_family"),
        "by_promotion": result.get("by_promotion"),
        "pilot_families": list(PILOT_FAMILIES),
    }

    (out_dir / "family_handoff_schema.json").write_text(
        json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "readiness_promotion.json").write_text(
        json.dumps(promotion, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "handoff_readiness_matrix.json").write_text(
        json.dumps(matrix_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    with (out_dir / "handoff_samples.jsonl").open("w", encoding="utf-8") as f:
        for row in result.get("matrix") or []:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    report_lines = [
        "# Enterprise internal-doc — Handoff readiness round",
        "",
        f"Artifact: `{out_dir.relative_to(ROOT)}`",
        "",
        "## Mục tiêu",
        "Formal hóa schema handoff theo family và kiểm tra promotion `extraction_ready` → `single_source_sufficient`.",
        "Không synthesis, không LangGraph trial.",
        "",
        _family_pilot_summary(schema),
        "## Kết quả promotion",
        "",
        f"- promoted / not_promoted: `{result.get('by_promotion')}`",
        "",
        "### Theo company",
        "",
        json.dumps(result.get("by_company"), ensure_ascii=False, indent=2),
        "",
        "### Theo family (pilot)",
        "",
        json.dumps(
            {k: result.get("by_family", {}).get(k) for k in PILOT_FAMILIES},
            ensure_ascii=False,
            indent=2,
        ),
        "",
        "## System decision",
        "",
        json.dumps(system, ensure_ascii=False, indent=2),
        "",
    ]
    (out_dir / "report.md").write_text("\n".join(report_lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run enterprise docs handoff readiness round")
    parser.add_argument("--out", type=Path, default=None, help="Output directory")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = (args.out or (ROOT / f"reports/enterprise_docs_handoff_readiness_{ts}")).resolve()

    prior = None
    if PRIOR_STRENGTHENING.exists():
        prior = json.loads(PRIOR_STRENGTHENING.read_text(encoding="utf-8"))

    result = run_handoff_readiness_matrix(include_demo=True, demo_family_filter=True)
    write_artifacts(out_dir, result, prior=prior)
    print(json.dumps({"out_dir": str(out_dir), "summary": result.get("by_promotion")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
