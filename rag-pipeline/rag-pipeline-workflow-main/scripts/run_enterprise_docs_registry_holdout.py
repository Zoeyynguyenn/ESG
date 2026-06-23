#!/usr/bin/env python3
"""Registry abstraction completion + holdout extraction round."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.family_generalization import summarize_holdout_by_family
from enterprise_docs.holdout_harness import run_holdout_matrix
from enterprise_docs.registry_migration_audit import export_migration_audit
from enterprise_docs.reusability_audit import analyze_reusability

PRIOR_BASELINE = ROOT / "reports/enterprise_docs_abstraction_holdout_20260618-155302/summary.json"
FRAMEWORK_BASELINE = ROOT / "reports/enterprise_docs_framework_20260618-152811/summary.json"


def _system_decision_gate(
    migration: dict[str, Any],
    holdout: dict[str, Any],
    family_view: dict[str, Any],
    prior: dict[str, Any] | None,
) -> dict[str, Any]:
    by_co = holdout.get("by_company") or {}
    h_ret = (by_co.get("hanssem") or {}).get("retrieval_feasible_rate", 0.0)
    m_ret = (by_co.get("musinsa") or {}).get("retrieval_feasible_rate", 0.0)
    h_ext = (by_co.get("hanssem") or {}).get("extraction_feasible_rate", 0.0)
    m_ext = (by_co.get("musinsa") or {}).get("extraction_feasible_rate", 0.0)
    ext_avg = (h_ext + m_ext) / 2

    prior_ext = None
    if prior:
        pb = prior.get("holdout_summary", {}).get("by_company") or {}
        prior_ext = (
            (pb.get("hanssem") or {}).get("extraction_feasible_rate", 0)
            + (pb.get("musinsa") or {}).get("extraction_feasible_rate", 0)
        ) / 2

    gov = (family_view.get("families") or {}).get("governance") or {}
    handoff_families = [
        fid
        for fid, spec in (family_view.get("families") or {}).items()
        if spec.get("handoff_candidate")
        and spec.get("reusability_level") in ("reusable_holdout", "retrieval_only")
        and spec.get("extraction_feasible_rate", 0) >= 0.5
    ]

    weakest = family_view.get("weakest_family")
    if gov.get("extraction_feasible_rate", 0) >= 0.4:
        weakest = family_view.get("weakest_family")

    return {
        "ready_for_holdout_expansion": h_ret >= 0.75 and m_ret >= 0.75,
        "ready_for_limited_langgraph_handoff": bool(handoff_families),
        "not_ready_for_synthesis": True,
        "requires_more_registry_abstraction": migration["counts"].get("partially_registry_driven", 0) > 0,
        "handoff_candidate_families": handoff_families,
        "pilot_lock_families": ["financial"],
        "holdout_retrieval_hanssem": h_ret,
        "holdout_retrieval_musinsa": m_ret,
        "holdout_extraction_avg": round(ext_avg, 4),
        "holdout_extraction_delta_vs_prior": round(ext_avg - prior_ext, 4) if prior_ext is not None else None,
        "governance_extraction_rate": gov.get("extraction_feasible_rate"),
        "governance_still_weakest": weakest == "governance",
        "weakest_family": weakest,
        "synthesis_gate_distance": {
            "current_quant_gate_estimate": 0.23,
            "target_quant_gate": 0.6,
            "holdout_extraction_target": 0.5,
            "holdout_extraction_gap": round(max(0, 0.5 - ext_avg), 4),
        },
        "priority_next": (
            "holdout_extraction_by_family"
            if ext_avg < 0.45
            else "limited_langgraph_handoff_prep"
            if handoff_families
            else "registry_abstraction_completion"
        ),
    }


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    mig = payload["registry_migration_audit"]
    hold = payload["holdout_summary"]
    fam = payload["family_generalization"]
    gate = payload["system_decision_gate"]
    delta = payload.get("baseline_delta") or {}

    lines = [
        "# Enterprise Internal-Doc — Registry + Holdout Extraction Round",
        "",
        f"Generated: {payload['timestamp']}",
        "",
        "## Registry migration",
        "",
        f"- Already registry-driven: **{mig['counts']['already_registry_driven']}** (was 8)",
        f"- Partially registry-driven: **{mig['counts']['partially_registry_driven']}** (was 5)",
        f"- Still code-driven: **{mig['counts']['still_code_driven']}** (was 1)",
        "",
        "## Holdout vs prior round",
        "",
        f"- Extraction avg: **{gate['holdout_extraction_avg']}** (delta {gate.get('holdout_extraction_delta_vs_prior')})",
        f"- Hanssem retrieval: **{gate['holdout_retrieval_hanssem']}** (delta {delta.get('hanssem_retrieval_delta')})",
        f"- Governance extraction: **{gate.get('governance_extraction_rate')}**",
        f"- Governance still weakest: **{gate.get('governance_still_weakest')}**",
        "",
        "## Family summary",
        "",
    ]
    for fid, spec in sorted((fam.get("families") or {}).items()):
        lines.append(
            f"- **{fid}**: retrieval={spec.get('retrieval_feasible_rate')}, "
            f"extraction={spec.get('extraction_feasible_rate')}, "
            f"tier={spec.get('reusability_level')}"
        )

    lines.extend([
        "",
        "## System gates",
        "",
        f"- `ready_for_holdout_expansion`: **{gate['ready_for_holdout_expansion']}**",
        f"- `ready_for_limited_langgraph_handoff`: **{gate['ready_for_limited_langgraph_handoff']}**",
        f"- `not_ready_for_synthesis`: **{gate['not_ready_for_synthesis']}**",
        f"- Handoff candidates: {gate.get('handoff_candidate_families') or 'none'}",
        f"- Synthesis gap (holdout extraction): **{gate['synthesis_gate_distance']['holdout_extraction_gap']}**",
        f"- Priority next: **{gate['priority_next']}**",
        "",
        payload.get("conclusion", ""),
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports-dir", default="reports")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / args.reports_dir / f"enterprise_docs_registry_holdout_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    migration = export_migration_audit()
    (out_dir / "registry_migration_audit.json").write_text(
        json.dumps(migration, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    holdout = run_holdout_matrix(include_demo=False)
    (out_dir / "holdout_matrix.json").write_text(
        json.dumps(holdout, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    family_view = holdout.get("by_family") or summarize_holdout_by_family(holdout.get("matrix") or [])
    (out_dir / "family_generalization.json").write_text(
        json.dumps(family_view, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    prior = None
    if PRIOR_BASELINE.exists():
        prior = json.loads(PRIOR_BASELINE.read_text(encoding="utf-8"))

    gate = _system_decision_gate(migration, holdout, family_view, prior)

    baseline_delta = {}
    if prior:
        pb = prior.get("holdout_summary", {}).get("by_company") or {}
        cb = holdout.get("by_company") or {}
        baseline_delta = {
            "hanssem_retrieval_delta": round(
                (cb.get("hanssem") or {}).get("retrieval_feasible_rate", 0)
                - (pb.get("hanssem") or {}).get("retrieval_feasible_rate", 0),
                4,
            ),
            "hanssem_extraction_delta": round(
                (cb.get("hanssem") or {}).get("extraction_feasible_rate", 0)
                - (pb.get("hanssem") or {}).get("extraction_feasible_rate", 0),
                4,
            ),
            "musinsa_extraction_delta": round(
                (cb.get("musinsa") or {}).get("extraction_feasible_rate", 0)
                - (pb.get("musinsa") or {}).get("extraction_feasible_rate", 0),
                4,
            ),
        }

    summary = {
        "timestamp": ts,
        "artifact_dir": str(out_dir.relative_to(ROOT)).replace("\\", "/"),
        "registry_migration_audit": migration,
        "holdout_summary": holdout,
        "family_generalization": family_view,
        "system_decision_gate": gate,
        "baseline_prior": str(PRIOR_BASELINE.relative_to(ROOT)).replace("\\", "/"),
        "baseline_delta": baseline_delta,
        "hotspot_reduction": {
            "partial_before": 5,
            "partial_after": migration["counts"].get("partially_registry_driven"),
            "code_driven_before": 1,
            "code_driven_after": migration["counts"].get("still_code_driven"),
            "already_registry_before": 8,
            "already_registry_after": migration["counts"].get("already_registry_driven"),
        },
        "conclusion": (
            f"Registry-driven components {migration['counts']['already_registry_driven']}; "
            f"holdout extraction avg {gate['holdout_extraction_avg']}; "
            f"governance extraction {gate.get('governance_extraction_rate')}; synthesis blocked."
        ),
    }

    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _write_report(out_dir / "report.md", summary)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nArtifacts: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
