"""Step 6: Promote SME-approved rows to Golden Set + eval markdown."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from golden_set.io_utils import write_jsonl


def _load_sme_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def run_step6(
    *,
    sme_csv_path: Path,
    gold_jsonl_path: Path,
    eval_md_path: Path,
    gold_version: str = "v2",
) -> Dict[str, Any]:
    rows = _load_sme_csv(sme_csv_path)
    gold: List[Dict[str, Any]] = []
    for i, r in enumerate(rows):
        decision = (r.get("sme_decision") or "").strip().lower()
        if decision not in ("approve", "approved", "yes", "ok"):
            continue
        q = (r.get("sme_revised_question") or r.get("question") or "").strip()
        a = (r.get("sme_revised_answer") or r.get("ground_truth_answer") or "").strip()
        if not q or not a:
            continue
        pkg = r.get("package_name", "")
        rec = r.get("ground_truth_record_id", "")
        expected_source = ""
        if pkg and rec:
            expected_source = (
                f"data/rag_dataset/05_company_export_json/{pkg}/records/company_evidence.jsonl"
            )
        gold.append(
            {
                "golden_version": gold_version,
                "question_id": f"GV2-{i+1:03d}",
                "question": q,
                "ground_truth_answer": a,
                "ground_truth_record_id": rec,
                "expected_source": expected_source,
                "company": r.get("company", ""),
                "package_name": pkg,
                "question_type": r.get("question_type", ""),
                "difficulty": r.get("difficulty", "medium"),
                "gri_code": r.get("gri_code", ""),
                "forbidden_rule": r.get("forbidden_rule", ""),
                "sme_notes": r.get("sme_notes", ""),
                "promoted_at": datetime.now().isoformat(timespec="seconds"),
            }
        )

    write_jsonl(gold_jsonl_path, gold)

    lines = [
        f"# Golden Set {gold_version} — promoted from Silver→Gold pipeline",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "| ID | Question | Expected Evidence Source | Expected Answer Notes | Record ID | Difficulty | Category | Status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for g in gold:
        lines.append(
            f"| {g['question_id']} | {g['question']} | {g.get('expected_source', '')} | "
            f"{g['ground_truth_answer'][:120]} | {g.get('ground_truth_record_id', '')} | "
            f"{g.get('difficulty', '')} | {g.get('question_type', '')} | approved |"
        )
    eval_md_path.parent.mkdir(parents=True, exist_ok=True)
    eval_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "gold_count": len(gold),
        "gold_jsonl": str(gold_jsonl_path),
        "eval_md": str(eval_md_path),
    }
