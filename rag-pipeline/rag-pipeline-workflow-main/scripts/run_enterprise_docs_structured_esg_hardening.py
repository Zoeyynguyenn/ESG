#!/usr/bin/env python3
"""Structured ESG hardening round — parsers, mapping, cross-doc confirmation."""

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
from enterprise_docs.parsers import export_parser_capabilities  # noqa: E402
from enterprise_docs.structured_esg_mapper import run_structured_esg_pipeline  # noqa: E402

PRIOR = ROOT / "reports/enterprise_docs_structured_esg_20260618-174141/summary.json"
PILOT_FAMILIES = ("employee_headcount", "environment_ghg", "governance")

# Baseline format readiness (pre-hardening v1.0)
PRIOR_FORMAT_READINESS = {
    "html": 0.38,
    "xml": 0.35,
    "pdf": 0.32,
}


def _delta(prior: dict[str, Any] | None, current: dict[str, Any], key: str) -> dict[str, Any]:
    if not prior:
        return {"note": "no_prior"}
    p = (prior.get("by_company") or {}).get(key) or (prior.get("by_family") or {}).get(key) or prior
    c = (current.get("by_company") or {}).get(key) or (current.get("by_family") or {}).get(key) or current
    if not isinstance(p, dict) or not isinstance(c, dict):
        return {}
    metrics = [
        "structured_record_coverage",
        "multi_source_confirmed_rate",
        "conflict_rate",
        "metric_absent_rate",
        "single_source_sufficient_rate",
    ]
    out: dict[str, Any] = {}
    for m in metrics:
        if m in p and m in c:
            out[m] = round(float(c[m]) - float(p[m]), 4)
    return out


def format_hardening_matrix(format_audit: dict[str, Any]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for fmt in ("html", "xml", "pdf"):
        row = (format_audit.get("by_format") or {}).get(fmt) or {}
        score = row.get("transformation_readiness_score")
        prior = PRIOR_FORMAT_READINESS.get(fmt)
        rows[fmt] = {
            "parser_version": row.get("parser_version", "1.1.0"),
            "readiness_score_before": prior,
            "readiness_score_after": score,
            "readiness_delta": round(float(score or 0) - float(prior or 0), 3) if score and prior else None,
            "readiness_tier": row.get("readiness_tier"),
            "structured_extraction_readiness": row.get("structured_extraction_readiness"),
            "document_count_inventory": row.get("document_count"),
        }
    live = format_audit.get("live_sample_probes") or []
    for probe in live:
        fmt = probe.get("source_type")
        if fmt in rows and probe.get("parse_success"):
            rows[fmt]["live_probe_ok"] = True
            rows[fmt]["live_has_table_markers"] = probe.get("has_table_markers")
            rows[fmt]["live_has_numeric"] = probe.get("has_numeric")
    return rows


def write_artifacts(
    out_dir: Path,
    result: dict[str, Any],
    format_audit: dict[str, Any],
    prior: dict[str, Any] | None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fmt_matrix = format_hardening_matrix(format_audit)

    summary = {
        "artifact": "enterprise_docs_structured_esg_hardening",
        "timestamp": out_dir.name.split("_")[-1],
        "phase": "structured_esg_hardening",
        "prior_artifact": str(PRIOR.parent.name) if PRIOR.exists() else None,
        "parser_capabilities": export_parser_capabilities(),
        "format_hardening_matrix": fmt_matrix,
        "by_company": result.get("by_company"),
        "by_family": {k: result.get("by_family", {}).get(k) for k in PILOT_FAMILIES},
        "by_format": result.get("by_format"),
        "format_parse_coverage": result.get("format_parse_coverage"),
        "total_records": len(result.get("records") or []),
        "delta_vs_prior": {
            "by_company": {k: _delta(prior, result, k) for k in (result.get("by_company") or {})},
            "by_family": {k: _delta(prior, result, k) for k in PILOT_FAMILIES},
        },
        "cross_doc_confirmation_count": sum(
            1 for r in (result.get("records") or []) if r.get("multi_source_confirmed")
        ),
        "metric_types": result.get("metric_types"),
        "constraints": {
            "no_synthesis": True,
            "no_langgraph_trial": True,
            "no_case_tuning": True,
        },
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "format_hardening_matrix.json").write_text(
        json.dumps(fmt_matrix, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "family_structured_esg_summary.json").write_text(
        json.dumps(result.get("by_family"), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "cross_doc_confirmation_matrix.json").write_text(
        json.dumps(result.get("cross_doc_confirmation_matrix") or [], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (out_dir / "structured_esg_records.jsonl").open("w", encoding="utf-8") as f:
        for rec in result.get("records") or []:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    report = _report(out_dir, summary, fmt_matrix, prior)
    (out_dir / "report.md").write_text(report, encoding="utf-8")


def _report(
    out_dir: Path,
    summary: dict[str, Any],
    fmt_matrix: dict[str, Any],
    prior: dict[str, Any] | None,
) -> str:
    lines = [
        "# Enterprise internal-doc — Structured ESG hardening",
        "",
        f"Artifact: `{out_dir.relative_to(ROOT)}`",
        "",
        "> Parser v1.1 html/xml/pdf + multi-source confirmation + ESG field normalization",
        "",
        "## Format hardening (html / xml / pdf)",
        "",
        json.dumps(fmt_matrix, ensure_ascii=False, indent=2),
        "",
        "## Delta vs prior structured ESG round",
        "",
        json.dumps(summary.get("delta_vs_prior"), ensure_ascii=False, indent=2),
        "",
        "## By company",
        "",
        json.dumps(summary.get("by_company"), ensure_ascii=False, indent=2),
        "",
        "## By family",
        "",
        json.dumps(summary.get("by_family"), ensure_ascii=False, indent=2),
        "",
        f"Cross-doc multi_source_confirmed count: **{summary.get('cross_doc_confirmation_count')}**",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = (args.out or (ROOT / f"reports/enterprise_docs_structured_esg_hardening_{ts}")).resolve()

    prior = json.loads(PRIOR.read_text(encoding="utf-8")) if PRIOR.exists() else None
    format_audit = audit_format_transformation(sample_probe=True)
    result = run_structured_esg_pipeline(include_demo=True)
    write_artifacts(out_dir, result, format_audit, prior)

    print(
        json.dumps(
            {
                "out_dir": str(out_dir),
                "multi_source_confirmed": summary_count(result),
                "format_hardening": format_hardening_matrix(format_audit),
            },
            ensure_ascii=False,
        )
    )


def summary_count(result: dict[str, Any]) -> int:
    return sum(1 for r in (result.get("records") or []) if r.get("conflict_status") == "multi_source_confirmed")


if __name__ == "__main__":
    main()
