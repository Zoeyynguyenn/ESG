"""Step 4: Automated QC — answerability, difficulty, groundedness."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Set

from golden_set.io_utils import read_jsonl, write_jsonl
from rag_common import tokenize


def _cjk_chunks(text: str, n: int = 2) -> Set[str]:
    compact = re.sub(r"\s+", "", text)
    if len(compact) < n:
        return {compact} if compact else set()
    return {compact[i : i + n] for i in range(len(compact) - n + 1)}


def _overlap(a: str, b: str) -> float:
    ta: Set[str] = set(tokenize(a))
    tb: Set[str] = set(tokenize(b))
    if ta and tb:
        return len(ta & tb) / max(1, len(ta))
    ca, cb = _cjk_chunks(a), _cjk_chunks(b)
    if ca and cb:
        return len(ca & cb) / max(1, len(ca))
    # Fallback: long substring in context
    a_norm = re.sub(r"\s+", "", a)
    b_norm = re.sub(r"\s+", "", b)
    if len(a_norm) >= 6 and a_norm in b_norm:
        return 1.0
    return 0.0


def _qc_row(row: Dict[str, Any], *, min_q: int, min_a: int, min_overlap: float, strict_ground: bool) -> tuple[bool, str]:
    q = (row.get("question") or "").strip()
    a = (row.get("ground_truth_answer") or "").strip()
    ctx = (row.get("context_excerpt") or "").strip()

    if len(q) < min_q:
        return False, "answerability:question_too_short"
    if len(a) < min_a:
        return False, "answerability:answer_too_short"
    if not ctx:
        return False, "groundedness:missing_context"

    ov = _overlap(a, ctx)
    if strict_ground and ov < min_overlap:
        return False, f"groundedness:low_overlap:{ov:.3f}"

    # Difficulty: drop obvious copy-paste questions
    q_lower = q.lower()
    if len(q_lower) < 20 and q_lower in ctx.lower():
        return False, "difficulty:verbatim_question"

    return True, "ok"


def run_step4(
    *,
    input_path: Path,
    pass_path: Path,
    reject_path: Path,
    min_question_chars: int = 12,
    min_answer_chars: int = 8,
    min_context_overlap: float = 0.15,
    drop_if_answer_not_in_context: bool = True,
) -> Dict[str, Any]:
    rows = read_jsonl(input_path)
    passed: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    for row in rows:
        ok, reason = _qc_row(
            row,
            min_q=min_question_chars,
            min_a=min_answer_chars,
            min_overlap=min_context_overlap,
            strict_ground=drop_if_answer_not_in_context,
        )
        tagged = dict(row)
        tagged["qc_status"] = "pass" if ok else "reject"
        tagged["qc_reason"] = reason
        if ok:
            passed.append(tagged)
        else:
            rejected.append(tagged)

    write_jsonl(pass_path, passed)
    write_jsonl(reject_path, rejected)
    return {
        "input": len(rows),
        "pass": len(passed),
        "reject": len(rejected),
        "pass_path": str(pass_path),
        "reject_path": str(reject_path),
    }
