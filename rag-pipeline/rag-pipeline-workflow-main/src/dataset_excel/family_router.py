"""Question-family routing, retrieval boost, and evidence reranking."""

from __future__ import annotations

from typing import Any

from dataset_excel.constants import NOISE_DOC_PATTERNS
from dataset_excel.profile import QuestionProfile
from dataset_excel.sanction import sanction_lane_from_evidence


def infer_question_profile(row: dict[str, Any]) -> QuestionProfile:
    q = row.get("question_text") or ""
    metric = row.get("metric_name") or ""
    blob = f"{q} {metric}"

    year = row.get("year")
    if year is not None:
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = None

    preferred_doc: list[str] = []
    preferred_schema: list[str] = []
    penalize_doc: list[str] = []
    account_keywords: list[str] = []
    wants_min_wage = False
    family = "generic"

    if any(k in blob for k in ("최저임금", "minimumwage", "minimum wage")):
        wants_min_wage = True
        preferred_doc = ["최저임금", "minimumwage"]
        preferred_schema = ["web_html"]
        penalize_doc = ["empSttus", "exctvSttus", "재무_"]
        family = "minimum_wage"
    elif any(k in blob for k in ("임원", "다양성")) and "여성" in blob:
        preferred_doc = ["exctvSttus"]
        preferred_schema = ["dart_executive_status"]
        penalize_doc = ["empSttus", "최저임금", "재무_"]
        family = "executive_diversity"
    elif any(k in blob for k in ("제품", "리콜", "품질 및 안전", "안전 컴플라이언스")):
        preferred_doc = ["제재이력_safetykorea", "제재이력"]
        preferred_schema = ["web_html"]
        penalize_doc = ["제재이력_pipc", "제재이력_ftc", "empSttus", "exctvSttus", "재무_", "최저임금"]
        family = "sanction_safetykorea"
    elif any(k in blob for k in ("개인정보", "민원", "정보보호")):
        preferred_doc = ["제재이력_pipc", "제재이력"]
        preferred_schema = ["web_html"]
        penalize_doc = ["제재이력_safetykorea", "제재이력_ftc", "empSttus", "exctvSttus", "재무_", "최저임금"]
        family = "sanction_pipc"
    elif any(k in blob for k in ("공정거래", "violtLaw", "ftc.go.kr")) or (
        "부패" in blob and "지배구조" not in blob and "사외이사" not in blob and "사내이사" not in blob
    ):
        preferred_doc = ["제재이력"]
        preferred_schema = ["web_html"]
        penalize_doc = ["empSttus", "exctvSttus", "재무_", "outcmpnyDrctrNdChangeSttus", "최저임금"]
        family = "fair_trade_sanction"
    elif any(k in blob for k in ("사외이사", "사내이사")) or ("지배구조" in blob and "부패" in blob):
        preferred_doc = ["outcmpnyDrctrNdChangeSttus"]
        preferred_schema = ["dart_board_director_change"]
        penalize_doc = ["empSttus", "exctvSttus", "재무_", "최저임금", "제재이력"]
        family = "board_director"
    elif any(k in blob for k in ("이사", "변동", "outcmpny")):
        preferred_doc = ["outcmpnyDrctrNdChangeSttus"]
        preferred_schema = ["dart_board_director_change"]
        penalize_doc = ["empSttus", "exctvSttus", "재무_", "최저임금", "제재이력"]
        family = "board_director"
    elif any(k in blob for k in ("매출액", "매출", "수익")):
        preferred_doc = ["재무_"]
        preferred_schema = ["dart_financial_statement"]
        account_keywords = ["매출액"]
        penalize_doc = ["empSttus", "exctvSttus", "최저임금"]
        family = "financial_revenue"
    elif "유형자산" in blob and "취득" in blob:
        preferred_doc = ["재무_"]
        preferred_schema = ["dart_financial_statement"]
        account_keywords = ["유형자산의 취득"]
        penalize_doc = ["empSttus", "exctvSttus", "최저임금", "제재이력"]
        family = "financial_capex"
    elif any(k in blob for k in ("이자비용", "이자")):
        preferred_doc = ["재무_"]
        preferred_schema = ["dart_financial_statement"]
        account_keywords = ["이자비용", "이자"]
        penalize_doc = ["empSttus", "exctvSttus", "최저임금"]
        family = "financial_interest"
    elif any(k in blob for k in ("세금", "법인세", "공과")):
        preferred_doc = ["재무_"]
        preferred_schema = ["dart_financial_statement"]
        account_keywords = []
        penalize_doc = ["empSttus", "exctvSttus", "최저임금", "제재이력", "outcmpnyDrctrNdChangeSttus", "exctvSttus"]
        family = "financial_tax"
    elif any(k in blob for k in ("구성원", "성별", "정규직", "계약직", "남성", "여성", "총 구성원", "급여", "평균 임금")):
        preferred_doc = ["empSttus"]
        preferred_schema = ["dart_employee_status"]
        penalize_doc = ["exctvSttus", "최저임금", "재무_"]
        family = "employee_status"
    elif any(k in blob for k in ("경제적 가치", "배당", "순이익")):
        preferred_doc = ["재무_"]
        preferred_schema = ["dart_financial_statement"]
        penalize_doc = ["empSttus", "exctvSttus", "최저임금"]
        family = "financial_generic"

    return QuestionProfile(
        year=year,
        preferred_doc_patterns=preferred_doc,
        preferred_schemas=preferred_schema,
        penalize_doc_patterns=penalize_doc,
        account_keywords=account_keywords,
        wants_min_wage=wants_min_wage,
        family=family,
    )


def heuristic_boost(profile: QuestionProfile, unit: dict[str, Any]) -> float:
    boost = 0.0
    doc_title = str(unit.get("doc_title") or "")
    schema = str(unit.get("schema") or "")
    unit_year = unit.get("year")

    if profile.year is not None and unit_year == profile.year:
        boost += 0.45
    elif profile.year is not None and unit_year not in (None, "") and unit_year != profile.year:
        boost -= 0.30

    if any(p in doc_title for p in profile.preferred_doc_patterns):
        boost += 0.55
    if profile.preferred_schemas and schema in profile.preferred_schemas:
        boost += 0.25
    if any(p in doc_title for p in profile.penalize_doc_patterns):
        boost -= 0.70
    if profile.family == "board_director" and "exctvSttus" in doc_title:
        boost -= 1.50
    if profile.family == "board_director" and "outcmpnyDrctrNdChangeSttus" in doc_title:
        boost += 1.35
    if profile.family == "employee_status" and "exctvSttus" in doc_title:
        boost -= 1.60
    if profile.family == "employee_status" and "empSttus" in doc_title:
        boost += 1.10
    if profile.family == "fair_trade_sanction" and "제재이력" in doc_title:
        boost += 1.20
    if profile.family == "sanction_safetykorea":
        if "제재이력_safetykorea" in doc_title or unit.get("sanction_lane") == "safetykorea":
            boost += 1.35
        if any(lane in doc_title for lane in ("제재이력_pipc", "제재이력_ftc")):
            boost -= 1.25
    if profile.family == "sanction_pipc":
        if "제재이력_pipc" in doc_title or unit.get("sanction_lane") == "pipc":
            boost += 1.35
        if any(lane in doc_title for lane in ("제재이력_safetykorea", "제재이력_ftc")):
            boost -= 1.25
    if profile.family == "financial_tax" and "재무_" in doc_title:
        boost += 0.65
    if profile.family not in ("fair_trade_sanction", "minimum_wage") and any(
        noise in doc_title for noise in NOISE_DOC_PATTERNS
    ):
        boost -= 1.15
    if profile.wants_min_wage and "최저임금" in doc_title:
        boost += 0.80
    if not profile.wants_min_wage and ("최저임금" in doc_title or "minimumwage" in doc_title.lower()):
        boost -= 0.85

    return boost


def rerank_evidence_for_family(evidence: list[dict[str, Any]], profile: QuestionProfile) -> list[dict[str, Any]]:
    if not evidence:
        return evidence

    def doc_title(item: dict[str, Any]) -> str:
        return str((item.get("metadata") or {}).get("doc_title") or "")

    if profile.family == "board_director":
        preferred = [e for e in evidence if "outcmpnyDrctrNdChangeSttus" in doc_title(e)]
        others = [e for e in evidence if e not in preferred]
        return preferred + others

    if profile.family == "employee_status":
        preferred = [e for e in evidence if "empSttus" in doc_title(e)]
        others = [e for e in evidence if e not in preferred]
        return preferred + others

    if profile.family in (
        "financial_tax",
        "financial_revenue",
        "financial_interest",
        "financial_generic",
        "financial_capex",
    ):
        clean = [e for e in evidence if not any(noise in doc_title(e) for noise in NOISE_DOC_PATTERNS)]
        noisy = [e for e in evidence if e not in clean]
        evidence = clean + noisy
        if profile.year is not None:
            year_match = [e for e in evidence if (e.get("metadata") or {}).get("year") == profile.year]
            year_other = [e for e in evidence if e not in year_match]
            evidence = year_match + year_other
        return evidence

    if profile.family == "fair_trade_sanction":
        expected_lane = "ftc"
        preferred = [
            e
            for e in evidence
            if sanction_lane_from_evidence(e) == expected_lane or "제재이력_ftc" in doc_title(e)
        ]
        others = [e for e in evidence if e not in preferred]
        return preferred + others

    if profile.family == "sanction_safetykorea":
        preferred = [
            e
            for e in evidence
            if sanction_lane_from_evidence(e) == "safetykorea" or "제재이력_safetykorea" in doc_title(e)
        ]
        others = [e for e in evidence if e not in preferred]
        return preferred + others

    if profile.family == "sanction_pipc":
        preferred = [
            e
            for e in evidence
            if sanction_lane_from_evidence(e) == "pipc" or "제재이력_pipc" in doc_title(e)
        ]
        others = [e for e in evidence if e not in preferred]
        return preferred + others

    return evidence
