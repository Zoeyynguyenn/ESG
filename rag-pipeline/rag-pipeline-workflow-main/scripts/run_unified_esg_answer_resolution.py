#!/usr/bin/env python3
"""Run unified ESG answer resolution — merge dataset RAG + internal-doc structured output."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from unified_esg_answer_resolution import (  # noqa: E402
    DEFAULT_DATASET_RESULTS,
    DEFAULT_EVAL_ROOT,
    DEFAULT_INTERNAL_RECORDS,
    SCHEMA_PATH,
    export_review_workbook,
    mandatory_resolution_answers,
    run_unified_resolution,
)
from unified_esg_resolution_policy import DEFAULT_POLICY  # noqa: E402

PRIOR_ARTIFACT = ROOT / "reports/enterprise_docs_operational_packaging_20260619-104141"


def _review_workbook_plan_md(*, artifact_rel: str, sb: dict, inputs: dict) -> str:
    return "\n".join(
        [
            "# Unified ESG review workbook plan",
            "",
            f"Artifact: `{artifact_rel}`",
            "",
            "## Nguyên tắc",
            "",
            "- **Không ghi đè** Excel workbook gốc (`이엠앤아이_Final_ESG_Data.xlsx`, v.v.)",
            "- **Không sửa** `results.jsonl` frozen RAG eval",
            "- Xuất artifact review riêng: `unified_esg_review.xlsx` + `unified_answers.jsonl`",
            "",
            "## Sheets",
            "",
            "| Sheet | Nội dung |",
            "|---|---|",
            "| `all_unified` | Toàn bộ records hợp nhất |",
            "| `MATCH_CONFIRMED` | Dataset + internal-doc khớp — auto-confirm |",
            "| `BACKFILL_INTERNAL` | Internal-doc bổ sung khi dataset thiếu |",
            "| `BACKFILL_DATASET` | Dataset/public source khi internal thiếu |",
            "| `CONFLICT_REVIEW` | Conflict — SME review |",
            "| `NO_ANSWER` | Không có đáp án / insufficient evidence |",
            "",
            "## Input sources",
            "",
            json.dumps(inputs, ensure_ascii=False, indent=2),
            "",
            "## Status breakdown",
            "",
            json.dumps(sb, ensure_ascii=False, indent=2),
            "",
            "## Workflow review",
            "",
            "1. Mở sheet `CONFLICT_REVIEW` trước — assign SME",
            "2. `BACKFILL_INTERNAL` với `auto_confirm=false` — RAG/SME xác nhận candidate",
            "3. `MATCH_CONFIRMED` — audit spot-check, không cần sửa Excel gốc",
            "4. `NO_ANSWER` — quyết định bổ sung source (corpus_limited) hay chấp nhận abstain",
            "",
        ]
    )


def _report_md(*, artifact_rel: str, summary: dict, answers: dict) -> str:
    return "\n".join(
        [
            "# Unified ESG answer resolution",
            "",
            f"Artifact: `{artifact_rel}`",
            "",
            "## Câu trả lời bắt buộc",
            "",
            json.dumps(answers, ensure_ascii=False, indent=2),
            "",
            "## Status breakdown",
            "",
            json.dumps(summary.get("status_breakdown"), ensure_ascii=False, indent=2),
            "",
            "## Inputs",
            "",
            json.dumps(summary.get("inputs"), ensure_ascii=False, indent=2),
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified ESG answer resolution")
    parser.add_argument("--dataset-results", type=Path, default=DEFAULT_DATASET_RESULTS)
    parser.add_argument("--internal-records", type=Path, default=DEFAULT_INTERNAL_RECORDS)
    parser.add_argument("--eval-root", type=Path, default=DEFAULT_EVAL_ROOT)
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = args.out_dir or (ROOT / f"reports/unified_esg_answer_resolution_{ts}")
    out_dir.mkdir(parents=True, exist_ok=True)

    result = run_unified_resolution(
        dataset_results_path=args.dataset_results,
        internal_records_path=args.internal_records,
        eval_root=args.eval_root,
    )
    answers = mandatory_resolution_answers(result)
    artifact_rel = str(out_dir.relative_to(ROOT)).replace("\\", "/")

    workbook_meta = export_review_workbook(
        result["unified_records"],
        out_dir / "unified_esg_review.xlsx",
    )

    unified_path = out_dir / "unified_answers.jsonl"
    with unified_path.open("w", encoding="utf-8") as f:
        for row in result["unified_records"]:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "artifact": "unified_esg_answer_resolution",
        "timestamp": out_dir.name.split("_")[-1],
        "phase": "unified_esg_answer_resolution",
        "prior_artifact": str(PRIOR_ARTIFACT.relative_to(ROOT)).replace("\\", "/"),
        "inputs": result["inputs"],
        "status_breakdown": result["status_breakdown"],
        "policy_version": result["policy_version"],
        "mandatory_answers": answers,
        "workbook": workbook_meta,
        "schema_path": str(SCHEMA_PATH.relative_to(ROOT)).replace("\\", "/"),
        "constraints": {
            "no_langgraph_runtime": True,
            "no_synthesis": True,
            "no_core_lane_rebuild": True,
            "no_source_excel_overwrite": True,
        },
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "resolution_policy.json").write_text(
        json.dumps(DEFAULT_POLICY, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "status_breakdown.json").write_text(
        json.dumps(result["status_breakdown"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "review_workbook_plan.md").write_text(
        _review_workbook_plan_md(
            artifact_rel=artifact_rel,
            sb=result["status_breakdown"],
            inputs=result["inputs"],
        ),
        encoding="utf-8",
    )
    (out_dir / "report.md").write_text(
        _report_md(artifact_rel=artifact_rel, summary=summary, answers=answers), encoding="utf-8"
    )

    print(json.dumps({"artifact": artifact_rel, "status_breakdown": result["status_breakdown"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
