#!/usr/bin/env python3
"""Gate eval: regression + holdout + extended holdout + non-headcount leakage check."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from eval_korean_metric_ablation import HOLDOUT_CASES, eval_suite  # noqa: E402
from eval_korean_metric_retrieval_regression import (  # noqa: E402
    EvalCase,
    MUSINSA_HEADCOUNT_CASES,
    _bootstrap,
)

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

FULL_FIX = {"rewrite": True, "synonym": True, "boost": True, "jina": True}


@dataclass
class GateSummary:
    suite: str
    top1: int
    cases: int
    top1_pct: float
    top3: int
    top3_pct: float


def _summarize(suite: str, rows: Sequence[Any]) -> GateSummary:
    n = len(rows)
    t1 = sum(1 for r in rows if r.top1)
    t3 = sum(1 for r in rows if r.top3)
    return GateSummary(
        suite=suite,
        top1=t1,
        cases=n,
        top1_pct=round(100 * t1 / n, 1) if n else 0,
        top3=t3,
        top3_pct=round(100 * t3 / n, 1) if n else 0,
    )


def _leakage_check(rows: Sequence[Any]) -> List[Dict[str, Any]]:
    from korean_metric_retrieval_hints import is_headcount_metric_query, is_non_headcount_metric_query

    out = []
    for r in rows:
        out.append(
            {
                "query": r.query,
                "headcount_triggered": is_headcount_metric_query(r.query),
                "non_headcount_guard": is_non_headcount_metric_query(r.query),
                "top1": r.top1,
                "failure": r.failure,
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path, default=ROOT / "reports" / "korean_headcount_gate_results.json")
    args = parser.parse_args()

    _bootstrap()

    from eval_korean_metric_ablation import ablation_patches

    suites = [
        ("regression16", MUSINSA_HEADCOUNT_CASES),
        ("holdout6", HOLDOUT_CASES),
        ("holdout_extended8", HOLDOUT_EXTENDED),
        ("non_headcount_sanity4", NON_HEADCOUNT_SANITY),
    ]

    all_rows = []
    summaries: Dict[str, Any] = {}

    with ablation_patches(FULL_FIX):
        for name, cases in suites:
            rows = eval_suite("full_fix", name, cases, FULL_FIX)
            all_rows.extend(rows)
            summaries[name] = asdict(_summarize(name, rows))
            s = summaries[name]
            print(f"{name}: top1={s['top1']}/{s['cases']} ({s['top1_pct']}%) top3={s['top3']}/{s['cases']}")
            time.sleep(0.2)

    sanity_rows = [r for r in all_rows if r.suite == "non_headcount_sanity4"]
    leakage = _leakage_check(sanity_rows)
    triggered = sum(1 for x in leakage if x["headcount_triggered"])
    print(f"\nNon-headcount leakage: headcount_triggered={triggered}/{len(leakage)}")
    for item in leakage:
        print(f"  {item['query'][:45]} -> triggered={item['headcount_triggered']}")

    payload = {
        "summaries": summaries,
        "leakage": leakage,
        "rows": [asdict(r) for r in all_rows],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {args.json_out}")

    reg = summaries["regression16"]
    hold = summaries["holdout6"]
    ok = reg["top1"] == reg["cases"] and hold["top1"] >= 5
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
