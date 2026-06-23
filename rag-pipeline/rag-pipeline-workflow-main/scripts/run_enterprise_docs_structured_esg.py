#!/usr/bin/env python3
"""Structured ESG output evaluation — document → structured ESG data (not handoff/LangGraph)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.format_transformation_audit import audit_format_transformation  # noqa: E402
from enterprise_docs.structured_esg_mapper import (  # noqa: E402
    export_esg_schema,
    run_structured_esg_pipeline,
)

SCHEMA_DATA = ROOT / "data/enterprise_docs/esg_target_schema.json"
PILOT_FAMILIES = ("employee_headcount", "environment_ghg", "governance")


def write_artifacts(out_dir: Path, result: dict[str, Any], format_audit: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    schema = result.get("esg_schema") or export_esg_schema()
    SCHEMA_DATA.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "artifact": "enterprise_docs_structured_esg",
        "timestamp": out_dir.name.split("_")[-1],
        "phase": "structured_esg_output",
        "focus": "document_to_structured_esg_data",
        "langgraph_handoff_priority": False,
        "pilot_families": list(PILOT_FAMILIES),
        "by_company": result.get("by_company"),
        "by_family": {k: result.get("by_family", {}).get(k) for k in PILOT_FAMILIES},
        "by_format": result.get("by_format"),
        "format_parse_coverage": result.get("format_parse_coverage"),
        "cross_doc_cases": len(result.get("cross_doc_conflict_matrix") or []),
        "total_records": len(result.get("records") or []),
        "format_priority": format_audit.get("format_priority_list"),
        "metric_types": result.get("metric_types"),
        "constraints": {
            "no_synthesis": True,
            "no_langgraph_trial": True,
            "no_case_tuning": True,
            "no_goldns_emni": True,
        },
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "format_audit.json").write_text(
        json.dumps(format_audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "esg_schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "cross_doc_conflict_matrix.json").write_text(
        json.dumps(
            {
                "taxonomy": result.get("conflict_taxonomy"),
                "cases": result.get("cross_doc_conflict_matrix"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    with (out_dir / "structured_esg_records.jsonl").open("w", encoding="utf-8") as f:
        for rec in result.get("records") or []:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    report = _build_report(out_dir, summary, format_audit, result)
    (out_dir / "report.md").write_text(report, encoding="utf-8")


def _build_report(
    out_dir: Path,
    summary: dict[str, Any],
    format_audit: dict[str, Any],
    result: dict[str, Any],
) -> str:
    lines = [
        "# Enterprise internal-doc — Structured ESG output evaluation",
        "",
        f"Artifact: `{out_dir.relative_to(ROOT)}`",
        "",
        "> **Trọng tâm**: `document → structured ESG data` — không LangGraph handoff/trial.",
        "",
        "## Format transformation audit",
        "",
        "### Priority",
        "",
        json.dumps(format_audit.get("format_priority_list"), ensure_ascii=False, indent=2),
        "",
        "### By format (readiness)",
        "",
    ]
    for fmt, row in sorted(
        (format_audit.get("by_format") or {}).items(),
        key=lambda x: -x[1].get("transformation_readiness_score", 0),
    ):
        lines.append(
            f"- **{fmt}**: docs={row.get('document_count')}, tier={row.get('readiness_tier')}, "
            f"score={row.get('transformation_readiness_score')}, extraction={row.get('structured_extraction_readiness')}"
        )
    lines.extend([
        "",
        "## ESG schema",
        "",
        "Chi tiết: `esg_schema.json` / `data/enterprise_docs/esg_target_schema.json`",
        "",
        "## Metrics by company",
        "",
        json.dumps(summary.get("by_company"), ensure_ascii=False, indent=2),
        "",
        "## Metrics by family",
        "",
        json.dumps(summary.get("by_family"), ensure_ascii=False, indent=2),
        "",
        "## Cross-doc conflict matrix",
        "",
        f"Cases: **{summary.get('cross_doc_cases')}** — chi tiết `cross_doc_conflict_matrix.json`",
        "",
        "## System focus",
        "",
        json.dumps(result.get("system_focus"), ensure_ascii=False, indent=2),
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = (args.out or (ROOT / f"reports/enterprise_docs_structured_esg_{ts}")).resolve()

    format_audit = audit_format_transformation()
    result = run_structured_esg_pipeline(include_demo=True)
    write_artifacts(out_dir, result, format_audit)
    print(json.dumps({"out_dir": str(out_dir), "summary": {
        "total_records": len(result.get("records") or []),
        "by_company": result.get("by_company"),
    }}, ensure_ascii=False))


if __name__ == "__main__":
    main()
