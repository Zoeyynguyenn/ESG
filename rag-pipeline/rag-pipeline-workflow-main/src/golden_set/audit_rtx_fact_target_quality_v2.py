"""Audit RTX v2 fact-target quality: mismatch, wording, residue, overlong."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from golden_set.io_utils import read_jsonl
from golden_set.rtx_fact_quality import audit_candidate_row


def audit_rows(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    error_counts: Counter = Counter()
    row_errors: List[Dict[str, Any]] = []
    usable = 0

    for row in rows:
        errors = audit_candidate_row(row)
        if not errors:
            usable += 1
        else:
            for e in set(errors):
                error_counts[e] += 1
            row_errors.append({"seed_id": row.get("seed_id"), "errors": errors, "question": row.get("question_draft", "")[:100]})

    needs_rebuild = len(rows) - usable
    return {
        "input_count": len(rows),
        "fact_mismatch_count": error_counts.get("fact_mismatch", 0),
        "unnatural_question_wording_count": error_counts.get("unnatural_question_wording", 0),
        "residue_led_question_count": error_counts.get("residue_led_question", 0),
        "overlong_fact_phrase_count": error_counts.get("overlong_fact_phrase", 0),
        "usable_without_rebuild_count": usable,
        "needs_rebuild_count": needs_rebuild,
        "error_counts": dict(error_counts),
        "example_rows": row_errors[:20],
    }


def write_report(summary: Dict[str, Any], path: Path) -> None:
    lines = [
        "# Golden Set — RTX Fact-Target Quality Audit (V2)",
        "",
        f"Generated: {summary.get('generated_at', '')}",
        "",
        "## Mục tiêu",
        "",
        "Đánh giá chất lượng `fact_target → question → disclosure` trên RTX v2",
        "trước khi quyết định mở review round 1.",
        "",
        "## Vì sao v2 chưa đủ mở review",
        "",
        "- v2 sửa duplicate (0 exact dup) nhưng question vẫn có thể là phrase extraction thô",
        "- Có row **fact mismatch** (question hỏi fact A, disclosure là fact B)",
        "- Có residue parse (`s Workforce`, `GHGemissions`, `What Reductions from...`)",
        "",
        "## Breakdown theo loại lỗi",
        "",
        f"- `fact_mismatch`: **{summary.get('fact_mismatch_count', 0)}** rows",
        f"- `unnatural_question_wording`: **{summary.get('unnatural_question_wording_count', 0)}** rows",
        f"- `residue_led_question`: **{summary.get('residue_led_question_count', 0)}** rows",
        f"- `overlong_fact_phrase`: **{summary.get('overlong_fact_phrase_count', 0)}** rows",
        f"- Usable without rebuild: **{summary.get('usable_without_rebuild_count', 0)}** / **{summary.get('input_count', 0)}**",
        "",
        "## Ví dụ cụ thể",
        "",
    ]
    examples_by_type: Dict[str, List[Dict]] = defaultdict(list)
    for ex in summary.get("example_rows", []):
        for err in ex.get("errors", []):
            if len(examples_by_type[err]) < 3:
                examples_by_type[err].append(ex)

    for err_type in ("fact_mismatch", "unnatural_question_wording", "residue_led_question", "overlong_fact_phrase"):
        lines.append(f"### {err_type}")
        for ex in examples_by_type.get(err_type, []):
            lines.append(f"- `{ex.get('seed_id')}`: {ex.get('question', '')}…")
        lines.append("")

    lines.extend(
        [
            "## Kết luận",
            "",
            f"- Usable: **{summary.get('usable_without_rebuild_count', 0)}**",
            f"- Needs rebuild: **{summary.get('needs_rebuild_count', 0)}**",
            "- Bước tiếp: **RTX v2.1 fact-quality rebuild** — không mở review trên v2.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_audit(*, input_path: Path, report_path: Path, summary_path: Path) -> Dict[str, Any]:
    rows = read_jsonl(input_path)
    result = audit_rows(rows)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        **result,
    }
    write_report(summary, report_path)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Audit RTX v2 fact-target quality")
    parser.add_argument("--input", default="data/golden_set/v2/reference_style/reference_seed_candidates_rtx_v2_fact_specific.jsonl")
    parser.add_argument("--report", default="reports/golden_set_rtx_fact_target_quality_audit_v2.md")
    parser.add_argument("--summary", default="reports/_rtx_fact_target_quality_audit_v2_summary.json")
    args = parser.parse_args(argv)

    summary = run_audit(
        input_path=root / args.input,
        report_path=root / args.report,
        summary_path=root / args.summary,
    )
    print(json.dumps({k: summary[k] for k in ("input_count", "needs_rebuild_count", "usable_without_rebuild_count")}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
