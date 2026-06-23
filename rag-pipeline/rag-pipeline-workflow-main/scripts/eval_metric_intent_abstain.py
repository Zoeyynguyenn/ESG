#!/usr/bin/env python3
"""Eval metric-intent abstain gate (headcount pass + blocked metrics abstain)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


@dataclass
class AbstainCase:
    query: str
    expect: str  # answer | abstain
    gt_status: str = ""
    note: str = ""
    group: str = ""


@dataclass
class AbstainResult:
    case: AbstainCase
    abstain_recommended: bool
    no_relevant_evidence: bool
    retrieval_confidence: str
    abstain_reason: str
    reliability_reason: str
    reliability_flags: List[str]
    items_count: int
    top1_preview: str
    top1_answerable: bool
    all_items_unanswerable: bool
    ok: bool
    extra: dict = field(default_factory=dict)


HEADCOUNT_SHOULD_ANSWER: List[AbstainCase] = [
    AbstainCase("무신사의 직원 수는 몇 명인가요?", "answer", "clean", "1891명 GT", "HC"),
    AbstainCase("해당 기업의 총 구성원 수는 몇 명인가요?", "answer", "clean", "1891명 GT", "HC"),
    AbstainCase("무신사 임직원은 몇 명인가요?", "answer", "clean", "", "HC"),
]

GENDER_RATIO_SHOULD_ABSTAIN: List[AbstainCase] = [
    AbstainCase("해당 기업의 남성 비율은 몇 %인가요?", "abstain", "not_present", "", "GR"),
    AbstainCase("해당 기업의 여성 비율은 몇 %인가요?", "abstain", "not_present", "", "GR"),
    AbstainCase("무신사의 여성 구성 비중은 얼마인가요?", "abstain", "not_present", "", "GR"),
]

BLOCKED_METRICS: List[AbstainCase] = [
    AbstainCase(
        "해당 기업의 장애인 고용률은 몇 %인가요?",
        "abstain",
        "not_present",
        "National mss.go.kr stats only; no Musinsa workforce disability rate",
        "BM",
    ),
    AbstainCase(
        "해당 기업의 육아휴직 대상자 수는 몇 명인가요?",
        "abstain",
        "not_present",
        "Policy text only; no numeric 대상자 count",
        "BM",
    ),
    AbstainCase(
        "무신사의 장애인 고용률은 얼마인가요?",
        "abstain",
        "not_present",
        "",
        "BM",
    ),
    AbstainCase(
        "이 회사 육아휴직 사용 인원은 몇 명입니까?",
        "abstain",
        "not_present",
        "",
        "BM",
    ),
    AbstainCase(
        "해당 기업의 여성기업 인증 비율은 몇 %인가요?",
        "abstain",
        "not_present",
        "No such company metric",
        "BM",
    ),
]


def _bootstrap() -> None:
    from evidence_api.env_bootstrap import load_repo_dotenv

    load_repo_dotenv()


def eval_cases(cases: Sequence[AbstainCase], company_id: str = "musinsa") -> List[AbstainResult]:
    from evidence_api.schemas import RetrieveRequest
    from evidence_api.service import EvidenceRetrievalService

    svc = EvidenceRetrievalService()
    out: List[AbstainResult] = []
    for case in cases:
        resp = svc.retrieve(RetrieveRequest(query=case.query, company_id=company_id, top_k=5))
        preview = ""
        top1_answerable = False
        if resp.items:
            top = resp.items[0]
            preview = (top.text or "")[:90].replace("\n", " ")
            top1_answerable = top.answerable_candidate
        check_pool = resp.items[:3]
        all_unanswerable = not check_pool or all(not it.answerable_candidate for it in check_pool)
        if case.expect == "abstain":
            ok = (
                resp.abstain_recommended
                and resp.no_relevant_evidence
                and resp.retrieval_confidence == "low"
                and len(resp.items) > 0
                and all_unanswerable
            )
        else:
            ok = (
                not resp.abstain_recommended
                and len(resp.items) > 0
                and any(it.answerable_candidate for it in resp.items)
            )
        out.append(
            AbstainResult(
                case=case,
                abstain_recommended=resp.abstain_recommended,
                no_relevant_evidence=resp.no_relevant_evidence,
                retrieval_confidence=resp.retrieval_confidence,
                abstain_reason=resp.abstain_reason or "",
                reliability_reason=resp.reliability_reason or "",
                reliability_flags=list(resp.reliability_flags),
                items_count=len(resp.items),
                top1_preview=preview,
                top1_answerable=top1_answerable,
                all_items_unanswerable=all_unanswerable,
                ok=ok,
            )
        )
        time.sleep(0.3)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=ROOT / "reports" / "metric_intent_abstain_eval.json")
    args = parser.parse_args()
    _bootstrap()

    suites = [
        ("headcount_answer", HEADCOUNT_SHOULD_ANSWER),
        ("gender_ratio_abstain", GENDER_RATIO_SHOULD_ABSTAIN),
        ("blocked_metrics", BLOCKED_METRICS),
    ]
    all_rows: List[AbstainResult] = []
    for name, cases in suites:
        rows = eval_cases(cases)
        all_rows.extend(rows)
        ok_n = sum(1 for r in rows if r.ok)
        print(f"\n=== {name} ({ok_n}/{len(rows)} ok) ===")
        for r in rows:
            mark = "OK" if r.ok else "FAIL"
            print(f"[{mark}] {r.case.query[:50]}")
            print(
                f"  abstain={r.abstain_recommended} items={r.items_count} "
                f"reason={r.abstain_reason!r} flags={r.reliability_flags} "
                f"top1_answerable={r.top1_answerable} preview={r.top1_preview!r}"
            )

    total_ok = sum(1 for r in all_rows if r.ok)
    print(f"\nTotal: {total_ok}/{len(all_rows)}")

    payload = {
        "summaries": {
            name: {
                "ok": sum(1 for r in all_rows if r.case.group == cases[0].group and r.ok),
                "cases": len(cases),
            }
            for name, cases in suites
        },
        "rows": [
            {
                "query": r.case.query,
                "group": r.case.group,
                "expect": r.case.expect,
                "gt_status": r.case.gt_status,
                "note": r.case.note,
                "abstain_recommended": r.abstain_recommended,
                "no_relevant_evidence": r.no_relevant_evidence,
                "retrieval_confidence": r.retrieval_confidence,
                "abstain_reason": r.abstain_reason,
                "reliability_reason": r.reliability_reason,
                "reliability_flags": r.reliability_flags,
                "items_count": r.items_count,
                "top1_preview": r.top1_preview,
                "top1_answerable": r.top1_answerable,
                "all_items_unanswerable": r.all_items_unanswerable,
                "ok": r.ok,
            }
            for r in all_rows
        ],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.json_out}")
    return 0 if total_ok == len(all_rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
