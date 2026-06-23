"""Step 4 Silver QC pilot R2.4 — limited QC on 5 compact usable rows (rule-based, no full judge)."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from golden_set.io_utils import read_jsonl, write_jsonl
from golden_set.step2_distill_r2_1 import (
    _fact_fingerprint,
    _is_weak_or_generic,
    _norm_ws,
    _overlap,
    _span_in_text,
)

QC_VERSION = "2.4.0-pilot"

NEWS_CHROME_MARKERS = [
    "기자",
    "발행일",
    "글자크기",
    "기사 공유",
    "페이스북",
    "네이버 채널",
    "Advertisements",
    "지면보기",
    "백세경제",
]

MATERIAL_ISSUE_PATTERN = re.compile(r"8개\s*중대\s*이슈|총\s*8개")


def _status_pass_partial_fail(score: float, *, pass_at: float = 0.55, partial_at: float = 0.30) -> str:
    if score >= pass_at:
        return "pass"
    if score >= partial_at:
        return "partial"
    return "fail"


def _has_news_chrome(text: str) -> bool:
    head = (text or "")[:800]
    return sum(1 for m in NEWS_CHROME_MARKERS if m in head) >= 2


def _faithfulness_score(row: Dict[str, Any], unit_text: str) -> Tuple[str, str]:
    answer = (row.get("ground_truth_answer") or "").strip()
    span = (row.get("evidence_span") or "").strip()
    if not answer or not span:
        return "fail", "missing_answer_or_evidence_span"
    if not _span_in_text(span, unit_text):
        return "fail", "evidence_span_not_in_unit"
    ov = _overlap(answer, span)
    if answer not in span and ov < 0.15:
        return "fail", f"answer_not_grounded_in_span:ov={ov:.2f}"
    if ov < 0.35 and answer not in span:
        return "partial", f"low_answer_span_overlap:ov={ov:.2f}"
    return "pass", "answer_subset_of_evidence_span"


def _answer_relevancy_score(row: Dict[str, Any]) -> Tuple[str, str]:
    q = (row.get("question") or "").strip()
    a = (row.get("ground_truth_answer") or "").strip()
    company = row.get("company") or "한샘"
    if not q or not a:
        return "fail", "missing_question_or_answer"
    weak = _is_weak_or_generic(q, a)
    if weak:
        return "fail", f"weak_or_generic:{weak}"
    if company not in q and "한샘" not in q:
        return "partial", "company_not_explicit_in_question"
    ov = _overlap(q, a)
    if ov < 0.05 and not re.search(r"\d", q) == re.search(r"\d", a):
        return "partial", "question_answer_topic_loose"
    return "pass", "question_specific_and_answerable"


def _groundedness_score(row: Dict[str, Any], unit_text: str) -> Tuple[str, str]:
    ctx = unit_text or (row.get("context_excerpt") or "")
    if not ctx:
        return "fail", "missing_unit_text"
    record_id = row.get("ground_truth_record_id") or ""
    if not record_id:
        return "fail", "missing_record_id"
    span = row.get("evidence_span") or ""
    if _has_news_chrome(ctx):
        if span and _span_in_text(span, ctx):
            return "partial", "news_chrome_in_unit_but_span_grounded"
        return "fail", "news_chrome_ambiguous_grounding"
    tax = set(row.get("unit_taxonomy") or [])
    if "nav_or_menu_noise" in tax:
        return "fail", "nav_or_menu_taxonomy"
    if "listing_or_index_noise" in tax or "secondary_news_rewrite" in tax:
        if span and _span_in_text(span, ctx):
            return "partial", "conditional_news_mixed_but_span_grounded"
        return "fail", "noisy_unit_taxonomy"
    ov = _overlap(row.get("ground_truth_answer") or "", ctx)
    if ov < 0.12:
        return "partial", f"low_answer_context_overlap:{ov:.2f}"
    return "pass", "primary_esg_body_grounded"


def _detect_batch_duplicates(rows: List[Dict[str, Any]]) -> Dict[str, bool]:
    by_fp: Dict[str, List[str]] = defaultdict(list)
    by_material: List[str] = []
    flags: Dict[str, bool] = {}

    for row in rows:
        sid = row.get("silver_id", "")
        span = row.get("evidence_span") or ""
        company = row.get("company") or ""
        fp = _fact_fingerprint(company, span)
        by_fp[fp].append(sid)
        q = row.get("question") or ""
        a = row.get("ground_truth_answer") or ""
        if MATERIAL_ISSUE_PATTERN.search(span) or MATERIAL_ISSUE_PATTERN.search(a) or MATERIAL_ISSUE_PATTERN.search(q):
            by_material.append(sid)

    for sids in by_fp.values():
        if len(sids) > 1:
            for sid in sids:
                flags[sid] = True
    if len(by_material) > 1:
        for sid in by_material:
            flags[sid] = True
    return flags


def _qc_decision(
    *,
    faithfulness: str,
    relevancy: str,
    groundedness: str,
    duplicate: bool,
) -> Tuple[str, bool, str]:
    fails = [faithfulness, relevancy, groundedness].count("fail")
    partials = [faithfulness, relevancy, groundedness].count("partial")

    if fails >= 1:
        return "reject", True, "one_or_more_rubric_fail"
    if duplicate:
        return "revise", True, "duplicate_same_fact_cluster_in_batch"
    if partials >= 2:
        return "revise", True, "multiple_partial_rubric_scores"
    if partials == 1:
        return "revise", True, "single_partial_rubric_score"
    return "pass", False, "all_rubric_pass_no_duplicate"


def qc_pilot_row(row: Dict[str, Any], *, unit_text: str, duplicate_flag: bool) -> Dict[str, Any]:
    faithfulness, f_reason = _faithfulness_score(row, unit_text)
    relevancy, r_reason = _answer_relevancy_score(row)
    groundedness, g_reason = _groundedness_score(row, unit_text)
    decision, needs_rewrite, qc_reason = _qc_decision(
        faithfulness=faithfulness,
        relevancy=relevancy,
        groundedness=groundedness,
        duplicate=duplicate_flag,
    )
    promotion = decision == "pass" and not duplicate_flag

    notes = []
    if duplicate_flag:
        notes.append("Trùng fact cluster với row khác trong batch (8개 중대 이슈).")
    if groundedness == "partial":
        notes.append("Unit có news chrome; evidence_span vẫn grounded.")
    if decision == "revise" and duplicate_flag:
        notes.append("Giữ 1 row/batch cho fact cluster; cân nhắc giữ bản quantitative (0004) hoặc narrative (0001).")

    out = dict(row)
    out.update(
        {
            "qc_version": QC_VERSION,
            "qc_mode": "pilot_limited",
            "qc_decision": decision,
            "qc_reason": qc_reason,
            "faithfulness_status": faithfulness,
            "faithfulness_detail": f_reason,
            "answer_relevancy_status": relevancy,
            "answer_relevancy_detail": r_reason,
            "groundedness_status": groundedness,
            "groundedness_detail": g_reason,
            "duplicate_flag": duplicate_flag,
            "needs_rewrite": needs_rewrite,
            "promotion_candidate": "yes" if promotion else "no",
            "review_notes": " ".join(notes) if notes else (
                "Sẵn sàng promote gold pilot mini-set."
                if decision == "pass"
                else f"QC {decision}: xem chi tiết rubric."
            ),
            "unit_text_chars": len(unit_text or ""),
        }
    )
    return out


def extract_usable_rows(
    distilled_path: Path,
    *,
    usable_ids: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    rows = read_jsonl(distilled_path)
    out = []
    for r in rows:
        if r.get("decision") != "keep":
            continue
        if usable_ids and r.get("silver_id") not in usable_ids:
            continue
        if not r.get("evidence_span") or not r.get("ground_truth_answer"):
            continue
        out.append(r)
    return out


def enrich_with_unit_text(rows: List[Dict[str, Any]], pilot_units_path: Path) -> List[Dict[str, Any]]:
    units = {u.get("record_id"): u for u in read_jsonl(pilot_units_path)}
    enriched = []
    for row in rows:
        rid = row.get("ground_truth_record_id")
        unit = units.get(rid, {})
        merged = dict(row)
        merged["unit_text"] = unit.get("text") or row.get("context_excerpt") or ""
        merged["pilot_source"] = unit.get("pilot_source", "")
        merged["fact_categories"] = unit.get("fact_categories", [])
        enriched.append(merged)
    return enriched


def run_silver_qc_pilot_r24(
    *,
    distilled_path: Path,
    pilot_units_path: Path,
    qc_input_path: Path,
    qc_output_path: Path,
    csv_path: Path,
    usable_ids: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    rows = extract_usable_rows(distilled_path, usable_ids=usable_ids)
    rows = enrich_with_unit_text(rows, pilot_units_path)
    write_jsonl(qc_input_path, [{k: v for k, v in r.items() if k != "unit_text"} for r in rows])

    dup_flags = _detect_batch_duplicates(rows)
    qc_rows = [
        qc_pilot_row(r, unit_text=r.get("unit_text") or "", duplicate_flag=dup_flags.get(r.get("silver_id", ""), False))
        for r in rows
    ]

    # Strip full unit text from output (keep excerpt)
    for r in qc_rows:
        r.pop("unit_text", None)

    write_jsonl(qc_output_path, qc_rows)
    _write_review_csv(csv_path, qc_rows)

    decisions = Counter(r["qc_decision"] for r in qc_rows)
    promo = sum(1 for r in qc_rows if r.get("promotion_candidate") == "yes")

    return {
        "qc_version": QC_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_count": len(qc_rows),
        "pass_count": decisions.get("pass", 0),
        "revise_count": decisions.get("revise", 0),
        "reject_count": decisions.get("reject", 0),
        "promotion_candidate_count": promo,
        "duplicate_flag_count": sum(1 for r in qc_rows if r.get("duplicate_flag")),
        "qc_input_path": str(qc_input_path),
        "qc_output_path": str(qc_output_path),
        "csv_path": str(csv_path),
        "rows": [
            {
                "silver_id": r.get("silver_id"),
                "record_id": r.get("ground_truth_record_id"),
                "qc_decision": r.get("qc_decision"),
                "promotion_candidate": r.get("promotion_candidate"),
                "duplicate_flag": r.get("duplicate_flag"),
                "faithfulness_status": r.get("faithfulness_status"),
                "answer_relevancy_status": r.get("answer_relevancy_status"),
                "groundedness_status": r.get("groundedness_status"),
            }
            for r in qc_rows
        ],
    }


def _write_review_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fields = [
        "silver_id",
        "ground_truth_record_id",
        "company",
        "question_type",
        "difficulty",
        "question",
        "ground_truth_answer",
        "evidence_span",
        "qc_decision",
        "qc_reason",
        "faithfulness_status",
        "answer_relevancy_status",
        "groundedness_status",
        "duplicate_flag",
        "needs_rewrite",
        "promotion_candidate",
        "review_notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def write_qc_report(summary: Dict[str, Any], qc_rows: List[Dict[str, Any]], report_path: Path) -> None:
    promo_rows = [r for r in qc_rows if r.get("promotion_candidate") == "yes"]
    revise_rows = [r for r in qc_rows if r.get("qc_decision") == "revise"]
    pass_rows = [r for r in qc_rows if r.get("qc_decision") == "pass"]

    gold_mini_ready = len(promo_rows) >= 3
    next_step = "promote mini-set" if gold_mini_ready and not revise_rows else "revise trước khi promote"

    lines = [
        "# Golden Set — Silver QC Pilot R2.4 (Hạn chế)",
        "",
        f"Generated: {summary.get('generated_at', '')}",
        "",
        "## Mục tiêu QC pilot hạn chế",
        "",
        "Kiểm tra 5 silver row usable từ compact pilot R2.4 trước khi cân nhắc **gold pilot mini-set**.",
        "Đây **không** phải gate production / full Silver QC.",
        "",
        "## Input gồm 5 row",
        "",
        "| silver_id | record_id | question_type | pilot_source |",
        "|-----------|-----------|---------------|--------------|",
    ]
    for r in qc_rows:
        lines.append(
            f"| `{r.get('silver_id')}` | `{r.get('ground_truth_record_id')}` | "
            f"`{r.get('question_type')}` | `{r.get('pilot_source', '')}` |"
        )

    lines.extend(
        [
            "",
            "File input: `data/golden_set/v2/step4_silver_qc/pilot_hanssem_5_usable_for_qc_r2_4.jsonl`",
            "",
            "## Rubric QC đã áp",
            "",
            "Theo `reports/golden_set_method_round2.md` (3 trục pass/partial/fail), rule-based pilot:",
            "",
            "| Trục | Tiêu chí chính |",
            "|------|----------------|",
            "| **Faithfulness** | `evidence_span` ∈ unit text; answer grounded trong span |",
            "| **Answer Relevancy** | Câu hỏi đặc hiệu, có company, không generic/weak |",
            "| **Groundedness** | Record ESG primary; không nav/listing; news chrome → partial |",
            "| **Duplicate** | Cùng `evidence_span` fingerprint hoặc fact cluster `8개 중대 이슈` trong batch |",
            "",
            "Quyết định: `pass` = 3 trục pass + không duplicate; `revise` = partial/duplicate; `reject` = any fail.",
            "",
            "## Kết quả từng row",
            "",
            "| silver_id | qc_decision | faithfulness | relevancy | groundedness | dup | promotion |",
            "|-----------|-------------|--------------|-----------|--------------|-----|-----------|",
        ]
    )
    for r in qc_rows:
        lines.append(
            f"| `{r.get('silver_id')}` | **{r.get('qc_decision')}** | {r.get('faithfulness_status')} | "
            f"{r.get('answer_relevancy_status')} | {r.get('groundedness_status')} | "
            f"{r.get('duplicate_flag')} | {r.get('promotion_candidate')} |"
        )

    lines.extend(
        [
            "",
            "### Chi tiết review",
            "",
        ]
    )
    for r in qc_rows:
        lines.extend(
            [
                f"#### {r.get('silver_id')} — `{r.get('ground_truth_record_id')}`",
                "",
                f"- **qc_decision:** `{r.get('qc_decision')}` — {r.get('qc_reason')}",
                f"- **question:** {(r.get('question') or '')[:100]}…",
                f"- **review_notes:** {r.get('review_notes')}",
                "",
            ]
        )

    lines.extend(
        [
            "## Tổng hợp",
            "",
            f"| Chỉ số | Giá trị |",
            f"|--------|--------:|",
            f"| pass | {summary.get('pass_count', 0)} |",
            f"| revise | {summary.get('revise_count', 0)} |",
            f"| reject | {summary.get('reject_count', 0)} |",
            f"| promotion_candidate=yes | {summary.get('promotion_candidate_count', 0)} |",
            f"| duplicate_flag | {summary.get('duplicate_flag_count', 0)} |",
            "",
            "## Các lỗi còn lại",
            "",
        ]
    )
    issues = []
    for r in qc_rows:
        if r.get("duplicate_flag"):
            issues.append(f"- `{r.get('silver_id')}`: duplicate fact cluster (8 material issues)")
        if r.get("groundedness_status") == "partial":
            issues.append(f"- `{r.get('silver_id')}`: news chrome trong unit (`{r.get('groundedness_detail')}`)")
    if not issues:
        lines.append("- Không có lỗi fail; chỉ revise do duplicate/partial.")
    else:
        lines.extend(issues)

    lines.extend(
        [
            "",
            "## Kết luận",
            "",
            f"- **Đủ tạo gold pilot mini-set?** {'**Có một phần**' if gold_mini_ready else '**Chưa đủ**'} "
            f"({summary.get('promotion_candidate_count', 0)} row promote ngay / {len(qc_rows)} input).",
            f"- **Bước tiếp theo:** **{next_step}**.",
            "",
        ]
    )

    if promo_rows:
        lines.extend(["### Promotion pilot đề xuất (ngay)", ""])
        for r in promo_rows:
            lines.append(
                f"- **{r.get('silver_id')}** — `{r.get('question_type')}` — {r.get('review_notes')}"
            )

    if revise_rows:
        lines.extend(["", "### Cần revise trước promote", ""])
        for r in revise_rows:
            lines.append(f"- **{r.get('silver_id')}** — {r.get('qc_reason')}: {r.get('review_notes')}")

    lines.extend(
        [
            "",
            "### Ghi chú chiến lược",
            "",
            "- Gate chính `>=8 usable` vẫn **chưa đạt** — QC pilot này không thay gate production.",
            "- Song song: mở rộng corpus Hansem để tăng unique-body pool.",
        ]
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
