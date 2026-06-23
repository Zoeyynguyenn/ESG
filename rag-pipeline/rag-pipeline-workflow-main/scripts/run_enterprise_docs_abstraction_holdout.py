#!/usr/bin/env python3
"""Enterprise internal-doc: abstraction consolidation + holdout robustness round."""

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

FRAMEWORK_BASELINE = ROOT / "reports/enterprise_docs_framework_20260618-152811/summary.json"


def _system_decision_gate(
    migration: dict[str, Any],
    holdout: dict[str, Any],
    family_view: dict[str, Any],
) -> dict[str, Any]:
    by_co = holdout.get("by_company") or {}
    h_ret = (by_co.get("hanssem") or {}).get("retrieval_feasible_rate", 0.0)
    m_ret = (by_co.get("musinsa") or {}).get("retrieval_feasible_rate", 0.0)
    h_ext = (by_co.get("hanssem") or {}).get("extraction_feasible_rate", 0.0)
    m_ext = (by_co.get("musinsa") or {}).get("extraction_feasible_rate", 0.0)

    partial_count = migration["counts"].get("partially_registry_driven", 0)
    still_code = migration["counts"].get("still_code_driven", 0)

    ready_holdout = h_ret >= 0.75 and m_ret >= 0.75 and holdout.get("matrix")
    handoff_families = [
        fid
        for fid, spec in (family_view.get("families") or {}).items()
        if spec.get("handoff_candidate") and spec.get("reusability_level") != "pilot_only"
    ]
    limited_handoff = bool(handoff_families) and (h_ext + m_ext) / 2 >= 0.35

    gates = {
        "ready_for_holdout_expansion": ready_holdout,
        "ready_for_limited_langgraph_handoff": limited_handoff,
        "not_ready_for_synthesis": True,
        "requires_more_registry_abstraction": partial_count >= 4 or still_code >= 1,
    }

    synthesis_conditions = {
        "min_quant_synthesis_gate_rate": 0.6,
        "min_holdout_extraction_rate": 0.5,
        "registry_partial_components_max": 2,
        "qualitative_synthesis_requires_explicit_gate": True,
    }

    return {
        **gates,
        "handoff_candidate_families": handoff_families,
        "pilot_lock_families": [
            fid
            for fid, spec in (family_view.get("families") or {}).items()
            if spec.get("scope") == "pilot_only" or spec.get("reusability_level") == "pilot_only"
        ],
        "holdout_retrieval_hanssem": h_ret,
        "holdout_retrieval_musinsa": m_ret,
        "holdout_extraction_avg": round((h_ext + m_ext) / 2, 4),
        "synthesis_open_conditions": synthesis_conditions,
        "priority_next": (
            "registry_abstraction_completion"
            if gates["requires_more_registry_abstraction"]
            else "holdout_harness_expansion"
            if gates["ready_for_holdout_expansion"]
            else "strengthen_extraction_families"
        ),
    }


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    mig = payload["registry_migration_audit"]
    hold = payload["holdout_summary"]
    fam = payload["family_generalization"]
    gate = payload["system_decision_gate"]

    lines = [
        "# Enterprise Internal-Doc — Abstraction + Holdout Robustness",
        "",
        f"Generated: {payload['timestamp']}",
        "",
        "## 1. Registry migration audit",
        "",
        f"- Already registry-driven: **{mig['counts']['already_registry_driven']}**",
        f"- Partially registry-driven: **{mig['counts']['partially_registry_driven']}**",
        f"- Still code-driven: **{mig['counts']['still_code_driven']}**",
        "",
        "### Pilot hotspots",
        "",
    ]
    for c in mig.get("pilot_hotspots") or []:
        lines.append(f"- `{c}`")

    lines.extend([
        "",
        "## 2. Holdout robustness round",
        "",
        "| company | probes | parser | retrieval | extraction | aggregation |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for cid, stats in sorted((hold.get("by_company") or {}).items()):
        lines.append(
            f"| `{cid}` | {stats.get('probe_count')} | {stats.get('parser_ok_rate')} | "
            f"{stats.get('retrieval_feasible_rate')} | {stats.get('extraction_feasible_rate')} | "
            f"{stats.get('aggregation_feasible_rate')} |"
        )

    lines.extend(["", "## 3. Family generalization", ""])
    for fid, spec in sorted((fam.get("families") or {}).items()):
        lines.append(
            f"- **{fid}**: retrieval={spec.get('retrieval_feasible_rate')}, "
            f"extraction={spec.get('extraction_feasible_rate')}, "
            f"reusability={spec.get('reusability_level')}, "
            f"dominant_readiness=`{spec.get('dominant_readiness_state')}`"
        )
    lines.append(f"\nStrongest: **{fam.get('strongest_family')}** | Weakest: **{fam.get('weakest_family')}**")

    lines.extend([
        "",
        "## 4. System decision gate",
        "",
        f"- `ready_for_holdout_expansion`: **{gate['ready_for_holdout_expansion']}**",
        f"- `ready_for_limited_langgraph_handoff`: **{gate['ready_for_limited_langgraph_handoff']}**",
        f"- `not_ready_for_synthesis`: **{gate['not_ready_for_synthesis']}**",
        f"- `requires_more_registry_abstraction`: **{gate['requires_more_registry_abstraction']}**",
        f"- Handoff candidate families: {gate.get('handoff_candidate_families') or 'none'}",
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
    out_dir = ROOT / args.reports_dir / f"enterprise_docs_abstraction_holdout_{ts}"
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

    reusability = analyze_reusability(
        [
            {
                "probe_id": r["probe_id"],
                "company": r["company_id"],
                "parser_ok": r["parser_ok"],
                "retrieval_feasible": r["retrieval_feasible"],
                "extraction_feasible": r["extraction_feasible"],
                "aggregation_feasible": r["aggregation_feasible"],
                "readiness_state": r["readiness_state"],
                "kind": r["kind"],
            }
            for r in holdout.get("matrix") or []
        ],
        demo_readiness_summary=None,
    )

    gate = _system_decision_gate(migration, holdout, family_view)

    baseline_delta = None
    if FRAMEWORK_BASELINE.exists():
        base = json.loads(FRAMEWORK_BASELINE.read_text(encoding="utf-8"))
        base_hold = base.get("holdout_summary", {}).get("by_company") or {}
        baseline_delta = {
            "hanssem_retrieval_delta": round(
                (holdout.get("by_company", {}).get("hanssem", {}).get("retrieval_feasible_rate", 0))
                - base_hold.get("hanssem", {}).get("retrieval_feasible_rate", 0),
                4,
            ),
            "musinsa_probe_count_delta": (
                holdout.get("by_company", {}).get("musinsa", {}).get("probe_count", 0)
                - base_hold.get("musinsa", {}).get("probe_count", 0)
            ),
        }

    summary = {
        "timestamp": ts,
        "artifact_dir": str(out_dir.relative_to(ROOT)).replace("\\", "/"),
        "registry_migration_audit": migration,
        "holdout_summary": holdout,
        "family_generalization": family_view,
        "reusability": {
            "reusable_system_coverage": reusability.get("reusable_system_coverage"),
            "pilot_only_dependency": reusability.get("pilot_only_dependency"),
        },
        "system_decision_gate": gate,
        "baseline_framework": str(FRAMEWORK_BASELINE.relative_to(ROOT)).replace("\\", "/"),
        "baseline_delta": baseline_delta,
        "conclusion": (
            f"Holdout expanded; retrieval hanssem {gate['holdout_retrieval_hanssem']}, musinsa {gate['holdout_retrieval_musinsa']}; "
            f"strongest family {family_view.get('strongest_family')}; synthesis still blocked."
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
