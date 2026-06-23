#!/usr/bin/env python3
"""Regression eval: Korean metric/headcount retrieval generalization (noise corpus kept)."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

GENERIC_PATTERN = re.compile(r"해당\s*기업|해당\s*회사|이\s*회사|이\s*기업")


@dataclass
class EvalCase:
    query: str
    expected_snippet: str
    expected_record_id: str = ""
    group: str = ""


@dataclass
class EvalResult:
    case: EvalCase
    rewritten: str
    top1_has_answer: bool
    top3_has_answer: bool
    pool_has_answer: bool
    bm25_has_answer: bool
    dense_has_answer: bool
    pre_rerank_rank: int  # 0 = not in pool
    post_rerank_rank: int  # 0 = not in top_k
    top1_record_id: str
    top1_preview: str
    rerank_status: str
    failure: str = ""
    extra: dict = field(default_factory=dict)


MUSINSA_HEADCOUNT_CASES: List[EvalCase] = [
    # A — paraphrase
    EvalCase("해당 기업의 총 구성원 수는 몇 명인가요?", "1891", "rec_27e2235c5c45f84a", "A"),
    EvalCase("해당 기업의 구성원 수는 몇 명인가요?", "1891", "rec_27e2235c5c45f84a", "A"),
    EvalCase("해당 회사의 총 인원은 몇 명인가요?", "1891", "rec_27e2235c5c45f84a", "A"),
    EvalCase("이 회사의 임직원 수는 몇 명인가요?", "1891", "rec_27e2235c5c45f84a", "A"),
    EvalCase("무신사의 총 구성원 수는 몇 명인가요?", "1891", "rec_27e2235c5c45f84a", "A"),
    EvalCase("무신사 임직원은 몇 명인가요?", "1891", "rec_27e2235c5c45f84a", "A"),
    EvalCase("무신사의 직원 수는 몇 명인가요?", "1891", "rec_27e2235c5c45f84a", "A"),
    EvalCase("무신사의 전체 인원은 몇 명인가요?", "1891", "rec_27e2235c5c45f84a", "A"),
    # B — generic short forms
    EvalCase("해당 기업 직원 수는?", "1891", "rec_27e2235c5c45f84a", "B"),
    EvalCase("해당 회사 인원은 몇 명인가요?", "1891", "rec_27e2235c5c45f84a", "B"),
    EvalCase("이 기업의 임직원 규모는 어느 정도인가요?", "1891", "rec_27e2235c5c45f84a", "B"),
    EvalCase("이 회사 사람 수는 몇 명입니까?", "1891", "rec_27e2235c5c45f84a", "B"),
    # C — unit / synonym sensitivity
    EvalCase("해당 기업 구성원은 몇 명", "1891", "rec_27e2235c5c45f84a", "C"),
    EvalCase("해당 회사 총 직원", "1891", "rec_27e2235c5c45f84a", "C"),
    EvalCase("이 회사 근로자 수는?", "1891", "rec_27e2235c5c45f84a", "C"),
    EvalCase("무신사 인원", "1891", "rec_27e2235c5c45f84a", "C"),
]


def _bootstrap() -> None:
    from evidence_api.env_bootstrap import load_repo_dotenv

    load_repo_dotenv()


def _has_answer(text: str, snippet: str) -> bool:
    return snippet in (text or "")


def _rewrite_miss(query: str, rewritten: str, display: str) -> bool:
    if GENERIC_PATTERN.search(rewritten):
        return True
    if GENERIC_PATTERN.search(query) and display not in rewritten:
        return True
    return False


def _rank_in_hits(hits: Sequence[Any], snippet: str) -> int:
    for i, h in enumerate(hits, start=1):
        if _has_answer(h.text, snippet):
            return i
    return 0


def _rerank_status_from_note(note: str) -> str:
    if "jina_api" in note:
        return "jina_api"
    if "fallback" in note:
        return "fallback"
    if "disabled" in note:
        return "disabled"
    return note.split(";")[-1] if note else "unknown"


def _classify_failure(
    case: EvalCase,
    rewritten: str,
    display: str,
    pool_has: bool,
    bm25_has: bool,
    dense_has: bool,
    pre_rank: int,
    top1_has: bool,
) -> str:
    if top1_has:
        return "pass"
    if _rewrite_miss(case.query, rewritten, display):
        return "rewrite_miss"
    if not pool_has:
        if not bm25_has and not dense_has:
            return "answerable_chunk_not_in_top_pool"
        if not bm25_has:
            return "bm25_recall_weak"
        return "answerable_chunk_not_in_top_pool"
    if pre_rank and pre_rank <= 3:
        return "rerank_failed_to_promote"
    if not bm25_has:
        return "bm25_recall_weak"
    if dense_has and not bm25_has:
        return "dense_noise_win"
    return "rerank_failed_to_promote"


def eval_company(
    company_id: str,
    cases: Sequence[EvalCase],
    pool: int = 64,
    top_k: int = 8,
) -> List[EvalResult]:
    from evidence_api.query_rewrite import company_display_name, rewrite_query_for_company
    from evidence_api.record_catalog import RecordCatalog
    from evidence_api.schemas import RetrieveRequest
    from evidence_api.service import EvidenceRetrievalService
    from evidence_api.staging_config import (
        apply_company_env,
        company_registry,
        load_staging_config,
        package_jsonl_paths,
        reset_retrieval_runtime_caches,
    )
    import retrieval_v3 as r3
    from export_json_retrieval_hints import should_apply_export_json_boost
    from korean_metric_retrieval_hints import prepare_bm25_query
    from retrieval_v3 import (
        retrieve_bm25_lexical,
        retrieve_hybrid_dense_bm25,
        retrieve_hybrid_dense_bm25_rerank,
        retrieve_semantic_dense,
    )

    cfg = load_staging_config()
    entry = company_registry(cfg)[company_id]
    display = company_display_name(company_id, entry)
    stack = cfg["stack"]
    mode = EvidenceRetrievalService._stack_retrieval_mode(stack)

    apply_company_env(cfg, company_id, base_dir=ROOT)
    reset_retrieval_runtime_caches()
    r3._bm25_index = None

    split = entry.get("record_split", "full")
    paths = package_jsonl_paths(ROOT, entry["package"], split)
    catalog = RecordCatalog(paths)

    results: List[EvalResult] = []
    for case in cases:
        rewritten = rewrite_query_for_company(case.query, company_id, entry)
        bm25_q = prepare_bm25_query(rewritten, lane_expand=should_apply_export_json_boost())

        bm25_hits, bm25_note = retrieve_bm25_lexical(bm25_q, pool, pool)
        dense_hits, _ = retrieve_semantic_dense(rewritten, pool, pool)
        hybrid_pool, _ = retrieve_hybrid_dense_bm25(rewritten, pool, pool)
        reranked, note = retrieve_hybrid_dense_bm25_rerank(rewritten, pool, top_k)

        bm25_has = any(_has_answer(h.text, case.expected_snippet) for h in bm25_hits)
        dense_has = any(_has_answer(h.text, case.expected_snippet) for h in dense_hits)
        pool_has = any(_has_answer(h.text, case.expected_snippet) for h in hybrid_pool)
        pre_rank = _rank_in_hits(hybrid_pool, case.expected_snippet)
        post_rank = _rank_in_hits(reranked, case.expected_snippet)

        top3_has = any(_has_answer(h.text, case.expected_snippet) for h in reranked[:3])
        top1_has = bool(reranked) and _has_answer(reranked[0].text, case.expected_snippet)

        # Service path for record_id / source alignment
        svc = EvidenceRetrievalService()
        resp = svc.retrieve(RetrieveRequest(query=case.query, company_id=company_id, top_k=top_k))
        if resp.items:
            svc_top1 = resp.items[0]
            top1_record_id = svc_top1.record_id or ""
            top1_preview = (svc_top1.text or "")[:72].replace("\n", " ")
            svc_top1_has = _has_answer(svc_top1.text or "", case.expected_snippet)
            svc_top3_has = any(_has_answer(it.text or "", case.expected_snippet) for it in resp.items[:3])
            top1_has = svc_top1_has
            top3_has = svc_top3_has
        else:
            top1_record_id = ""
            top1_preview = ""

        failure = _classify_failure(
            case, rewritten, display, pool_has, bm25_has, dense_has, pre_rank, top1_has
        )

        results.append(
            EvalResult(
                case=case,
                rewritten=rewritten,
                top1_has_answer=top1_has,
                top3_has_answer=top3_has,
                pool_has_answer=pool_has,
                bm25_has_answer=bm25_has,
                dense_has_answer=dense_has,
                pre_rerank_rank=pre_rank,
                post_rerank_rank=post_rank,
                top1_record_id=top1_record_id,
                top1_preview=top1_preview,
                rerank_status=_rerank_status_from_note(note),
                failure=failure,
                extra={
                    "bm25_query": bm25_q,
                    "bm25_note": bm25_note,
                    "pool_size": len(hybrid_pool),
                    "bm25_rank": _rank_in_hits(bm25_hits, case.expected_snippet),
                    "dense_rank": _rank_in_hits(dense_hits, case.expected_snippet),
                    "post_rerank_rank": post_rank,
                    "retrieve_note": note,
                    "mode": mode,
                },
            )
        )
        # Jina rate limit courtesy
        time.sleep(0.5)

    return results


def _print_table(company_id: str, results: Sequence[EvalResult]) -> None:
    print(f"\n=== {company_id} ({len(results)} cases) ===")
    header = (
        f"{'grp':<3} {'top1':<4} {'top3':<4} {'pool':<4} {'bm25':<4} "
        f"{'pre#':<4} {'post#':<5} {'rerank':<12} {'fail':<28} query"
    )
    print(header)
    print("-" * len(header) + "-" * 40)
    for r in results:
        q_short = r.case.query[:42] + ("…" if len(r.case.query) > 42 else "")
        print(
            f"{r.case.group:<3} "
            f"{'Y' if r.top1_has_answer else 'N':<4} "
            f"{'Y' if r.top3_has_answer else 'N':<4} "
            f"{'Y' if r.pool_has_answer else 'N':<4} "
            f"{'Y' if r.bm25_has_answer else 'N':<4} "
            f"{r.pre_rerank_rank or '-':<4} "
            f"{r.post_rerank_rank or '-':<5} "
            f"{r.rerank_status:<12} "
            f"{r.failure:<28} "
            f"{q_short}"
        )

    print("\n--- detail (failures and rewrites) ---")
    for r in results:
        mark = "PASS" if r.top1_has_answer else "FAIL"
        print(f"\n[{mark}] {r.case.group} | {r.case.query}")
        print(f"  rewritten: {r.rewritten!r}")
        print(f"  top1_record_id: {r.top1_record_id!r}  preview: {r.top1_preview!r}")
        if not r.top1_has_answer:
            print(
                f"  pool={r.pool_has_answer} bm25={r.bm25_has_answer} dense={r.dense_has_answer} "
                f"pre_rerank_rank={r.pre_rerank_rank} failure={r.failure}"
            )
            print(f"  bm25_rank={r.extra.get('bm25_rank')} dense_rank={r.extra.get('dense_rank')}")


def _summary(results: Sequence[EvalResult]) -> dict[str, Any]:
    n = len(results)
    top1 = sum(1 for r in results if r.top1_has_answer)
    top3 = sum(1 for r in results if r.top3_has_answer)
    failures: dict[str, int] = {}
    for r in results:
        if r.failure != "pass":
            failures[r.failure] = failures.get(r.failure, 0) + 1
    return {
        "cases": n,
        "top1_pass": top1,
        "top1_pct": round(100 * top1 / n, 1) if n else 0,
        "top3_pass": top3,
        "top3_pct": round(100 * top3 / n, 1) if n else 0,
        "failures_by_class": failures,
        "jina_api_count": sum(1 for r in results if r.rerank_status == "jina_api"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", default="musinsa", choices=["musinsa", "rayshion", "hanssem", "all"])
    parser.add_argument("--json-out", type=Path, help="Write full results JSON")
    args = parser.parse_args()

    _bootstrap()

    from evidence_api.service import EvidenceRetrievalService

    svc = EvidenceRetrievalService()
    companies = ["musinsa", "rayshion", "hanssem"] if args.company == "all" else [args.company]

    all_results: dict[str, List[EvalResult]] = {}
    for cid in companies:
        if not svc.is_indexed(cid):
            print(f"SKIP {cid}: index not ready (prebuild --company {cid} --force)")
            continue
        cases = MUSINSA_HEADCOUNT_CASES if cid == "musinsa" else []
        if not cases:
            print(f"SKIP {cid}: no regression cases defined (no clear GT in package)")
            continue
        all_results[cid] = eval_company(cid, cases)
        _print_table(cid, all_results[cid])
        s = _summary(all_results[cid])
        print(f"\nSummary {cid}: top1={s['top1_pass']}/{s['cases']} ({s['top1_pct']}%) "
              f"top3={s['top3_pass']}/{s['cases']} ({s['top3_pct']}%) "
              f"jina_api={s['jina_api_count']}/{s['cases']}")
        if s["failures_by_class"]:
            print(f"  failures: {s['failures_by_class']}")

    if args.json_out and all_results:
        payload = {
            cid: [
                {
                    "query": r.case.query,
                    "group": r.case.group,
                    "expected_snippet": r.case.expected_snippet,
                    "expected_record_id": r.case.expected_record_id,
                    "rewritten": r.rewritten,
                    "top1_has_answer": r.top1_has_answer,
                    "top3_has_answer": r.top3_has_answer,
                    "pool_has_answer": r.pool_has_answer,
                    "bm25_has_answer": r.bm25_has_answer,
                    "dense_has_answer": r.dense_has_answer,
                    "pre_rerank_rank": r.pre_rerank_rank,
                    "post_rerank_rank": r.post_rerank_rank,
                    "top1_record_id": r.top1_record_id,
                    "fail_kind": r.failure,
                    "rerank_status": r.rerank_status,
                    "failure": r.failure,
                    "extra": r.extra,
                }
                for r in res
            ]
            for cid, res in all_results.items()
        }
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nWrote {args.json_out}")

    # Exit non-zero if musinsa below suggested bar
    mus = all_results.get("musinsa", [])
    if mus:
        s = _summary(mus)
        if s["top1_pct"] < 80 or s["top3_pct"] < 100:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
