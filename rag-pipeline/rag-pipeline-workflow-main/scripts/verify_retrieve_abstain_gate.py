#!/usr/bin/env python3
"""Unit tests for metric-intent abstain gate."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from evidence_api.abstain import (
    MetricIntent,
    assess_candidate,
    chunk_is_answerable,
    domain_mismatch,
    evaluate_abstain,
    evaluate_retrieval_reliability,
    is_gender_ratio_query,
    metric_anchor_passes,
    parse_metric_intent,
)
from evidence_api.schemas import EvidenceItem


def _item(text: str, source: str = "") -> EvidenceItem:
    return EvidenceItem(text=text, source=source, score=0.5, confidence="low")


def test_headcount_bypass() -> None:
    assert parse_metric_intent("무신사의 직원 수는 몇 명인가요?") is None
    assert parse_metric_intent("해당 기업의 총 구성원 수는 몇 명인가요?") is None
    d = evaluate_abstain("무신사의 직원 수는 몇 명인가요?", "무신사", [_item("총직원 1891명")])
    assert not d.abstain_recommended


def test_gender_ratio_abstain() -> None:
    assert is_gender_ratio_query("해당 기업의 여성 비율은 몇 %인가요?")
    assert is_gender_ratio_query("무신사의 남성 직원 비율은 몇 %인가요?")
    noise = _item("성별 : 공용 0 / 300 등록", "musinsa.com")
    d = evaluate_abstain("해당 기업의 여성 비율은 몇 %인가요?", "무신사", [noise])
    assert d.abstain_recommended and d.no_relevant_evidence
    d2 = evaluate_abstain("무신사의 남성 직원 비율은 몇 %인가요?", "무신사", [noise])
    assert d2.abstain_recommended


def test_disability_rate_abstain() -> None:
    intent = parse_metric_intent("해당 기업의 장애인 고용률은 몇 %인가요?")
    assert intent is not None and intent.kind == "percentage"
    national = _item(
        "우리나라 장애인은 2024년 말 등록 기준으로 총 인구의 5.14%인 263만 명이며, "
        "장애인 고용률은 34.5%로 전체 인구 63.3%에 비해",
        "https://www.mss.go.kr/foo",
    )
    assert domain_mismatch(national.text, national.source, "무신사")
    d = evaluate_abstain("해당 기업의 장애인 고용률은 몇 %인가요?", "무신사", [national])
    assert d.abstain_recommended


def test_parental_leave_count_abstain() -> None:
    intent = parse_metric_intent("해당 기업의 육아휴직 대상자 수는 몇 명인가요?")
    assert intent is not None and intent.kind == "count"
    policy = _item(
        "다자녀 직원 대상 육아휴직 호봉 인정 기준을 확대하고, 5세 이하 육아기 단축근무 제도를 운영",
        "https://www.mss.go.kr/foo",
    )
    assert not metric_anchor_passes(policy.text, intent)
    d = evaluate_abstain("해당 기업의 육아휴직 대상자 수는 몇 명인가요?", "무신사", [policy])
    assert d.abstain_recommended

    intent2 = parse_metric_intent("이 회사 육아휴직 사용 인원은 몇 명입니까?")
    assert intent2 is not None and intent2.kind == "count"
    d2 = evaluate_abstain(
        "이 회사 육아휴직 사용 인원은 몇 명입니까?",
        "무신사",
        [_item("임원진 7명 영입", "")],
    )
    assert d2.abstain_recommended


def test_answerable_percentage() -> None:
    intent = MetricIntent(kind="percentage", topic_terms=["장애인", "고용률"])
    good = "무신사 장애인 고용률 3.2% 달성"
    assert chunk_is_answerable(good, "", "무신사", intent)


def test_item_annotations() -> None:
    national = _item(
        "우리나라 장애인 고용률은 34.5%",
        "https://www.mss.go.kr/foo",
    )
    decision = evaluate_retrieval_reliability(
        "해당 기업의 장애인 고용률은 몇 %인가요?", "무신사", [national]
    )
    assert decision.abstain_recommended
    assert len(decision.item_assessments) == 1
    ann = decision.item_assessments[0]
    assert not ann.answerable_candidate
    assert ann.candidate_confidence == "low"
    assert "domain_mismatch" in ann.candidate_flags


def test_headcount_item_annotation() -> None:
    good = _item("무신사 총직원 1891명 규모", "")
    ann = assess_candidate(good.text, good.source, "무신사", query="무신사 직원 수는 몇 명인가요?")
    assert ann.answerable_candidate
    assert ann.candidate_confidence in ("high", "medium")


def main() -> int:
    test_headcount_bypass()
    test_gender_ratio_abstain()
    test_disability_rate_abstain()
    test_parental_leave_count_abstain()
    test_answerable_percentage()
    test_item_annotations()
    test_headcount_item_annotation()
    print("verify_retrieve_abstain_gate: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
