"""Helpers cho benchmark matrix: resume, error taxonomy, matrix hash."""

from __future__ import annotations

import csv
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ERROR_CODES = (
    "model_not_cached_local",
    "case_timeout_dev_lane",
    "ingest_failed",
    "benchmark_eval_failed",
    "invalid_case_output",
    "runtime_exception",
    "unknown",
)


def matrix_fingerprint(cfg: Dict[str, Any], mode: str, lane: str) -> str:
    """Hash ngan de match resume theo phien ban matrix + mode/lane."""
    stagewise = cfg.get("stagewise", {})
    chunk_ids = stagewise.get("dev_chunking_ids") or [
        c["id"] for c in cfg.get("dimensions", {}).get("chunking", [])
    ]
    payload = {
        "benchmark_id": cfg.get("benchmark_id"),
        "mode": mode,
        "lane": lane,
        "dev_chunking_ids": chunk_ids
        if mode == "stagewise" and lane in ("dev", "company_public_dev")
        else "all",
        "embedding": [e["id"] for e in cfg.get("dimensions", {}).get("embedding", [])],
        "retrieval": [r["id"] for r in cfg.get("dimensions", {}).get("retrieval", [])],
        "reranker": [r["id"] for r in cfg.get("dimensions", {}).get("reranker", [])],
    }
    raw = repr(payload).encode("utf-8")
    return hashlib.md5(raw).hexdigest()[:12]


def case_match_key(
    config_id: str,
    dataset_lane: str,
    benchmark_kind: str,
    mode: str,
    matrix_hash: str,
) -> Tuple[str, str, str, str, str]:
    return (config_id, dataset_lane, benchmark_kind, mode, matrix_hash)


def normalize_error_code(error_reason: str, status: str = "") -> str:
    if status == "timeout":
        return "case_timeout_dev_lane"
    if not error_reason:
        return ""
    reason = str(error_reason)
    for code in ERROR_CODES:
        if reason.startswith(code):
            return code
    if reason.startswith("model_not_cached_local"):
        return "model_not_cached_local"
    if "invalid_case_output" in reason:
        return "invalid_case_output"
    return "runtime_exception"


def load_results_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def index_results_by_key(
    rows: List[Dict[str, Any]],
    benchmark_kind: str,
    mode: str,
    matrix_hash: str,
) -> Dict[Tuple[str, str, str, str, str], Dict[str, Any]]:
    out: Dict[Tuple[str, str, str, str, str], Dict[str, Any]] = {}
    for row in rows:
        lane = row.get("dataset_lane", "")
        cid = row.get("config_id", "")
        bk = row.get("benchmark_kind") or benchmark_kind
        md = row.get("benchmark_mode") or mode
        mh = row.get("matrix_hash") or matrix_hash
        key = case_match_key(cid, lane, bk, md, mh)
        prev = out.get(key)
        if prev is None or _run_id_ts(row.get("run_id", "")) >= _run_id_ts(prev.get("run_id", "")):
            out[key] = row
    return out


def _run_id_ts(run_id: str) -> str:
    m = re.search(r"bench_(\d{8}-\d{6})", run_id or "")
    return m.group(1) if m else ""


def should_skip_case(
    existing: Optional[Dict[str, Any]],
    *,
    resume: bool,
    force_rerun: bool,
) -> bool:
    if force_rerun or not resume or not existing:
        return False
    return str(existing.get("status", "")).lower() == "success"


def archive_csv(csv_path: Path) -> Optional[Path]:
    if not csv_path.exists():
        return None
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = csv_path.parent / f"benchmark_results_archive_{ts}.csv"
    archive.write_bytes(csv_path.read_bytes())
    return archive


def stagewise_chunking_dims(cfg: Dict[str, Any], mode: str, lane: str) -> List[Dict[str, Any]]:
    all_chunking = cfg["dimensions"]["chunking"]
    if mode != "stagewise" or lane not in ("dev", "company_public_dev"):
        return all_chunking
    allow = cfg.get("stagewise", {}).get("dev_chunking_ids")
    if not allow:
        return all_chunking
    allow_set = set(allow)
    return [c for c in all_chunking if c["id"] in allow_set]
