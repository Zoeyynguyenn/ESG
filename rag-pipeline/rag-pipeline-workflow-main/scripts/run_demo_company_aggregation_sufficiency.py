#!/usr/bin/env python3
"""Benchmark aggregation sufficiency taxonomy + targeted narrative parse."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.cross_doc_retriever import build_index_from_units, retrieve_for_plan
from enterprise_docs.diagnostics import evaluate_cross_doc, evaluate_single_doc
from enterprise_docs.evidence_aggregator import aggregate_cross_doc
from enterprise_docs.structured_extractor import extract_from_retrieval

BASELINE_142543 = ROOT / "reports/demo_company_extractor_aggregator_20260618-142543"
BASELINE_143749 = ROOT / "reports/demo_company_resolution_retrieval_20260618-143749"
BASELINE_144715 = ROOT / "reports/demo_company_bridge_table_parse_20260618-144715"

FOCUS_CASES = (
    "QUANT-0208", "QUANT-0209", "QUANT-0210", "QUANT-0213",
    "QUANT-0044", "QUANT-0046", "QUANT-0133",
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _load_summary(path: Path) -> dict[str, Any]:
    p = path / "summary.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _delta(new: Any, old: Any) -> dict[str, Any]:
    if new is None or old is None:
        return {"new": new, "old": old, "delta": None}
    try:
        return {"new": new, "old": old, "delta": round(float(new) - float(old), 4)}
    except (TypeError, ValueError):
        return {"new": new, "old": old, "delta": None}


def _single_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    ready = [r for r in results if r.get("single_doc_ready")]
    return {
        "single_extraction_success_rate_on_ready": round(
            sum(1 for r in ready if r.get("extraction_success")) / max(1, len(ready)), 4
        ),
        "single_extraction_success_rate_all": round(
            sum(1 for r in results if r.get("extraction_success")) / max(1, len(results)), 4
        ),
        "wrong_row_risk_count": sum(1 for r in results if r.get("wrong_row_risk")),
        "narrative_metric_parse_success_count": sum(
            1 for r in results if r.get("narrative_metric_parse_used") and r.get("extraction_success")
        ),
    }


def _cross_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    quant = [r for r in results if r.get("kind") == "quantitative"]
    n = max(1, len(quant))
    return {
        "quant_aggregation_success_rate": round(
            sum(1 for r in quant if r.get("aggregation_status") == "success") / n, 4
        ),
        "resolved_single_source_sufficient_rate": round(
            sum(1 for r in quant if r.get("sufficiency_status") == "resolved_single_source_sufficient") / n, 4
        ),
        "aggregation_partial_rate": round(
            sum(1 for r in results if r.get("aggregation_status") == "partial") / max(1, len(results)), 4
        ),
        "aggregation_conflict_rate": round(
            sum(1 for r in results if r.get("aggregation_status") == "conflict") / max(1, len(results)), 4
        ),
        "metric_absent_in_role_rate": round(
            sum(1 for r in quant if r.get("roles_absent_by_design")) / n, 4
        ),
        "missing_numeric_role_rate": round(
            sum(1 for r in quant if r.get("missing_numeric_roles")) / n, 4
        ),
        "narrative_metric_parse_success_count": sum(
            1 for r in quant
            if r.get("narrative_metric_parse_used") and r.get("aggregation_status") == "success"
        ),
        "narrative_metric_parse_success_rate": round(
            sum(
                1 for r in quant
                if r.get("narrative_metric_parse_used") and r.get("resolved_value")
            ) / n,
            4,
        ),
    }


def _focus_audit(plan: dict, ret, ext, agg, diag: dict) -> dict[str, Any]:
    recommendation = "failed"
    if agg.sufficiency_status == "resolved_single_source_sufficient":
        recommendation = "resolved_single_source_sufficient"
    elif agg.sufficiency_status == "resolved":
        recommendation = "resolved"
    elif agg.sufficiency_status == "partial_metric_absent_in_role":
        recommendation = "metric_absent"
    elif agg.sufficiency_status == "partial_missing_numeric_role":
        recommendation = "partial"
    elif ext.extraction_reason == "source_not_disclosed_for_metric":
        recommendation = "not_disclosed_honest_fail"
    elif all(agg.roles_absent_by_design) and not agg.roles_with_metric:
        recommendation = "metric_absent"

    return {
        "item_id": plan.get("item_id"),
        "extraction_ok": ext.success,
        "extraction_reason": ext.extraction_reason,
        "needs_multi_role": bool(plan.get("needs_merge")),
        "required_roles": agg.required_roles,
        "optional_roles": agg.optional_roles,
        "roles_with_metric": agg.roles_with_metric,
        "roles_absent_by_design": agg.roles_absent_by_design,
        "missing_numeric_roles": agg.missing_numeric_roles,
        "sufficiency_status": agg.sufficiency_status,
        "sufficiency_reason": agg.sufficiency_reason,
        "aggregation_status": agg.aggregation_status,
        "resolved_value": agg.resolved_value,
        "narrative_parse": ext.narrative_metric_parse_used,
        "recommended_label": recommendation,
    }


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Demo Company — Aggregation Sufficiency Taxonomy",
        "",
        f"Generated: {summary['timestamp']}",
        "",
        "## Delta vs `144715`",
        "",
    ]
    for k, d in summary.get("delta_vs_144715", {}).items():
        if k != "baseline_label" and isinstance(d, dict):
            lines.append(f"- `{k}`: {d.get('old')} → **{d.get('new')}** (Δ {d.get('delta')})")

    lines.extend(["", "## Focus case audit", ""])
    for c in summary.get("focus_case_analysis", []):
        lines.append(
            f"- **{c['item_id']}**: {c.get('recommended_label')} — "
            f"sufficiency=`{c.get('sufficiency_status')}` value=`{c.get('resolved_value')}`"
        )

    lines.extend([
        "",
        "## Benchmark honesty",
        "",
        summary.get("benchmark_honesty_note", ""),
        "",
        "## Kết luận",
        "",
        summary.get("conclusion", ""),
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="data/enterprise_docs/demo_company/corpus_units.jsonl")
    parser.add_argument("--single-subset", default="data/enterprise_docs/demo_company/eval_subset_single.jsonl")
    parser.add_argument("--cross-subset", default="data/enterprise_docs/demo_company/eval_subset_cross.jsonl")
    parser.add_argument("--reports-dir", default="reports")
    args = parser.parse_args()

    units = _load_jsonl(ROOT / args.corpus)
    lookup = {str(u["unit_id"]): u for u in units if u.get("unit_id")}
    index, logical_map = build_index_from_units(units)

    single_results: list[dict[str, Any]] = []
    for plan in _load_jsonl(ROOT / args.single_subset):
        ret = retrieve_for_plan(plan, index, logical_map)
        diag = evaluate_single_doc(plan, ret, logical_to_corpus=logical_map)
        ext = extract_from_retrieval(plan, ret, unit_lookup=lookup, retrieval_ready=bool(diag.get("single_doc_ready")))
        single_results.append({
            "item_id": plan.get("item_id"),
            "single_doc_ready": diag.get("single_doc_ready"),
            "extraction_success": ext.success,
            "wrong_row_risk": ext.wrong_row_risk,
            "narrative_metric_parse_used": ext.narrative_metric_parse_used,
            "narrative_parse_reason": ext.narrative_parse_reason,
        })

    cross_results: list[dict[str, Any]] = []
    focus_analysis: list[dict[str, Any]] = []
    for plan in _load_jsonl(ROOT / args.cross_subset):
        ret = retrieve_for_plan(plan, index, logical_map)
        diag = evaluate_cross_doc(plan, ret, logical_to_corpus=logical_map)
        ext = extract_from_retrieval(plan, ret, unit_lookup=lookup, retrieval_ready=True)
        agg = aggregate_cross_doc(plan, ret, unit_lookup=lookup, logical_to_corpus=logical_map)
        row = {
            "item_id": plan.get("item_id"),
            "kind": plan.get("kind"),
            "aggregation_status": agg.aggregation_status,
            "sufficiency_status": agg.sufficiency_status,
            "sufficiency_reason": agg.sufficiency_reason,
            "resolved_value": agg.resolved_value,
            "required_roles": agg.required_roles,
            "optional_roles": agg.optional_roles,
            "roles_with_metric": agg.roles_with_metric,
            "roles_absent_by_design": agg.roles_absent_by_design,
            "missing_numeric_roles": agg.missing_numeric_roles,
            "narrative_metric_parse_used": any(
                c.narrative_metric_parse_used for c in agg.aggregated_evidence_units
            ),
            "extraction_success": ext.success,
        }
        cross_results.append(row)
        if plan.get("item_id") in FOCUS_CASES:
            focus_analysis.append(_focus_audit(plan, ret, ext, agg, diag))

    single_m = _single_metrics(single_results)
    cross_m = _cross_metrics(cross_results)

    prev = _load_summary(BASELINE_144715)
    prev_cross = prev.get("cross") or {}

    delta_keys = [
        "quant_aggregation_success_rate",
        "resolved_single_source_sufficient_rate",
        "aggregation_partial_rate",
        "aggregation_conflict_rate",
        "metric_absent_in_role_rate",
        "missing_numeric_role_rate",
        "narrative_metric_parse_success_count",
    ]
    delta_144715 = {"baseline_label": "144715"}
    for k in delta_keys:
        delta_144715[k] = _delta(cross_m.get(k), prev_cross.get(k))

    partial_before = [
        r["item_id"] for r in _load_jsonl(BASELINE_144715 / "results_cross.jsonl")
        if r.get("aggregation_status") == "partial"
    ]
    now_single_sufficient = [
        r["item_id"] for r in cross_results
        if r.get("sufficiency_status") == "resolved_single_source_sufficient"
    ]

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / args.reports_dir / f"demo_company_aggregation_sufficiency_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "timestamp": ts,
        "single": single_m,
        "cross": cross_m,
        "delta_vs_144715": delta_144715,
        "focus_case_analysis": focus_analysis,
        "partial_to_single_source_sufficient": [
            qid for qid in partial_before if qid in now_single_sufficient
        ],
        "open_synthesis": False,
        "benchmark_honesty_note": (
            "quant_aggregation_success chi tang khi co rationale single_source_sufficient; "
            "partial giam khi role phu la metric_absent_in_role, khong inflate success vo co."
        ),
        "conclusion": (
            f"partial→single_source_sufficient: {len(now_single_sufficient)} cases; "
            f"quant_success={cross_m.get('quant_aggregation_success_rate')}; "
            "chua mo synthesis; khoa demo_company."
        ),
        "answers": {
            "partial_were_single_source_sufficient": now_single_sufficient,
            "metric_absent_cases": [
                r["item_id"] for r in cross_results
                if r.get("roles_absent_by_design") and r.get("kind") == "quantitative"
            ],
            "narrative_saved_env_investment": any(
                r.get("item_id") == "QUANT-0133" and r.get("narrative_metric_parse_used")
                for r in cross_results
            ),
            "biggest_bottleneck": "aggregation" if cross_m.get("quant_aggregation_success_rate", 0) < 0.5 else "extraction",
            "open_synthesis": False,
            "stay_on_demo_company": True,
        },
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out_dir / "results_single.jsonl").open("w", encoding="utf-8") as f:
        for row in single_results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (out_dir / "results_cross.jsonl").open("w", encoding="utf-8") as f:
        for row in cross_results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    _write_report(out_dir / "report.md", summary)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nArtifacts: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
