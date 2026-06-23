#!/usr/bin/env python3
"""Run extractive RAG benchmark for goldns/emni dataset-excel workstream (v5)."""

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

from dataset_excel.constants import (  # noqa: E402
    BASELINE_VERSION,
    V2_BASELINE_METRICS,
    V3_BASELINE_METRICS,
    V4_BASELINE_METRICS,
)
from dataset_excel.diagnostics import eval_row  # noqa: E402
from dataset_excel.retrieval import build_index  # noqa: E402
from dataset_excel.reusability_audit import analyze_reusability  # noqa: E402
from dataset_excel.rule_registry import export_rule_inventory  # noqa: E402


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _load_eval_rows(eval_root: Path, companies: list[str] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for company_dir in sorted(p for p in eval_root.iterdir() if p.is_dir()):
        if companies and company_dir.name not in companies:
            continue
        for partition in ("answerable_gold", "abstain_gold"):
            rows.extend(_read_jsonl(company_dir / f"{partition}.jsonl"))
    return rows


def _aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    answerable = [r for r in results if r.get("scoring_rule") != "abstain_expected"]
    abstain = [r for r in results if r.get("scoring_rule") == "abstain_expected"]

    def rate(rows: list[dict[str, Any]], key: str) -> float:
        return round(sum(1 for r in rows if r.get(key)) / max(1, len(rows)), 4)

    metrics = {
        "retrieval_hit_top1": rate(answerable, "retrieval_hit_top1"),
        "retrieval_hit_topk": rate(answerable, "retrieval_hit_topk"),
        "source_match_top1": rate(answerable, "source_match_top1"),
        "source_match_topk": rate(answerable, "source_match_topk"),
        "answer_accuracy": rate(answerable, "answer_correct"),
        "abstain_accuracy": rate(abstain, "abstain_correct"),
    }
    metrics["overall_score"] = round(
        (
            metrics["retrieval_hit_top1"]
            + metrics["source_match_top1"]
            + metrics["answer_accuracy"]
            + metrics["abstain_accuracy"]
        )
        / 4,
        4,
    )

    by_company: dict[str, Any] = {}
    for company_id in sorted({r["company_id"] for r in results}):
        c_rows = [r for r in results if r["company_id"] == company_id]
        c_ans = [r for r in c_rows if r.get("scoring_rule") != "abstain_expected"]
        c_abs = [r for r in c_rows if r.get("scoring_rule") == "abstain_expected"]
        by_company[company_id] = {
            "total": len(c_rows),
            "answerable": len(c_ans),
            "abstain": len(c_abs),
            "retrieval_hit_top1": rate(c_ans, "retrieval_hit_top1"),
            "answer_accuracy": rate(c_ans, "answer_correct"),
            "abstain_accuracy": rate(c_abs, "abstain_correct"),
        }

    fail_by_family = Counter(
        r.get("question_family") or "unknown"
        for r in answerable
        if r.get("fail_type") in ("answer_fail", "retrieval_top1_miss", "answer_correct_but_wrong_top1")
    )
    fail_type_breakdown = Counter(r.get("fail_type") for r in answerable if r.get("fail_type"))
    fail_type_breakdown["retrieval_top1_miss"] = sum(
        1 for r in answerable if not r.get("retrieval_hit_top1")
    )
    diagnostic_breakdown = Counter(tag for r in answerable for tag in (r.get("diagnostic_tags") or []))
    coverage_gap_cases = [
        {
            "question_id": r.get("question_id"),
            "company_id": r.get("company_id"),
            "question_family": r.get("question_family"),
            "coverage_gap": r.get("coverage_gap"),
            "source_url": r.get("source_url"),
            "fail_type": r.get("fail_type"),
        }
        for r in answerable
        if "coverage_gap" in (r.get("diagnostic_tags") or [])
    ]
    fail_type_examples: dict[str, list[dict[str, Any]]] = {}
    for key in ("answer_fail", "answer_correct_but_wrong_top1", "semantic_ambiguity"):
        fail_type_examples[key] = [
            {
                "question_id": r.get("question_id"),
                "company_id": r.get("company_id"),
                "question_family": r.get("question_family"),
                "gold": r.get("gold_answer_raw"),
                "pred": r.get("predicted_answer"),
                "top1": (r.get("top_doc_titles") or [""])[0],
            }
            for r in answerable
            if r.get("fail_type") == key
        ][:8]
    fail_type_examples["retrieval_top1_miss"] = [
        {
            "question_id": r.get("question_id"),
            "company_id": r.get("company_id"),
            "question_family": r.get("question_family"),
            "gold": r.get("gold_answer_raw"),
            "pred": r.get("predicted_answer"),
            "top1": (r.get("top_doc_titles") or [""])[0],
            "answer_correct": r.get("answer_correct"),
        }
        for r in answerable
        if not r.get("retrieval_hit_top1")
    ][:8]
    wrong_top_docs = Counter(
        (r.get("top_doc_titles") or ["unknown"])[0] or "unknown"
        for r in answerable
        if not r.get("retrieval_hit_top1")
    )
    emni_fail_examples = [
        r
        for r in answerable
        if r.get("company_id") == "emni" and (not r.get("answer_correct") or not r.get("retrieval_hit_top1"))
    ][:10]
    semantic_audit_cases = [
        {
            "question_id": r.get("question_id"),
            "question_family": r.get("question_family"),
            "note": r.get("semantic_audit_note") or r.get("semantic_ambiguity"),
        }
        for r in answerable
        if r.get("semantic_audit_note") or r.get("semantic_ambiguity")
    ]

    delta_vs_v2 = {key: round(metrics[key] - V2_BASELINE_METRICS[key], 4) for key in V2_BASELINE_METRICS if key in metrics}
    delta_vs_v3 = {key: round(metrics[key] - V3_BASELINE_METRICS[key], 4) for key in V3_BASELINE_METRICS if key in metrics}
    delta_vs_v4 = {key: round(metrics[key] - V4_BASELINE_METRICS[key], 4) for key in V4_BASELINE_METRICS if key in metrics}

    reusability = analyze_reusability(results, baseline_metrics=metrics)

    return {
        "total_questions": len(results),
        "answerable_count": len(answerable),
        "abstain_count": len(abstain),
        **metrics,
        "delta_vs_v2": delta_vs_v2,
        "delta_vs_v3": delta_vs_v3,
        "delta_vs_v4": delta_vs_v4,
        "v2_baseline": V2_BASELINE_METRICS,
        "v3_baseline": V3_BASELINE_METRICS,
        "v4_baseline": V4_BASELINE_METRICS,
        "metric_definitions": {
            "retrieval_hit_top1": "answerable only; doc_title/file_url/lane khop o top-1 evidence",
            "retrieval_hit_topk": "answerable only; doc_title/file_url/lane khop trong top-k evidence",
            "source_match_top1": "alias cua retrieval_hit_top1",
            "source_match_topk": "alias cua retrieval_hit_topk",
            "answer_accuracy": "answerable only; predicted answer match gold",
            "abstain_accuracy": "abstain only; model abstain khi gold khong co provenance",
            "overall_score": "trung binh 4 metric: retrieval_hit_top1, source_match_top1, answer_accuracy, abstain_accuracy",
        },
        "fail_type_definitions": {
            "answer_fail": "answerable; answer sai",
            "retrieval_top1_miss": "answerable; tong so cau retrieval top-1 miss (co the overlap answer_fail)",
            "answer_correct_but_wrong_top1": "answerable; answer dung nhung top-1 doc/lane sai",
            "semantic_ambiguity": "answerable; co semantic_ambiguity hoac semantic_audit_note",
            "coverage_gap": "answerable; thieu source that (vi du FTC blocked)",
            "rule_extractor_gap": "answerable; answer sai do rule extractor/mapping",
        },
        "by_company": by_company,
        "fail_by_family": dict(fail_by_family.most_common()),
        "fail_type_breakdown": dict(fail_type_breakdown),
        "diagnostic_breakdown": dict(diagnostic_breakdown),
        "coverage_gap_cases": coverage_gap_cases,
        "fail_type_examples": fail_type_examples,
        "wrong_top_docs": dict(wrong_top_docs.most_common(10)),
        "emni_fail_examples": emni_fail_examples,
        "semantic_audit_cases": semantic_audit_cases,
        "coverage_gaps_logged": [
            "case.ftc.go.kr self_redirect_loop_blocked_by_site (FTC lane chua co raw HTML)",
        ],
        "blocked_sources_logged": [
            "case.ftc.go.kr self_redirect_loop_blocked_by_site (web download lane)",
        ],
        "baseline_version": BASELINE_VERSION,
        "generalization_hardening": reusability,
    }


def _markdown_report(summary: dict[str, Any], run_id: str) -> str:
    lines = [
        f"# Goldns/Emni RAG Eval Report ({run_id})",
        "",
        "## Metrics (v5)",
        "",
        f"- retrieval_hit_top1: **{summary['retrieval_hit_top1']}**",
        f"- retrieval_hit_topk: **{summary['retrieval_hit_topk']}**",
        f"- source_match_top1: **{summary['source_match_top1']}**",
        f"- source_match_topk: **{summary['source_match_topk']}**",
        f"- answer_accuracy: **{summary['answer_accuracy']}**",
        f"- abstain_accuracy: **{summary['abstain_accuracy']}**",
        f"- overall_score: **{summary['overall_score']}**",
        "",
        "## Generalization hardening view",
        "",
    ]
    gh = summary.get("generalization_hardening") or {}
    lines.append(f"- reusable_system_coverage: **{gh.get('reusable_system_coverage')}**")
    lines.append(f"- company_specific_dependency: **{gh.get('company_specific_dependency')}**")
    qual = (gh.get("qualitative_summary") or {}).get("reusable_system_coverage_interpretation")
    if qual:
        lines.append(f"- {qual}")

    lines.extend(["", "## Delta vs v4", ""])
    for key, delta in summary.get("delta_vs_v4", {}).items():
        lines.append(f"- `{key}`: {delta:+.4f} (v4={summary.get('v4_baseline', {}).get(key)})")

    lines.extend(["", "## Delta vs v3", ""])
    for key, delta in summary.get("delta_vs_v3", {}).items():
        lines.append(f"- `{key}`: {delta:+.4f} (v3={summary.get('v3_baseline', {}).get(key)})")

    lines.extend(["", "## Delta vs v2", ""])
    for key, delta in summary.get("delta_vs_v2", {}).items():
        lines.append(f"- `{key}`: {delta:+.4f} (v2={summary.get('v2_baseline', {}).get(key)})")

    lines.extend(["", "## Metric definitions", ""])
    for key, desc in summary.get("metric_definitions", {}).items():
        lines.append(f"- `{key}`: {desc}")

    lines.extend(["", "## Fail type breakdown", ""])
    for key, count in summary.get("fail_type_breakdown", {}).items():
        lines.append(f"- `{key}`: {count}")
    lines.extend(["", "## Diagnostic breakdown", ""])
    for key, count in summary.get("diagnostic_breakdown", {}).items():
        lines.append(f"- `{key}`: {count}")
    if summary.get("coverage_gap_cases"):
        lines.extend(["", "## Coverage gap cases", ""])
        for item in summary.get("coverage_gap_cases", []):
            lines.append(
                f"- `{item.get('question_id')}` ({item.get('company_id')}) "
                f"family={item.get('question_family')} gap={item.get('coverage_gap') or 'coverage_gap'} "
                f"fail_type={item.get('fail_type')}"
            )
    for key in (
        "answer_fail",
        "retrieval_top1_miss",
        "answer_correct_but_wrong_top1",
        "semantic_ambiguity",
    ):
        examples = summary.get("fail_type_examples", {}).get(key) or []
        if not examples:
            continue
        lines.extend(["", f"### {key} examples", ""])
        for item in examples:
            lines.append(
                f"- `{item.get('question_id')}` ({item.get('company_id')}) "
                f"family={item.get('question_family')} gold={item.get('gold')} pred={item.get('pred')} top1={item.get('top1')}"
            )

    lines.extend(["", "## Fail by question family (answer/retrieval issues)", ""])
    for family, count in summary.get("fail_by_family", {}).items():
        lines.append(f"- {family}: {count}")

    lines.extend(["", "## Wrong top-1 docs", ""])
    for doc, count in summary.get("wrong_top_docs", {}).items():
        lines.append(f"- {doc}: {count}")

    lines.extend(["", "## emni fail examples (up to 10)", ""])
    for item in summary.get("emni_fail_examples", []):
        lines.append(
            f"- `{item.get('question_id')}` family={item.get('question_family')} "
            f"gold={item.get('gold_answer_raw')} pred={item.get('predicted_answer')} "
            f"top1={((item.get('top_doc_titles') or [''])[0])} reason={item.get('predict_reason')}"
        )

    lines.extend(["", "## Semantic audit / ambiguity", ""])
    for item in summary.get("semantic_audit_cases", []):
        lines.append(f"- `{item.get('question_id')}` ({item.get('question_family')}): {item.get('note')}")

    if not summary.get("semantic_audit_cases"):
        lines.append("- (none logged)")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="data/corpus/20260617_goldns_emni/corpus_units.jsonl")
    parser.add_argument("--eval-root", default="data/dataset_excel_eval_ready/20260617_goldns_emni")
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--pool", type=int, default=32)
    parser.add_argument("--company", action="append", default=None)
    args = parser.parse_args()

    corpus_path = ROOT / args.corpus
    eval_root = ROOT / args.eval_root
    output_dir = ROOT / args.output_dir
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")

    export_rule_inventory(ROOT / "data/dataset_excel/rule_inventory.json")

    units = _read_jsonl(corpus_path)
    if not units:
        raise SystemExit(f"Corpus empty: {corpus_path}")

    index = build_index(units)
    eval_rows = _load_eval_rows(eval_root, args.company)
    results = [eval_row(row, index, top_k=args.top_k, pool=args.pool) for row in eval_rows]
    summary = _aggregate(results)

    artifact_dir = output_dir / f"goldns_emni_rag_eval_{run_id}"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(artifact_dir / "results.jsonl", results)
    (artifact_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (artifact_dir / "report.md").write_text(_markdown_report(summary, run_id), encoding="utf-8")
    (output_dir / "goldns_emni_rag_eval_latest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
