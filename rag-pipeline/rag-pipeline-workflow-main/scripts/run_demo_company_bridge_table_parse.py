#!/usr/bin/env python3
"""Benchmark EN↔KR bridge + table-unit-first retrieval + narrative metric parse."""

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

FOCUS_CASES = (
    "QUANT-0208",
    "QUANT-0209",
    "QUANT-0210",
    "QUANT-0213",
    "QUANT-0044",
    "QUANT-0046",
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _unit_lookup(units: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(u["unit_id"]): u for u in units if u.get("unit_id")}


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
    n = len(results)
    ready = [r for r in results if r.get("single_doc_ready")]
    n_ready = len(ready)
    return {
        "count": n,
        "single_doc_ready_count": n_ready,
        "single_extraction_success_rate_on_ready": round(
            sum(1 for r in ready if r.get("extraction_success")) / max(1, n_ready), 4
        ),
        "single_extraction_success_rate_all": round(
            sum(1 for r in results if r.get("extraction_success")) / max(1, n), 4
        ),
        "wrong_row_risk_count": sum(1 for r in results if r.get("wrong_row_risk")),
        "semantic_bridge_usage_count": sum(1 for r in results if r.get("semantic_bridge_used")),
        "narrative_metric_parse_success_count": sum(
            1 for r in results if r.get("narrative_metric_parse_used") and r.get("extraction_success")
        ),
        "metric_type": {
            "single_extraction_success": "proxy",
            "wrong_row_risk": "heuristic",
            "semantic_bridge_usage_count": "exact",
            "narrative_metric_parse_success_count": "exact",
        },
    }


def _cross_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(results)
    quant = [r for r in results if r.get("kind") == "quantitative"]
    return {
        "count": n,
        "quantitative_cross_count": len(quant),
        "aggregation_success_rate": round(
            sum(1 for r in results if r.get("aggregation_status") == "success") / max(1, n), 4
        ),
        "aggregation_partial_rate": round(
            sum(1 for r in results if r.get("aggregation_status") == "partial") / max(1, n), 4
        ),
        "aggregation_conflict_rate": round(
            sum(1 for r in results if r.get("aggregation_status") == "conflict") / max(1, n), 4
        ),
        "quant_aggregation_success_rate": round(
            sum(1 for r in quant if r.get("aggregation_status") == "success") / max(1, len(quant)), 4
        ),
        "table_unit_hit_rate": round(
            sum(1 for r in quant if r.get("table_unit_preferred")) / max(1, len(quant)), 4
        ),
        "semantic_bridge_usage_count": sum(1 for r in quant if r.get("semantic_bridge_used")),
        "narrative_metric_parse_success_count": sum(
            1 for r in quant if r.get("narrative_metric_parse_used") and r.get("aggregation_status") == "success"
        ),
        "missing_role_rate": round(
            sum(1 for r in quant if r.get("missing_roles_after_retrieval")) / max(1, len(quant)), 4
        ),
        "metric_type": {
            "quant_aggregation_success": "exact",
            "table_unit_hit_rate": "heuristic",
            "missing_role_rate": "exact",
        },
    }


def _analyze_focus_case(
    plan: dict[str, Any],
    retrieval: Any,
    extraction: Any,
    agg: Any,
    diag: dict[str, Any],
) -> dict[str, Any]:
    qid = plan.get("item_id")
    unit_types = [
        {"unit_id": u.unit_id, "is_table": u.is_table_unit, "doc": u.logical_document_id}
        for u in retrieval.top_units[:6]
    ]
    return {
        "item_id": qid,
        "docs_sufficient": not retrieval.missing_roles_after_retrieval,
        "role_coverage": retrieval.role_coverage,
        "table_unit_preferred": retrieval.table_unit_preferred,
        "table_candidates_seen": retrieval.table_candidates_seen,
        "units_retrieved": unit_types,
        "extraction_success": extraction.success,
        "extraction_reason": extraction.extraction_reason,
        "semantic_bridge_used": extraction.semantic_bridge_used or agg.resolution_status,
        "bridge_reason": extraction.bridge_reason,
        "narrative_parse": extraction.narrative_metric_parse_used,
        "aggregation_status": agg.aggregation_status,
        "aggregation_reason": agg.aggregation_reason,
        "resolved_value": agg.resolved_value,
        "primary_fail_stage": extraction.fail_stage or agg.fail_stage or diag.get("fail_stage"),
    }


def _write_report(path: Path, *, summary: dict[str, Any]) -> None:
    lines = [
        "# Demo Company — Bridge + Table-First + Narrative Parse",
        "",
        f"Generated: {summary['timestamp']}",
        "",
        "## Delta vs `143749`",
        "",
    ]
    for k, d in summary.get("delta_vs_143749", {}).items():
        if k != "baseline_label" and isinstance(d, dict):
            lines.append(f"- `{k}`: {d.get('old')} → **{d.get('new')}** (Δ {d.get('delta')})")

    lines.extend(["", "## Focus cases", ""])
    for c in summary.get("focus_case_analysis", []):
        lines.append(f"### {c['item_id']}")
        lines.append(f"- docs_sufficient: {c.get('docs_sufficient')}")
        lines.append(f"- table_unit_preferred: {c.get('table_unit_preferred')}")
        lines.append(f"- extraction: {c.get('extraction_success')} — {c.get('extraction_reason')}")
        lines.append(f"- aggregation: {c.get('aggregation_status')} — {c.get('aggregation_reason')}")
        lines.append(f"- fail_stage: {c.get('primary_fail_stage')}")
        lines.append("")

    lines.extend(["", "## Kết luận", "", summary.get("conclusion", ""), ""])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="data/enterprise_docs/demo_company/corpus_units.jsonl")
    parser.add_argument("--single-subset", default="data/enterprise_docs/demo_company/eval_subset_single.jsonl")
    parser.add_argument("--cross-subset", default="data/enterprise_docs/demo_company/eval_subset_cross.jsonl")
    parser.add_argument("--reports-dir", default="reports")
    args = parser.parse_args()

    units = _load_jsonl(ROOT / args.corpus)
    lookup = _unit_lookup(units)
    index, logical_map = build_index_from_units(units)
    single_rows = _load_jsonl(ROOT / args.single_subset)
    cross_rows = _load_jsonl(ROOT / args.cross_subset)

    single_results: list[dict[str, Any]] = []
    for plan in single_rows:
        retrieval = retrieve_for_plan(plan, index, logical_map)
        diag = evaluate_single_doc(plan, retrieval, logical_to_corpus=logical_map)
        ext = extract_from_retrieval(plan, retrieval, unit_lookup=lookup, retrieval_ready=bool(diag.get("single_doc_ready")))
        single_results.append({
            "item_id": plan.get("item_id"),
            "kind": plan.get("kind"),
            "single_doc_ready": diag.get("single_doc_ready"),
            "extraction_success": ext.success,
            "predicted_value": ext.predicted_value,
            "extraction_reason": ext.extraction_reason,
            "wrong_row_risk": ext.wrong_row_risk,
            "semantic_bridge_used": ext.semantic_bridge_used,
            "bridge_reason": ext.bridge_reason,
            "narrative_metric_parse_used": ext.narrative_metric_parse_used,
            "normalized_numeric_value": ext.normalized_numeric_value,
            "normalized_unit": ext.normalized_unit,
            "selected_row_label": ext.selected_row_label,
            "extraction_fail_stage": ext.fail_stage,
        })

    cross_results: list[dict[str, Any]] = []
    focus_analysis: list[dict[str, Any]] = []
    for plan in cross_rows:
        retrieval = retrieve_for_plan(plan, index, logical_map)
        diag = evaluate_cross_doc(plan, retrieval, logical_to_corpus=logical_map)
        ext = extract_from_retrieval(plan, retrieval, unit_lookup=lookup, retrieval_ready=True)
        agg = aggregate_cross_doc(plan, retrieval, unit_lookup=lookup)
        row = {
            "item_id": plan.get("item_id"),
            "kind": plan.get("kind"),
            "aggregation_status": agg.aggregation_status,
            "aggregation_reason": agg.aggregation_reason,
            "predicted_value": agg.predicted_value,
            "resolved_value": agg.resolved_value,
            "resolution_status": agg.resolution_status,
            "missing_roles_after_retrieval": retrieval.missing_roles_after_retrieval,
            "table_unit_preferred": retrieval.table_unit_preferred,
            "table_candidates_seen": retrieval.table_candidates_seen,
            "semantic_bridge_used": ext.semantic_bridge_used,
            "bridge_reason": ext.bridge_reason,
            "narrative_metric_parse_used": ext.narrative_metric_parse_used,
            "extraction_success": ext.success,
            "extraction_reason": ext.extraction_reason,
        }
        cross_results.append(row)
        if plan.get("item_id") in FOCUS_CASES:
            focus_analysis.append(_analyze_focus_case(plan, retrieval, ext, agg, diag))

    single_m = _single_metrics(single_results)
    cross_m = _cross_metrics(cross_results)

    prev = _load_summary(BASELINE_143749)
    prev_cross = prev.get("cross") or {}
    prev_single = prev.get("single") or {}

    delta_keys = [
        ("single", "single_extraction_success_rate_on_ready"),
        ("single", "wrong_row_risk_count"),
        ("cross", "quant_aggregation_success_rate"),
        ("cross", "aggregation_conflict_rate"),
        ("cross", "table_unit_hit_rate"),
        ("cross", "semantic_bridge_usage_count"),
        ("cross", "narrative_metric_parse_success_count"),
        ("cross", "missing_role_rate"),
    ]
    delta_143749 = {"baseline_label": "143749"}
    new_blob = {"single": single_m, "cross": cross_m}
    old_blob = {"single": prev_single, "cross": prev_cross}
    for section, key in delta_keys:
        delta_143749[key] = _delta(new_blob[section].get(key), old_blob[section].get(key))

    rescued = [
        r["item_id"]
        for r in cross_results
        if r["item_id"] in FOCUS_CASES
        and r.get("aggregation_status") == "success"
    ]
    still_fail = [
        r["item_id"]
        for r in cross_results
        if r["item_id"] in FOCUS_CASES
        and r.get("aggregation_status") not in ("success",)
    ]

    quant_success = cross_m.get("quant_aggregation_success_rate", 0)
    wrong_row = single_m.get("wrong_row_risk_count", 0)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / args.reports_dir / f"demo_company_bridge_table_parse_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "timestamp": ts,
        "single": single_m,
        "cross": cross_m,
        "delta_vs_142543_note": "see delta_vs_143749 for latest comparison",
        "delta_vs_143749": delta_143749,
        "focus_case_analysis": focus_analysis,
        "rescued_focus_cases": rescued,
        "still_failing_focus_cases": still_fail,
        "open_synthesis": False,
        "expand_to_hanssem_musinsa": False,
        "conclusion": (
            f"Bridge/table/narrative round: quant_success={quant_success}, "
            f"wrong_row={wrong_row}, rescued={rescued}, still_fail={still_fail}. "
            "Chua mo synthesis; khoa tiep demo_company."
        ),
        "answers": {
            "bridge_cases_rescued": len(rescued),
            "table_first_helped_financial": cross_m.get("table_unit_hit_rate", 0) > float(prev_cross.get("table_unit_hit_rate") or 0),
            "narrative_parser_usable": cross_m.get("narrative_metric_parse_success_count", 0) > 0,
            "biggest_bottleneck": "extraction" if quant_success < 0.5 else "aggregation",
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
    _write_report(out_dir / "report.md", summary=summary)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nArtifacts: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
