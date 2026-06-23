"""Version 6: graph-like orchestrator — route, extract, verify, resolve."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import BASE_DIR, DATA_DIR, FINAL_TOP_K
from extraction_v4 import (
    DEFAULT_RETRIEVAL_MODE,
    compute_extraction_metrics,
    extract_field,
    iter_schema_fields,
    load_schema,
)
from gap_analysis_v5 import analyze_gaps
from router_v6 import route_all_fields, route_field
from verification_v6 import _extract_with_hits, run_verification_loop
from workflow_v5 import INTAKE_TEMPLATE_PATH, load_intake, resolve_intake

V6_RUNS_DIR = BASE_DIR / "artifacts" / "v6_runs"
REPORTS_DIR = BASE_DIR / "reports"
V5_BASELINE_RUN = BASE_DIR / "artifacts" / "v5_runs" / "demo_v5_001"


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def load_v5_baseline_metrics() -> Dict[str, Any]:
    """Doc metric V5 tu gap/workflow neu co."""
    defaults = {
        "extraction_coverage_rate": 0.8929,
        "verified_rate": 0.6786,
        "insufficient_rate": 0.1786,
        "conflict_rate": 0.1429,
        "priority_field_completion_rate": 0.0,
        "end_to_end_duration_sec": 106.1,
    }
    gap_path = V5_BASELINE_RUN / "gap_analysis.json"
    if gap_path.exists():
        gap = json.loads(gap_path.read_text(encoding="utf-8"))
        s = gap.get("summary", {})
        defaults["priority_field_completion_rate"] = s.get("priority_field_completion_rate", 0.0)
        em = s.get("extraction_metrics", {})
        for k in ("field_coverage_rate", "verified_rate", "insufficient_rate", "conflict_rate"):
            if k in em:
                key = "extraction_coverage_rate" if k == "field_coverage_rate" else k
                defaults[key] = em[k]
    log_path = V5_BASELINE_RUN / "workflow_log.json"
    if log_path.exists():
        log = json.loads(log_path.read_text(encoding="utf-8"))
        wm = log.get("workflow_metrics", {})
        if wm:
            defaults.update({k: wm.get(k, defaults.get(k)) for k in defaults})
    defaults["run_id"] = "demo_v5_001"
    return defaults


def build_profile_v6(
    intake: Dict[str, Any],
    trace: List[Dict[str, Any]],
) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    schema = load_schema()
    fields = iter_schema_fields(schema)
    priority = intake.get("priority_fields") or []
    default_mode = intake.get("retrieval_mode", DEFAULT_RETRIEVAL_MODE)
    base_top_k = int(intake.get("top_k", FINAL_TOP_K))

    routes = route_all_fields(fields, default_mode, base_top_k, priority)
    records: List[Dict[str, Any]] = []
    verification_logs: List[Dict[str, Any]] = []

    for field in fields:
        fid = field["id"]
        route = routes[fid]
        trace.append(
            {
                "stage": "route",
                "field": fid,
                "category": route.category,
                "primary_mode": route.primary_mode,
                "fallback_mode": route.fallback_mode,
                "top_k": route.top_k,
                "pool": route.pool,
            }
        )

        query = route.query_rewrites[0]
        try:
            rec = _extract_with_hits(field, route, query, route.primary_mode, route.top_k, route.pool)
        except Exception as exc:
            trace.append({"stage": "extract_error", "field": fid, "error": str(exc)})
            rec = extract_field(field, default_mode, base_top_k)

        rec["v6_route_category"] = route.category
        rec["v6_primary_mode"] = route.primary_mode

        if rec.get("status") in ("insufficient", "conflict"):
            trace.append({"stage": "verify_trigger", "field": fid, "status": rec.get("status")})
            out = run_verification_loop(field, route, rec)
            verification_logs.append(out["log"])
            rec = out["record"]
            if out["log"].get("success"):
                trace.append({"stage": "verify_success", "field": fid, "strategy": rec.get("verification_strategy")})

        records.append(rec)

    profile = {
        "schema_version": schema.get("schema_version", "v1"),
        "entity": intake.get("entity_name") or schema.get("entity"),
        "retrieval_mode": default_mode,
        "orchestration": "v6_route_verify_resolve",
        "field_count": len(records),
        "records": records,
        "run_id": intake.get("run_id"),
    }
    return profile, verification_logs


def compute_v6_metrics(
    profile: Dict[str, Any],
    gap: Dict[str, Any],
    verification_logs: List[Dict[str, Any]],
    duration_sec: float,
    success: bool,
) -> Dict[str, Any]:
    ext = compute_extraction_metrics(profile)
    triggered = sum(1 for lg in verification_logs if not lg.get("skipped"))
    successes = sum(1 for lg in verification_logs if lg.get("success"))
    conflict_resolved = sum(
        1 for r in profile.get("records", []) if r.get("conflict_resolved")
    )
    return {
        "execution_success": success,
        "end_to_end_duration_sec": round(duration_sec, 2),
        "extraction_coverage_rate": ext.get("field_coverage_rate"),
        "verified_rate": ext.get("verified_rate"),
        "insufficient_rate": ext.get("insufficient_rate"),
        "conflict_rate": ext.get("conflict_rate"),
        "evidence_presence_rate": ext.get("evidence_presence_rate"),
        "priority_field_completion_rate": gap.get("summary", {}).get("priority_field_completion_rate"),
        "verification_loop_trigger_count": triggered,
        "verification_loop_success_rate": round(successes / max(triggered, 1), 4),
        "conflict_resolved_count": conflict_resolved,
        "fields_verified": ext.get("fields_verified"),
        "fields_insufficient": ext.get("fields_insufficient"),
        "fields_conflict": ext.get("fields_conflict"),
    }


def delta_v6_vs_v5(v6: Dict[str, Any], v5: Dict[str, Any]) -> Dict[str, Any]:
    keys = [
        "extraction_coverage_rate",
        "verified_rate",
        "insufficient_rate",
        "conflict_rate",
        "priority_field_completion_rate",
        "end_to_end_duration_sec",
    ]
    delta = {}
    for k in keys:
        a, b = v6.get(k), v5.get(k)
        if a is None or b is None:
            continue
        d = round(float(a) - float(b), 4)
        delta[k] = {"v5": b, "v6": a, "delta": d}
    return delta


def assess_v6_status(v6_metrics: Dict[str, Any], v5_metrics: Dict[str, Any]) -> str:
    if not v6_metrics.get("execution_success"):
        return "not_pass"
    pri_v6 = v6_metrics.get("priority_field_completion_rate", 0) or 0
    pri_v5 = v5_metrics.get("priority_field_completion_rate", 0) or 0
    ins_delta = (v5_metrics.get("insufficient_rate", 1) or 1) - (v6_metrics.get("insufficient_rate", 1) or 1)
    con_delta = (v5_metrics.get("conflict_rate", 1) or 1) - (v6_metrics.get("conflict_rate", 1) or 1)
    verify_ok = v6_metrics.get("verification_loop_trigger_count", 0) > 0
    improved = pri_v6 > pri_v5 or ins_delta > 0.02 or con_delta > 0.02
    if verify_ok and improved:
        return "pass_with_limits"
    if verify_ok and v6_metrics.get("extraction_coverage_rate", 0) >= 0.5:
        return "pass_with_limits"
    return "not_pass"


def write_v6_report(
    path: Path,
    intake: Dict[str, Any],
    metrics: Dict[str, Any],
    gap: Dict[str, Any],
    trace: List[Dict[str, Any]],
    verification_logs: List[Dict[str, Any]],
) -> None:
    lines = [
        "# V6 Workflow Report",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        f"Run ID: `{intake.get('run_id')}`",
        "",
        "## Orchestration",
        "",
        "Flow: route -> extract (per-field mode) -> verification loop -> conflict resolve",
        "",
        "## V6 metrics",
        "",
        "```json",
        json.dumps(metrics, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Gap summary",
        "",
        "```json",
        json.dumps(gap.get("summary", {}), ensure_ascii=False, indent=2),
        "```",
        "",
        f"## Trace events: {len(trace)}",
        "",
        f"## Verification logs: {len(verification_logs)}",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_comparison_report(path: Path, v6: Dict[str, Any], v5: Dict[str, Any], delta: Dict[str, Any], status: str) -> None:
    lines = [
        "# V6 vs V5 Comparison",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        f"**V6 status:** `{status}`",
        "",
        "| Metric | V5 | V6 | Delta |",
        "|---|---:|---:|---:|",
    ]
    for k, d in delta.items():
        lines.append(f"| {k} | {d['v5']} | {d['v6']} | {d['delta']:+.4f} |")
    lines.extend(
        [
            "",
            "## V6-only metrics",
            "",
            f"- verification_loop_trigger_count: {v6.get('verification_loop_trigger_count')}",
            f"- verification_loop_success_rate: {v6.get('verification_loop_success_rate')}",
            f"- conflict_resolved_count: {v6.get('conflict_resolved_count')}",
            "",
            "## Nhan dinh",
            "",
        ]
    )
    pri_d = delta.get("priority_field_completion_rate", {}).get("delta", 0)
    if pri_d > 0:
        lines.append(f"- Priority completion tang {pri_d:+.2f} so voi V5.")
    ins_d = delta.get("insufficient_rate", {}).get("delta", 0)
    if ins_d < 0:
        lines.append(f"- Insufficient rate giam {abs(ins_d):.2f} (tot hon).")
    con_d = delta.get("conflict_rate", {}).get("delta", 0)
    if con_d < 0:
        lines.append(f"- Conflict rate giam {abs(con_d):.2f}.")
    if pri_d <= 0 and ins_d >= 0:
        lines.append("- Can tiep tuc nang parser V4 + routing rules cho boolean/table.")
    path.write_text("\n".join(lines), encoding="utf-8")


def run_v6_workflow(
    intake_path: Optional[Path] = None,
    retrieval_mode: Optional[str] = None,
    top_k: Optional[int] = None,
    run_id: Optional[str] = None,
    output_dir: Optional[Path] = None,
    v5_baseline_run: Optional[Path] = None,
) -> Dict[str, Any]:
    global V5_BASELINE_RUN
    if v5_baseline_run:
        V5_BASELINE_RUN = v5_baseline_run

    t0 = time.perf_counter()
    trace: List[Dict[str, Any]] = []
    intake = resolve_intake(intake_path, retrieval_mode, top_k, run_id)
    if not run_id and intake.get("run_id", "").startswith("demo_v5"):
        intake["run_id"] = f"v6_{_ts()}"
    if run_id:
        intake["run_id"] = run_id

    run_dir = output_dir or (V6_RUNS_DIR / intake["run_id"])
    run_dir.mkdir(parents=True, exist_ok=True)

    profile, verification_logs = build_profile_v6(intake, trace)
    extraction_metrics = compute_extraction_metrics(profile)
    gap = analyze_gaps(profile, intake, extraction_metrics)

    duration = time.perf_counter() - t0
    v6_metrics = compute_v6_metrics(profile, gap, verification_logs, duration, True)
    v5_metrics = load_v5_baseline_metrics()
    delta = delta_v6_vs_v5(v6_metrics, v5_metrics)
    v6_status = assess_v6_status(v6_metrics, v5_metrics)

    (run_dir / "orchestration_trace.json").write_text(
        json.dumps({"intake": intake, "trace": trace}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "extracted_profile_v6.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "gap_analysis_v6.json").write_text(
        json.dumps(gap, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "verification_log.json").write_text(
        json.dumps(verification_logs, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report_path = REPORTS_DIR / f"v6-workflow-report-{_ts()}.md"
    compare_path = REPORTS_DIR / f"v6-vs-v5-comparison-{_ts()}.md"
    write_v6_report(report_path, intake, v6_metrics, gap, trace, verification_logs)
    write_comparison_report(compare_path, v6_metrics, v5_metrics, delta, v6_status)

    return {
        "v6_status": v6_status,
        "roadmap_decision": "ket_thuc_roadmap_voi_pass_with_limits" if v6_status != "not_pass" else "can_vong_cai_tien",
        "v6_metrics": v6_metrics,
        "v5_metrics": v5_metrics,
        "delta": delta,
        "run_dir": str(run_dir),
        "report_path": str(report_path),
        "compare_path": str(compare_path),
        "profile": profile,
        "gap": gap,
        "verification_logs": verification_logs,
    }
