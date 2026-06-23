#!/usr/bin/env python3
"""Ablation + holdout audit for KO headcount retrieval (no retrieval code changes)."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Sequence
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from eval_korean_metric_retrieval_regression import (  # noqa: E402
    EvalCase,
    MUSINSA_HEADCOUNT_CASES,
    _bootstrap,
    _classify_failure,
    _has_answer,
    _rank_in_hits,
    _rerank_status_from_note,
    _rewrite_miss,
)

HOLDOUT_CASES: List[EvalCase] = [
    EvalCase("무신사의 인력 규모는 어느 정도인가요?", "1891", "", "H"),
    EvalCase("이 회사 전체 임직원 규모를 알려주세요", "1891", "", "H"),
    EvalCase("해당 회사 고용 인원은 몇 명입니까?", "1891", "", "H"),
    EvalCase("무신사의 총 고용 규모는 몇 명인가요?", "1891", "", "H"),
    EvalCase("해당 기업의 사람 규모는 어느 정도인가요?", "1891", "", "H"),
    EvalCase("이 기업 종업원 수는 몇 명인가요?", "1891", "", "H"),
]

HOLDOUT_EXTENDED: List[EvalCase] = [
    EvalCase("이 회사의 전체 인력은 얼마나 되나요?", "1891", "", "HX"),
    EvalCase("해당 기업 종업원 규모는?", "1891", "", "HX"),
    EvalCase("무신사 고용 인원 규모", "1891", "", "HX"),
    EvalCase("무신사 전체 직원 규모는 어느 정도입니까?", "1891", "", "HX"),
    EvalCase("해당 회사의 근로자 규모는 몇 명인가요?", "1891", "", "HX"),
    EvalCase("이 기업 총 인력 규모", "1891", "", "HX"),
    EvalCase("무신사의 인원 규모는?", "1891", "", "HX"),
    EvalCase("해당 기업 고용 규모는 얼마입니까?", "1891", "", "HX"),
]

NON_HEADCOUNT_SANITY: List[EvalCase] = [
    EvalCase("무신사의 사외이사 수는 몇 명인가요?", "사외이사 3", "", "NH"),
    EvalCase("무신사의 이사회 규모는 어느 정도인가요?", "이사회", "", "NH"),
    EvalCase("무신사의 임원진 규모는 어느 정도인가요?", "임원진 7명", "", "NH"),
    EvalCase("이 회사 사외이사 인원은?", "사외이사 3", "", "NH"),
]

# Non-headcount metrics with GT in Musinsa package (not indexed separately).
OTHER_METRIC_CASES: List[EvalCase] = [
    EvalCase("무신사 사외이사는 몇 명인가요?", "사외이사 3", "rec_b8977fd8e7adeb1b", "M-board"),
    EvalCase("해당 기업의 사외이사 수는?", "사외이사 3", "", "M-board"),
    EvalCase("이 회사 사외이사 인원은?", "사외이사 3", "", "M-board"),
    EvalCase("무신사 임원진은 몇 명인가요?", "임원진 7명", "", "M-exec"),
    EvalCase("해당 기업 임원진 수는?", "임원진 7명", "", "M-exec"),
]

ABLATION_CONFIGS: Dict[str, Dict[str, bool]] = {
    "full_fix": {"rewrite": True, "synonym": True, "boost": True, "jina": True},
    "no_rewrite": {"rewrite": False, "synonym": True, "boost": True, "jina": True},
    "no_synonym_expansion": {"rewrite": True, "synonym": False, "boost": True, "jina": True},
    "no_headcount_boost": {"rewrite": True, "synonym": True, "boost": False, "jina": True},
    "no_jina": {"rewrite": True, "synonym": True, "boost": True, "jina": False},
}


@dataclass
class RunRow:
    config: str
    suite: str
    query: str
    group: str
    rewritten: str
    top1: bool
    top3: bool
    pool: bool
    bm25: bool
    pre_rank: int
    post_rank: int
    rerank_status: str
    failure: str


def _reset_runtime() -> None:
    import retrieval_v3 as r3
    from evidence_api.staging_config import reset_retrieval_runtime_caches

    reset_retrieval_runtime_caches()
    r3._bm25_index = None
    r3._reranker = None
    r3._rerank_status = "not_loaded"


@contextlib.contextmanager
def ablation_patches(flags: Dict[str, bool]) -> Iterator[None]:
  import korean_metric_retrieval_hints as kmh
  import evidence_api.query_rewrite as qr

  patches = []
  if not flags.get("rewrite", True):
      patches.append(
          patch.object(qr, "rewrite_query_for_company", lambda q, _cid, _ent: (q or "").strip())
      )
  if not flags.get("synonym", True):
      patches.append(patch.object(kmh, "expand_headcount_synonyms", lambda q: q))
  if not flags.get("boost", True):
      patches.append(
          patch.object(kmh, "apply_headcount_metric_boost", lambda _q, hits: hits)
      )
      patches.append(
          patch.object(kmh, "headcount_rerank_blend_alpha", lambda alpha: alpha)
      )

  old_jina = os.environ.get("RAG_RERANK_ENABLED")
  if not flags.get("jina", True):
      os.environ["RAG_RERANK_ENABLED"] = "false"
  else:
      os.environ["RAG_RERANK_ENABLED"] = "true"

  started = [p.start() for p in patches]
  try:
      yield
  finally:
      for p in patches:
          p.stop()
      if old_jina is None:
          os.environ.pop("RAG_RERANK_ENABLED", None)
      else:
          os.environ["RAG_RERANK_ENABLED"] = old_jina
      _reset_runtime()


def eval_suite(
    config_name: str,
    suite_name: str,
    cases: Sequence[EvalCase],
    flags: Dict[str, bool],
    *,
    company_id: str = "musinsa",
    pool: int = 64,
    top_k: int = 8,
    sleep_sec: float = 0.35,
) -> List[RunRow]:
    from evidence_api.query_rewrite import company_display_name, rewrite_query_for_company
    from evidence_api.schemas import RetrieveRequest
    from evidence_api.service import EvidenceRetrievalService
    from evidence_api.staging_config import (
        apply_company_env,
        company_registry,
        load_staging_config,
        reset_retrieval_runtime_caches,
    )
    from export_json_retrieval_hints import should_apply_export_json_boost
    from korean_metric_retrieval_hints import prepare_bm25_query
    import retrieval_v3 as r3
    from retrieval_v3 import (
        retrieve_bm25_lexical,
        retrieve_hybrid_dense_bm25,
        retrieve_hybrid_dense_bm25_rerank,
    )

    cfg = load_staging_config()
    entry = company_registry(cfg)[company_id]
    display = company_display_name(company_id, entry)
    apply_company_env(cfg, company_id, base_dir=ROOT)
    reset_retrieval_runtime_caches()
    r3._bm25_index = None
    r3._reranker = None

    rows: List[RunRow] = []
    svc = EvidenceRetrievalService()

    for case in cases:
        rewritten = rewrite_query_for_company(case.query, company_id, entry)
        bm25_q = prepare_bm25_query(rewritten, lane_expand=should_apply_export_json_boost())
        bm25_hits, _ = retrieve_bm25_lexical(bm25_q, pool, pool)
        hybrid_pool, _ = retrieve_hybrid_dense_bm25(rewritten, pool, pool)
        reranked, note = retrieve_hybrid_dense_bm25_rerank(rewritten, pool, top_k)

        pool_has = any(_has_answer(h.text, case.expected_snippet) for h in hybrid_pool)
        bm25_has = any(_has_answer(h.text, case.expected_snippet) for h in bm25_hits)
        pre_rank = _rank_in_hits(hybrid_pool, case.expected_snippet)
        post_rank = _rank_in_hits(reranked, case.expected_snippet)

        resp = svc.retrieve(RetrieveRequest(query=case.query, company_id=company_id, top_k=top_k))
        top1 = bool(resp.items) and _has_answer(resp.items[0].text or "", case.expected_snippet)
        top3 = any(_has_answer(it.text or "", case.expected_snippet) for it in resp.items[:3])

        failure = _classify_failure(
            case, rewritten, display, pool_has, bm25_has, False, pre_rank, top1
        )
        if _rewrite_miss(case.query, rewritten, display) and failure == "pass":
            failure = "rewrite_miss"

        rows.append(
            RunRow(
                config=config_name,
                suite=suite_name,
                query=case.query,
                group=case.group,
                rewritten=rewritten,
                top1=top1,
                top3=top3,
                pool=pool_has,
                bm25=bm25_has,
                pre_rank=pre_rank,
                post_rank=post_rank,
                rerank_status=_rerank_status_from_note(note),
                failure=failure,
            )
        )
        if flags.get("jina", True):
            time.sleep(sleep_sec)

    return rows


def _summarize(rows: Sequence[RunRow]) -> Dict[str, Any]:
    n = len(rows)
    return {
        "cases": n,
        "top1": sum(1 for r in rows if r.top1),
        "top1_pct": round(100 * sum(1 for r in rows if r.top1) / n, 1) if n else 0,
        "top3": sum(1 for r in rows if r.top3),
        "top3_pct": round(100 * sum(1 for r in rows if r.top3) / n, 1) if n else 0,
        "failures": {},
    }


def _add_failures(summary: Dict[str, Any], rows: Sequence[RunRow]) -> None:
    for r in rows:
        if r.failure != "pass":
            summary["failures"][r.failure] = summary["failures"].get(r.failure, 0) + 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=ROOT / "reports" / "korean_metric_ablation_results.json")
    parser.add_argument("--configs", nargs="*", default=list(ABLATION_CONFIGS))
    parser.add_argument("--skip-other-metrics", action="store_true")
    args = parser.parse_args()

    _bootstrap()

    all_rows: List[RunRow] = []
    summary_by_config: Dict[str, Dict[str, Any]] = {}

    suites = [
        ("regression16", MUSINSA_HEADCOUNT_CASES),
        ("holdout6", HOLDOUT_CASES),
    ]
    if not args.skip_other_metrics:
        suites.append(("other_metric5", OTHER_METRIC_CASES))

    for config_name in args.configs:
        if config_name not in ABLATION_CONFIGS:
            print(f"SKIP unknown config: {config_name}")
            continue
        flags = ABLATION_CONFIGS[config_name]
        print(f"\n=== {config_name} {flags} ===")
        config_summary: Dict[str, Any] = {}
        with ablation_patches(flags):
            for suite_name, cases in suites:
                rows = eval_suite(config_name, suite_name, cases, flags)
                all_rows.extend(rows)
                s = _summarize(rows)
                _add_failures(s, rows)
                config_summary[suite_name] = s
                print(
                    f"  {suite_name}: top1={s['top1']}/{s['cases']} ({s['top1_pct']}%) "
                    f"top3={s['top3']}/{s['cases']} ({s['top3_pct']}%)"
                )
                if s["failures"]:
                    print(f"    failures: {s['failures']}")
        summary_by_config[config_name] = config_summary

    payload = {
        "summary_by_config": summary_by_config,
        "rows": [asdict(r) for r in all_rows],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
