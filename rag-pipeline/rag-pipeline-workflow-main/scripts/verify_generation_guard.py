#!/usr/bin/env python3
"""Tests for downstream generation guard (retrieve flags -> abstain or safe LLM)."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _item(text: str, answerable: bool, **extra) -> "EvidenceItem":
    from evidence_api.schemas import EvidenceItem

    return EvidenceItem(
        text=text,
        source="test",
        score=extra.get("score", 0.9),
        confidence=extra.get("confidence", "high"),
        value=extra.get("value"),
        metric_name=extra.get("metric_name"),
        answerable_candidate=answerable,
        candidate_confidence="high" if answerable else "low",
        candidate_flags=[] if answerable else ["missing_metric_anchor"],
    )


def test_unit_should_abstain() -> None:
    from evidence_api.generation_guard import should_abstain
    from evidence_api.schemas import RetrieveResponse

    noise = _item("80.4%", False, value="80.4%", metric_name="esg_metric")
    resp = RetrieveResponse(
        items=[noise],
        company_id="musinsa",
        query="장애인 고용률",
        abstain_recommended=True,
        no_relevant_evidence=True,
        retrieval_confidence="low",
        reliability_flags=["metric_anchor_missing"],
        abstain_reason="metric_anchor_missing",
    )
    assert should_abstain(resp)

    good = _item("총직원 1891명", True)
    ok = RetrieveResponse(items=[good], company_id="musinsa", query="직원 수")
    assert not should_abstain(ok)


def test_unit_no_misleading_fields_in_prompt() -> None:
    from evidence_api.generation_guard import build_safe_context, item_for_prompt, resolve_answer
    from evidence_api.schemas import RetrieveResponse

    noise = _item("national 34.5%", False, value="34.5%", metric_name="esg_metric", score=0.99)
    good = _item("무신사 총직원 1891명", True, score=0.5)
    resp = RetrieveResponse(
        items=[noise, good],
        company_id="musinsa",
        query="직원 수",
        abstain_recommended=False,
    )

    prompt = item_for_prompt(good)
    assert "score" not in prompt
    assert "confidence" not in prompt

    ctx = build_safe_context(resp.items)
    assert "34.5%" not in ctx
    assert "1891" in ctx

    calls: List[str] = []

    def fake_llm(context: str, question: str) -> str:
        calls.append(context)
        assert "34.5%" not in context
        return "1891명"

    out = resolve_answer(resp, "직원 수", llm_generate=fake_llm)
    assert not out.abstained
    assert out.used_llm
    assert out.answer == "1891명"
    assert len(calls) == 1


def test_unit_abstain_blocks_llm() -> None:
    from evidence_api.generation_guard import resolve_answer
    from evidence_api.schemas import RetrieveResponse

    noise = _item("80.4%", False, value="80.4%", metric_name="esg_metric")
    resp = RetrieveResponse(
        items=[noise],
        company_id="musinsa",
        query="해당 기업의 장애인 고용률은 몇 %인가요?",
        abstain_recommended=True,
        no_relevant_evidence=True,
        retrieval_confidence="low",
    )

    def bad_llm(_c: str, _q: str) -> str:
        raise AssertionError("LLM must not be called when abstaining")

    out = resolve_answer(resp, resp.query, llm_generate=bad_llm)
    assert out.abstained
    assert not out.used_llm
    assert "신뢰할 수 있는 수치 근거" in out.answer
    assert "80.4" not in out.answer


def _bootstrap() -> None:
    from evidence_api.env_bootstrap import load_repo_dotenv

    load_repo_dotenv()


def test_integration_cases() -> None:
    from evidence_api.generation_guard import resolve_answer
    from evidence_api.query_rewrite import company_display_name
    from evidence_api.schemas import RetrieveRequest
    from evidence_api.service import EvidenceRetrievalService
    from evidence_api.staging_config import company_registry, load_staging_config

    svc = EvidenceRetrievalService()
    cfg = load_staging_config()
    display = company_display_name("musinsa", company_registry(cfg)["musinsa"])

    cases = [
        ("HC", "무신사의 직원 수는 몇 명인가요?", False),
        ("GR", "해당 기업의 여성 비율은 몇 %인가요?", True),
        ("BM", "해당 기업의 장애인 고용률은 몇 %인가요?", True),
        ("BM", "해당 기업의 육아휴직 대상자 수는 몇 명인가요?", True),
    ]

    llm_calls = 0

    def counting_llm(context: str, question: str) -> str:
        nonlocal llm_calls
        llm_calls += 1
        return "SHOULD_NOT_USE_NOISE"

    for group, query, expect_abstain in cases:
        llm_calls = 0
        resp = svc.retrieve(RetrieveRequest(query=query, company_id="musinsa", top_k=5))
        out = resolve_answer(resp, query, company_display=display, llm_generate=counting_llm)
        if expect_abstain:
            assert out.abstained, f"{group} should abstain: {query}"
            assert not out.used_llm, f"{group} must not call LLM: {query}"
            assert "80.4" not in out.answer
            assert "SHOULD_NOT" not in out.answer
        else:
            assert not out.abstained, f"{group} should not abstain: {query}"
            assert llm_calls == 1, f"{group} should call LLM once: {query}"
        time.sleep(0.25)


def main() -> int:
    test_unit_should_abstain()
    test_unit_no_misleading_fields_in_prompt()
    test_unit_abstain_blocks_llm()
    print("unit: OK")
    _bootstrap()
    test_integration_cases()
    print("integration: OK")
    print("verify_generation_guard: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
