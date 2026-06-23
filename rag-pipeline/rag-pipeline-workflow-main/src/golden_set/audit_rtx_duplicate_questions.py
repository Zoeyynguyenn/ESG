"""Audit duplicate / over-generic question failure on RTX lane artifacts."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from golden_set.io_utils import read_jsonl

BANNED_GENERIC = [
    "What ESG-related policies or performance does RTX disclose?",
    "What quantitative ESG metrics does RTX disclose?",
    "How have RTX's key ESG metrics changed over time?",
    "How is ESG governance structured at RTX?",
    "What ethics and compliance practices does RTX disclose?",
    "What ESG metric or policy does RTX disclose?",
    "What does RTX disclose about ESG metric or policy?",
    "How has RTX's ESG metric or policy changed over reported years?",
]

NEAR_DUP_PREFIX_LEN = 55


def _question_field(row: Dict[str, Any]) -> str:
    for k in ("polished_question_draft", "rewritten_question_draft", "question_draft"):
        v = row.get(k)
        if v:
            return str(v).strip()
    return ""


def _normalize_q(q: str) -> str:
    t = q.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = t.replace("rtx", "").strip()
    return t


def audit_questions(rows: Sequence[Dict[str, Any]], label: str) -> Dict[str, Any]:
    questions = [_question_field(r) for r in rows]
    q_counter = Counter(questions)
    exact_dup_templates = {q: n for q, n in q_counter.items() if n > 1 and q}
    affected = sum(n for n in exact_dup_templates.values())

    by_dk: Counter = Counter()
    by_qt: Counter = Counter()
    for r in rows:
        q = _question_field(r)
        if q in exact_dup_templates:
            by_dk[r.get("document_kind") or "unknown"] += 1
            by_qt[r.get("question_type") or "unknown"] += 1

    prefix_groups: Dict[str, List[str]] = defaultdict(list)
    for q in q_counter:
        if not q:
            continue
        prefix = _normalize_q(q)[:NEAR_DUP_PREFIX_LEN]
        prefix_groups[prefix].append(q)

    near_dup_groups = {p: qs for p, qs in prefix_groups.items() if len(qs) > 1}
    near_affected = sum(q_counter[q] for qs in near_dup_groups.values() for q in qs)

    banned_hits = sum(q_counter.get(b, 0) for b in BANNED_GENERIC)

    return {
        "label": label,
        "total_rows": len(rows),
        "unique_questions": len(q_counter),
        "exact_duplicate_question_count": len(exact_dup_templates),
        "exact_duplicate_affected_rows": affected,
        "near_duplicate_question_count": len(near_dup_groups),
        "near_duplicate_affected_rows": near_affected,
        "banned_generic_hits": banned_hits,
        "top_duplicate_templates": [
            {"question": q, "count": n}
            for q, n in q_counter.most_common(15)
            if n > 1
        ],
        "by_document_kind_affected": dict(by_dk.most_common(12)),
        "by_question_type_affected": dict(by_qt.most_common(8)),
    }


def write_audit_report(summaries: Sequence[Dict[str, Any]], path: Path) -> None:
    v1 = next((s for s in summaries if s["label"] == "v1"), summaries[0])
    m2 = next((s for s in summaries if s["label"] == "manual_round2"), None)

    lines = [
        "# Golden Set — RTX Duplicate Question Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Mục tiêu",
        "",
        "Xác định mức độ lỗi **duplicate / over-generic question** trên lane RTX",
        "trước khi rebuild question layer fact-specific (v2).",
        "",
        "## Triệu chứng lỗi",
        "",
        "- Nhiều row dùng cùng `question_draft` nhưng khác `question_type`, `document_kind`, `disclosure`",
        "- Reviewer không thể phân biệt fact target đúng/sai",
        "- Workbook không đạt chuẩn Golden Set ở tầng question synthesis",
        "",
        "## Top exact duplicate question templates (v1)",
        "",
        f"- Total rows v1: **{v1['total_rows']}**",
        f"- Unique questions v1: **{v1['unique_questions']}**",
        f"- Exact duplicate templates: **{v1['exact_duplicate_question_count']}**",
        f"- Rows affected: **{v1['exact_duplicate_affected_rows']}** ({100*v1['exact_duplicate_affected_rows']/max(v1['total_rows'],1):.1f}%)",
        f"- Banned generic template hits: **{v1['banned_generic_hits']}**",
        "",
    ]
    for item in v1.get("top_duplicate_templates", [])[:10]:
        lines.append(f"- `{item['count']}`× `{item['question']}`")

    lines.extend(["", "## Top near-duplicate templates (v1)", ""])
    lines.append(f"- Near-duplicate prefix groups: **{v1['near_duplicate_question_count']}**")
    lines.append(f"- Rows in near-duplicate groups: **{v1['near_duplicate_affected_rows']}**")

    if m2:
        lines.extend(
            [
                "",
                "## Manual round 2 (sau polish) — vẫn còn generic",
                "",
                f"- Reviewable rows: **{m2['total_rows']}**",
                f"- Unique questions: **{m2['unique_questions']}**",
                f"- Exact duplicate templates: **{m2['exact_duplicate_question_count']}**",
                f"- Rows affected: **{m2['exact_duplicate_affected_rows']}**",
                f"- Fallback generic hits: **{m2['banned_generic_hits']}**",
            ]
        )

    lines.extend(
        [
            "",
            "### Breakdown affected rows by document_kind (v1)",
            "",
        ]
    )
    for dk, n in v1.get("by_document_kind_affected", {}).items():
        lines.append(f"- `{dk}`: {n}")

    lines.extend(
        [
            "",
            "## Ảnh hưởng",
            "",
            "- **Review**: reviewer không biết row nào test fact nào",
            "- **Gold set**: không thể promote câu hỏi không gắn fact target",
            "- **Benchmark**: metric retrieval/answer sẽ meaningless nếu question không specific",
            "",
            "## Kết luận",
            "",
            "Lane RTX phải **rebuild question layer (v2 fact-specific)** trước khi mở lại review round 1.",
            "Tạm dừng manual review round 2 execution, canonical, gold decision, benchmark.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_audit(
    *,
    v1_path: Path,
    reviewed_path: Path,
    manual_path: Path,
    report_path: Path,
    summary_path: Path,
) -> Dict[str, Any]:
    v1_rows = read_jsonl(v1_path)
    r1_rows = read_jsonl(reviewed_path) if reviewed_path.exists() else []
    m2_rows = [
        r
        for r in read_jsonl(manual_path)
        if r.get("review_decision") in ("keep", "rewrite")
        or r.get("manual_review_lane") in ("lane_a_ready_keep", "lane_b_rewrite_light", "lane_c_rewrite_heavy")
    ] if manual_path.exists() else []

    summaries = [
        audit_questions(v1_rows, "v1"),
        audit_questions(r1_rows, "reviewed_round1"),
        audit_questions(m2_rows, "manual_round2"),
    ]

    primary = summaries[0]
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "exact_duplicate_question_count": primary["exact_duplicate_question_count"],
        "near_duplicate_question_count": primary["near_duplicate_question_count"],
        "top_duplicate_templates": primary["top_duplicate_templates"][:10],
        "affected_rows_count": primary["exact_duplicate_affected_rows"],
        "banned_generic_hits": primary["banned_generic_hits"],
        "by_document_kind": primary["by_document_kind_affected"],
        "by_question_type": primary["by_question_type_affected"],
        "v1_unique_questions": primary["unique_questions"],
        "v1_total_rows": primary["total_rows"],
        "manual_round2": summaries[2] if len(summaries) > 2 else {},
        "verdict": "rebuild_question_layer_required",
    }

    write_audit_report(summaries, report_path)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Audit RTX duplicate questions")
    parser.add_argument("--v1", default="data/golden_set/v2/reference_style/reference_seed_candidates_rtx_v1.jsonl")
    parser.add_argument("--reviewed", default="data/golden_set/v2/reference_style/reference_seed_candidates_rtx_reviewed_round1.jsonl")
    parser.add_argument("--manual", default="data/golden_set/v2/reference_style/reference_seed_candidates_rtx_manual_round2.jsonl")
    parser.add_argument("--report", default="reports/golden_set_rtx_duplicate_question_audit.md")
    parser.add_argument("--summary", default="reports/_rtx_duplicate_question_audit_summary.json")
    args = parser.parse_args(argv)

    summary = run_audit(
        v1_path=root / args.v1,
        reviewed_path=root / args.reviewed,
        manual_path=root / args.manual,
        report_path=root / args.report,
        summary_path=root / args.summary,
    )
    print(json.dumps({k: summary[k] for k in ("exact_duplicate_question_count", "affected_rows_count", "v1_unique_questions")}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
