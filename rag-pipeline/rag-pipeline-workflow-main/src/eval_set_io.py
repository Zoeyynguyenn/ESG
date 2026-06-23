"""Parse va validate eval_set.md (schema 8 cot)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import BASE_DIR, EVAL_SET_PATH

EVAL_COLUMNS = [
    "id",
    "question",
    "expected_source",
    "expected_answer",
    "extracted_field",
    "difficulty",
    "category",
    "status",
]
EXPECTED_COL_COUNT = 8
ROW_ID_PREFIXES = ("| ESG-", "| CP-", "| CE-", "| GV2-")


@dataclass
class EvalRow:
    id: str
    question: str
    expected_source: str
    expected_answer: str
    extracted_field: str = ""
    difficulty: str = ""
    category: str = ""
    status: str = "draft"

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "question": self.question,
            "expected_source": self.expected_source,
            "expected_answer": self.expected_answer,
            "extracted_field": self.extracted_field,
            "difficulty": self.difficulty,
            "category": self.category,
            "status": self.status,
        }


@dataclass
class ValidationIssue:
    id: str
    severity: str
    message: str


@dataclass
class ValidationReport:
    valid: bool
    row_count: int
    issues: List[ValidationIssue] = field(default_factory=list)
    rows: List[EvalRow] = field(default_factory=list)


def parse_eval_set(path: Path = EVAL_SET_PATH) -> List[Dict[str, str]]:
    return [r.to_dict() for r in parse_eval_set_rows(path)]


def _row_from_cells(cells: List[str]) -> EvalRow | None:
    if not cells or not cells[0]:
        return None
    rid = cells[0]
    if rid.startswith("GV2-") and len(cells) >= 8:
        return EvalRow(
            id=rid,
            question=cells[1],
            expected_source=cells[2],
            expected_answer=cells[3],
            extracted_field=cells[4],
            difficulty=cells[5],
            category=cells[6],
            status=cells[7],
        )
    if rid.startswith("GV2-") and len(cells) >= 7:
        return EvalRow(
            id=rid,
            question=cells[1],
            expected_source=cells[2],
            expected_answer=cells[3],
            extracted_field="",
            difficulty=cells[4],
            category=cells[5],
            status=cells[6],
        )
    if len(cells) < EXPECTED_COL_COUNT:
        return None
    return EvalRow(
        id=cells[0],
        question=cells[1],
        expected_source=cells[2],
        expected_answer=cells[3],
        extracted_field=cells[4],
        difficulty=cells[5],
        category=cells[6],
        status=cells[7],
    )


def parse_eval_set_rows(path: Path = EVAL_SET_PATH) -> List[EvalRow]:
    rows: List[EvalRow] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith(ROW_ID_PREFIXES):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        row = _row_from_cells(cells)
        if row:
            rows.append(row)
    return rows


def _is_insufficient_row(row: EvalRow) -> bool:
    cat = (row.category or "").lower()
    ans = (row.expected_answer or "").lower()
    return (
        cat == "insufficient"
        or row.id.startswith("ESG-I")
        or row.id.startswith("CP-I")
        or row.id.startswith("CE-I")
        or "khong du" in ans
        or "không đủ" in ans
        or "정보가 부족" in ans
    )


def validate_eval_set(path: Path = EVAL_SET_PATH) -> ValidationReport:
    issues: List[ValidationIssue] = []
    rows = parse_eval_set_rows(path)
    seen_ids: Dict[str, int] = {}

    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith(ROW_ID_PREFIXES):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rid = cells[0] if cells else f"line_{i}"
        if len(cells) < EXPECTED_COL_COUNT:
            issues.append(
                ValidationIssue(rid, "error", f"Dong {i}: thieu cot ({len(cells)}/{EXPECTED_COL_COUNT})")
            )

    for row in rows:
        if row.id in seen_ids:
            issues.append(
                ValidationIssue(row.id, "error", f"Trung ID (lan {seen_ids[row.id] + 1})")
            )
        seen_ids[row.id] = seen_ids.get(row.id, 0) + 1

        if not row.question:
            issues.append(ValidationIssue(row.id, "error", "Question trong"))
        if not row.expected_source.strip():
            issues.append(ValidationIssue(row.id, "error", "Expected source trong"))
        if not row.expected_answer.strip() and not _is_insufficient_row(row):
            issues.append(ValidationIssue(row.id, "error", "Expected answer trong (khong phai insufficient)"))
        if _is_insufficient_row(row) and "khong du" not in row.expected_answer.lower():
            issues.append(
                ValidationIssue(row.id, "warn", "Insufficient nhung expected answer khong co 'khong du'")
            )

    errors = [x for x in issues if x.severity == "error"]
    return ValidationReport(valid=len(errors) == 0, row_count=len(rows), issues=issues, rows=rows)


def write_validation_report(
    report: ValidationReport,
    path: Optional[Path] = None,
    filename_prefix: str = "v2-evalset-validation",
) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = path or (BASE_DIR / "reports" / f"{filename_prefix}-{ts}.md")
    lines = [
        "# V2 Eval Set Validation",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        f"File: `{EVAL_SET_PATH.relative_to(BASE_DIR)}`",
        "",
        "## Ket qua",
        "",
        f"- valid: **{report.valid}**",
        f"- row_count: {report.row_count}",
        f"- errors: {sum(1 for i in report.issues if i.severity == 'error')}",
        f"- warnings: {sum(1 for i in report.issues if i.severity == 'warn')}",
        "",
    ]
    if report.issues:
        lines.extend(["## Issues", "", "| ID | Severity | Message |", "|---|---|---|"])
        for iss in report.issues:
            lines.append(f"| {iss.id} | {iss.severity} | {iss.message} |")
    else:
        lines.append("Khong co issue.")
    lines.extend(["", "## Schema", "", "| Cot |", "|---|"])
    for c in EVAL_COLUMNS:
        lines.append(f"| {c} |")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
