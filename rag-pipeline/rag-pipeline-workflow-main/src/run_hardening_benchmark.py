"""Post-roadmap hardening benchmark runner."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from config import BASE_DIR
from hardening_config import HARDENING_MATRIX, HardeningConfig
from hardening_orchestrator import (
    REPORTS_DIR,
    check_consistency_subset,
    load_v6_baseline_metrics,
    run_hardening_profile,
    save_hardening_run,
    write_hardening_run_report,
    write_test_matrix,
    _ts,
)
from workflow_v5 import load_intake


PRIORITY_FIELDS = [
    "wastewater_treatment_policy",
    "water_reuse_target",
    "third_party_audit_frequency",
    "overtime_limit",
    "whistleblowing_response_sla",
    "ltifr_target_2026",
]


def assess_hardening(all_metrics: List[Dict[str, Any]], v6_base: Dict[str, Any]) -> tuple[str, bool]:
    """hardening_status, readiness_for_realistic_pilot."""
    any_success = all(m.get("execution_success") for m in all_metrics)
    no_water_100 = all(m.get("water_reuse_wrong_100_count", 0) == 0 for m in all_metrics)
    public_run = next((m for m in all_metrics if "public" in m.get("_run_id", "")), None)
    no_boost = next((m for m in all_metrics if "no_policy" in m.get("_run_id", "")), None)

    pri_public = public_run.get("priority_field_completion_rate", 0) if public_run else 0
    pri_v6 = v6_base.get("priority_field_completion_rate", 1.0)

    if not any_success:
        return "not_pass", False
    if no_water_100 and any_success:
        status = "pass_with_limits"
    else:
        status = "pass_with_limits" if any_success else "not_pass"

    readiness = (
        no_water_100
        and pri_public >= 0.4
        and (no_boost is None or no_boost.get("insufficient_rate", 1) <= 0.25)
    )
    return status, readiness


def write_summary_compare(
    path: Path,
    runs: List[Dict[str, Any]],
    v6_base: Dict[str, Any],
    hardening_status: str,
    readiness: bool,
) -> None:
    lines = [
        "# Hardening Summary vs V6 Baseline",
        "",
        f"Status: **{hardening_status}** | readiness_for_realistic_pilot: **{'yes' if readiness else 'no'}**",
        "",
        "| Run | coverage | verified | insufficient | conflict | priority | public_cov | water_100_err | avg_attempt | p95_lat |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in runs:
        m = r["metrics"]
        lines.append(
            f"| {r['run_id']} | {m.get('extraction_coverage_rate')} | {m.get('verified_rate')} | "
            f"{m.get('insufficient_rate')} | {m.get('conflict_rate')} | "
            f"{m.get('priority_field_completion_rate')} | {m.get('public_field_coverage_rate')} | "
            f"{m.get('water_reuse_wrong_100_count')} | {m.get('avg_field_attempt_count')} | "
            f"{m.get('p95_field_latency_sec')} |"
        )
    lines.extend(
        [
            "",
            "## V6 baseline (demo_v6_001)",
            "",
            "```json",
            json.dumps(v6_base, indent=2),
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--configs",
        type=str,
        default="v6_current,v6_no_policy_boost,v6_public_only,v6_mixed_strict",
        help="Comma-separated config ids",
    )
    parser.add_argument("--quick", action="store_true", help="Only mixed current + public_only")
    args = parser.parse_args(argv)

    if args.quick:
        config_ids = ["v6_current", "v6_public_only"]
    else:
        config_ids = [x.strip() for x in args.configs.split(",")]

    cfg_map = {c.config_id: c for c in HARDENING_MATRIX}
    intake = load_intake(BASE_DIR / "data" / "rag_dataset" / "v5_intake_template.json")

    ts = _ts()
    matrix_path = REPORTS_DIR / f"hardening-test-matrix-{ts}.md"
    planned = [f"hardening_{cid}_{ts}" for cid in config_ids]
    write_test_matrix(matrix_path, HARDENING_MATRIX, planned)

    results: List[Dict[str, Any]] = []
    v6_base = load_v6_baseline_metrics()

    for cid in config_ids:
        if cid not in cfg_map:
            print(f"Skip unknown config: {cid}")
            continue
        cfg = cfg_map[cid]
        run_id = f"hardening_{cid}_{ts}"
        print(f"Running {run_id} ...")
        intake_run = {**intake, "run_id": run_id}
        result = run_hardening_profile(cfg, intake_run, run_id)
        save_hardening_run(run_id, result, cfg)
        consistency = None
        if cid == "v6_current":
            consistency = check_consistency_subset(cfg, intake_run, PRIORITY_FIELDS[:5])
        report_path = REPORTS_DIR / f"hardening-run-{run_id}.md"
        write_hardening_run_report(
            report_path, run_id, cfg, result["metrics"], result["gap"], consistency
        )
        m = result["metrics"]
        m["_run_id"] = run_id
        m["_config_id"] = cid
        if consistency:
            m["conflict_resolution_consistency"] = consistency.get("consistency_rate")
        results.append({"run_id": run_id, "config_id": cid, "metrics": m, "report": str(report_path)})

    status, readiness = assess_hardening([r["metrics"] for r in results], v6_base)
    summary_path = REPORTS_DIR / f"hardening-summary-{ts}.md"
    write_summary_compare(summary_path, results, v6_base, status, readiness)

    out = {
        "hardening_status": status,
        "readiness_for_realistic_pilot": readiness,
        "matrix_path": str(matrix_path),
        "summary_path": str(summary_path),
        "runs": results,
        "v6_baseline": v6_base,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
