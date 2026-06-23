"""Revise-before-promote R2.4 — manual-rule revisions for 4 QC revise rows."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from golden_set.io_utils import read_jsonl, write_jsonl
from golden_set.step2_distill_r2_1 import _span_in_text

REVISE_VERSION = "2.4.0"

# Curated revisions keyed by silver_id
REVISE_SPECS: Dict[str, Dict[str, Any]] = {
    "SV2-P24-0001": {
        "revise_group": "duplicate_cluster_conflict",
        "revise_action": "keep_as_duplicate_winner",
        "revised_question": "한샘은 2025 지속가능경영보고서에서 이중 중대성 평가를 통해 선정한 8개 중대 이슈는 무엇인가요?",
        "revised_answer": "▲기후변화 완화 ▲책임있는 조달 ▲지속 가능한 제품 설계 ▲사업장 근무 조건 ▲인권경영 ▲협력사 동반성장 ▲제품 안전 및 품질 ▲공정거래 등 총 8개 중대 이슈를 선정했다.",
        "revised_evidence_span": "한샘은 이중 중대성 평가를 통해 ▲기후변화 완화 ▲책임있는 조달 ▲지속 가능한 제품 설계 ▲사업장 근무 조건 ▲인권경영 ▲협력사 동반성장 ▲제품 안전 및 품질 ▲공정거래 등 총 8개 중대 이슈를 선정했다.",
        "revised_decision": "promote_ready",
        "revised_promotion_candidate": "yes",
        "revised_notes": (
            "Giữ thay 0004: unit rec_3adad134 sạch (noise=0), span grounded; "
            "0004 trùng fact cluster và unit news chrome (백세경제)."
        ),
    },
    "SV2-P24-0004": {
        "revise_group": "duplicate_cluster_conflict",
        "revise_action": "drop_duplicate_loser",
        "revised_question": None,
        "revised_answer": None,
        "revised_evidence_span": None,
        "revised_decision": "do_not_promote",
        "revised_promotion_candidate": "no",
        "revised_notes": (
            "Loại khỏi mini-set: trùng fact 8 issues với SV2-P24-0001; "
            "unit rec_2d0cf95b có news chrome (백세경제); giữ bản 0001 vì evidence sạch hơn."
        ),
    },
    "SV2-P24-0002": {
        "revise_group": "partial_grounding_but_salvageable",
        "revise_action": "rewrite_question_anchor_year",
        "revised_question": "한샘은 2023년 지속가능경영보고서에서 공개한 2050년 탄소중립 목표는 무엇인가요?",
        "revised_answer": "2050년까지 ‘탄소중립(Net Zero·넷제로)’을 달성하는 목표를 공개했다.",
        "revised_evidence_span": "2050년까지 ‘탄소중립(Net Zero·넷제로)’을 달성하는 목표를 공개했다.",
        "revised_decision": "promote_ready",
        "revised_promotion_candidate": "yes",
        "revised_notes": (
            "Cứu được: thêm anchor năm 2023 + Net Zero; Q/A/span bám verbatim unit rec_41a160ead; "
            "unit conditional/news mixed nhưng span trong body chính."
        ),
    },
    "SV2-P24-0005": {
        "revise_group": "news_chrome_partial",
        "revise_action": "rewrite_minimal_fact_strip",
        "revised_question": "한샘은 한국기업지배구조원(KGCS) ESG경영 평가에서 어떤 등급을 획득했나요?",
        "revised_answer": "전년 대비 1등급 상승한 ‘A’등급을 획득했다.",
        "revised_evidence_span": "한샘은 지난해 한국기업지배구조원(KGCS)의 ESG경영 평가 결과, 전년 대비 1등급 상승한 ‘A’등급을 획득했다.",
        "revised_decision": "do_not_promote",
        "revised_promotion_candidate": "no",
        "revised_notes": (
            "Không promote: unit rec_ba9d092 noise=16, chrome dài + unrelated tail; "
            "fact KGCS có thể dùng sau khi corpus sạch hơn; không ép vào gold pilot."
        ),
    },
}

PASS_UNCHANGED = {
    "SV2-P24-0003": {
        "revise_group": "qc_pass_unchanged",
        "revise_action": "none",
        "revised_decision": "promote_ready",
        "revised_promotion_candidate": "yes",
        "revised_notes": "QC pass — giữ nguyên TCFD row.",
    },
}


def _validate_revised(row: Dict[str, Any], unit_text: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    span = spec.get("revised_evidence_span")
    if not span:
        return True, "n/a_drop"
    if not _span_in_text(span, unit_text):
        return False, "revised_span_not_in_unit"
    ans = spec.get("revised_answer") or ""
    if ans and not _span_in_text(ans, span) and ans not in span:
        # answer should be substring of span or overlap
        if ans.replace(" ", "") not in span.replace(" ", ""):
            return False, "revised_answer_not_in_span"
    return True, "ok"


def apply_revise_row(
    row: Dict[str, Any],
    *,
    unit_text: str,
    spec: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    sid = row.get("silver_id", "")
    if spec is None:
        spec = REVISE_SPECS.get(sid) or PASS_UNCHANGED.get(sid, {})

    out = dict(row)
    group = spec.get("revise_group", "")
    action = spec.get("revise_action", "none")

    if action in ("none",) or sid in PASS_UNCHANGED:
        out.update(
            {
                "revise_version": REVISE_VERSION,
                "revise_group": spec.get("revise_group", ""),
                "revise_action": "none",
                "revised_question": row.get("question"),
                "revised_answer": row.get("ground_truth_answer"),
                "revised_evidence_span": row.get("evidence_span"),
                "revised_decision": spec.get("revised_decision", "promote_ready"),
                "revised_promotion_candidate": spec.get("revised_promotion_candidate", "yes"),
                "revised_notes": spec.get("revised_notes", ""),
                "revise_validation": "unchanged_pass",
            }
        )
        return out

    rq = spec.get("revised_question")
    ra = spec.get("revised_answer")
    rs = spec.get("revised_evidence_span")

    valid, vnote = _validate_revised(row, unit_text, spec)
    promo = spec.get("revised_promotion_candidate", "no")
    decision = spec.get("revised_decision", "do_not_promote")
    if not valid and promo == "yes":
        promo = "no"
        decision = "needs_rework"
        notes = f"{spec.get('revised_notes', '')} VALIDATION FAIL: {vnote}"
    else:
        notes = spec.get("revised_notes", "")

    out.update(
        {
            "revise_version": REVISE_VERSION,
            "revise_group": group,
            "revise_action": action,
            "revised_question": rq,
            "revised_answer": ra,
            "revised_evidence_span": rs,
            "revised_decision": decision,
            "revised_promotion_candidate": promo,
            "revised_notes": notes,
            "revise_validation": vnote,
        }
    )
    return out


def run_revise_before_promote(
    *,
    qc_result_path: Path,
    pilot_units_path: Path,
    output_path: Path,
) -> Dict[str, Any]:
    rows = read_jsonl(qc_result_path)
    units = {u.get("record_id"): u for u in read_jsonl(pilot_units_path)}

    revised_rows: List[Dict[str, Any]] = []
    for row in rows:
        rid = row.get("ground_truth_record_id")
        unit_text = (units.get(rid) or {}).get("text") or row.get("context_excerpt") or ""
        sid = row.get("silver_id", "")
        if row.get("qc_decision") == "pass":
            revised_rows.append(apply_revise_row(row, unit_text=unit_text, spec=PASS_UNCHANGED.get(sid)))
        elif row.get("qc_decision") == "revise":
            revised_rows.append(apply_revise_row(row, unit_text=unit_text, spec=REVISE_SPECS.get(sid)))
        else:
            r = dict(row)
            r.update(
                {
                    "revise_version": REVISE_VERSION,
                    "revise_action": "skip",
                    "revised_decision": "do_not_promote",
                    "revised_promotion_candidate": "no",
                }
            )
            revised_rows.append(r)

    write_jsonl(output_path, revised_rows)

    before_promo = sum(1 for r in rows if r.get("promotion_candidate") == "yes")
    after_promo = sum(1 for r in revised_rows if r.get("revised_promotion_candidate") == "yes")
    salvaged = sum(
        1
        for r in revised_rows
        if r.get("qc_decision") == "revise" and r.get("revised_promotion_candidate") == "yes"
    )
    dropped_dup = sum(1 for r in revised_rows if r.get("revise_action") == "drop_duplicate_loser")

    return {
        "revise_version": REVISE_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_rows": len(rows),
        "revise_rows": sum(1 for r in rows if r.get("qc_decision") == "revise"),
        "before_promotion_candidate": before_promo,
        "after_promotion_candidate": after_promo,
        "salvaged_from_revise": salvaged,
        "dropped_duplicate_losers": dropped_dup,
        "output_path": str(output_path),
        "promote_ready_ids": [
            r.get("silver_id")
            for r in revised_rows
            if r.get("revised_promotion_candidate") == "yes"
        ],
    }


def write_revise_report(summary: Dict[str, Any], rows: List[Dict[str, Any]], report_path: Path) -> None:
    promote = [r for r in rows if r.get("revised_promotion_candidate") == "yes"]
    not_promote = [r for r in rows if r.get("revised_promotion_candidate") != "yes"]
    revise_in = [r for r in rows if r.get("qc_decision") == "revise"]

    mini_set_ok = len(promote) >= 2

    lines = [
        "# Golden Set — Revise Before Promote R2.4",
        "",
        f"Generated: {summary.get('generated_at', '')}",
        "",
        "## Mục tiêu revise",
        "",
        "Xử lý 4 row `revise` từ Silver QC pilot để nâng số row **promote-ready** cho gold pilot mini-set, ưu tiên chất lượng hơn số lượng.",
        "",
        "## 4 row revise là gì",
        "",
        "| silver_id | revise_group | qc_reason |",
        "|-----------|--------------|-----------|",
    ]
    for r in revise_in:
        lines.append(
            f"| `{r.get('silver_id')}` | `{r.get('revise_group', '')}` | `{r.get('qc_reason', '')}` |"
        )

    lines.extend(
        [
            "",
            "## Chiến lược xử lý từng nhóm lỗi",
            "",
            "### duplicate_cluster_conflict (`0001` / `0004`)",
            "",
            "- Chỉ giữ **1** row cho fact cluster **8개 중대 이슈**.",
            "- **Giữ `SV2-P24-0001`** (unit `rec_3adad134`, noise=0, primary body).",
            "- **Loại `SV2-P24-0004`**: trùng fact + unit news chrome (백세경제).",
            "",
            "### partial_grounding_but_salvageable (`0002` Net Zero)",
            "",
            "- Rewrite câu hỏi neo năm **2023** + **탄소중립**; giữ answer/span verbatim từ unit.",
            "",
            "### news_chrome_partial (`0005` KGCS)",
            "",
            "- Thử rewrite Q neo **KGCS**; sau validate vẫn **không promote** vì unit noise=16 và tail unrelated.",
            "",
            "## Kết quả từng row",
            "",
            "| silver_id | revise_action | revised_decision | promotion | ghi chú |",
            "|-----------|---------------|------------------|-----------|---------|",
        ]
    )
    for r in rows:
        lines.append(
            f"| `{r.get('silver_id')}` | `{r.get('revise_action', '')}` | "
            f"`{r.get('revised_decision', '')}` | `{r.get('revised_promotion_candidate', '')}` | "
            f"{(r.get('revised_notes') or '')[:60]}… |"
        )

    lines.extend(
        [
            "",
            "### Row cứu được / có điều kiện / không promote",
            "",
            "**Cứu được (promote-ready):**",
        ]
    )
    for r in promote:
        lines.append(f"- `{r.get('silver_id')}` — {r.get('revised_notes', '')[:100]}")

    lines.extend(["", "**Không promote:**", ""])
    for r in not_promote:
        if r.get("silver_id") != "SV2-P24-0003" or r.get("revised_promotion_candidate") != "yes":
            if r.get("revised_promotion_candidate") != "yes":
                lines.append(f"- `{r.get('silver_id')}` — {r.get('revised_notes', '')[:100]}")

    lines.extend(
        [
            "",
            "## So sánh trước/sau revise",
            "",
            "| Metric | Trước QC | Sau QC | Sau revise |",
            "|--------|----------:|-------:|-----------:|",
            f"| promotion_candidate | {summary.get('before_promotion_candidate', 1)} | {summary.get('before_promotion_candidate', 1)} | **{summary.get('after_promotion_candidate', 0)}** |",
            f"| revise row salvaged | — | — | **{summary.get('salvaged_from_revise', 0)}** |",
            f"| duplicate dropped | — | — | **{summary.get('dropped_duplicate_losers', 0)}** |",
            "",
            "## Kết quả cuối",
            "",
            f"- **Tổng promote-ready sau revise: {summary.get('after_promotion_candidate', 0)}**",
            f"- IDs: {', '.join(f'`{x}`' for x in summary.get('promote_ready_ids', []))}",
            "",
            "## Kết luận",
            "",
        ]
    )

    if mini_set_ok:
        lines.extend(
            [
                f"- **Đủ tạo gold pilot mini-set?** **Có** — {len(promote)} row sạch đủ cho mini-set thử nghiệm (không phải gate production).",
                "- **Bước tiếp theo:** `promote mini-set` (step 6 pilot, không full promotion).",
                "",
                "### Mini-set candidates",
                "",
                "| silver_id | unit_id | question (revised) | recommendation |",
                "|-----------|---------|-------------------|----------------|",
            ]
        )
        for r in promote:
            q = r.get("revised_question") or r.get("question") or ""
            uid = (r.get("ground_truth_context_ids") or [""])[0]
            lines.append(
                f"| `{r.get('silver_id')}` | `{uid}` | {q[:70]}… | **promote** |"
            )
    else:
        lines.extend(
            [
                "- **Đủ tạo gold pilot mini-set?** **Chưa**.",
                "- **Dừng tại:** revise xong nhưng chưa đủ row sạch; cần mở rộng corpus Hansem hoặc SME rewrite thủ công.",
            ]
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
