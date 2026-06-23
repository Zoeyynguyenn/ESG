#!/usr/bin/env python3
"""Cross-role extraction hardening — re-run capability benchmark as regression gate."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.cross_role_extraction import alignment_failure_summary  # noqa: E402
from enterprise_docs.crossdoc_capability_benchmark import (  # noqa: E402
    CAPABILITY_METRICS,
    run_capability_benchmark,
)
from enterprise_docs.crossdoc_case_builder import all_capability_cases, write_capability_cases_jsonl  # noqa: E402
from enterprise_docs.value_equivalence import registry_snapshot  # noqa: E402

PRIOR_ARTIFACT = ROOT / "reports/enterprise_docs_crossdoc_core_capability_20260619-100639/summary.json"


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


def _mandatory_answers(
    bench: dict[str, Any],
    *,
    delta: dict[str, Any],
    alignment_matrix: dict[str, Any],
) -> dict[str, Any]:
    cm = bench.get("capability_metrics") or {}
    ff = bench.get("by_family_constructed") or {}

    best_family = None
    best_score = -1.0
    for fid, stats in ff.items():
        fs = float(stats.get("fusion_success_rate") or 0) + float(
            stats.get("classification_accuracy") or 0
        )
        if fs > best_score:
            best_score = fs
            best_family = fid

    extract_delta = delta.get("cross_role_extraction_alignment_rate") or {}
    extract_before = extract_delta.get("before")
    extract_after = extract_delta.get("after")
    extract_increased = (
        extract_after is not None
        and extract_before is not None
        and float(extract_after) > float(extract_before)
    )

    mismatch_counts = alignment_matrix.get("by_mismatch_type") or {}
    hardest = "none"
    if mismatch_counts:
        hardest = max(mismatch_counts.items(), key=lambda x: x[1])[0]

    fusion_rate = cm.get("evidence_fusion_success_rate")
    extract_rate = cm.get("cross_role_extraction_alignment_rate")
    fusion_fail_due = "extraction"
    if extract_rate and float(extract_rate) >= 0.5 and fusion_rate and float(fusion_rate) < 0.8:
        fusion_fail_due = "equivalence_or_aggregation"
    elif extract_rate and float(extract_rate) < 0.5:
        fusion_fail_due = "extraction"

    promo_rate = cm.get("single_source_to_multi_source_promotion_rate")
    promotion_ghost = promo_rate == 1.0 and fusion_rate is not None and float(fusion_rate) < 1.0

    return {
        "1_cross_role_extraction_alignment_increased": {
            "before": extract_before,
            "after": extract_after,
            "delta": extract_delta.get("delta"),
            "increased": extract_increased,
        },
        "2_hardest_mismatch_type": hardest,
        "3_fusion_fail_primary_cause": fusion_fail_due,
        "4_best_hardened_family": best_family,
        "5_promotion_ghost_remaining": {
            "promotion_rate": promo_rate,
            "fusion_rate": fusion_rate,
            "still_ghost": promotion_ghost,
            "note": "promotion now requires fusion_ok for expected multi-source cases",
        },
        "6_next_step_for_real_docs": (
            "Giữ constructed suite làm regression gate; tiếp tục harden mismatch còn lại; "
            "plug-in tài liệu thật bằng cách thêm natural cases — không rebuild pipeline"
        ),
    }


def _report(out_dir: Path, summary: dict[str, Any], answers: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Enterprise internal-doc — Cross-role extraction hardening",
            "",
            f"Artifact: `{out_dir.relative_to(ROOT)}`",
            "",
            "## Câu trả lời bắt buộc",
            "",
            json.dumps(answers, ensure_ascii=False, indent=2),
            "",
            "## Capability metrics delta vs prior benchmark",
            "",
            json.dumps(summary.get("capability_metrics_delta"), ensure_ascii=False, indent=2),
            "",
            "## Current capability metrics",
            "",
            json.dumps(summary.get("capability_metrics"), ensure_ascii=False, indent=2),
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = (args.out or (ROOT / f"reports/enterprise_docs_cross_role_hardening_{ts}")).resolve()

    cases_meta = write_capability_cases_jsonl()
    bench = run_capability_benchmark()
    prior_metrics = _load_prior_metrics()
    current_metrics = bench.get("capability_metrics") or {}
    delta = _metrics_delta(prior_metrics, current_metrics)
    alignment_matrix = alignment_failure_summary(bench.get("case_results") or [])
    answers = _mandatory_answers(bench, delta=delta, alignment_matrix=alignment_matrix)

    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "artifact": "enterprise_docs_cross_role_hardening",
        "timestamp": out_dir.name.split("_")[-1],
        "phase": "cross_role_extraction_hardening",
        "prior_artifact": "enterprise_docs_crossdoc_core_capability_20260619-100639",
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
    (out_dir / "alignment_failure_matrix.json").write_text(
        json.dumps(alignment_matrix, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "readiness_promotion_matrix.json").write_text(
        json.dumps(bench.get("promotion_matrix"), ensure_ascii=False, indent=2), encoding="utf-8"
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
