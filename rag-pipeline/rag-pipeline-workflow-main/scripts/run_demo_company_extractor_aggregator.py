#!/usr/bin/env python3
"""Pilot benchmark: structured extraction (single) + evidence aggregation (cross)."""

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


def _single_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(results)
    if not n:
        return {}
    ready = [r for r in results if r.get("single_doc_ready")]
    n_ready = len(ready)
    n_ready_success = sum(1 for r in ready if r.get("extraction_success"))
    breakdown = Counter(r.get("extraction_fail_stage") or r.get("fail_stage") for r in results)
    return {
        "count": n,
        "single_doc_ready_count": n_ready,
        "single_extraction_success_rate_on_ready": round(
            n_ready_success / max(1, n_ready), 4
        ),
        "single_extraction_success_rate_all": round(
            sum(1 for r in results if r.get("extraction_success")) / n, 4
        ),
        "single_fail_breakdown": dict(breakdown),
        "note": "no gold answer in subset — success = parseable numeric only, NOT correctness (see QUANT-0001 wrong-row risk)",
    }


def _cross_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(results)
    if not n:
        return {}
    breakdown = Counter(r.get("aggregation_fail_stage") or r.get("fail_stage") for r in results)
    return {
        "count": n,
        "quantitative_cross_count": sum(1 for r in results if r.get("kind") == "quantitative"),
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
            sum(1 for r in results if r.get("missing_roles")) / n, 4
        ),
        "cross_fail_breakdown": dict(breakdown),
        "note": "qualitative rows marked synthesis_gap — quant aggregation measured separately",
    }


def _write_report(
    path: Path,
    *,
    summary: dict[str, Any],
    single_results: list[dict[str, Any]],
    cross_results: list[dict[str, Any]],
) -> None:
    single_ok = [r for r in single_results if r.get("extraction_success")][:2]
    single_fail = [r for r in single_results if not r.get("extraction_success")][:2]
    cross_ok = [r for r in cross_results if r.get("aggregation_status") == "success"][:2]
    cross_bad = [r for r in cross_results if r.get("aggregation_status") in ("conflict", "partial", "failed")][:2]

    lines = [
        "# Demo Company Extractor + Aggregator Pilot Report",
        "",
        f"Generated: {summary.get('timestamp')}",
        "",
        "## Single-doc extraction pilot",
        "",
        f"- Subset size: **{summary['single']['count']}**",
        f"- Ready for extraction: **{summary['single']['single_doc_ready_count']}**",
        f"- `single_extraction_success_rate_on_ready`: **{summary['single']['single_extraction_success_rate_on_ready']}**",
        f"- `single_extraction_success_rate_all`: **{summary['single']['single_extraction_success_rate_all']}**",
        "",
        "### Fail breakdown",
        "",
    ]
    for k, v in summary["single"].get("single_fail_breakdown", {}).items():
        lines.append(f"- `{k}`: {v}")

    lines.extend(["", "## Cross-doc aggregation pilot", ""])
    for k, v in summary["cross"].items():
        if k not in ("note", "cross_fail_breakdown"):
            lines.append(f"- `{k}`: **{v}**")
    lines.extend(["", "### Fail breakdown", ""])
    for k, v in summary["cross"].get("cross_fail_breakdown", {}).items():
        lines.append(f"- `{k}`: {v}")

    lines.extend(["", "## Ví dụ single", ""])
    for r in single_ok:
        lines.append(
            f"- **{r['item_id']}** value=`{r.get('predicted_value')}` "
            f"doc=`{r.get('selected_doc')}` reason=`{r.get('extraction_reason')}`"
        )
    for r in single_fail:
        lines.append(
            f"- **{r['item_id']}** FAIL stage=`{r.get('extraction_fail_stage')}` "
            f"reason=`{r.get('extraction_reason')}`"
        )

    lines.extend(["", "## Ví dụ cross", ""])
    for r in cross_ok:
        lines.append(
            f"- **{r['item_id']}** status=`{r.get('aggregation_status')}` "
            f"value=`{r.get('predicted_value')}` flags={r.get('conflict_flags')}"
        )
    for r in cross_bad:
        lines.append(
            f"- **{r['item_id']}** status=`{r.get('aggregation_status')}` "
            f"reason=`{r.get('aggregation_reason')}` missing_roles={r.get('missing_roles')}"
        )

    lines.extend([
        "",
        "## Kết luận",
        "",
        summary.get("conclusion", ""),
        "",
        "## Bước tiếp theo",
        "",
        summary.get("next_step", ""),
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
            "conflict_flags": agg.conflict_flags,
            "missing_roles": agg.missing_roles,
            "candidate_count": len(agg.aggregated_evidence_units),
            "unique_docs_with_values": len({c.logical_document_id for c in agg.aggregated_evidence_units}),
            "aggregation_fail_stage": agg.fail_stage,
            "fail_stage": diag.get("fail_stage"),
        })

    single_agg = _single_metrics(single_results)
    cross_agg = _cross_metrics(cross_results)

    # Quant-only cross aggregation stats
    cross_quant = [r for r in cross_results if r.get("kind") == "quantitative"]
    if cross_quant:
        cross_agg["quant_aggregation_success_rate"] = round(
            sum(1 for r in cross_quant if r.get("aggregation_status") == "success")
            / len(cross_quant),
            4,
        )

    success_on_ready = float(single_agg.get("single_extraction_success_rate_on_ready") or 0)
    agg_success = float(cross_agg.get("quant_aggregation_success_rate", cross_agg.get("aggregation_success_rate")) or 0)

    if success_on_ready >= 0.6:
        conclusion = (
            "structured_extractor giải quyết đúng bottleneck unit-level cho nhóm ready; "
            "có thể mở rộng extractor pilot."
        )
    else:
        conclusion = (
            "extractor giúp phân loại fail (retrieval vs extraction) nhưng success rate còn thấp — "
            "cần cải thiện table row matching / unit targeting."
        )

    if agg_success < 0.4:
        conclusion += " evidence_aggregator chưa đủ ổn cho cross quant merge — chưa synthesis."
    else:
        conclusion += " aggregator tạo được mergeable evidence một phần — vẫn chưa đủ cho qualitative synthesis."

    synthesis_ok = agg_success >= 0.6 and success_on_ready >= 0.7
    next_step = (
        "Mở rộng extractor + conflict resolution trong aggregator; thêm role-aware subquery retrieval."
        if not synthesis_ok
        else "Có thể pilot synthesis trên subset quant nhỏ; qualitative vẫn defer."
    )

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / args.reports_dir / f"demo_company_extractor_aggregator_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "timestamp": ts,
        "corpus_unit_count": len(units),
        "single": single_agg,
        "cross": cross_agg,
        "primary_bottleneck_after_pilot": _infer_bottleneck(single_results, cross_results),
        "conclusion": conclusion,
        "next_step": next_step,
        "open_synthesis": False,
        "metric_notes": {
            "single_extraction_success": "proxy — parseable numeric, no gold match",
            "aggregation_success": "real aggregator output status, not retrieval approximation",
        },
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out_dir / "results_single.jsonl").open("w", encoding="utf-8") as f:
        for row in single_results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (out_dir / "results_cross.jsonl").open("w", encoding="utf-8") as f:
        for row in cross_results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    _write_report(out_dir / "report.md", summary=summary, single_results=single_results, cross_results=cross_results)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nArtifacts: {out_dir}")
    return 0


def _infer_bottleneck(single: list[dict], cross: list[dict]) -> str:
    ext_fail = Counter(r.get("extraction_fail_stage") for r in single if not r.get("extraction_success"))
    agg_fail = Counter(
        r.get("aggregation_fail_stage")
        for r in cross
        if r.get("kind") == "quantitative" and r.get("aggregation_status") != "success"
    )
    if ext_fail.get("extraction_gap", 0) >= ext_fail.get("retrieval_gap", 0):
        top = "extraction"
    else:
        top = "retrieval"
    if agg_fail.get("aggregation_gap", 0) > 0:
        return f"aggregation (cross quant) + {top} (single)"
    return top


if __name__ == "__main__":
    raise SystemExit(main())
