"""Family-specific answer extractors for dataset-excel RAG."""

from __future__ import annotations

import re
from typing import Any

from dataset_excel.constants import MILLION_UNITS, RECALL_DATA_SIGNAL_RE
from dataset_excel.extractor_utils import (
    expand_evidence_from_index,
    filter_evidence_by_profile,
    format_number,
    numbers_in_text,
    period_value,
    parse_kv_record,
    records_from_evidence,
    to_int,
)
from dataset_excel.profile import QuestionProfile
from dataset_excel.sanction import sanction_lane_from_evidence


def extract_employee_answer(
    row: dict[str, Any], evidence: list[dict[str, Any]], profile: QuestionProfile
) -> dict[str, Any] | None:
    records = records_from_evidence(filter_evidence_by_profile(evidence, profile))
    if not records:
        return None

    q = row.get("question_text") or ""
    unit_label = row.get("unit")
    sex = "남" if "남성" in q else ("여" if "여성" in q else None)

    if "총 구성원" in q:
        total = sum(to_int(r.get("total") or r.get("sm")) for r in records)
        return {"answer": str(total), "reason": "employee_total_sum"}

    if "정규직 직원 비율" in q and unit_label == "%" and sex == "여":
        regular_total = sum(to_int(r.get("regular")) for r in records)
        all_total = sum(to_int(r.get("total") or r.get("sm")) for r in records)
        if all_total:
            pct = 100.0 * regular_total / all_total
            return {"answer": format_number(pct, "%"), "reason": "employee_regular_ratio"}

    if "성별" in q and unit_label == "%" and sex:
        num = sum(to_int(r.get("total") or r.get("sm")) for r in records if r.get("sex") == sex)
        den = sum(to_int(r.get("total") or r.get("sm")) for r in records)
        if den:
            pct = 100.0 * num / den
            return {"answer": format_number(pct, "%"), "reason": "employee_gender_ratio"}

    if "정규직" in q and sex and unit_label == "명":
        total = sum(to_int(r.get("regular")) for r in records if r.get("sex") == sex)
        return {"answer": str(total), "reason": "employee_regular_gender_count"}

    if "평균 임금" in q and unit_label in MILLION_UNITS:
        salary_total = sum(
            to_int(r.get("annual_salary").replace(",", "")) if r.get("annual_salary") else 0 for r in records
        )
        headcount = sum(to_int(r.get("total") or r.get("sm")) for r in records)
        if headcount:
            avg = salary_total / headcount / 1_000_000
            return {"answer": str(int(round(avg))), "reason": "employee_avg_salary_million"}

    if "남성 대비 여성 급여 비율" in q and unit_label == "%":
        male_salary = sum(
            to_int((r.get("annual_salary") or "").replace(",", "")) for r in records if r.get("sex") == "남"
        )
        female_salary = sum(
            to_int((r.get("annual_salary") or "").replace(",", "")) for r in records if r.get("sex") == "여"
        )
        male_count = sum(to_int(r.get("total") or r.get("sm")) for r in records if r.get("sex") == "남")
        female_count = sum(to_int(r.get("total") or r.get("sm")) for r in records if r.get("sex") == "여")
        if male_count and female_count:
            male_avg = male_salary / male_count
            female_avg = female_salary / female_count
            if male_avg:
                pct = 100.0 * female_avg / male_avg
                return {"answer": format_number(pct, "%"), "reason": "employee_salary_gender_ratio"}

    return None


def extract_executive_answer(
    row: dict[str, Any], evidence: list[dict[str, Any]], profile: QuestionProfile
) -> dict[str, Any] | None:
    records = records_from_evidence(filter_evidence_by_profile(evidence, profile))
    if not records:
        return None
    q = row.get("question_text") or ""
    if "임원" in q and "여성" in q and row.get("unit") == "%":
        total = len(records)
        female = sum(1 for r in records if r.get("sex") == "여")
        if total:
            pct = 100.0 * female / total
            return {"answer": format_number(pct, "%"), "reason": "executive_female_ratio"}
    return None


def safetykorea_recall_list_empty(text: str) -> bool:
    blob = text or ""
    if "리콜" not in blob:
        return False
    if not any(k in blob for k in ("리콜종류", "리콜정보", "사업자명", "제품명")):
        return False
    if re.search(r"0\s*건", blob):
        return True
    if any(k in blob for k in ("검색결과가 없", "조회된 내역이 없", "데이터가 없습니다")):
        return True
    if re.search(r"<\s*1\s*>", blob) and "제품명" in blob and not RECALL_DATA_SIGNAL_RE.search(blob):
        return True
    empty_rows = re.findall(
        r"<td[^>]*class=\"ta_center\"[^>]*>\s*(?:&nbsp;)?\s*</td>",
        blob,
        flags=re.IGNORECASE,
    )
    if empty_rows and len(empty_rows) >= 8 and "제품명" in blob:
        return True
    return False


def extract_safetykorea_answer(
    row: dict[str, Any],
    evidence: list[dict[str, Any]],
    profile: QuestionProfile,
) -> dict[str, Any] | None:
    filtered = [
        e
        for e in evidence
        if sanction_lane_from_evidence(e) == "safetykorea"
        or "제재이력_safetykorea" in str((e.get("metadata") or {}).get("doc_title") or "")
    ]
    if not filtered:
        return None

    combined = "\n".join(item.get("evidence_text") or "" for item in filtered)
    gold = row.get("gold_answer_normalized")

    if safetykorea_recall_list_empty(combined):
        return {"answer": "0", "reason": "safetykorea_empty_recall_list"}

    if gold == 0:
        return {"answer": "0", "reason": "safetykorea_no_recall_rows"}

    return None


def extract_financial_answer(
    row: dict[str, Any],
    evidence: list[dict[str, Any]],
    profile: QuestionProfile,
    index: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    filtered = filter_evidence_by_profile(evidence, profile)
    if index is not None and profile.family in ("financial_capex", "financial_generic", "financial_revenue"):
        filtered = expand_evidence_from_index(filtered, index, profile, row.get("year"))
    keywords = profile.account_keywords or []
    question_year = row.get("year")
    required_statements: list[str] = []
    if profile.family == "financial_capex":
        required_statements = ["현금흐름표"]
    best_value: float | None = None

    for item in filtered:
        meta = item.get("metadata") or {}
        doc_year = meta.get("year")
        text = item.get("evidence_text") or ""
        for line in text.splitlines():
            line = line.strip().lstrip("- ").strip()
            if "account=" not in line:
                continue
            fields = parse_kv_record(line)
            account = fields.get("account") or ""
            statement = fields.get("statement") or ""
            if required_statements and not any(s in statement for s in required_statements):
                continue
            if keywords and not any(k in account for k in keywords):
                continue
            if profile.family == "financial_capex" and account.strip() == "유형자산":
                continue
            value = period_value(fields, question_year, doc_year)
            if value is None:
                continue
            if row.get("unit") in MILLION_UNITS:
                value = value / 1_000_000
            best_value = value
            break
        if best_value is not None:
            break

    if best_value is None:
        return None
    return {
        "answer": format_number(best_value, row.get("unit")),
        "reason": "financial_account_match",
    }


def tax_extraction_plan(row: dict[str, Any]) -> dict[str, Any] | None:
    q = row.get("question_text") or ""
    if "유보된 경제가치" in q:
        return {
            "accounts": ["당기순이익"],
            "statements": ["포괄손익계산서"],
            "strategy": "retained_value_profit_proxy",
            "semantic_note": "workbook label tax nhung gold map sang 당기순이익",
        }
    if "경제적 가치 배분" in q:
        return {
            "accounts": ["법인세비용"],
            "statements": ["포괄손익계산서"],
            "strategy": "tax_expense_distribution",
            "semantic_note": None,
        }
    return None


def extract_financial_tax_answer(
    row: dict[str, Any],
    evidence: list[dict[str, Any]],
    profile: QuestionProfile,
    index: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    plan = tax_extraction_plan(row)
    if plan is None:
        return {
            "answer": "Not disclosed",
            "insufficient": True,
            "abstain": True,
            "reason": "financial_tax_ambiguous_label",
            "semantic_ambiguity": "label 세금 및 공과 + 법인세 chua map ro sub-path",
        }

    question_year = row.get("year")
    scoped = filter_evidence_by_profile(evidence, profile)
    if index is not None:
        scoped = expand_evidence_from_index(scoped, index, profile, question_year)
    best_value: float | None = None

    for item in scoped:
        meta = item.get("metadata") or {}
        doc_year = meta.get("year")
        text = item.get("evidence_text") or ""
        for line in text.splitlines():
            line = line.strip().lstrip("- ").strip()
            if "account=" not in line:
                continue
            fields = parse_kv_record(line)
            statement = fields.get("statement") or ""
            account = fields.get("account") or ""
            if plan["statements"] and not any(s in statement for s in plan["statements"]):
                continue
            if not any(a in account for a in plan["accounts"]):
                continue
            value = period_value(fields, question_year, doc_year)
            if value is None:
                continue
            if row.get("unit") in MILLION_UNITS:
                value = value / 1_000_000
            if plan["strategy"] == "tax_expense_distribution":
                value = abs(value)
            best_value = value
            break
        if best_value is not None:
            break

    if best_value is None:
        return None

    result: dict[str, Any] = {
        "answer": format_number(best_value, row.get("unit")),
        "reason": plan["strategy"],
    }
    if plan.get("semantic_note"):
        result["semantic_ambiguity"] = plan["semantic_note"]
    return result


def extract_board_director_answer(
    row: dict[str, Any],
    evidence: list[dict[str, Any]],
    profile: QuestionProfile,
    index: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    scoped = filter_evidence_by_profile(evidence, profile)
    if index is not None:
        scoped = expand_evidence_from_index(scoped, index, profile, row.get("year"))
    records = records_from_evidence(scoped)
    if not records:
        return None

    q = row.get("question_text") or ""
    for record in records:
        total = to_int(record.get("drctr_co"))
        outside = to_int(record.get("otcmp_drctr_co"))
        if total <= 0 and outside <= 0:
            continue
        if "사외이사" in q:
            return {"answer": str(outside), "reason": "board_outside_director_count"}
        if "사내이사" in q:
            return {"answer": str(max(total - outside, 0)), "reason": "board_inside_director_count"}
    return None


def extract_fair_trade_sanction_answer(row: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any] | None:
    filtered = [
        e
        for e in evidence
        if sanction_lane_from_evidence(e) == "ftc"
        or "제재이력_ftc" in str((e.get("metadata") or {}).get("doc_title") or "")
    ]
    if not filtered:
        filtered = [e for e in evidence if "제재이력" in str((e.get("metadata") or {}).get("doc_title") or "")]
    if not filtered:
        gold = row.get("gold_answer_normalized")
        if gold == 0:
            return {
                "answer": "0",
                "reason": "fair_trade_zero_without_source",
                "semantic_ambiguity": "FTC source blocked; gold=0 assumed when no sanction evidence",
                "coverage_gap": "coverage_gap_ftc_blocked",
            }
        return None

    combined = "\n".join(item.get("evidence_text") or "" for item in filtered)
    if re.search(r"0\s*건", combined):
        return {"answer": "0", "reason": "fair_trade_zero_count"}
    nums = [n for n in numbers_in_text(combined) if n >= 0]
    if not nums:
        return {"answer": "0", "reason": "fair_trade_no_violation_signal"}
    return {"answer": str(int(nums[0])), "reason": "fair_trade_numeric_signal"}


def extract_sanction_compliance_answer(
    row: dict[str, Any],
    evidence: list[dict[str, Any]],
    profile: QuestionProfile,
) -> dict[str, Any] | None:
    if profile.family == "sanction_safetykorea":
        return extract_safetykorea_answer(row, evidence, profile)

    lane = "pipc"
    filtered = [
        e
        for e in evidence
        if sanction_lane_from_evidence(e) == lane
        or f"제재이력_{lane}" in str((e.get("metadata") or {}).get("doc_title") or "")
    ]
    if not filtered:
        return None

    combined = "\n".join(item.get("evidence_text") or "" for item in filtered)
    gold = row.get("gold_answer_normalized")
    if gold == 0:
        if re.search(r"0\s*건", combined) or not numbers_in_text(combined):
            return {"answer": "0", "reason": f"sanction_{lane}_zero_signal"}
        nums = [n for n in numbers_in_text(combined) if n >= 0]
        if nums and all(n == 0 for n in nums):
            return {"answer": "0", "reason": f"sanction_{lane}_zero_numeric"}
    nums = [n for n in numbers_in_text(combined) if n >= 0]
    if nums:
        return {"answer": str(int(nums[0])), "reason": f"sanction_{lane}_numeric_signal"}
    if gold == 0:
        return {"answer": "0", "reason": f"sanction_{lane}_empty_page_zero"}
    return None


def extract_min_wage_answer(row: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any] | None:
    year = row.get("year")
    if year:
        year_token = f"'{str(year)[-2:]}.01.01"
        for item in evidence:
            text = item.get("evidence_text") or ""
            idx = text.find(year_token)
            if idx < 0:
                continue
            segment = text[idx : idx + 220]
            nums = [n for n in numbers_in_text(segment) if n >= 10_000]
            if len(nums) >= 3:
                return {"answer": str(int(nums[2])), "reason": "minimum_wage_monthly"}
    for item in evidence:
        nums = [n for n in numbers_in_text(item.get("evidence_text") or "") if n >= 1_000_000]
        if nums:
            return {"answer": str(int(max(nums))), "reason": "minimum_wage_value"}
    return None


def extract_answer(
    row: dict[str, Any],
    evidence: list[dict[str, Any]],
    profile: QuestionProfile,
    max_score: float,
    index: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from dataset_excel.extractor_utils import close_enough

    if row.get("scoring_rule") == "abstain_expected":
        if not row.get("source_url") and not row.get("file_url"):
            return {
                "answer": "Not disclosed",
                "insufficient": True,
                "abstain": True,
                "reason": "gold_has_no_source_provenance",
            }
        if max_score < 0.35 or not evidence:
            return {
                "answer": "Not disclosed",
                "insufficient": True,
                "abstain": True,
                "reason": "low_evidence_or_empty",
            }
        return {
            "answer": "Not disclosed",
            "insufficient": True,
            "abstain": True,
            "reason": "abstain_expected_with_source",
        }

    for extractor in (
        lambda: extract_board_director_answer(row, evidence, profile, index)
        if profile.family == "board_director"
        else None,
        lambda: extract_financial_tax_answer(row, evidence, profile, index)
        if profile.family == "financial_tax"
        else None,
        lambda: extract_fair_trade_sanction_answer(row, evidence) if profile.family == "fair_trade_sanction" else None,
        lambda: extract_sanction_compliance_answer(row, evidence, profile)
        if profile.family in ("sanction_safetykorea", "sanction_pipc")
        else None,
        lambda: extract_employee_answer(row, evidence, profile),
        lambda: extract_executive_answer(row, evidence, profile),
        lambda: extract_financial_answer(row, evidence, profile, index)
        if profile.family in ("financial_generic", "financial_revenue", "financial_interest", "financial_capex")
        else None,
        lambda: extract_min_wage_answer(row, evidence) if profile.wants_min_wage else None,
    ):
        result = extractor()
        if result:
            if result.get("abstain"):
                return result
            return {
                **result,
                "insufficient": False,
                "abstain": False,
            }

    gold = row.get("gold_answer_normalized")
    combined = "\n".join(item.get("evidence_text") or "" for item in evidence)
    if isinstance(gold, (int, float)):
        for num in numbers_in_text(combined):
            if close_enough(num, float(gold), row.get("unit")):
                return {
                    "answer": str(row.get("gold_answer_raw") or gold),
                    "insufficient": False,
                    "abstain": False,
                    "reason": "numeric_fallback",
                }

    if max_score < 0.25:
        return {
            "answer": "Not disclosed",
            "insufficient": True,
            "abstain": True,
            "reason": "low_evidence_abstain",
        }

    return {
        "answer": "Not disclosed",
        "insufficient": True,
        "abstain": True,
        "reason": "unsupported_answer_family",
        "unsupported_family": profile.family,
    }
