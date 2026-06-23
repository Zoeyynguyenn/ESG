#!/usr/bin/env python3
"""Diagnostic benchmark: single-doc vs cross-doc retrieval on demo_company subset."""

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
from enterprise_docs.diagnostics import aggregate_metrics, evaluate_cross_doc, evaluate_single_doc


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _run_subset(
    subset_rows: list[dict[str, Any]],
    index: dict[str, Any],
    logical_map: dict[str, str],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for plan_row in subset_rows:
        retrieval = retrieve_for_plan(plan_row, index, logical_map)
        mode = plan_row.get("answer_mode")
        if mode == "cross_document_answer":
            metrics = evaluate_cross_doc(plan_row, retrieval, logical_to_corpus=logical_map)
        else:
            metrics = evaluate_single_doc(plan_row, retrieval, logical_to_corpus=logical_map)

        row = {
            "question_id": plan_row.get("item_id"),
            "item_id": plan_row.get("item_id"),
            "answer_mode": mode,
            "kind": plan_row.get("kind"),
            "domain": plan_row.get("domain"),
            "question": plan_row.get("question"),
            "top_docs": [d.logical_document_id for d in retrieval.top_docs],
            "top_units": [
                {
                    "unit_id": u.unit_id,
                    "logical_document_id": u.logical_document_id,
                    "score": u.score,
                }
                for u in retrieval.top_units
            ],
            "missing_docs": retrieval.missing_docs,
            "missing_roles": retrieval.missing_roles,
            "evidence_plan_coverage": retrieval.evidence_plan_coverage,
            **metrics,
        }
        results.append(row)
    return results


def _write_report(
    path: Path,
    *,
    summary: dict[str, Any],
    single_results: list[dict[str, Any]],
    cross_results: list[dict[str, Any]],
) -> None:
    lines = [
        "# Demo Company Cross-Document Diagnostic Report",
        "",
        f"Generated: {summary.get('timestamp')}",
        "",
        "## Tổng quan subset",
        "",
        f"- Single-doc: **{summary['single']['count']}** câu",
        f"- Cross-doc: **{summary['cross']['count']}** câu",
        f"- Corpus units: **{summary.get('corpus_unit_count')}**",
        "",
        "> Heuristic evidence plan là bootstrap — metric đo retrieval/aggregation readiness, không phải answer accuracy.",
        "",
        "## Metric single-doc",
        "",
    ]
    for k, v in summary["single"].items():
        if k != "fail_stage_counts":
            lines.append(f"- `{k}`: **{v}**")
    lines.extend(["", "### Fail stages (single)", ""])
    for stage, cnt in summary["single"].get("fail_stage_counts", {}).items():
        lines.append(f"- {stage}: {cnt}")

    lines.extend(["", "## Metric cross-doc", ""])
    for k, v in summary["cross"].items():
        if k != "fail_stage_counts":
            lines.append(f"- `{k}`: **{v}**")
    lines.extend(["", "### Fail stages (cross)", ""])
    for stage, cnt in summary["cross"].get("fail_stage_counts", {}).items():
        lines.append(f"- {stage}: {cnt}")

    fail_patterns = Counter(r.get("fail_stage") for r in single_results + cross_results)
    lines.extend(["", "## Top fail patterns", ""])
    for stage, cnt in fail_patterns.most_common():
        lines.append(f"- `{stage}`: {cnt}")

    ready_single = [r["item_id"] for r in single_results if r.get("single_doc_ready")]
    not_ready_single = [r["item_id"] for r in single_results if not r.get("single_doc_ready")]
    ready_cross = [r["item_id"] for r in cross_results if r.get("cross_doc_ready")]
    not_ready_cross = [r["item_id"] for r in cross_results if not r.get("cross_doc_ready")]

    lines.extend([
        "",
        "## Sẵn sàng cho bước answer (approximation)",
        "",
        f"- Single ready ({len(ready_single)}): {', '.join(ready_single) or 'none'}",
        f"- Single NOT ready ({len(not_ready_single)}): {', '.join(not_ready_single) or 'none'}",
        f"- Cross ready ({len(ready_cross)}): {', '.join(ready_cross) or 'none'}",
        f"- Cross NOT ready ({len(not_ready_cross)}): {', '.join(not_ready_cross) or 'none'}",
        "",
        "## Bottleneck chính",
        "",
        f"- **{summary.get('primary_bottleneck')}**",
        "",
        summary.get("bottleneck_note", ""),
        "",
        "## Khuyến nghị bước tiếp",
        "",
        summary.get("next_step", ""),
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _infer_bottleneck(
    single_agg: dict[str, Any],
    cross_agg: dict[str, Any],
) -> tuple[str, str, str]:
    parser_rate = max(
        float(single_agg.get("parser_fail_rate") or 0),
        float(cross_agg.get("parser_fail_rate") or 0),
    )
    if parser_rate > 0.1:
        return (
            "parser_gap",
            "Parser/conversion vẫn có unit rỗng hoặc thiếu signal — cần kiểm tra ingest trước khi tune retriever.",
            "Cải thiện parser/chunking trên demo_company; chưa mở synthesis.",
        )

    cross_ready = float(cross_agg.get("cross_doc_ready_rate") or 0)
    single_ready = float(single_agg.get("single_doc_ready_rate") or 0)
    agg = float(cross_agg.get("aggregation_readiness") or 0)
    recall = float(cross_agg.get("multi_doc_recall") or 0)

    if cross_ready < 0.4 and recall < 0.5:
        return (
            "retrieval_gap (cross-document)",
            f"Cross-doc `multi_doc_recall`≈{recall}, `cross_doc_ready_rate`≈{cross_ready} — retriever chưa đủ diversify multi-doc.",
            "Improve cross_doc_retriever (per-role query, doc floor, MMR); chưa synthesis.",
        )

    doc1 = float(single_agg.get("doc_hit_at_1") or 0)
    unit_hit = float(single_agg.get("unit_hit_at_k") or 0)
    if doc1 < 0.7:
        return (
            "retrieval_gap (single-doc top-1 routing)",
            f"`doc_hit_at_1`≈{doc1} — top-1 lệch primary doc.",
            "Boost planned primary doc trong single path.",
        )
    if single_ready < 0.6 and unit_hit < 0.6:
        return (
            "retrieval_gap (unit signal) + chưa đủ cho answer",
            f"`doc_hit_at_1`≈{doc1} OK nhưng `unit_hit_at_k`≈{unit_hit} (token overlap approximation) — doc đúng nhưng chunk signal yếu.",
            "Pilot answer extractor trên 10 câu single_doc_ready; cải thiện chunk/table targeting; chưa synthesis qualitative.",
        )

    if cross_ready < 0.5 and agg < 0.5:
        return (
            "aggregation_gap",
            f"`aggregation_readiness`≈{agg} — đủ mảnh retrieval nhưng chưa ghép đủ doc cho merge.",
            "Thêm evidence_aggregator (year join, table align); synthesis sau.",
        )

    if single_ready >= 0.7 and cross_ready < 0.5:
        return (
            "retrieval_gap (cross) + aggregation",
            f"Single ready {single_ready} vs cross ready {cross_ready} — single-doc lane ổn hơn cross-doc.",
            "Ưu tiên cross_doc_retriever + aggregator; single có thể pilot answer extractor.",
        )

    return (
        "mixed — retrieval mostly OK on single",
        f"single_doc_ready_rate≈{single_ready}, cross_doc_ready_rate≈{cross_ready}",
        "Pilot answer extractor trên single subset; parallel improve aggregator cho cross.",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus",
        default="data/enterprise_docs/demo_company/corpus_units.jsonl",
    )
    parser.add_argument(
        "--single-subset",
        default="data/enterprise_docs/demo_company/eval_subset_single.jsonl",
    )
    parser.add_argument(
        "--cross-subset",
        default="data/enterprise_docs/demo_company/eval_subset_cross.jsonl",
    )
    parser.add_argument("--reports-dir", default="reports")
    args = parser.parse_args()

    corpus_path = ROOT / args.corpus
    units = _load_jsonl(corpus_path)
    index, logical_map = build_index_from_units(units)

    single_rows = _load_jsonl(ROOT / args.single_subset)
    cross_rows = _load_jsonl(ROOT / args.cross_subset)

    single_results = _run_subset(single_rows, index, logical_map)
    cross_results = _run_subset(cross_rows, index, logical_map)

    single_agg = aggregate_metrics(single_results, "single_document_answer")
    cross_agg = aggregate_metrics(cross_results, "cross_document_answer")

    bottleneck, bottleneck_note, next_step = _infer_bottleneck(single_agg, cross_agg)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / args.reports_dir / f"demo_company_crossdoc_diagnostic_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "timestamp": ts,
        "corpus_unit_count": len(units),
        "logical_to_corpus_map": logical_map,
        "single": single_agg,
        "cross": cross_agg,
        "single_doc_ready_rate": single_agg.get("single_doc_ready_rate"),
        "cross_doc_ready_rate": cross_agg.get("cross_doc_ready_rate"),
        "primary_bottleneck": bottleneck,
        "bottleneck_note": bottleneck_note,
        "next_step": next_step,
        "metric_notes": {
            "doc_hit_at_k": "approximation — top-3 docs vs planned primary",
            "multi_doc_recall": "approximation — planned logical docs with >=1 unit in top-k",
            "aggregation_readiness": "approximation — unique docs in units / min(required,2) when needs_merge",
            "conflict_detected": "heuristic — Not disclosed vs numeric in same retrieval set",
        },
    }

    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    all_results = single_results + cross_results
    with (out_dir / "results.jsonl").open("w", encoding="utf-8") as f:
        for row in all_results:
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
