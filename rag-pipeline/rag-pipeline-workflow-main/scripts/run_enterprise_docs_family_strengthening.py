#!/usr/bin/env python3
"""Family-focused holdout strengthening round."""

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
from enterprise_docs.family_readiness_gate import build_family_readiness_gate
from enterprise_docs.holdout_harness import run_holdout_matrix
from enterprise_docs.registry_migration_audit import export_migration_audit

PRIOR_BASELINE = ROOT / "reports/enterprise_docs_family_holdout_20260618-163238/summary.json"


def _family_delta(
    current: dict[str, Any],
    prior: dict[str, Any] | None,
    bucket: str,
    key: str = "extraction_feasible_rate",
) -> float | None:
    if not prior:
        return None
    pf = (prior.get("family_generalization") or {}).get("families") or {}
    cf = (current.get("families") or {}).get(bucket) or {}
    if bucket not in pf:
        return None
    return round(cf.get(key, 0) - pf[bucket].get(key, 0), 4)


def _system_decision_gate(
    holdout: dict[str, Any],
    family_view: dict[str, Any],
    readiness_gate: dict[str, Any],
    prior: dict[str, Any] | None,
) -> dict[str, Any]:
    by_co = holdout.get("by_company") or {}
    h_ext = (by_co.get("hanssem") or {}).get("extraction_feasible_rate", 0.0)
    m_ext = (by_co.get("musinsa") or {}).get("extraction_feasible_rate", 0.0)
    ext_avg = (h_ext + m_ext) / 2

    prior_ext = None
    if prior:
        gate = prior.get("system_decision_gate") or {}
        prior_ext = gate.get("holdout_extraction_avg")

    families = family_view.get("families") or {}
    gov = families.get("governance") or {}
    env = families.get("environment_ghg") or {}
    emp = families.get("employee_headcount") or {}

    gated = readiness_gate.get("families") or {}
    near_handoff = [
        fid
        for fid, spec in gated.items()
        if spec.get("handoff_candidate_likelihood") in ("medium", "high")
        and spec.get("scope") != "pilot_only"
    ]

    return {
        "ready_for_holdout_expansion": ext_avg >= 0.4,
        "ready_for_limited_langgraph_handoff": False,
        "handoff_prep_candidate_families": near_handoff,
        "not_ready_for_synthesis": True,
        "requires_more_registry_abstraction": False,
        "nearest_handoff_family": readiness_gate.get("nearest_handoff_family"),
        "handoff_likelihood_families": near_handoff,
        "holdout_extraction_avg": round(ext_avg, 4),
        "holdout_extraction_delta_vs_prior": round(ext_avg - prior_ext, 4) if prior_ext is not None else None,
        "governance_extraction_rate": gov.get("extraction_feasible_rate"),
        "governance_delta_vs_prior": _family_delta(family_view, prior, "governance"),
        "environment_ghg_extraction_rate": env.get("extraction_feasible_rate"),
        "environment_ghg_quant_extraction_rate": env.get("quant_extraction_rate"),
        "environment_ghg_delta_vs_prior": _family_delta(family_view, prior, "environment_ghg"),
        "employee_headcount_extraction_rate": emp.get("extraction_feasible_rate"),
        "employee_headcount_delta_vs_prior": _family_delta(family_view, prior, "employee_headcount"),
        "weakest_family": family_view.get("weakest_family"),
        "strongest_family": family_view.get("strongest_family"),
        "synthesis_gate_distance": {
            "current_quant_gate_estimate": 0.23,
            "target_quant_gate": 0.6,
            "holdout_extraction_target": 0.5,
            "holdout_extraction_gap": round(max(0, 0.5 - ext_avg), 4),
        },
        "priority_next": (
            "handoff_preparation"
            if near_handoff and ext_avg >= 0.5
            else "family_strengthening"
            if ext_avg < 0.5
            else "controlled_holdout_expansion"
        ),
    }


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    fam = payload["family_generalization"]
    gate = payload["system_decision_gate"]
    rg = payload["family_readiness_gate"]
    delta = payload.get("baseline_delta") or {}

    lines = [
        "# Enterprise Internal-Doc — Family Strengthening Round",
        "",
        f"Generated: {payload['timestamp']}",
        "",
        "## Holdout vs prior",
        "",
        f"- Extraction avg: **{gate['holdout_extraction_avg']}** (delta {gate.get('holdout_extraction_delta_vs_prior')})",
        f"- Governance extraction: **{gate.get('governance_extraction_rate')}** (delta {gate.get('governance_delta_vs_prior')})",
        f"- Environment GHG extraction: **{gate.get('environment_ghg_extraction_rate')}** "
        f"(quant {gate.get('environment_ghg_quant_extraction_rate')}, delta {gate.get('environment_ghg_delta_vs_prior')})",
        f"- Employee headcount: **{gate.get('employee_headcount_extraction_rate')}** "
        f"(delta {gate.get('employee_headcount_delta_vs_prior')})",
        "",
        "## Family readiness gate",
        "",
        f"- Nearest handoff family: **{rg.get('nearest_handoff_family') or 'none'}**",
        f"- Handoff likelihood families: {gate.get('handoff_likelihood_families') or 'none'}",
        "",
        "## Family summary",
        "",
    ]
    for fid, spec in sorted((fam.get("families") or {}).items()):
        rg_spec = (rg.get("families") or {}).get(fid) or {}
        lines.append(
            f"- **{fid}**: extraction={spec.get('extraction_feasible_rate')}, "
            f"quant_extraction={spec.get('quant_extraction_rate')}, "
            f"likelihood={rg_spec.get('handoff_candidate_likelihood')}, "
            f"tier={spec.get('reusability_level')}"
        )

    lines.extend([
        "",
        "## System gates",
        "",
        f"- Synthesis gap: **{gate['synthesis_gate_distance']['holdout_extraction_gap']}**",
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
    out_dir = ROOT / args.reports_dir / f"enterprise_docs_family_strengthening_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    migration = export_migration_audit()
    (out_dir / "registry_migration_audit.json").write_text(
        json.dumps(migration, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    holdout = run_holdout_matrix(include_demo=False)
    (out_dir / "holdout_matrix.json").write_text(
        json.dumps(holdout, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    matrix = holdout.get("matrix") or []
    family_view = holdout.get("by_family") or summarize_holdout_by_family(matrix)
    (out_dir / "family_generalization.json").write_text(
        json.dumps(family_view, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    readiness_gate = build_family_readiness_gate(family_view, matrix)
    (out_dir / "family_readiness_gate.json").write_text(
        json.dumps(readiness_gate, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    prior = None
    if PRIOR_BASELINE.exists():
        prior = json.loads(PRIOR_BASELINE.read_text(encoding="utf-8"))

    gate = _system_decision_gate(holdout, family_view, readiness_gate, prior)

    baseline_delta = {}
    if prior:
        pb = prior.get("holdout_summary", {}).get("by_company") or {}
        cb = holdout.get("by_company") or {}
        baseline_delta = {
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
        "family_readiness_gate": readiness_gate,
        "system_decision_gate": gate,
        "baseline_prior": str(PRIOR_BASELINE.relative_to(ROOT)).replace("\\", "/"),
        "baseline_delta": baseline_delta,
        "conclusion": (
            f"Holdout extraction avg {gate['holdout_extraction_avg']}; "
            f"env_ghg {gate.get('environment_ghg_extraction_rate')}; "
            f"governance {gate.get('governance_extraction_rate')}; synthesis blocked."
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
