#!/usr/bin/env python3
"""Limited LangGraph handoff preparation round (contract + payload + prep gate, no runtime trial)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.langgraph_handoff_prep import (  # noqa: E402
    build_langgraph_handoff_contract,
    export_handoff_payload_schema,
    run_handoff_prep_matrix,
)
from enterprise_docs.review_owner_policy import export_review_owner_rules  # noqa: E402

PRIOR = ROOT / "reports/enterprise_docs_holdout_handoff_enablement_20260618-171016/summary.json"
PILOT_FAMILIES = ("employee_headcount", "environment_ghg", "governance")
CONTRACT_DATA = ROOT / "data/enterprise_docs/langgraph_handoff_contract.json"


def write_artifacts(out_dir: Path, result: dict[str, Any], prior: dict[str, Any] | None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    contract = result.get("family_handoff_contract") or build_langgraph_handoff_contract()
    schema = result.get("payload_schema") or export_handoff_payload_schema()
    review_rules = result.get("review_owner_rules") or export_review_owner_rules()

    CONTRACT_DATA.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "artifact": "enterprise_docs_langgraph_handoff_prep",
        "timestamp": out_dir.name.split("_")[-1],
        "phase": "langgraph_handoff_preparation",
        "gate_type": "preparation_gate_not_integration_gate_not_runtime_trial",
        "pilot_families": list(PILOT_FAMILIES),
        "by_company": result.get("by_company"),
        "by_family": {k: result.get("by_family", {}).get(k) for k in PILOT_FAMILIES},
        "by_blocker_category": result.get("by_blocker_category"),
        "by_prep_status": result.get("by_prep_status"),
        "system_decision": result.get("system_decision"),
        "prior_enablement": {
            "holdout_promotion_rate": (prior or {}).get("system_decision", {}).get("holdout_promotion_rate"),
            "ready_for_limited_langgraph_handoff_preparation": (
                (prior or {}).get("system_decision", {}).get("ready_for_limited_langgraph_handoff_preparation")
            ),
        },
        "metric_types": {
            "exact": [
                "promoted_count",
                "handoff_allowed_for_preparation",
                "blocked_count",
                "review_required_count",
                "prep_status",
            ],
            "heuristic": ["dominant_blocker", "dominant_review_owner", "by_blocker_category"],
            "proxy": ["recommend_trial", "trial_readiness_note"],
        },
        "constraints": {
            "no_synthesis": True,
            "no_langgraph_runtime_trial": True,
            "no_case_tuning": True,
            "no_loosening_promotion_rules": True,
        },
    }

    matrix_payload = {
        "by_company": result.get("by_company"),
        "by_family": result.get("by_family"),
        "by_blocker_category": result.get("by_blocker_category"),
        "by_prep_status": result.get("by_prep_status"),
        "cases": [
            {
                "question_id": r.get("question_id"),
                "company_id": r.get("company_id"),
                "family_id": r.get("family_id"),
                "prep_status": r.get("prep_status"),
                "handoff_allowed_for_preparation": r.get("handoff_allowed_for_preparation"),
                "needs_review_by": r.get("needs_review_by"),
                "promoted": r.get("promoted"),
                "readiness_state_after": r.get("readiness_state_after"),
                "handoff_blockers": r.get("handoff_blockers"),
            }
            for r in (result.get("matrix") or [])
        ],
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "family_handoff_contract.json").write_text(
        json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "handoff_payload_schema.json").write_text(
        json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "review_owner_rules.json").write_text(
        json.dumps(review_rules, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "handoff_prep_matrix.json").write_text(
        json.dumps(matrix_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    samples = result.get("payload_samples") or {}
    with (out_dir / "handoff_payload_samples.jsonl").open("w", encoding="utf-8") as f:
        for label, payload in samples.items():
            if payload:
                f.write(
                    json.dumps({"sample_label": label, "payload": payload}, ensure_ascii=False) + "\n"
                )

    report = _build_report(out_dir, summary, contract, review_rules, prior)
    (out_dir / "report.md").write_text(report, encoding="utf-8")


def _build_report(
    out_dir: Path,
    summary: dict[str, Any],
    contract: dict[str, Any],
    review_rules: dict[str, Any],
    prior: dict[str, Any] | None,
) -> str:
    sd = summary.get("system_decision") or {}
    lines = [
        "# Enterprise internal-doc — Limited LangGraph handoff preparation",
        "",
        f"Artifact: `{out_dir.relative_to(ROOT)}`",
        "",
        "> **Preparation gate only** — không runtime trial, không synthesis, không integration thật.",
        "",
        "## Family handoff contract (3 pilot families)",
        "",
    ]
    for fid in PILOT_FAMILIES:
        fam = (contract.get("families") or {}).get(fid) or {}
        lines.append(f"### `{fid}`")
        lines.append("")
        lines.append(f"- question_type: `{fam.get('question_type')}`")
        min_h = fam.get("handoff_minimum") or {}
        lines.append(f"- min_confidence_table: **{min_h.get('min_confidence_table')}**")
        lines.append(f"- min_confidence_narrative: **{min_h.get('min_confidence_narrative')}**")
        lines.append(f"- blockers: {fam.get('handoff_blockers')}")
        lines.append("")

    lines.extend(
        [
            "## Payload schema",
            "",
            "Nhóm field: `identity`, `readiness`, `answer`, `evidence`, `review_control`.",
            "Chi tiết: `handoff_payload_schema.json`.",
            "",
            "## Review owner rules",
            "",
            json.dumps(review_rules.get("rules"), ensure_ascii=False, indent=2),
            "",
            "## Results by company",
            "",
            json.dumps(summary.get("by_company"), ensure_ascii=False, indent=2),
            "",
            "## Results by family",
            "",
            json.dumps(summary.get("by_family"), ensure_ascii=False, indent=2),
            "",
            "## Blocker categories",
            "",
            json.dumps(summary.get("by_blocker_category"), ensure_ascii=False, indent=2),
            "",
            "## System decision",
            "",
            json.dumps(sd, ensure_ascii=False, indent=2),
            "",
            "## Prior enablement reference",
            "",
            json.dumps(summary.get("prior_enablement"), ensure_ascii=False, indent=2),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = (args.out or (ROOT / f"reports/enterprise_docs_langgraph_handoff_prep_{ts}")).resolve()

    prior = json.loads(PRIOR.read_text(encoding="utf-8")) if PRIOR.exists() else None
    result = run_handoff_prep_matrix(include_demo=True)
    write_artifacts(out_dir, result, prior)
    print(
        json.dumps(
            {"out_dir": str(out_dir), "system": result.get("system_decision")},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
