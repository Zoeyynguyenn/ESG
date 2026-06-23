"""Post-V6 hardening orchestrator with observability + corpus scope."""

from __future__ import annotations

import json
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import BASE_DIR, FINAL_TOP_K
from extraction_v4 import compute_extraction_metrics, iter_schema_fields, load_schema
from gap_analysis_v5 import analyze_gaps
from hardening_config import HardeningConfig, corpus_scope_allows_source
from normalize_v6 import normalize_field_value
from retrieval_v3 import retrieve
from router_v6 import route_all_fields
from verification_v6 import run_verification_loop

from conflict_resolver_v6 import rank_hits, resolve_from_hits
from extraction_v4 import extract_value_from_text, _assign_status_confidence, _best_snippet, _detect_conflict, extract_field

HARDENING_RUNS_DIR = BASE_DIR / "artifacts" / "hardening_runs"
REPORTS_DIR = BASE_DIR / "reports"
V6_BASELINE_RUN = BASE_DIR / "artifacts" / "v6_runs" / "demo_v6_001"
INTAKE_PATH = BASE_DIR / "data" / "rag_dataset" / "v5_intake_template.json"


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _snapshot_candidates(hits, field, strict: bool, top_n: int = 5) -> List[Dict[str, Any]]:
    ranked = rank_hits(hits, strict=strict)[:top_n]
    out = []
    for h in ranked:
        val = extract_value_from_text(field, h.text)
        out.append(
            {
                "source": h.source,
                "score": round(h.score, 4),
                "value": val,
                "snippet": h.text[:120],
            }
        )
    return out


def _filter_hits(hits: List[Any], scope: str) -> Tuple[List[Any], int]:
    if scope == "mixed":
        return hits, 0
    kept = [h for h in hits if corpus_scope_allows_source(h.source, scope)]
    return kept, len(hits) - len(kept)


def extract_field_hardened(
    field: Dict[str, Any],
    route,
    cfg: HardeningConfig,
    trace_events: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    t0 = time.perf_counter()
    fid = field["id"]
    meta_ids = {
        "synthetic_controlled_doc_count",
        "public_esg_source_catalog_present",
        "environment_policy_present",
    }
    field_log: Dict[str, Any] = {"field": fid, "attempt_count": 0}

    if fid in meta_ids:
        rec = extract_field(field, cfg.retrieval_mode, cfg.top_k, cfg.pool)
        field_log["latency_sec"] = round(time.perf_counter() - t0, 4)
        field_log["attempt_count"] = 1
        return rec, field_log

    query = route.query_rewrites[0]
    rec = {
        "field": fid,
        "value": None,
        "evidence_text": "",
        "source": "",
        "status": "insufficient",
        "confidence": "low",
        "group": field.get("group", ""),
    }

    try:
        hits, note = retrieve(query, route.primary_mode, route.pool, route.top_k)
        field_log["attempt_count"] = 1
    except Exception as exc:
        rec["evidence_text"] = str(exc)
        field_log["latency_sec"] = round(time.perf_counter() - t0, 4)
        field_log["error"] = str(exc)
        return rec, field_log

    hits, dropped = _filter_hits(hits, cfg.corpus_scope)
    if dropped:
        field_log["corpus_filtered_dropped"] = dropped
    if not hits:
        rec["status"] = "insufficient"
        rec["resolve_reason"] = "corpus_scope_no_hits"
        field_log["latency_sec"] = round(time.perf_counter() - t0, 4)
        field_log["candidates"] = []
        return rec, field_log

    field_log["candidates"] = _snapshot_candidates(hits, field, cfg.strict_conflict)

    ranked = rank_hits(hits, route.source_bias, strict=cfg.strict_conflict)
    parsed = []
    for h in ranked[:6]:
        v = extract_value_from_text(field, h.text)
        if v is not None:
            norm = normalize_field_value(fid, v, field.get("expected_type", "string"))
            v = norm["value"]
            if norm.get("normalize_warning"):
                field_log["normalize_warning"] = norm["normalize_warning"]
            parsed.append((v, h))

    if len(parsed) > 1 or fid in {"whistleblowing_response_sla", "ltifr_target_2026", "board_committee_count"}:
        resolved = resolve_from_hits(
            field, hits, query, route.source_bias, strict=cfg.strict_conflict
        )
        if resolved.get("resolved"):
            rec.update(
                value=resolved["value"],
                source=resolved["source"],
                evidence_text=resolved["evidence_text"],
                confidence=resolved["confidence"],
                status=resolved["status"],
                conflict_resolved=True,
                resolve_reason=resolved.get("resolve_reason"),
                resolver_trace=resolved.get("trace"),
            )
            field_log["resolve_reason"] = resolved.get("resolve_reason")
            field_log["latency_sec"] = round(time.perf_counter() - t0, 4)
            return rec, field_log

    if parsed:
        val, hit = parsed[0]
        conflict = _detect_conflict([p[0] for p in parsed])
        status, conf = _assign_status_confidence(val, hit.score, conflict, field, hit.source)
        rec.update(
            value=val,
            source=hit.source,
            evidence_text=_best_snippet(hit.text, query),
            confidence=conf,
            status=status,
            retrieval_score=round(hit.score, 4),
        )
        if conflict:
            rec["conflict_values"] = [p[0] for p in parsed[:5]]
            rec["resolve_reason"] = "unresolved_multi_value"
    else:
        rec["source"] = ranked[0].source
        rec["evidence_text"] = ranked[0].text[:300]
        rec["resolve_reason"] = "no_parse_match"

    field_log["latency_sec"] = round(time.perf_counter() - t0, 4)
    return rec, field_log


def run_hardening_profile(
    cfg: HardeningConfig,
    intake: Dict[str, Any],
    run_id: str,
) -> Dict[str, Any]:
    schema = load_schema()
    fields = iter_schema_fields(schema)
    priority = intake.get("priority_fields") or []
    routes = route_all_fields(fields, cfg.retrieval_mode, cfg.top_k, priority)

    trace_events: List[Dict[str, Any]] = []
    verification_logs: List[Dict[str, Any]] = []
    field_logs: List[Dict[str, Any]] = []
    records: List[Dict[str, Any]] = []

    t0 = time.perf_counter()
    for field in fields:
        route = routes[field["id"]]
        rec, flog = extract_field_hardened(field, route, cfg, trace_events)
        flog["config_id"] = cfg.config_id
        field_logs.append(flog)

        if rec.get("status") in ("insufficient", "conflict"):
            from router_v6 import FieldRoute

            out = run_verification_loop(
                field,
                route,
                rec,
                max_attempts=cfg.verification_max_attempts,
                enable_policy_boost=cfg.enable_policy_boost and cfg.corpus_scope == "mixed",
                corpus_scope=cfg.corpus_scope,
                strict_conflict=cfg.strict_conflict,
            )
            vlog = out["log"]
            rec = out["record"]
            flog["attempt_count"] = flog.get("attempt_count", 0) + len(vlog.get("attempts", []))
            verification_logs.append(vlog)

        etype = field.get("expected_type", "string")
        if rec.get("value") is not None:
            norm = normalize_field_value(field["id"], rec["value"], etype)
            if norm.get("normalize_warning"):
                rec["normalize_warning"] = norm["normalize_warning"]
                if norm["normalize_warning"] == "rejected_100_wastewater_confusion":
                    rec["value"] = norm["value"]
                    if rec["value"] is None:
                        rec["status"] = "insufficient"
                        rec["resolve_reason"] = "normalize_reject_water_reuse"

        records.append(rec)
        trace_events.append(
            {
                "field": field["id"],
                "status": rec.get("status"),
                "value": rec.get("value"),
                "source": rec.get("source"),
                "resolve_reason": rec.get("resolve_reason"),
                "latency_sec": flog.get("latency_sec"),
                "attempt_count": flog.get("attempt_count"),
            }
        )

    profile = {
        "schema_version": schema.get("schema_version"),
        "entity": intake.get("entity_name"),
        "hardening_config": cfg.to_dict(),
        "run_id": run_id,
        "records": records,
        "field_count": len(records),
    }
    gap = analyze_gaps(profile, intake, compute_extraction_metrics(profile))
    duration = time.perf_counter() - t0

    latencies = [f["latency_sec"] for f in field_logs if f.get("latency_sec")]
    metrics = compute_hardening_metrics(profile, gap, field_logs, verification_logs, duration, True)
    return {
        "profile": profile,
        "gap": gap,
        "metrics": metrics,
        "trace_events": trace_events,
        "field_logs": field_logs,
        "verification_logs": verification_logs,
        "duration_sec": duration,
    }


def _needs_verify(rec: Dict[str, Any]) -> bool:
    return rec.get("status") in ("insufficient", "conflict")


def is_public_source(source: str) -> bool:
    s = source.lower().replace("\\", "/")
    return "02_esg_public" in s or "03_esg_public" in s


def compute_hardening_metrics(
    profile: Dict[str, Any],
    gap: Dict[str, Any],
    field_logs: List[Dict[str, Any]],
    verification_logs: List[Dict[str, Any]],
    duration_sec: float,
    success: bool,
) -> Dict[str, Any]:
    ext = compute_extraction_metrics(profile)
    records = profile.get("records", [])
    public_ok = sum(
        1
        for r in records
        if r.get("value") is not None and is_public_source(r.get("source", ""))
    )
    public_total = sum(1 for r in records if is_public_source(r.get("source", "")) or r.get("value"))
    attempts = [f.get("attempt_count", 0) for f in field_logs]
    latencies = [f.get("latency_sec", 0) for f in field_logs if f.get("latency_sec")]

    triggered = sum(1 for v in verification_logs if not v.get("skipped"))
    v_success = sum(1 for v in verification_logs if v.get("success"))

    return {
        "execution_success": success,
        "end_to_end_duration_sec": round(duration_sec, 2),
        "extraction_coverage_rate": ext.get("field_coverage_rate"),
        "verified_rate": ext.get("verified_rate"),
        "insufficient_rate": ext.get("insufficient_rate"),
        "conflict_rate": ext.get("conflict_rate"),
        "priority_field_completion_rate": gap.get("summary", {}).get("priority_field_completion_rate"),
        "public_field_coverage_rate": round(public_ok / max(len(records), 1), 4),
        "public_evidence_field_count": public_ok,
        "verification_loop_trigger_count": triggered,
        "verification_loop_success_rate": round(v_success / max(triggered, 1), 4),
        "conflict_resolved_count": sum(1 for r in records if r.get("conflict_resolved")),
        "avg_field_attempt_count": round(statistics.mean(attempts) if attempts else 0, 2),
        "p95_field_latency_sec": round(
            sorted(latencies)[int(0.95 * len(latencies)) - 1] if latencies else 0, 4
        ),
        "water_reuse_wrong_100_count": sum(
            1 for r in records if r.get("field") == "water_reuse_target" and r.get("value") == 100
        ),
    }


def check_consistency_subset(
    cfg: HardeningConfig,
    intake: Dict[str, Any],
    field_ids: List[str],
) -> Dict[str, Any]:
    """Chay 2 lan tren subset field de do consistency."""
    schema = load_schema()
    fields = [f for f in iter_schema_fields(schema) if f["id"] in field_ids]
    routes = route_all_fields(fields, cfg.retrieval_mode, cfg.top_k, intake.get("priority_fields"))

    run1, run2 = [], []
    for field in fields:
        r1, _ = extract_field_hardened(field, routes[field["id"]], cfg, [])
        r2, _ = extract_field_hardened(field, routes[field["id"]], cfg, [])
        run1.append(r1.get("value"))
        run2.append(r2.get("value"))
    match = sum(1 for a, b in zip(run1, run2) if a == b)
    return {
        "fields": field_ids,
        "consistent_pairs": match,
        "total": len(field_ids),
        "consistency_rate": round(match / max(len(field_ids), 1), 4),
    }


def load_v6_baseline_metrics() -> Dict[str, Any]:
    path = V6_BASELINE_RUN / "gap_analysis_v6.json"
    defaults = {
        "extraction_coverage_rate": 1.0,
        "verified_rate": 1.0,
        "insufficient_rate": 0.0,
        "conflict_rate": 0.0,
        "priority_field_completion_rate": 1.0,
        "water_reuse_wrong_100_count": 1,
    }
    prof = V6_BASELINE_RUN / "extracted_profile_v6.json"
    if prof.exists():
        data = json.loads(prof.read_text(encoding="utf-8"))
        for r in data.get("records", []):
            if r.get("field") == "water_reuse_target" and r.get("value") == 100:
                defaults["water_reuse_wrong_100_count"] = 1
    if path.exists():
        gap = json.loads(path.read_text(encoding="utf-8"))
        em = gap.get("summary", {}).get("extraction_metrics", {})
        defaults.update(
            {
                "extraction_coverage_rate": em.get("field_coverage_rate", 1.0),
                "verified_rate": em.get("verified_rate", 1.0),
                "insufficient_rate": em.get("insufficient_rate", 0.0),
                "conflict_rate": em.get("conflict_rate", 0.0),
                "priority_field_completion_rate": gap.get("summary", {}).get(
                    "priority_field_completion_rate", 1.0
                ),
            }
        )
    return defaults


def save_hardening_run(run_id: str, result: Dict[str, Any], cfg: HardeningConfig) -> Path:
    run_dir = HARDENING_RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "extracted_profile.json").write_text(
        json.dumps(result["profile"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "gap_analysis.json").write_text(
        json.dumps(result["gap"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "trace_hardened.json").write_text(
        json.dumps(
            {
                "config": cfg.to_dict(),
                "events": result["trace_events"],
                "field_logs": result["field_logs"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_dir / "verification_hardened.json").write_text(
        json.dumps(result["verification_logs"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(
        json.dumps(result["metrics"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return run_dir


def write_hardening_run_report(
    path: Path,
    run_id: str,
    cfg: HardeningConfig,
    metrics: Dict[str, Any],
    gap: Dict[str, Any],
    consistency: Optional[Dict[str, Any]] = None,
) -> None:
    lines = [
        f"# Hardening Run — {run_id}",
        "",
        f"Config: `{cfg.config_id}` — {cfg.label}",
        "",
        "## Config",
        "",
        "```json",
        json.dumps(cfg.to_dict(), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Metrics",
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
    ]
    if consistency:
        lines.extend(["## Consistency check", "", "```json", json.dumps(consistency, indent=2), "```", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_test_matrix(path: Path, configs: List[HardeningConfig], planned_runs: List[str]) -> None:
    lines = [
        "# Hardening Test Matrix",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "| # | Config ID | Corpus | Policy boost | Strict conflict | Retrieval |",
        "|---|-----------|--------|--------------|-----------------|-----------|",
    ]
    for i, c in enumerate(configs, 1):
        lines.append(
            f"| {i} | {c.config_id} | {c.corpus_scope} | {c.enable_policy_boost} | {c.strict_conflict} | {c.retrieval_mode} |"
        )
    lines.extend(["", "## Planned runs", ""])
    for r in planned_runs:
        lines.append(f"- {r}")
    path.write_text("\n".join(lines), encoding="utf-8")
