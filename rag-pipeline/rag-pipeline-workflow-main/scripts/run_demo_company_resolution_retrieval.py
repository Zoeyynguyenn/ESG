#!/usr/bin/env python3
"""Benchmark row disambiguation + conflict resolution + role-aware retrieval."""

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

BASELINE_EXTRACTOR = ROOT / "reports/demo_company_extractor_aggregator_20260618-142543"
BASELINE_DIAGNOSTIC = ROOT / "reports/demo_company_crossdoc_diagnostic_20260618-141731"


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


def _load_baseline_summary(path: Path) -> dict[str, Any]:
    p = path / "summary.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _delta(new: float | int | None, old: float | int | None) -> dict[str, Any]:
    if new is None or old is None:
        return {"new": new, "old": old, "delta": None}
    try:
        d = float(new) - float(old)
        return {"new": new, "old": old, "delta": round(d, 4)}
    except (TypeError, ValueError):
        return {"new": new, "old": old, "delta": None}


def _single_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(results)
    if not n:
        return {}
    ready = [r for r in results if r.get("single_doc_ready")]
    n_ready = len(ready)
    n_ready_success = sum(1 for r in ready if r.get("extraction_success"))
    wrong_row = sum(1 for r in results if r.get("wrong_row_risk"))
    breakdown = Counter(r.get("extraction_fail_stage") or r.get("fail_stage") for r in results)
    return {
        "count": n,
        "single_doc_ready_count": n_ready,
        "single_extraction_success_rate_on_ready": round(n_ready_success / max(1, n_ready), 4),
        "single_extraction_success_rate_all": round(
            sum(1 for r in results if r.get("extraction_success")) / n, 4
        ),
        "wrong_row_risk_count": wrong_row,
        "wrong_row_risk_rate_on_ready": round(
            sum(1 for r in ready if r.get("wrong_row_risk")) / max(1, n_ready), 4
        ),
        "single_fail_breakdown": dict(breakdown),
        "metric_type": {
            "single_extraction_success": "proxy — parseable numeric, NOT gold accuracy",
            "wrong_row_risk": "heuristic — weak row_match or extra label tokens vs question",
        },
    }


def _cross_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(results)
    if not n:
        return {}
    quant = [r for r in results if r.get("kind") == "quantitative"]
    breakdown = Counter(r.get("aggregation_fail_stage") or r.get("fail_stage") for r in results)
    resolved_count = sum(
        1
        for r in quant
        if r.get("resolution_status") in ("resolved", "resolved_with_preference_rule")
    )
    return {
        "count": n,
        "quantitative_cross_count": len(quant),
        "aggregation_success_rate": round(
            sum(1 for r in results if r.get("aggregation_status") == "success") / n, 4
        ),
        "aggregation_partial_rate": round(
            sum(1 for r in results if r.get("aggregation_status") == "partial") / n, 4
        ),
        "aggregation_conflict_rate": round(
            sum(1 for r in results if r.get("aggregation_status") == "conflict") / n, 4
        ),
        "aggregation_missing_role_rate": round(
            sum(1 for r in quant if r.get("missing_numeric_roles")) / max(1, len(quant)), 4
        ),
        "quant_aggregation_success_rate": round(
            sum(1 for r in quant if r.get("aggregation_status") == "success") / max(1, len(quant)),
            4,
        ),
        "quant_resolution_rate": round(resolved_count / max(1, len(quant)), 4),
        "cross_fail_breakdown": dict(breakdown),
        "metric_type": {
            "aggregation_success": "exact — aggregator legacy status success",
            "quant_resolution_rate": "exact — resolution_status resolved* on quant rows",
        },
    }


def _retrieval_metrics(cross_results: list[dict[str, Any]]) -> dict[str, Any]:
    quant = [r for r in cross_results if r.get("kind") == "quantitative"]
    if not quant:
        return {}
    role_cov = [float(r.get("role_coverage") or 0) for r in quant]
    csv_hits = sum(1 for r in quant if r.get("csv_role_hit"))
    missing_role = sum(1 for r in quant if r.get("missing_roles_after_retrieval"))
    return {
        "role_coverage_rate": round(sum(role_cov) / len(quant), 4),
        "csv_role_hit_rate": round(csv_hits / len(quant), 4),
        "missing_role_rate": round(missing_role / len(quant), 4),
        "metric_type": {
            "role_coverage_rate": "heuristic — fraction of planned roles with unit hit",
            "csv_role_hit_rate": "exact — doc_evidence_csv in role_hits",
            "missing_role_rate": "exact — quant rows with missing_roles_after_retrieval",
        },
    }


def _compare_metrics(
    new_summary: dict[str, Any],
    baseline: dict[str, Any],
    *,
    label: str,
) -> dict[str, Any]:
    keys = [
        ("single", "single_doc_ready_count"),
        ("single", "single_extraction_success_rate_on_ready"),
        ("single", "single_extraction_success_rate_all"),
        ("single", "wrong_row_risk_count"),
        ("cross", "quant_aggregation_success_rate"),
        ("cross", "aggregation_success_rate"),
        ("cross", "aggregation_conflict_rate"),
        ("cross", "aggregation_partial_rate"),
        ("cross", "aggregation_missing_role_rate"),
        ("retrieval", "role_coverage_rate"),
        ("retrieval", "csv_role_hit_rate"),
        ("retrieval", "missing_role_rate"),
    ]
    out: dict[str, Any] = {"baseline_label": label}
    for section, key in keys:
        new_val = (new_summary.get(section) or {}).get(key)
        old_val = (baseline.get(section) or {}).get(key)
        out[key] = _delta(new_val, old_val)
    return out


def _write_report(
    path: Path,
    *,
    summary: dict[str, Any],
    single_results: list[dict[str, Any]],
    cross_results: list[dict[str, Any]],
) -> None:
    delta = summary.get("delta_vs_142543", {})
    improved = summary.get("improved_cases", [])
    still_fail = summary.get("still_failing_cases", [])

    lines = [
        "# Demo Company — Row Disambiguation + Conflict Resolution + Role-Aware Retrieval",
        "",
        f"Generated: {summary.get('timestamp')}",
        "",
        "## Delta vs vòng `142543`",
        "",
    ]
    for key, d in delta.items():
        if key == "baseline_label" or not isinstance(d, dict):
            continue
        lines.append(f"- `{key}`: {d.get('old')} → **{d.get('new')}** (Δ {d.get('delta')})")

    lines.extend(["", "## Single-doc (row disambiguation)", ""])
    for k, v in summary.get("single", {}).items():
        if k != "metric_type":
            lines.append(f"- `{k}`: **{v}**")

    lines.extend(["", "## Cross-doc (conflict resolution)", ""])
    for k, v in summary.get("cross", {}).items():
        if k not in ("metric_type", "cross_fail_breakdown"):
            lines.append(f"- `{k}`: **{v}**")

    lines.extend(["", "## Retrieval-aware", ""])
    for k, v in summary.get("retrieval", {}).items():
        if k != "metric_type":
            lines.append(f"- `{k}`: **{v}**")

    lines.extend(["", "## 3 case cải thiện", ""])
    for c in improved[:3]:
        lines.append(f"- **{c['item_id']}**: {c.get('note', '')}")

    lines.extend(["", "## 3 case vẫn fail", ""])
    for c in still_fail[:3]:
        lines.append(f"- **{c['item_id']}**: {c.get('note', '')}")

    lines.extend([
        "",
        "## Kết luận",
        "",
        summary.get("conclusion", ""),
        "",
        f"**open_synthesis**: {summary.get('open_synthesis')}",
        "",
        "## Bước tiếp theo",
        "",
        summary.get("next_step", ""),
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _compare_cases(
    new_single: list[dict],
    old_single: list[dict],
    new_cross: list[dict],
    old_cross: list[dict],
) -> tuple[list[dict], list[dict]]:
    old_s = {r["item_id"]: r for r in old_single}
    old_c = {r["item_id"]: r for r in old_cross}
    improved: list[dict] = []
    still_fail: list[dict] = []

    for r in new_single:
        oid = r["item_id"]
        o = old_s.get(oid, {})
        if oid == "QUANT-0001" and o.get("extraction_reason", "").endswith("구성원 총 교육 시간"):
            if r.get("selected_row_label") and "임직원" in str(r.get("selected_row_label", "")):
                improved.append({
                    "item_id": oid,
                    "note": f"wrong-row fixed: {o.get('extraction_reason')} → {r.get('selected_row_label')}",
                })
        if o.get("wrong_row_risk") and not r.get("wrong_row_risk"):
            improved.append({"item_id": oid, "note": "wrong_row_risk cleared"})
        if o.get("extraction_success") and r.get("wrong_row_risk") and not o.get("wrong_row_risk"):
            still_fail.append({
                "item_id": oid,
                "note": f"new wrong_row_risk: {r.get('wrong_row_risk_reason')}",
            })

    for r in new_cross:
        oid = r["item_id"]
        o = old_c.get(oid, {})
        if o.get("aggregation_status") in ("conflict", "partial") and r.get("aggregation_status") == "success":
            improved.append({
                "item_id": oid,
                "note": f"{o.get('aggregation_status')} → success ({r.get('resolution_reason')})",
            })
        elif r.get("aggregation_status") in ("conflict", "partial", "failed") and r.get("kind") == "quantitative":
            still_fail.append({
                "item_id": oid,
                "note": f"status={r.get('aggregation_status')} reason={r.get('aggregation_reason')}",
            })

    return improved, still_fail


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
        extraction = extract_from_retrieval(
            plan,
            retrieval,
            unit_lookup=lookup,
            retrieval_ready=bool(diag.get("single_doc_ready")),
        )
        single_results.append({
            "item_id": plan.get("item_id"),
            "kind": plan.get("kind"),
            "question": plan.get("question"),
            "single_doc_ready": diag.get("single_doc_ready"),
            "extraction_success": extraction.success,
            "predicted_value": extraction.predicted_value,
            "predicted_unit": extraction.predicted_unit,
            "selected_doc": extraction.selected_doc,
            "selected_unit_ids": extraction.selected_unit_ids,
            "extraction_reason": extraction.extraction_reason,
            "extraction_confidence": extraction.extraction_confidence,
            "extraction_fail_stage": extraction.fail_stage,
            "year_used": extraction.year_used,
            "row_match_score": extraction.row_match_score,
            "row_match_reason": extraction.row_match_reason,
            "selected_row_label": extraction.selected_row_label,
            "top_row_candidates": extraction.top_row_candidates,
            "wrong_row_risk": extraction.wrong_row_risk,
            "wrong_row_risk_reason": extraction.wrong_row_risk_reason,
            "fail_stage": diag.get("fail_stage"),
        })

    cross_results: list[dict[str, Any]] = []
    for plan in cross_rows:
        retrieval = retrieve_for_plan(plan, index, logical_map)
        diag = evaluate_cross_doc(plan, retrieval, logical_to_corpus=logical_map)
        agg = aggregate_cross_doc(plan, retrieval, unit_lookup=lookup)
        cross_results.append({
            "item_id": plan.get("item_id"),
            "kind": plan.get("kind"),
            "question": plan.get("question"),
            "needs_merge": plan.get("needs_merge"),
            "cross_doc_ready": diag.get("cross_doc_ready"),
            "aggregation_status": agg.aggregation_status,
            "aggregation_reason": agg.aggregation_reason,
            "predicted_value": agg.predicted_value,
            "predicted_unit": agg.predicted_unit,
            "resolved_value": agg.resolved_value,
            "resolution_status": agg.resolution_status,
            "resolution_reason": agg.resolution_reason,
            "primary_doc_used": agg.primary_doc_used,
            "conflict_flags": agg.conflict_flags,
            "missing_roles": agg.missing_roles,
            "missing_numeric_roles": agg.missing_roles,
            "missing_roles_retrieval": retrieval.missing_roles_after_retrieval,
            "candidate_count": len(agg.aggregated_evidence_units),
            "unique_docs_with_values": len({c.logical_document_id for c in agg.aggregated_evidence_units}),
            "aggregation_fail_stage": agg.fail_stage,
            "role_coverage": retrieval.role_coverage,
            "role_hits": retrieval.role_hits,
            "missing_roles_after_retrieval": retrieval.missing_roles_after_retrieval,
            "csv_role_hit": retrieval.csv_role_hit,
            "fail_stage": diag.get("fail_stage"),
        })

    single_agg = _single_metrics(single_results)
    cross_agg = _cross_metrics(cross_results)
    retrieval_agg = _retrieval_metrics(cross_results)

    baseline_142 = _load_baseline_summary(BASELINE_EXTRACTOR)
    old_single = _load_jsonl(BASELINE_EXTRACTOR / "results_single.jsonl") if BASELINE_EXTRACTOR.exists() else []
    old_cross = _load_jsonl(BASELINE_EXTRACTOR / "results_cross.jsonl") if BASELINE_EXTRACTOR.exists() else []
    improved, still_fail = _compare_cases(single_results, old_single, cross_results, old_cross)

    wrong_row_ready = single_agg.get("wrong_row_risk_rate_on_ready", 1.0)
    quant_success = cross_agg.get("quant_aggregation_success_rate", 0)
    missing_role = retrieval_agg.get("missing_role_rate", 1.0)

    open_synthesis = False
    if quant_success >= 0.7 and wrong_row_ready <= 0.1 and missing_role <= 0.2:
        open_synthesis = False  # still defer qualitative per constraints

    conclusion_parts = []
    baseline_wrong = (baseline_142.get("single") or {}).get("wrong_row_risk_count", 10)
    if single_agg.get("wrong_row_risk_count", 99) < baseline_wrong:
        conclusion_parts.append("row disambiguation giảm wrong-row risk so với vòng 142543.")
    else:
        conclusion_parts.append("row disambiguation cải thiện một phần nhưng wrong-row risk vẫn cần theo dõi.")

    if quant_success > float((baseline_142.get("cross") or {}).get("quant_aggregation_success_rate", 0)):
        conclusion_parts.append("conflict resolution chuyển thêm case conflict/partial sang resolved.")
    else:
        conclusion_parts.append("conflict resolution chưa tăng quant success đáng kể.")

    if missing_role < float((baseline_142.get("cross") or {}).get("aggregation_missing_role_rate", 1)):
        conclusion_parts.append("role-aware retrieval giảm missing role một phần.")
    else:
        conclusion_parts.append("role-aware retrieval chưa giảm missing role đủ.")

    conclusion_parts.append("Chưa mở qualitative synthesis — bottleneck extraction/aggregation vẫn còn.")
    conclusion = " ".join(conclusion_parts)

    bottleneck = "extraction"
    if cross_agg.get("aggregation_conflict_rate", 0) > 0.15:
        bottleneck = "aggregation"
    if retrieval_agg.get("missing_role_rate", 0) > 0.4:
        bottleneck = "retrieval"

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / args.reports_dir / f"demo_company_resolution_retrieval_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "timestamp": ts,
        "corpus_unit_count": len(units),
        "single": single_agg,
        "cross": cross_agg,
        "retrieval": retrieval_agg,
        "delta_vs_142543": _compare_metrics(
            {"single": single_agg, "cross": cross_agg, "retrieval": retrieval_agg},
            baseline_142,
            label="demo_company_extractor_aggregator_20260618-142543",
        ),
        "delta_vs_141731_note": "diagnostic baseline is retrieval-only approximation — compare role metrics qualitatively",
        "improved_cases": improved,
        "still_failing_cases": still_fail,
        "primary_bottleneck_after_round": bottleneck,
        "conclusion": conclusion,
        "next_step": (
            "Tiếp tục siết row scoring cho HR/GHG tables; mở rộng metric-key normalization; "
            "tăng CSV unit floor cho cross-doc partial cases."
        ),
        "open_synthesis": open_synthesis,
        "expand_to_hanssem_musinsa": False,
        "answers": {
            "row_disambiguation_reduced_wrong_row": single_agg.get("wrong_row_risk_count", 0)
            < (baseline_142.get("single") or {}).get("wrong_row_risk_count", 99),
            "conflict_resolution_cases_moved_to_resolved": cross_agg.get("quant_resolution_rate"),
            "role_aware_retrieval_reduced_missing_role": missing_role
            < float((baseline_142.get("cross") or {}).get("aggregation_missing_role_rate", 1)),
            "biggest_bottleneck": bottleneck,
            "open_qualitative_synthesis": False,
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

    _write_report(
        out_dir / "report.md",
        summary=summary,
        single_results=single_results,
        cross_results=cross_results,
    )

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nArtifacts: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
