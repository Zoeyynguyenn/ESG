#!/usr/bin/env python3
"""Classify demo_company questions into single-doc vs cross-doc evidence plans."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.doc_router import build_evidence_plan  # noqa: E402


def _load_questions(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--questions-root",
        default=r"C:\Users\nguye\Downloads\data-company\demo_company\questions\questions",
    )
    parser.add_argument(
        "--output-jsonl",
        default="data/enterprise_docs/demo_company/question_evidence_plans.jsonl",
    )
    parser.add_argument(
        "--output-summary",
        default="data/enterprise_docs/demo_company/question_analysis_summary.json",
    )
    args = parser.parse_args()

    qroot = Path(args.questions_root)
    rows: list[dict] = []
    for name in ("quantitative.json", "qualitative.json"):
        for q in _load_questions(qroot / name):
            plan = build_evidence_plan(q)
            rows.append(
                {
                    "item_id": q.get("item_id"),
                    "kind": q.get("kind"),
                    "domain": q.get("domain"),
                    "category": q.get("category"),
                    "subcategory": q.get("subcategory"),
                    "item": q.get("item"),
                    "question": q.get("question"),
                    "answer_mode": plan.answer_mode,
                    "primary_document_ids": plan.primary_document_ids,
                    "supporting_document_ids": plan.supporting_document_ids,
                    "roles": plan.roles,
                    "needs_merge": plan.needs_merge,
                    "needs_conflict_resolution": plan.needs_conflict_resolution,
                    "notes": plan.notes,
                }
            )

    out_jsonl = ROOT / args.output_jsonl
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    mode_counts = Counter(r["answer_mode"] for r in rows)
    kind_mode = {
        f"{kind}:{mode}": count
        for (kind, mode), count in Counter((r["kind"], r["answer_mode"]) for r in rows).items()
    }
    cross_examples = [r for r in rows if r["answer_mode"] == "cross_document_answer"][:12]

    summary = {
        "total_questions": len(rows),
        "quantitative": sum(1 for r in rows if r["kind"] == "quantitative"),
        "qualitative": sum(1 for r in rows if r["kind"] == "qualitative"),
        "answer_mode_counts": dict(mode_counts),
        "by_kind_and_mode": kind_mode,
        "cross_document_examples": cross_examples,
        "single_document_examples": [r for r in rows if r["answer_mode"] == "single_document_answer"][:8],
    }

    out_summary = ROOT / args.output_summary
    out_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
