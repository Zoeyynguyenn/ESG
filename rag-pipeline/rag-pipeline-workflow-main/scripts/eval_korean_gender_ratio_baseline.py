#!/usr/bin/env python3
"""Baseline eval for KO gender-ratio metric class (Musinsa). No retrieval patches."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# gt_status: clean = verifiable snippet in indexed company_evidence; blocked = no clean GT
@dataclass
class RatioCase:
    query: str
    gt_status: str  # clean | blocked | ambiguous
    expected_snippet: str = ""
    expected_note: str = ""
    group: str = "R"


@dataclass
class RatioResult:
    case: RatioCase
    rewritten: str
    bm25_query: str
    headcount_path: bool
    ratio_path: bool
    rerank_status: str
    top1_has_gt: Optional[bool]
    top3_has_gt: Optional[bool]
    pool_has_gt: Optional[bool]
    bm25_has_gt: Optional[bool]
    pre_rank: int
    post_rank: int
    top1_record_id: str
    top1_preview: str
    failure: str
    abstain_recommended: bool = False
    no_relevant_evidence: bool = False
    retrieval_confidence: str = "high"
    abstain_reason: str = ""
    abstain_ok: bool = False
    extra: dict = field(default_factory=dict)


PRIMARY_CASES: List[RatioCase] = [
    RatioCase(
        "해당 기업의 남성 비율은 몇 %인가요?",
        "blocked",
        "",
        "No Musinsa workforce male % in indexed company_evidence",
        "P",
    ),
    RatioCase(
        "해당 기업의 여성 비율은 몇 %인가요?",
        "blocked",
        "",
        "No Musinsa workforce female % in indexed company_evidence",
        "P",
    ),
]

MINI_REGRESSION: List[RatioCase] = [
    RatioCase("무신사의 여성 비율은 몇 퍼센트인가요?", "blocked", "", "QT-002 dataset_issue in golden_set", "R"),
    RatioCase("이 회사의 남성 구성 비율은 몇 %인가요?", "blocked", "", "", "R"),
    RatioCase("무신사의 여성 구성 비중은 얼마인가요?", "blocked", "", "", "R"),
    RatioCase("해당 회사의 성비 중 여성 비율은 몇 %입니까?", "blocked", "", "", "R"),
    RatioCase("해당 기업 남녀 비율 중 남성은?", "blocked", "", "", "R"),
    RatioCase("무신사 임직원 여성 비율", "blocked", "", "", "R"),
    RatioCase("이 회사 여성 구성원 비율은?", "blocked", "", "", "R"),
    RatioCase("해당 회사의 남성 직원 비율은 몇 %인가요?", "blocked", "", "", "R"),
]

# Ambiguous: wrong-metric snippets that must NOT be treated as GT pass
AMBIGUOUS_SNIPPETS = ("여성 패션 잡화 거래액 50%", "여성비율(47.0)", "여성기업")


def _bootstrap() -> None:
    from evidence_api.env_bootstrap import load_repo_dotenv

    load_repo_dotenv()


def _has_snippet(text: str, snippet: str) -> bool:
    return bool(snippet) and snippet in (text or "")


def _rank(hits: Sequence[Any], snippet: str) -> int:
    if not snippet:
        return 0
    for i, h in enumerate(hits, start=1):
        if _has_snippet(h.text, snippet):
            return i
    return 0


def _rerank_status(note: str) -> str:
    return "jina_api" if "jina_api" in note else note.split(";")[-1] if note else "unknown"


def _classify_failure(
    case: RatioCase,
    pool_has: Optional[bool],
    bm25_has: Optional[bool],
    pre_rank: int,
    top1_has: Optional[bool],
) -> str:
    if case.gt_status == "blocked":
        return "gt_blocked"
    if top1_has:
        return "pass"
    if not pool_has:
        return "answerable_chunk_not_in_top_pool"
    if pre_rank and pre_rank <= 3:
        return "rerank_failed_to_promote"
    if not bm25_has:
        return "bm25_recall_weak"
    return "rerank_failed_to_promote"


def eval_cases(cases: Sequence[RatioCase], company_id: str = "musinsa") -> List[RatioResult]:
    from evidence_api.query_rewrite import rewrite_query_for_company
    from evidence_api.schemas import RetrieveRequest
    from evidence_api.service import EvidenceRetrievalService
    from evidence_api.staging_config import (
        apply_company_env,
        company_registry,
        load_staging_config,
        reset_retrieval_runtime_caches,
    )
    from export_json_retrieval_hints import should_apply_export_json_boost
    from korean_metric_retrieval_hints import is_headcount_metric_query, prepare_bm25_query
    import retrieval_v3 as r3
    from retrieval_v3 import (
        retrieve_bm25_lexical,
        retrieve_hybrid_dense_bm25,
        retrieve_hybrid_dense_bm25_rerank,
    )

    try:
        from korean_metric_retrieval_hints import is_gender_ratio_metric_query
    except ImportError:
        def is_gender_ratio_metric_query(_q: str) -> bool:  # type: ignore
            return False

    cfg = load_staging_config()
    entry = company_registry(cfg)[company_id]
    apply_company_env(cfg, company_id, base_dir=ROOT)
    reset_retrieval_runtime_caches()
    r3._bm25_index = None
    r3._reranker = None

    svc = EvidenceRetrievalService()
    pool = int(cfg["stack"].get("candidate_pool", 64))
    top_k = 8
    results: List[RatioResult] = []

    for case in cases:
        rewritten = rewrite_query_for_company(case.query, company_id, entry)
        bm25_q = prepare_bm25_query(rewritten, lane_expand=should_apply_export_json_boost())
        bm25_hits, _ = retrieve_bm25_lexical(bm25_q, pool, pool)
        hybrid_pool, _ = retrieve_hybrid_dense_bm25(rewritten, pool, pool)
        reranked, note = retrieve_hybrid_dense_bm25_rerank(rewritten, pool, top_k)

        snippet = case.expected_snippet
        if case.gt_status == "clean" and snippet:
            pool_has = any(_has_snippet(h.text, snippet) for h in hybrid_pool)
            bm25_has = any(_has_snippet(h.text, snippet) for h in bm25_hits)
            pre_rank = _rank(hybrid_pool, snippet)
            post_rank = _rank(reranked, snippet)
        else:
            pool_has = bm25_has = None
            pre_rank = post_rank = 0

        resp = svc.retrieve(RetrieveRequest(query=case.query, company_id=company_id, top_k=top_k))
        top1_preview = ""
        top1_rid = ""
        top1_has = top3_has = None
        if resp.items:
            top1_rid = resp.items[0].record_id or ""
            top1_preview = (resp.items[0].text or "")[:90].replace("\n", " ")
            if snippet:
                top1_has = _has_snippet(resp.items[0].text or "", snippet)
                top3_has = any(_has_snippet(it.text or "", snippet) for it in resp.items[:3])

        ambiguous_hits = [
            s for s in AMBIGUOUS_SNIPPETS if resp.items and any(s in (it.text or "") for it in resp.items[:3])
        ]

        check_pool = resp.items[:3]
        all_unanswerable = not check_pool or all(not it.answerable_candidate for it in check_pool)
        abstain_ok = (
            case.gt_status == "blocked"
            and resp.abstain_recommended
            and resp.no_relevant_evidence
            and resp.retrieval_confidence == "low"
            and len(resp.items) > 0
            and all_unanswerable
        )

        results.append(
            RatioResult(
                case=case,
                rewritten=rewritten,
                bm25_query=bm25_q,
                headcount_path=is_headcount_metric_query(rewritten),
                ratio_path=is_gender_ratio_metric_query(rewritten),
                rerank_status=_rerank_status(note),
                top1_has_gt=top1_has,
                top3_has_gt=top3_has,
                pool_has_gt=pool_has,
                bm25_has_gt=bm25_has,
                pre_rank=pre_rank,
                post_rank=post_rank,
                top1_record_id=top1_rid,
                top1_preview=top1_preview,
                failure=_classify_failure(case, pool_has, bm25_has, pre_rank, top1_has),
                abstain_recommended=resp.abstain_recommended,
                no_relevant_evidence=resp.no_relevant_evidence,
                retrieval_confidence=resp.retrieval_confidence,
                abstain_reason=resp.abstain_reason or "",
                abstain_ok=abstain_ok,
                extra={"ambiguous_top3": ambiguous_hits, "retrieve_note": note},
            )
        )
        time.sleep(0.35)

    return results


def _print_results(title: str, rows: Sequence[RatioResult]) -> None:
    print(f"\n=== {title} ({len(rows)} cases) ===")
    for r in rows:
        gt = r.case.gt_status
        print(f"[{r.failure}] {r.case.query[:55]}")
        print(f"  rewritten: {r.rewritten!r}")
        print(f"  headcount_path={r.headcount_path} ratio_path={r.ratio_path} rerank={r.rerank_status}")
        print(f"  top1: {r.top1_preview!r}")
        print(
            f"  abstain={r.abstain_recommended} no_evidence={r.no_relevant_evidence} "
            f"conf={r.retrieval_confidence} reason={r.abstain_reason!r} ok={r.abstain_ok}"
        )
        if r.extra.get("ambiguous_top3"):
            print(f"  ambiguous_top3: {r.extra['ambiguous_top3']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=ROOT / "reports" / "korean_gender_ratio_baseline.json")
    args = parser.parse_args()

    _bootstrap()
    all_cases = PRIMARY_CASES + MINI_REGRESSION
    rows = eval_cases(all_cases)
    _print_results("primary", rows[: len(PRIMARY_CASES)])
    _print_results("mini_regression", rows[len(PRIMARY_CASES) :])

    blocked = sum(1 for r in rows if r.failure == "gt_blocked")
    abstain_ok = sum(1 for r in rows if r.abstain_ok)
    print(f"\nSummary: {blocked}/{len(rows)} gt_blocked (no clean GT to score pass/fail)")
    print(f"Abstain gate: {abstain_ok}/{len(rows)} cases abstain_ok (items kept + flags + all unanswerable)")

    payload = {
        "gt_audit": {
            "indexed_lane": "splits/full.jsonl (company_evidence only)",
            "musinsa_male_workforce_pct": "not_found",
            "musinsa_female_workforce_pct": "not_found",
            "golden_set_qt002": "dataset_issue",
            "ai_extracted_gender_metrics": "taxonomy stubs without numeric values; not indexed",
            "noise_false_positives": list(AMBIGUOUS_SNIPPETS),
        },
        "rows": [
            {
                "query": r.case.query,
                "group": r.case.group,
                "gt_status": r.case.gt_status,
                "expected_note": r.case.expected_note,
                "rewritten": r.rewritten,
                "bm25_query": r.bm25_query,
                "headcount_path": r.headcount_path,
                "ratio_path": r.ratio_path,
                "rerank_status": r.rerank_status,
                "top1_record_id": r.top1_record_id,
                "top1_preview": r.top1_preview,
                "failure": r.failure,
                "abstain_recommended": r.abstain_recommended,
                "no_relevant_evidence": r.no_relevant_evidence,
                "retrieval_confidence": r.retrieval_confidence,
                "abstain_reason": r.abstain_reason,
                "abstain_ok": r.abstain_ok,
                "extra": r.extra,
            }
            for r in rows
        ],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.json_out}")
    return 0 if abstain_ok == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
