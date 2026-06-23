#!/usr/bin/env python3
"""Holdout handoff-readiness enablement round (routing + confidence + packaging)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.confidence_policy import export_confidence_policy  # noqa: E402
from enterprise_docs.handoff_readiness import (  # noqa: E402
    audit_holdout_routing_alignment,
    run_handoff_readiness_matrix,
)

PRIOR = ROOT / "reports/enterprise_docs_handoff_readiness_20260618-165702/summary.json"
PILOT_FAMILIES = ("employee_headcount", "environment_ghg", "governance")


def _system_decision(result: dict[str, Any], prior: dict[str, Any] | None) -> dict[str, Any]:
    by_co = result.get("by_company") or {}
    by_family = result.get("by_family") or {}

    holdout_promoted: dict[str, int] = {}
    for row in result.get("matrix") or []:
        if row.get("company_id") not in ("hanssem", "musinsa"):
            continue
        fid = row.get("family_id")
        if fid in PILOT_FAMILIES and row.get("promoted"):
            holdout_promoted[fid] = holdout_promoted.get(fid, 0) + 1

    holdout_ready = [fid for fid in PILOT_FAMILIES if holdout_promoted.get(fid, 0) > 0]
    holdout_cases = [r for r in (result.get("matrix") or []) if r.get("company_id") in ("hanssem", "musinsa")]
    holdout_n = max(1, len(holdout_cases))
    holdout_promoted_n = sum(1 for r in holdout_cases if r.get("promoted"))

    prior_holdout_promo = None
    if prior:
        prior_holdout_promo = (prior.get("system_decision") or {}).get("holdout_promotion_rate")

    limited_prep_ok = len(holdout_ready) >= 1 and all(
        (by_family.get(fid) or {}).get("handoff_candidate_count", 0) > 0 for fid in holdout_ready
    )

    return {
        "phase": "holdout_handoff_enablement",
        "ready_for_limited_langgraph_handoff": False,
        "ready_for_limited_langgraph_handoff_preparation": limited_prep_ok,
        "not_ready_for_synthesis": True,
        "not_ready_for_langgraph_trial": True,
        "holdout_promoted_families": holdout_ready,
        "holdout_promoted_by_family": holdout_promoted,
        "holdout_promotion_rate": round(holdout_promoted_n / holdout_n, 4),
        "holdout_promotion_delta_vs_prior": (
            round(holdout_promoted_n / holdout_n - prior_holdout_promo, 4)
            if prior_holdout_promo is not None
            else None
        ),
        "holdout_promoted_family_count": len(holdout_ready),
        "demo_promoted_count": (by_co.get("demo_company") or {}).get("promoted_count"),
        "gaps_before_trial": [
            g
            for g in [
                "holdout_promotion_zero" if not holdout_ready else None,
                "musinsa_environment_corpus_gap" if not holdout_promoted.get("environment_ghg") else None,
                "confidence_policy_calibration",
                "review_owner_rule_enforcement",
            ]
            if g
        ],
    }


def _promotion_delta(prior: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    if not prior:
        return {"note": "no_prior_artifact"}
    p_co = prior.get("by_company") or {}
    c_co = current.get("by_company") or {}
    return {
        "demo_promoted_delta": (c_co.get("demo_company") or {}).get("promoted_count", 0)
        - (p_co.get("demo_company") or {}).get("promoted_count", 0),
        "hanssem_promoted_delta": (c_co.get("hanssem") or {}).get("promoted_count", 0)
        - (p_co.get("hanssem") or {}).get("promoted_count", 0),
        "musinsa_promoted_delta": (c_co.get("musinsa") or {}).get("promoted_count", 0)
        - (p_co.get("musinsa") or {}).get("promoted_count", 0),
        "holdout_readiness_after_before": {
            "hanssem": {
                "before": (p_co.get("hanssem") or {}).get("readiness_after"),
                "after": (c_co.get("hanssem") or {}).get("readiness_after"),
            },
            "musinsa": {
                "before": (p_co.get("musinsa") or {}).get("readiness_after"),
                "after": (c_co.get("musinsa") or {}).get("readiness_after"),
            },
        },
    }


def write_artifacts(
    out_dir: Path,
    *,
    result: dict[str, Any],
    routing_audit: dict[str, Any],
    prior: dict[str, Any] | None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    system = _system_decision(result, prior)
    delta = _promotion_delta(prior, result)
    confidence = export_confidence_policy()

    summary = {
        "artifact": "enterprise_docs_holdout_handoff_enablement",
        "timestamp": out_dir.name.split("_")[-1],
        "pilot_families": list(PILOT_FAMILIES),
        "by_company": result.get("by_company"),
        "by_family": {k: result.get("by_family", {}).get(k) for k in PILOT_FAMILIES},
        "by_promotion": result.get("by_promotion"),
        "system_decision": system,
        "metric_types": confidence.get("metric_types"),
        "constraints": {
            "no_synthesis": True,
            "no_langgraph_trial": True,
            "no_case_tuning": True,
        },
    }

    matrix_payload = {
        "by_company": result.get("by_company"),
        "by_family": result.get("by_family"),
        "by_promotion": result.get("by_promotion"),
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "handoff_readiness_matrix.json").write_text(
        json.dumps(matrix_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "promotion_delta.json").write_text(
        json.dumps(delta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "confidence_policy.json").write_text(
        json.dumps(confidence, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "routing_alignment_audit.json").write_text(
        json.dumps(routing_audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    with (out_dir / "handoff_samples.jsonl").open("w", encoding="utf-8") as f:
        for row in result.get("matrix") or []:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    report = [
        "# Enterprise internal-doc — Holdout handoff enablement",
        "",
        f"Artifact: `{out_dir.relative_to(ROOT)}`",
        "",
        "## Routing alignment",
        "",
        json.dumps(routing_audit.get("mismatches_found"), ensure_ascii=False, indent=2),
        "",
        f"- alignment_gap_rate: **{routing_audit.get('alignment_gap_rate')}** (heuristic proxy)",
        "",
        "## Confidence policy",
        "",
        json.dumps(confidence.get("rules"), ensure_ascii=False, indent=2),
        "",
        "## Results by company",
        "",
        json.dumps(result.get("by_company"), ensure_ascii=False, indent=2),
        "",
        "## Pilot families",
        "",
        json.dumps(summary.get("by_family"), ensure_ascii=False, indent=2),
        "",
        "## System decision",
        "",
        json.dumps(system, ensure_ascii=False, indent=2),
        "",
        "## Promotion delta vs prior",
        "",
        json.dumps(delta, ensure_ascii=False, indent=2),
        "",
    ]
    (out_dir / "report.md").write_text("\n".join(report), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = (args.out or (ROOT / f"reports/enterprise_docs_holdout_handoff_enablement_{ts}")).resolve()

    prior = json.loads(PRIOR.read_text(encoding="utf-8")) if PRIOR.exists() else None
    routing_audit = audit_holdout_routing_alignment()
    result = run_handoff_readiness_matrix(include_demo=True, demo_family_filter=True)
    write_artifacts(out_dir, result=result, routing_audit=routing_audit, prior=prior)
    print(json.dumps({"out_dir": str(out_dir), "system": _system_decision(result, prior)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
