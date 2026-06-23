"""Create a cleaned Golden Set v2 subset for fair benchmark reruns."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_JSONL = ROOT / "data/golden_set/v2/step6_gold/golden_set.jsonl"
OUTPUT_JSONL = ROOT / "data/golden_set/v2/step6_gold/golden_set_clean.jsonl"
REPORT_PATH = ROOT / "reports/golden_v2_cleaning_report.md"

DROP_REASONS = {
    "GV2-033": "drop_date_only",
    "GV2-034": "drop_nav_menu",
    "GV2-035": "drop_nav_menu",
    "GV2-036": "drop_company_mismatch",
    "GV2-037": "drop_nav_menu",
    "GV2-038": "drop_nav_menu",
    "GV2-039": "drop_nav_menu_duplicate",
    "GV2-040": "drop_nav_menu_duplicate",
    "GV2-041": "drop_nav_menu",
    "GV2-042": "drop_nav_menu_duplicate",
    "GV2-043": "drop_nav_menu_duplicate",
    "GV2-044": "drop_company_mismatch",
    "GV2-045": "drop_nav_menu_duplicate",
    "GV2-047": "drop_company_mismatch",
    "GV2-048": "drop_company_mismatch_duplicate",
    "GV2-049": "drop_company_mismatch",
    "GV2-050": "drop_generic_vendor_content",
    "GV2-051": "drop_generic_vendor_content",
    "GV2-052": "drop_generic_vendor_content",
    "GV2-053": "drop_generic_vendor_content",
    "GV2-054": "drop_generic_vendor_content",
    "GV2-055": "drop_company_mismatch",
    "GV2-056": "drop_company_mismatch",
    "GV2-057": "drop_company_mismatch_duplicate",
    "GV2-059": "drop_company_mismatch",
    "GV2-060": "drop_company_mismatch_duplicate",
    "GV2-061": "drop_company_mismatch",
    "GV2-063": "drop_company_mismatch",
    "GV2-064": "drop_company_mismatch",
    "GV2-065": "drop_company_mismatch_duplicate",
    "GV2-068": "drop_date_only",
    "GV2-069": "drop_date_only_listing",
    "GV2-070": "drop_date_only_listing",
    "GV2-071": "drop_date_only_listing",
    "GV2-072": "drop_date_only_listing",
    "GV2-073": "drop_date_only_listing",
    "GV2-074": "drop_date_only_listing",
    "GV2-075": "drop_nav_lookup",
    "GV2-078": "drop_duplicate_same_fact",
    "GV2-080": "drop_duplicate_same_fact",
    "GV2-081": "drop_question_answer_mismatch",
    "GV2-085": "drop_duplicate_same_fact",
    "GV2-086": "drop_duplicate_same_fact",
    "GV2-088": "drop_duplicate_same_fact",
    "GV2-090": "drop_duplicate_same_fact",
    "GV2-092": "drop_question_answer_mismatch",
}


def load_rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    rows = load_rows(INPUT_JSONL)
    kept = [row for row in rows if row["question_id"] not in DROP_REASONS]
    dropped = [row for row in rows if row["question_id"] in DROP_REASONS]
    write_jsonl(OUTPUT_JSONL, kept)

    drop_counts = Counter(DROP_REASONS.values())
    keep_counts = Counter(row["package_name"] for row in kept)

    lines = [
        "# Golden Set v2 Cleaning Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Source: `{INPUT_JSONL.relative_to(ROOT)}`",
        f"Output: `{OUTPUT_JSONL.relative_to(ROOT)}`",
        "",
        "## Summary",
        "",
        f"- input_rows: **{len(rows)}**",
        f"- kept_rows: **{len(kept)}**",
        f"- dropped_rows: **{len(dropped)}**",
        "",
        "## Kept By Package",
        "",
        "| package_name | kept |",
        "|---|---:|",
    ]
    for package_name, count in sorted(keep_counts.items()):
        lines.append(f"| {package_name} | {count} |")

    lines.extend(
        [
            "",
            "## Drop Reasons",
            "",
            "| reason | count |",
            "|---|---:|",
        ]
    )
    for reason, count in sorted(drop_counts.items()):
        lines.append(f"| {reason} | {count} |")

    lines.extend(
        [
            "",
            "## Dropped Rows",
            "",
            "| ID | package_name | reason | question |",
            "|---|---|---|---|",
        ]
    )
    for row in dropped:
        lines.append(
            f"| {row['question_id']} | {row['package_name']} | {DROP_REASONS[row['question_id']]} | "
            f"{row['question']} |"
        )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "input_rows": len(rows),
                "kept_rows": len(kept),
                "dropped_rows": len(dropped),
                "output_jsonl": str(OUTPUT_JSONL),
                "report": str(REPORT_PATH),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
