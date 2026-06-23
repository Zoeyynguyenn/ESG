#!/usr/bin/env python3
"""Validate canonical ESG intake and partition into eval-ready subsets."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


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


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _has_real_source(source: dict[str, Any]) -> bool:
    return bool((source.get("source_url") or "").strip() or (source.get("file_url") or "").strip())


def _pick_primary_source(source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    prioritized = sorted(
        source_rows,
        key=lambda row: (
            0 if row.get("source_priority") else 1,
            0 if _has_real_source(row) else 1,
        ),
    )
    return prioritized[0]


def _validate_company_dir(company_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    questions = _read_jsonl(company_dir / "questions.jsonl")
    gold_answers = _read_jsonl(company_dir / "gold_answers.jsonl")
    sources = _read_jsonl(company_dir / "sources.jsonl")
    manifest = json.loads((company_dir / "manifest.json").read_text(encoding="utf-8"))

    issues: list[dict[str, Any]] = []
    questions_by_id = {row["question_id"]: row for row in questions}
    gold_by_id = {row["question_id"]: row for row in gold_answers}
    sources_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in sources:
        sources_by_id[row["question_id"]].append(row)

    qid_counts = Counter(row["question_id"] for row in questions)
    gold_counts = Counter(row["question_id"] for row in gold_answers)

    for question_id, count in qid_counts.items():
        if count > 1:
            issues.append({"company_id": manifest["company_id"], "question_id": question_id, "severity": "high", "issue_code": "duplicate_question_id_in_questions", "details": f"count={count}"})
    for question_id, count in gold_counts.items():
        if count > 1:
            issues.append({"company_id": manifest["company_id"], "question_id": question_id, "severity": "high", "issue_code": "duplicate_question_id_in_gold_answers", "details": f"count={count}"})

    partition_rows: list[dict[str, Any]] = []
    partition_counter = Counter()

    all_ids = [row["question_id"] for row in questions]
    for question_id in all_ids:
        question = questions_by_id.get(question_id)
        gold = gold_by_id.get(question_id)
        source_rows = sources_by_id.get(question_id, [])
        primary_source = _pick_primary_source(source_rows) if source_rows else {}

        reasons: list[str] = []
        partition = "needs_review"

        if not question:
            reasons.append("missing_question")
        if not gold:
            reasons.append("missing_gold_answer")
        if not source_rows:
            reasons.append("missing_source_row")

        if question and gold:
            disclosure_status = gold.get("disclosure_status")
            scoring_rule = gold.get("scoring_rule")
            requires_abstain = bool(question.get("requires_abstain_when_missing"))
            normalized = gold.get("gold_answer_normalized")

            if disclosure_status == "Not disclosed":
                if scoring_rule != "abstain_expected":
                    reasons.append("not_disclosed_scoring_rule_mismatch")
                if not requires_abstain:
                    reasons.append("not_disclosed_requires_abstain_false")
                if normalized != "NOT_DISCLOSED":
                    reasons.append("not_disclosed_normalized_mismatch")
                if not reasons:
                    partition = "abstain_gold"
            elif disclosure_status == "matched":
                if scoring_rule != "value_match_with_unit":
                    reasons.append("matched_scoring_rule_mismatch")
                if requires_abstain:
                    reasons.append("matched_requires_abstain_true")
                if normalized in (None, "", "NOT_DISCLOSED"):
                    reasons.append("matched_missing_normalized_answer")
                if not _has_real_source(primary_source):
                    reasons.append("matched_missing_real_source")
                if not reasons:
                    partition = "answerable_gold"
            else:
                reasons.append(f"unsupported_disclosure_status:{disclosure_status}")

        if partition == "needs_review" and not reasons:
            reasons.append("unclassified")

        if partition == "needs_review":
            severity = "medium"
            if any(code.startswith("missing_") or code.startswith("duplicate_") for code in reasons):
                severity = "high"
            issues.append(
                {
                    "company_id": manifest["company_id"],
                    "question_id": question_id,
                    "severity": severity,
                    "issue_code": "partitioned_to_needs_review",
                    "details": ";".join(reasons),
                }
            )

        partition_counter[partition] += 1
        partition_rows.append(
            {
                "question_id": question_id,
                "company_id": manifest["company_id"],
                "company_name": manifest["company_name"],
                "partition": partition,
                "review_reasons": reasons,
                "question_text": question.get("question_text") if question else None,
                "question_type": question.get("question_type") if question else None,
                "metric_name": question.get("metric_name") if question else None,
                "year": question.get("year") if question else None,
                "unit": question.get("unit") if question else None,
                "gold_answer_raw": gold.get("gold_answer_raw") if gold else None,
                "gold_answer_normalized": gold.get("gold_answer_normalized") if gold else None,
                "disclosure_status": gold.get("disclosure_status") if gold else None,
                "scoring_rule": gold.get("scoring_rule") if gold else None,
                "source_url": primary_source.get("source_url"),
                "file_url": primary_source.get("file_url"),
                "doc_title": primary_source.get("doc_title"),
                "evidence_text": primary_source.get("evidence_text") or (gold.get("evidence_text") if gold else None),
                "confidence": gold.get("confidence") if gold else None,
            }
        )

    summary = {
        "company_id": manifest["company_id"],
        "company_name": manifest["company_name"],
        "question_count": len(questions),
        "gold_answer_count": len(gold_answers),
        "source_row_count": len(sources),
        "answerable_gold_count": partition_counter["answerable_gold"],
        "abstain_gold_count": partition_counter["abstain_gold"],
        "needs_review_count": partition_counter["needs_review"],
        "issue_count": len(issues),
    }
    return partition_rows, {"summary": summary, "issues": issues}


def _write_summary_report(path: Path, summaries: list[dict[str, Any]]) -> None:
    lines = [
        "# ESG Intake Validation And Partition Summary",
        "",
        "| Company | Questions | Answerable | Abstain | Needs review | Issues |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in summaries:
        lines.append(
            f"| {item['company_name']} | {item['question_count']} | {item['answerable_gold_count']} | "
            f"{item['abstain_gold_count']} | {item['needs_review_count']} | {item['issue_count']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", default="data/dataset_excel_intake/20260617_goldns_emni")
    parser.add_argument("--output-root", default="data/dataset_excel_eval_ready/20260617_goldns_emni")
    args = parser.parse_args()

    input_root = Path(args.input_root)
    output_root = Path(args.output_root)
    company_dirs = sorted(p for p in input_root.iterdir() if p.is_dir())

    all_partition_rows: list[dict[str, Any]] = []
    all_issues: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []

    for company_dir in company_dirs:
        partition_rows, validation = _validate_company_dir(company_dir)
        summary = validation["summary"]
        issues = validation["issues"]
        summaries.append(summary)
        all_partition_rows.extend(partition_rows)
        all_issues.extend(issues)

        company_output = output_root / company_dir.name
        answerable = [row for row in partition_rows if row["partition"] == "answerable_gold"]
        abstain = [row for row in partition_rows if row["partition"] == "abstain_gold"]
        review = [row for row in partition_rows if row["partition"] == "needs_review"]

        _write_jsonl(company_output / "answerable_gold.jsonl", answerable)
        _write_jsonl(company_output / "abstain_gold.jsonl", abstain)
        _write_jsonl(company_output / "needs_review.jsonl", review)
        _write_jsonl(company_output / "partition_all.jsonl", partition_rows)
        _write_jsonl(company_output / "validation_issues.jsonl", issues)

        _write_csv(company_output / "answerable_gold.csv", answerable)
        _write_csv(company_output / "abstain_gold.csv", abstain)
        _write_csv(company_output / "needs_review.csv", review)
        _write_csv(company_output / "partition_all.csv", partition_rows)
        _write_csv(company_output / "validation_issues.csv", issues)

        (company_output / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    _write_jsonl(output_root / "all_companies_partition_all.jsonl", all_partition_rows)
    _write_jsonl(output_root / "all_companies_validation_issues.jsonl", all_issues)
    _write_csv(output_root / "all_companies_partition_all.csv", all_partition_rows)
    _write_csv(output_root / "all_companies_validation_issues.csv", all_issues)
    _write_summary_report(output_root / "README.md", summaries)
    (output_root / "summary.json").write_text(
        json.dumps({"companies": summaries}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
