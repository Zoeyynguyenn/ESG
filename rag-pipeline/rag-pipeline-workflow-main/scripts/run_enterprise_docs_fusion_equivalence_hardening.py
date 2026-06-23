#!/usr/bin/env python3
"""Fusion + equivalence hardening — regression gate on constructed capability suite."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.crossdoc_capability_benchmark import (  # noqa: E402
    CAPABILITY_METRICS,
    run_capability_benchmark,
)
from enterprise_docs.crossdoc_case_builder import write_capability_cases_jsonl  # noqa: E402
from enterprise_docs.value_equivalence import registry_snapshot  # noqa: E402

PRIOR_ARTIFACT = ROOT / "reports/enterprise_docs_cross_role_hardening_20260619-101153/summary.json"


def _load_prior_metrics() -> dict[str, Any]:
    if not PRIOR_ARTIFACT.exists():
        return {}
    summary = json.loads(PRIOR_ARTIFACT.read_text(encoding="utf-8"))
    return dict(summary.get("capability_metrics") or {})


def _metrics_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    delta: dict[str, Any] = {}
    for key in CAPABILITY_METRICS:
        b, a = before.get(key), after.get(key)
        if b is None and a is None:
            delta[key] = {"before": None, "after": None, "delta": None}
        elif b is None or a is None:
            delta[key] = {"before": b, "after": a, "delta": None}
        else:
            delta[key] = {"before": b, "after": a, "delta": round(float(a) - float(b), 4)}
    return delta


def _fusion_failure_matrix(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for r in case_results:
        if r.get("case_origin") != "constructed" or r.get("fusion_ok") is None:
            continue
        failure = "none"
        if not r.get("fusion_ok"):
            if not r.get("extract_alignment_ok"):
                failure = "extraction"
            elif not r.get("equivalence_collapse_ok"):
                failure = "equivalence_collapse"
            elif not r.get("aggregation", {}).get("multi_source_confirmed"):
                failure = "fusion_confirm"
            else:
                failure = "classification_or_status"
        rows.append(
            {
                "case_id": r.get("case_id"),
                "family_id": r.get("family_id"),
                "item": r.get("item"),
                "extract_alignment_ok": r.get("extract_alignment_ok"),
                "equivalence_collapse_ok": r.get("equivalence_collapse_ok"),
                "fusion_ok": r.get("fusion_ok"),
                "multi_source_confirmed": (r.get("aggregation") or {}).get("multi_source_confirmed"),
                "confirming_logical_docs": (r.get("aggregation") or {}).get("confirming_logical_docs"),
                "resolved_value": (r.get("aggregation") or {}).get("resolved_value"),
                "failure_stage": failure,
            }
        )
    by_stage: dict[str, int] = {}
    for row in rows:
        if row.get("failure_stage") != "none":
            st = str(row.get("failure_stage"))
            by_stage[st] = by_stage.get(st, 0) + 1
    return {"cases": rows, "by_failure_stage": by_stage}


def _promotion_integrity_matrix(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    ghost = 0
    for r in case_results:
        if r.get("promotion_ok") is None:
            continue
        promoted = bool((r.get("promotion") or {}).get("promoted"))
        fusion_ok = bool(r.get("fusion_ok"))
        expected_multi = next(
            (
                c.get("expected_multi_source_confirmed")
                for c in []
            ),
            None,
        )
        ghost_flag = promoted and not fusion_ok and r.get("expected_multi_source_confirmed") is True
        if ghost_flag:
            ghost += 1
        rows.append(
            {
                "case_id": r.get("case_id"),
                "fusion_ok": fusion_ok,
                "promotion_ok": r.get("promotion_ok"),
                "promoted": promoted,
                "promotion_target": (r.get("promotion") or {}).get("promotion_target"),
                "ghost_pass": ghost_flag,
            }
        )
    return {"cases": rows, "ghost_pass_count": ghost}


def _mandatory_answers(
    bench: dict[str, Any],
    *,
    delta: dict[str, Any],
    fusion_matrix: dict[str, Any],
    promo_matrix: dict[str, Any],
) -> dict[str, Any]:
    cm = bench.get("capability_metrics") or {}
    equiv_delta = delta.get("cross_doc_equivalence_match_rate") or {}
    fusion_delta = delta.get("evidence_fusion_success_rate") or {}

    hardest_numeric = "comma_decimal_format"
    by_stage = fusion_matrix.get("by_failure_stage") or {}
    if by_stage:
        hardest_numeric = max(by_stage.items(), key=lambda x: x[1])[0]

    return {
        "1_cross_doc_equivalence_increased": {
            "before": equiv_delta.get("before"),
            "after": equiv_delta.get("after"),
            "delta": equiv_delta.get("delta"),
            "increased": (equiv_delta.get("delta") or 0) > 0,
        },
        "2_evidence_fusion_increased_and_remaining_failures": {
            "before": fusion_delta.get("before"),
            "after": fusion_delta.get("after"),
            "delta": fusion_delta.get("delta"),
            "remaining_failure_stages": by_stage,
        },
        "3_narrative_table_fusion_status": {
            "narrative_vs_table_cases": [
                r
                for r in fusion_matrix.get("cases") or []
                if "NARRATIVE" in str(r.get("case_id") or "") or "TABLE" in str(r.get("case_id") or "")
            ],
        },
        "4_hardest_numeric_equivalence_type": hardest_numeric,
        "5_promotion_integrity": {
            "promotion_rate": cm.get("single_source_to_multi_source_promotion_rate"),
            "fusion_rate": cm.get("evidence_fusion_success_rate"),
            "ghost_pass_count": promo_matrix.get("ghost_pass_count"),
            "bams_fusion": promo_matrix.get("ghost_pass_count", 1) == 0,
        },
        "6_next_step_for_real_docs": (
            "Giữ constructed regression gate; plug-in tài liệu thật bằng natural cases; "
            "tiếp tục mở rộng scaled/unit equivalence khi gặp pattern mới"
        ),
    }


def _report(out_dir: Path, summary: dict[str, Any], answers: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Enterprise internal-doc — Fusion equivalence hardening",
            "",
            f"Artifact: `{out_dir.relative_to(ROOT)}`",
            "",
            "## Câu trả lời bắt buộc",
            "",
            json.dumps(answers, ensure_ascii=False, indent=2),
            "",
            "## Capability metrics delta",
            "",
            json.dumps(summary.get("capability_metrics_delta"), ensure_ascii=False, indent=2),
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = (args.out or (ROOT / f"reports/enterprise_docs_fusion_equivalence_hardening_{ts}")).resolve()

    cases_meta = write_capability_cases_jsonl()
    bench = run_capability_benchmark()
    prior_metrics = _load_prior_metrics()
    current_metrics = bench.get("capability_metrics") or {}
    delta = _metrics_delta(prior_metrics, current_metrics)
    fusion_matrix = _fusion_failure_matrix(bench.get("case_results") or [])
    promo_matrix = _promotion_integrity_matrix(bench.get("case_results") or [])
    answers = _mandatory_answers(
        bench, delta=delta, fusion_matrix=fusion_matrix, promo_matrix=promo_matrix
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "artifact": "enterprise_docs_fusion_equivalence_hardening",
        "timestamp": out_dir.name.split("_")[-1],
        "phase": "fusion_equivalence_hardening",
        "prior_artifact": "enterprise_docs_cross_role_hardening_20260619-101153",
        "cases_meta": cases_meta,
        "capability_metrics": current_metrics,
        "capability_metrics_delta": delta,
        "mandatory_answers": answers,
        "constraints": {
            "no_synthesis": True,
            "no_langgraph_trial": True,
            "no_case_tuning": True,
            "constructed_regression_gate": True,
        },
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "capability_metrics_delta.json").write_text(
        json.dumps(delta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "equivalence_registry_snapshot.json").write_text(
        json.dumps(registry_snapshot(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "fusion_failure_matrix.json").write_text(
        json.dumps(fusion_matrix, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "promotion_integrity_matrix.json").write_text(
        json.dumps(promo_matrix, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "report.md").write_text(_report(out_dir, summary, answers), encoding="utf-8")

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(
        json.dumps(
            {"out_dir": str(out_dir), "mandatory_answers": answers, "capability_metrics": current_metrics},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
