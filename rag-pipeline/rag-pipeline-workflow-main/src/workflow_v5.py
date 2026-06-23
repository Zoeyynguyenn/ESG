"""Version 5: orchestration workflow intake -> retrieve -> extract -> gap -> report."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import BASE_DIR, DATA_DIR, FINAL_TOP_K
from extraction_v4 import (
    DEFAULT_RETRIEVAL_MODE,
    build_esg_profile,
    compute_extraction_metrics,
    load_schema,
)
from gap_analysis_v5 import analyze_gaps
from report_v5 import write_workflow_report
from retrieval_v3 import get_corpus_chunks, retrieve
from rag_stack import stack_available

INTAKE_TEMPLATE_PATH = DATA_DIR / "v5_intake_template.json"
V5_RUNS_DIR = BASE_DIR / "artifacts" / "v5_runs"
REPORTS_DIR = BASE_DIR / "reports"


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def load_intake(path: Optional[Path] = None) -> Dict[str, Any]:
    p = path or INTAKE_TEMPLATE_PATH
    if not p.exists():
        raise FileNotFoundError(f"Intake file khong ton tai: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not data.get("run_id"):
        data["run_id"] = f"v5_{_ts()}"
    return data


def resolve_intake(
    intake_path: Optional[Path] = None,
    retrieval_mode: Optional[str] = None,
    top_k: Optional[int] = None,
    run_id: Optional[str] = None,
    entity_name: Optional[str] = None,
) -> Dict[str, Any]:
    intake = load_intake(intake_path)
    if run_id:
        intake["run_id"] = run_id
    if retrieval_mode:
        intake["retrieval_mode"] = retrieval_mode
    if top_k is not None:
        intake["top_k"] = top_k
    if entity_name:
        intake["entity_name"] = entity_name
    intake.setdefault("retrieval_mode", DEFAULT_RETRIEVAL_MODE)
    intake.setdefault("top_k", FINAL_TOP_K)
    intake["resolved_at"] = datetime.now().isoformat(timespec="seconds")
    return intake


class StageLog:
    def __init__(self) -> None:
        self.stages: List[Dict[str, Any]] = []
        self._t0 = time.perf_counter()
        self._stage_start = self._t0

    def start(self, name: str) -> None:
        self._stage_start = time.perf_counter()

    def end(self, name: str, status: str, record_count: Optional[int] = None, detail: Any = None) -> None:
        dur = time.perf_counter() - self._stage_start
        entry: Dict[str, Any] = {
            "name": name,
            "status": status,
            "duration_sec": round(dur, 4),
            "record_count": record_count,
        }
        if detail is not None:
            entry["detail"] = detail
        self.stages.append(entry)

    def total_duration(self) -> float:
        return round(time.perf_counter() - self._t0, 4)


def stage_intake_input(intake: Dict[str, Any], log: StageLog) -> Dict[str, Any]:
    log.start("intake_input")
    schema = load_schema()
    all_ids = []
    for items in schema.get("groups", {}).values():
        for f in items:
            all_ids.append(f["id"])
    intake["schema_field_ids"] = all_ids
    log.end("intake_input", "ok", record_count=len(intake.get("required_fields") or []))
    return intake


def stage_load_or_select_corpus(log: StageLog) -> Dict[str, Any]:
    log.start("load_or_select_corpus")
    info: Dict[str, Any] = {"corpus": str(DATA_DIR), "chroma_ready": stack_available()}
    try:
        chunks = get_corpus_chunks()
        info["chunk_count"] = len(chunks)
        info["status"] = "ok"
        log.end("load_or_select_corpus", "ok", record_count=len(chunks), detail=info)
    except Exception as exc:
        info["status"] = "error"
        info["error"] = str(exc)
        log.end("load_or_select_corpus", "error", detail=info)
    return info


def stage_retrieve_evidence(intake: Dict[str, Any], log: StageLog) -> Dict[str, Any]:
    log.start("retrieve_evidence")
    mode = intake.get("retrieval_mode", DEFAULT_RETRIEVAL_MODE)
    top_k = int(intake.get("top_k", FINAL_TOP_K))
    probe_q = "chinh sach moi truong giam tieu thu dien"
    try:
        hits, note = retrieve(probe_q, mode, pool=24, top_k=top_k)
        info = {
            "retrieval_mode": mode,
            "probe_query": probe_q,
            "hits": len(hits),
            "retrieve_note": note,
            "top_source": hits[0].source if hits else None,
        }
        log.end("retrieve_evidence", "ok", record_count=len(hits), detail=info)
        return info
    except Exception as exc:
        info = {"retrieval_mode": mode, "error": str(exc)}
        log.end("retrieve_evidence", "error", detail=info)
        return info


def stage_extract_structured_data(intake: Dict[str, Any], log: StageLog) -> Dict[str, Any]:
    log.start("extract_structured_data")
    mode = intake.get("retrieval_mode", DEFAULT_RETRIEVAL_MODE)
    top_k = int(intake.get("top_k", FINAL_TOP_K))
    profile = build_esg_profile(retrieval_mode=mode, top_k=top_k)
    if intake.get("entity_name"):
        profile["entity"] = intake["entity_name"]
    profile["run_id"] = intake.get("run_id")
    profile["intake_framework"] = intake.get("target_framework")
    metrics = compute_extraction_metrics(profile)
    log.end("extract_structured_data", "ok", record_count=profile.get("field_count"), detail=metrics)
    return {"profile": profile, "extraction_metrics": metrics}


def stage_gap_analysis(
    intake: Dict[str, Any],
    profile: Dict[str, Any],
    extraction_metrics: Dict[str, Any],
    log: StageLog,
) -> Dict[str, Any]:
    log.start("gap_analysis")
    gap = analyze_gaps(profile, intake, extraction_metrics)
    log.end(
        "gap_analysis",
        "ok",
        record_count=gap.get("summary", {}).get("missing_count"),
        detail={
            "conflicts": gap.get("summary", {}).get("conflict_count"),
            "priority_risk_high": gap.get("summary", {}).get("priority_risk_high"),
        },
    )
    return gap


def stage_generate_report(
    intake: Dict[str, Any],
    workflow_log: Dict[str, Any],
    profile: Dict[str, Any],
    gap: Dict[str, Any],
    workflow_metrics: Dict[str, Any],
    log: StageLog,
    report_path: Optional[Path] = None,
) -> Path:
    log.start("generate_report")
    path = report_path or (REPORTS_DIR / f"v5-workflow-report-{_ts()}.md")
    write_workflow_report(path, intake, workflow_log, profile, gap, workflow_metrics)
    log.end("generate_report", "ok", record_count=1, detail=str(path))
    return path


def compute_workflow_metrics(
    extraction_metrics: Dict[str, Any],
    gap: Dict[str, Any],
    log: StageLog,
    success: bool,
) -> Dict[str, Any]:
    return {
        "execution_success": success,
        "end_to_end_duration_sec": log.total_duration(),
        "extraction_coverage_rate": extraction_metrics.get("field_coverage_rate"),
        "verified_rate": extraction_metrics.get("verified_rate"),
        "insufficient_rate": extraction_metrics.get("insufficient_rate"),
        "conflict_rate": extraction_metrics.get("conflict_rate"),
        "evidence_presence_rate": extraction_metrics.get("evidence_presence_rate"),
        "priority_field_completion_rate": gap.get("summary", {}).get(
            "priority_field_completion_rate"
        ),
        "required_missing_count": gap.get("summary", {}).get("required_missing_count"),
        "priority_risk_high_count": gap.get("summary", {}).get("priority_risk_high"),
    }


def assess_v5_status(workflow_metrics: Dict[str, Any], artifacts_ok: bool) -> str:
    if not workflow_metrics.get("execution_success") or not artifacts_ok:
        return "not_pass"
    if workflow_metrics.get("extraction_coverage_rate", 0) >= 0.5 and artifacts_ok:
        return "pass_with_limits"
    return "not_pass"


def run_v5_workflow(
    intake_path: Optional[Path] = None,
    retrieval_mode: Optional[str] = None,
    top_k: Optional[int] = None,
    run_id: Optional[str] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    log = StageLog()
    success = False
    run_dir: Optional[Path] = None
    report_path: Optional[Path] = None

    try:
        intake = resolve_intake(intake_path, retrieval_mode, top_k, run_id)
        intake = stage_intake_input(intake, log)

        run_dir = output_dir or (V5_RUNS_DIR / intake["run_id"])
        run_dir.mkdir(parents=True, exist_ok=True)

        corpus_info = stage_load_or_select_corpus(log)
        retrieve_info = stage_retrieve_evidence(intake, log)
        extract_out = stage_extract_structured_data(intake, log)
        profile = extract_out["profile"]
        extraction_metrics = extract_out["extraction_metrics"]
        gap = stage_gap_analysis(intake, profile, extraction_metrics, log)

        workflow_log_body = {
            "run_id": intake["run_id"],
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "corpus_info": corpus_info,
            "retrieve_info": retrieve_info,
            "stages": log.stages,
            "execution_success": False,
        }
        workflow_metrics = compute_workflow_metrics(extraction_metrics, gap, log, False)

        (run_dir / "intake_resolved.json").write_text(
            json.dumps(intake, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (run_dir / "extracted_profile.json").write_text(
            json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (run_dir / "gap_analysis.json").write_text(
            json.dumps(gap, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        report_path = stage_generate_report(
            intake, workflow_log_body, profile, gap, workflow_metrics, log
        )

        success = True
        workflow_metrics["execution_success"] = True
        workflow_log_body["execution_success"] = True
        workflow_log_body["end_to_end_duration_sec"] = log.total_duration()
        workflow_log_body["workflow_metrics"] = workflow_metrics
        workflow_log_body["report_path"] = str(report_path)

        (run_dir / "workflow_log.json").write_text(
            json.dumps(workflow_log_body, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        v5_status = assess_v5_status(workflow_metrics, artifacts_ok=True)
        return {
            "v5_status": v5_status,
            "advance_v6": "chua",
            "workflow_metrics": workflow_metrics,
            "run_dir": str(run_dir),
            "report_path": str(report_path),
            "gap_analysis": gap,
            "intake": intake,
        }
    except Exception as exc:
        workflow_log_body = {
            "run_id": run_id or "unknown",
            "execution_success": False,
            "error": str(exc),
            "stages": log.stages,
            "end_to_end_duration_sec": log.total_duration(),
        }
        if run_dir:
            (run_dir / "workflow_log.json").write_text(
                json.dumps(workflow_log_body, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        raise
