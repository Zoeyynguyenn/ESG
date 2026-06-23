"""Step 2 R2.1: Distillation with keep/drop, evidence_span, post-validation."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from golden_set.io_utils import append_jsonl, read_jsonl

DISTILLATION_VERSION = "2.1.0"

SYSTEM_PROMPT = """Bạn là ESG Golden Set Distillation Agent — chuyên gia tạo cặp câu hỏi–đáp án chuẩn (grounded Q&A) cho đánh giá RAG pipeline trong lĩnh vực ESG doanh nghiệp Hàn Quốc.

Nhiệm vụ DUY NHẤT: đọc MỘT corpus unit (một đoạn evidence) và quyết định:
- (A) sinh ĐÚNG MỘT cặp question + ground_truth_answer grounded, HOẶC
- (B) trả decision=drop nếu unit không đủ chất lượng để làm Golden Set.

Bạn KHÔNG phải chatbot tư vấn. Bạn KHÔNG được suy đoán, tổng hợp từ kiến thức ngoài unit, hay "cố gắng tạo câu hỏi" khi unit là noise.

Ngôn ngữ: question và ground_truth_answer PHẢI bằng tiếng Hàn (ko) khi unit là tiếng Hàn. Không dùng tiếng Việt hay tiếng Anh trong question/answer (trừ tên riêng/mã chuẩn như GRI, TCFD nếu đã có trong unit)."""

USER_PROMPT_TEMPLATE = """## Distillation task

Đọc corpus unit dưới đây và trả về JSON theo output contract.

### Input unit

- unit_id: {unit_id}
- company: {company}
- package_name: {package_name}
- record_id: {record_id}
- record_role: {record_role}
- source_type: {source_type}
- section_path: {section_path}
- source_file: {source_file}
- pre_filter_eligibility: {eligibility}
- unit_taxonomy: {unit_taxonomy_json}

### Text (toàn bộ unit — nguồn duy nhất được phép dùng)

\"\"\"
{text}
\"\"\"

---

## HARD CONSTRAINTS — TUYỆT ĐỐI KHÔNG SINH CÂU HỎI (phải decision=drop)

Trả decision=drop với drop_reason tương ứng nếu unit thuộc hoặc có dấu hiệu:

1. nav_or_menu_noise — mục lục (TOC), menu portal, 정보공개, 민원, "어디서 확인/찾을 수", 지면보기, 사이트맵
2. listing_or_index_noise — metadata danh sách file, DART 공시, 접수번호, 파일 크기, chỉ mô tả ngày công bố/file index
3. date_only_disclosure — fact duy nhất là ngày tháng / lịch 공시, không có giá trị ESG có nghĩa
4. cross_company_mismatch — nội dung chủ yếu về công ty/tổ chức KHÁC {company}
5. vendor_or_training_content — nội dung vendor làm báo cáo, đào tạo ESG, quảng bá dịch vụ
6. insufficient_substance / unanswerable_from_unit — không có câu khẳng định ESG cụ thể
7. ambiguous_grounding — không chọn được evidence_span một câu/đoạn ngắn chứa toàn bộ answer

CẤM: chỉ hỏi ngày tháng trống nghĩa; hỏi menu/lookup; hỏi công ty khác; sinh nhiều câu hỏi.

---

## POSITIVE TARGETS — ƯU TIÊN SINH CÂU HỎI KHI

Unit có primary ESG narrative, metric disclosure, governance/policy, risk/strategy, stakeholder/materiality.

Khi keep:
- Câu hỏi nêu rõ {company} hoặc đại từ công ty rõ ràng
- Answer ngắn (1–3 câu), trích từ unit
- evidence_span: trích NGUYÊN VĂN đoạn ngắn nhất trong unit chứa answer
- question_type: quantitative_fact | quantitative_metric | qualitative_strategy | qualitative_governance | qualitative_risk | qualitative_narrative | simple
- difficulty: easy | medium | hard

---

## OUTPUT FORMAT

Trả về ĐÚNG MỘT JSON object (không markdown):

Khi keep: decision, drop_reason=null, question, ground_truth_answer, question_type, difficulty, evidence_span, why_grounded

Khi drop: decision=drop, drop_reason, các field còn lại null"""


def _openai_chat(system: str, user: str, model: str, temperature: float = 0.1) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    return (resp.choices[0].message.content or "").strip()


def _parse_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return json.loads(text)


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _span_in_text(span: str, text: str) -> bool:
    if not span:
        return False
    a = _norm_ws(span)
    b = _norm_ws(text)
    if a in b:
        return True
    # tolerate minor whitespace differences across newlines
    a_compact = re.sub(r"\s+", "", a)
    b_compact = re.sub(r"\s+", "", b)
    return a_compact in b_compact


def _cjk_bigrams(text: str) -> Set[str]:
    chars = [c for c in text if "\uac00" <= c <= "\ud7a3"]
    if len(chars) < 2:
        return set()
    return {chars[i] + chars[i + 1] for i in range(len(chars) - 1)}


def _overlap(a: str, b: str) -> float:
    ba, bb = _cjk_bigrams(a), _cjk_bigrams(b)
    if not ba or not bb:
        return 0.0
    return len(ba & bb) / max(len(ba), 1)


def _fact_fingerprint(company: str, evidence_span: str) -> str:
    raw = f"{company}|{_norm_ws(evidence_span).lower()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]


WEAK_QUESTION_PATTERNS = [
    re.compile(r"무엇인가요\?$"),
    re.compile(r"어떤 .* 보고서"),
    re.compile(r"지속가능경영보고서를 발간"),
    re.compile(r"^(한샘|㈜한샘)은? .* 무엇"),
]
DATE_ONLY_Q = re.compile(r"(언제|몇 월|몇 일|날짜|일자|제출일|공시일|발행일)")


def _is_weak_or_generic(question: str, answer: str) -> Optional[str]:
    q = (question or "").strip()
    a = (answer or "").strip()
    if len(q) < 15:
        return "question_too_short"
    if len(a) < 8:
        return "answer_too_short"
    for pat in WEAK_QUESTION_PATTERNS:
        if pat.search(q) and len(a) < 40:
            return "generic_paraphrase"
    if DATE_ONLY_Q.search(q) and not re.search(r"\d{4}년", a):
        return "date_only_question"
    return None


def _build_user_prompt(unit: Dict[str, Any], text: str) -> str:
    tax = unit.get("unit_taxonomy") or []
    eligibility = unit.get("prefilter_decision") or "eligible"
    return USER_PROMPT_TEMPLATE.format(
        unit_id=unit.get("unit_id", ""),
        company=unit.get("company", ""),
        package_name=unit.get("package_name", ""),
        record_id=unit.get("record_id", ""),
        record_role=unit.get("record_role", ""),
        source_type=unit.get("source_type", ""),
        section_path=unit.get("section_path", ""),
        source_file=unit.get("source_file", ""),
        eligibility=eligibility,
        unit_taxonomy_json=json.dumps(tax, ensure_ascii=False),
        text=text,
    )


def _validate_keep(
    body: Dict[str, Any],
    unit: Dict[str, Any],
    seen_fingerprints: Set[str],
) -> Tuple[str, Optional[str], Optional[str]]:
    """Return (decision, drop_reason, validation_note)."""
    text = unit.get("text") or ""
    question = (body.get("question") or "").strip()
    answer = (body.get("ground_truth_answer") or "").strip()
    span = (body.get("evidence_span") or "").strip()
    why = (body.get("why_grounded") or "").strip()

    if not question or not answer:
        return "drop", "insufficient_substance", "missing_question_or_answer"
    if not span:
        return "drop", "ambiguous_grounding", "missing_evidence_span"
    if not why:
        return "drop", "ambiguous_grounding", "missing_why_grounded"
    if not _span_in_text(span, text):
        return "drop", "ambiguous_grounding", "evidence_span_not_in_unit"
    if not _span_in_text(answer, span) and _overlap(answer, span) < 0.2:
        return "drop", "ambiguous_grounding", "answer_not_in_evidence_span"
    if _overlap(answer, span) < 0.15 and answer not in span:
        return "drop", "ambiguous_grounding", "low_answer_span_overlap"

    weak = _is_weak_or_generic(question, answer)
    if weak:
        return "drop", "unanswerable_from_unit", weak

    fp = _fact_fingerprint(unit.get("company", ""), span)
    if fp in seen_fingerprints:
        return "drop", "duplicate_same_fact", "duplicate_evidence_span_in_batch"
    seen_fingerprints.add(fp)

    return "keep", None, None


def _row_from_unit(
    unit: Dict[str, Any],
    body: Dict[str, Any],
    *,
    silver_id: str,
    decision: str,
    drop_reason: Optional[str],
    validation_note: Optional[str],
    context_excerpt: str,
    llm_raw_decision: str,
) -> Dict[str, Any]:
    return {
        "silver_id": silver_id,
        "pipeline_stage": "silver_distilled_pilot",
        "distillation_version": DISTILLATION_VERSION,
        "decision": decision,
        "drop_reason": drop_reason,
        "llm_decision": llm_raw_decision,
        "validation_note": validation_note,
        "question": body.get("question") if decision == "keep" else None,
        "ground_truth_answer": body.get("ground_truth_answer") if decision == "keep" else None,
        "ground_truth_context_ids": [unit.get("unit_id")],
        "ground_truth_record_id": unit.get("record_id", ""),
        "question_type": body.get("question_type") if decision == "keep" else None,
        "difficulty": body.get("difficulty") if decision == "keep" else None,
        "evidence_span": body.get("evidence_span") if decision == "keep" else None,
        "why_grounded": body.get("why_grounded") if decision == "keep" else None,
        "company": unit.get("company", ""),
        "package_name": unit.get("package_name", ""),
        "gri_code": unit.get("gri_code", ""),
        "context_excerpt": context_excerpt[:400],
        "source_file": unit.get("source_file", ""),
        "prefilter_rule_id": unit.get("prefilter_rule_id", ""),
        "unit_taxonomy": unit.get("unit_taxonomy") or [],
    }


def run_distill_r2_1(
    *,
    input_path: Path,
    output_path: Path,
    model: str = "gpt-4o-mini",
    max_chars: int = 4000,
    limit: int = 0,
    id_prefix: str = "SV2-P21",
) -> Dict[str, Any]:
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        raise SystemExit("OPENAI_API_KEY missing for distillation R2.1")

    units = read_jsonl(input_path)
    if limit > 0:
        units = units[:limit]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    seen_fp: Set[str] = set()
    rows: List[Dict[str, Any]] = []
    errors = 0

    for i, unit in enumerate(units):
        text = (unit.get("text") or "")[:max_chars]
        ctx_excerpt = text[:400]
        silver_id = f"{id_prefix}-{i+1:04d}"
        user_prompt = _build_user_prompt(unit, text)

        try:
            raw = _openai_chat(SYSTEM_PROMPT, user_prompt, model)
            body = _parse_json(raw)
            llm_decision = (body.get("decision") or "").strip().lower()

            if llm_decision == "drop":
                row = _row_from_unit(
                    unit,
                    body,
                    silver_id=silver_id,
                    decision="drop",
                    drop_reason=body.get("drop_reason") or "insufficient_substance",
                    validation_note=None,
                    context_excerpt=ctx_excerpt,
                    llm_raw_decision="drop",
                )
            else:
                decision, drop_reason, validation_note = _validate_keep(body, unit, seen_fp)
                row = _row_from_unit(
                    unit,
                    body,
                    silver_id=silver_id,
                    decision=decision,
                    drop_reason=drop_reason,
                    validation_note=validation_note,
                    context_excerpt=ctx_excerpt,
                    llm_raw_decision=llm_decision or "keep",
                )
            append_jsonl(output_path, row)
            rows.append(row)
        except Exception as exc:
            errors += 1
            row = {
                "silver_id": silver_id,
                "pipeline_stage": "silver_distilled_pilot",
                "distillation_version": DISTILLATION_VERSION,
                "decision": "drop",
                "drop_reason": "llm_parse_error",
                "validation_note": str(exc)[:200],
                "company": unit.get("company", ""),
                "ground_truth_record_id": unit.get("record_id", ""),
                "unit_id": unit.get("unit_id"),
            }
            append_jsonl(output_path, row)
            rows.append(row)

    summary = analyze_pilot_rows(rows, input_count=len(units))
    summary.update(
        {
            "distillation_version": DISTILLATION_VERSION,
            "model": model,
            "input_path": str(input_path),
            "output_path": str(output_path),
            "errors": errors,
        }
    )
    return summary


def analyze_pilot_rows(rows: List[Dict[str, Any]], *, input_count: int) -> Dict[str, Any]:
    keep_rows = [r for r in rows if r.get("decision") == "keep"]
    drop_rows = [r for r in rows if r.get("decision") == "drop"]

    qtypes = Counter(r.get("question_type") or "null" for r in keep_rows)
    diffs = Counter(r.get("difficulty") or "null" for r in keep_rows)
    drop_reasons = Counter(r.get("drop_reason") or "unknown" for r in drop_rows)

    missing_answer = sum(1 for r in keep_rows if not (r.get("ground_truth_answer") or "").strip())
    missing_span = sum(1 for r in keep_rows if not (r.get("evidence_span") or "").strip())
    missing_why = sum(1 for r in keep_rows if not (r.get("why_grounded") or "").strip())

    weak_generic = 0
    good_grounding = 0
    duplicate_facts = sum(1 for r in drop_rows if r.get("drop_reason") == "duplicate_same_fact")

    for r in keep_rows:
        q, a = r.get("question") or "", r.get("ground_truth_answer") or ""
        span = r.get("evidence_span") or ""
        if _is_weak_or_generic(q, a):
            weak_generic += 1
        elif span and _overlap(a, span) >= 0.2:
            good_grounding += 1

    usable = [
        r
        for r in keep_rows
        if r.get("evidence_span")
        and r.get("why_grounded")
        and not _is_weak_or_generic(r.get("question") or "", r.get("ground_truth_answer") or "")
    ]

    return {
        "input_units": input_count,
        "output_rows": len(rows),
        "keep_count": len(keep_rows),
        "drop_count": len(drop_rows),
        "usable_count": len(usable),
        "by_question_type": dict(qtypes),
        "by_difficulty": dict(diffs),
        "by_drop_reason": dict(drop_reasons),
        "missing_ground_truth_answer": missing_answer,
        "missing_evidence_span": missing_span,
        "missing_why_grounded": missing_why,
        "weak_or_generic_keep": weak_generic,
        "good_grounding_keep": good_grounding,
        "duplicate_same_fact_drops": duplicate_facts,
        "usable_silver_ids": [r.get("silver_id") for r in usable],
    }
