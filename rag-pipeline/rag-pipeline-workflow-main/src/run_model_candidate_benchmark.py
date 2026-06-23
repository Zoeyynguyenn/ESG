"""Overnight model candidate benchmark on company_public_dev lane."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

CANDIDATE_CSV_FIELDS = [
    "run_id",
    "config_id",
    "dataset_lane",
    "benchmark_kind",
    "vector_store",
    "qdrant_status",
    "chunking",
    "embedding_model",
    "embedding_model_effective",
    "retrieval_mode",
    "retrieval_mode_effective",
    "reranker",
    "reranker_effective",
    "reranker_effective_model",
    "candidate_pool",
    "answer_mode",
    "llm_provider",
    "retrieval_hit_rate",
    "citation_correctness",
    "groundedness",
    "answer_correctness",
    "insufficient_information_handling",
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "ragas_status",
    "ragas_reason",
    "model_judge",
    "index_build_time",
    "query_time_avg",
    "reranker_latency",
    "latency",
    "latency_normalized",
    "composite_score",
    "status",
    "error_code",
    "error_reason",
    "started_at",
    "ended_at",
    "ingest_status",
]


def _load_yaml(path: Path) -> Dict[str, Any]:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_dotenv(base_dir: Path) -> None:
    def _apply(path: Path, *, override: bool) -> None:
        if not path.exists():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            key = k.strip()
            val = v.strip().strip('"').strip("'")
            if not key or not val:
                continue
            if override or key not in os.environ:
                os.environ[key] = val

    _apply(base_dir / ".env", override=False)
    _apply(base_dir / ".env.local", override=False)
    if not os.environ.get("OPENAI_BASE_URL", "").strip():
        os.environ.pop("OPENAI_BASE_URL", None)


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


def _compute_composite(rows: List[Dict[str, Any]], weights: Dict[str, float]) -> None:
    success = [r for r in rows if r.get("status") == "success"]
    if not success:
        for r in rows:
            r["composite_score"] = 0.0
            r["latency_normalized"] = ""
        return
    lats = [_safe_float(r.get("latency")) for r in success]
    lat_min, lat_max = min(lats), max(lats)
    for r in rows:
        if r.get("status") != "success":
            r["composite_score"] = 0.0
            r["latency_normalized"] = ""
            continue
        lat = _safe_float(r.get("latency"), lat_max)
        lat_norm = 1.0 if lat_max - lat_min < 1e-9 else 1 - ((lat - lat_min) / (lat_max - lat_min))
        penalty = 0.0
        score = (
            weights["retrieval_hit_rate"] * _safe_float(r.get("retrieval_hit_rate"))
            + weights["citation_correctness"] * _safe_float(r.get("citation_correctness"))
            + weights["answer_correctness"] * _safe_float(r.get("answer_correctness"))
            + weights["insufficient_information_handling"]
            * _safe_float(r.get("insufficient_information_handling"))
            + weights["groundedness"] * _safe_float(r.get("groundedness"))
            + weights["latency_normalized"] * lat_norm
            + weights["stability_penalty"] * penalty
        )
        r["latency_normalized"] = round(lat_norm, 4)
        r["composite_score"] = round(score, 4)


def _prefetch_models(models: List[str], *, local_only: bool = False) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for m in models:
        if m.startswith("openai:") or m.startswith("text-embedding-"):
            out[m] = "api_model_skip_prefetch"
            continue
        try:
            from sentence_transformers import SentenceTransformer

            if local_only:
                SentenceTransformer(m, local_files_only=True)
            else:
                SentenceTransformer(m)
            out[m] = "cached_ok"
        except Exception as exc:
            out[m] = f"model_download_failed:{exc}"
    return out


def _case_timeout_sec(cand: Dict[str, Any], cfg: Dict[str, Any], cli_override: int) -> int:
    timeout = int(cand.get("timeout_sec") or cfg["timeouts"]["default_sec"])
    if cand.get("embedding_heavy"):
        timeout = max(timeout, int(cfg["timeouts"].get("embedding_heavy_sec", timeout)))
    if cli_override > 0:
        timeout = max(timeout, cli_override)
    return timeout


def _parse_case_json(stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
    for line in reversed((stdout or "").splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            return json.loads(line)
        except Exception:
            continue
    return None


def _run_case(
    base_dir: Path,
    cand: Dict[str, Any],
    lane_cfg: Dict[str, Any],
    cfg: Dict[str, Any],
    run_id: str,
    *,
    reuse_index: bool,
    timeout_sec: int,
    enable_ragas: bool,
    ragas_max_questions: int = 10,
) -> Dict[str, Any]:
    lane = cfg["lane"]
    reranker = cand.get("reranker", "none")
    reranker_model = cand.get("reranker_model", "")
    reranker_backend = cand.get("reranker_backend", "")
    pool = int(cand.get("candidate_pool", 24))
    company_filter = str(cand.get("company_filter") or lane_cfg.get("company_filter") or "").strip()
    corpus_version = str(cand.get("corpus_version") or cfg.get("corpus_version") or "").strip()
    eval_rel = str(cand.get("eval_set_path") or cfg.get("eval_set_path") or "").strip()
    answer_mode = str(cand.get("answer_mode") or "extractive").strip().lower()
    cmd = [
        sys.executable,
        str(base_dir / "src" / "run_benchmark_case.py"),
        "--run-id",
        run_id,
        "--config-id",
        cand["config_id"],
        "--dataset-lane",
        lane,
        "--benchmark-mode",
        "retrieval_only",
        "--benchmark-lane",
        lane,
        "--chunking-profile",
        str(cand.get("chunking_profile") or lane_cfg["chunking_profile"]),
        "--chunk-size",
        str(cand.get("chunk_size") or lane_cfg["chunk_size"]),
        "--chunk-overlap",
        str(cand.get("chunk_overlap") or lane_cfg["chunk_overlap"]),
        "--embedding-model",
        cand["embedding_model"],
        "--retrieval-mode",
        cand["retrieval_mode"],
        "--reranker",
        reranker,
        "--top-k",
        str(lane_cfg["top_k"]),
        "--pool",
        str(pool),
        "--index-key",
        cand["config_id"],
        "--parser-version",
        cfg["parser_version"],
        "--corpus-version",
        corpus_version,
        "--corpus-ratio",
        str(cfg["lane_config"]["corpus_ratio"]),
        "--eval-max-questions",
        str(cfg["lane_config"]["eval_questions"]),
        "--reuse-index",
        "true" if reuse_index else "false",
        "--cache-root",
        cfg["cache_root"],
        "--eval-set-path",
        str(base_dir / eval_rel),
        "--vector-store",
        cand.get("vector_store", "chroma"),
        "--pdf-parser",
        str(cand.get("pdf_parser") or lane_cfg.get("pdf_parser") or "pypdf"),
        "--collect-failure-audit",
        "--answer-mode",
        answer_mode,
    ]
    if company_filter:
        cmd.extend(["--company-filter", company_filter])
    if reranker_model:
        cmd.extend(["--reranker-model", reranker_model])
    if reranker_backend:
        cmd.extend(["--reranker-backend", reranker_backend])
    if enable_ragas:
        cmd.append("--enable-ragas")
        cmd.extend(["--ragas-max-questions", str(ragas_max_questions)])
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(base_dir),
            timeout=timeout_sec,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {
            "run_id": run_id,
            "config_id": cand["config_id"],
            "dataset_lane": lane,
            "benchmark_kind": "model_candidate",
            "status": "timeout",
            "error_code": "case_timeout_dev_lane",
            "error_reason": f"case_timeout_dev_lane:{timeout_sec}s",
        }
    parsed = _parse_case_json(proc.stdout or "", proc.stderr or "")
    if parsed:
        return parsed
    return {
        "run_id": run_id,
        "config_id": cand["config_id"],
        "dataset_lane": lane,
        "benchmark_kind": "model_candidate",
        "status": "failed",
        "error_code": "invalid_case_output",
        "error_reason": (proc.stderr or proc.stdout or "")[:1000],
    }


def _write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def _merge_into_benchmark_csv(base_dir: Path, candidate_rows: List[Dict[str, Any]]) -> None:
    main_csv = base_dir / "reports" / "benchmark_results.csv"
    existing: List[Dict[str, Any]] = []
    if main_csv.exists():
        with main_csv.open(encoding="utf-8", newline="") as f:
            existing = list(csv.DictReader(f))
    kept = [r for r in existing if r.get("benchmark_kind") != "model_candidate"]
    merged = kept + candidate_rows
    if not merged:
        return
    fields = list(merged[0].keys())
    for r in merged:
        for k in r:
            if k not in fields:
                fields.append(k)
    tmp = main_csv.with_suffix(".csv.tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in merged:
                w.writerow(r)
        tmp.replace(main_csv)
    except OSError as exc:
        print(f"WARN: skip merge into {main_csv.name}: {exc}", file=sys.stderr)


def _write_failure_audit(path: Path, rows: List[Dict[str, Any]], prefetch: Dict[str, str]) -> None:
    lines = [
        "# Model Candidate Failure Audit",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Model prefetch",
        "",
        "| model | status |",
        "|---|---|",
    ]
    for m, st in prefetch.items():
        lines.append(f"| `{m}` | {st[:80]} |")
    lines.extend(["", "## Case status", "", "| config_id | status | error_code | error_reason |", "|---|---|---|---|"])
    for r in rows:
        lines.append(
            f"| `{r.get('config_id')}` | {r.get('status')} | {r.get('error_code','')} | "
            f"{str(r.get('error_reason',''))[:100]} |"
        )
    lines.extend(["", "## Sample questions (per config)", ""])
    for r in rows:
        samples = r.get("failure_audit_samples")
        if isinstance(samples, str):
            try:
                samples = json.loads(samples)
            except Exception:
                samples = []
        if not samples:
            continue
        lines.append(f"### `{r.get('config_id')}`")
        lines.append("")
        for s in samples[:5]:
            lines.append(f"- **{s.get('question_id')}**: hit={s.get('retrieval_hit')} cit={s.get('citation_correct')}")
            lines.append(f"  - expected: `{s.get('expected_source','')[:80]}`")
            lines.append(f"  - normalized_expected: `{str(s.get('normalized_expected_source',''))[:80]}`")
            lines.append(f"  - normalized_top: {s.get('normalized_top_sources')}")
            lines.append(f"  - match_reason: `{s.get('match_reason','')}` | fail_kind: `{s.get('fail_kind','')}`")
            if s.get("expected_record_id") or s.get("expected_doc_id"):
                lines.append(
                    f"  - expected_record_id/doc_id: `{s.get('expected_record_id','')}` / `{s.get('expected_doc_id','')}`"
                )
            lines.append(f"  - top: {s.get('top_sources')}")
            diag = []
            if not s.get("retrieval_hit"):
                if s.get("fail_kind") == "alias_mismatch":
                    diag.append("alias_mismatch")
                else:
                    diag.append("retrieval_miss")
            if s.get("retrieval_hit") and not s.get("citation_correct"):
                diag.append("citation_top1_miss")
            lines.append(f"  - diagnosis: {', '.join(diag) or 'ok'}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_candidate_summary(path: Path, rows: List[Dict[str, Any]], prefetch: Dict[str, str]) -> None:
    success = [r for r in rows if r.get("status") == "success"]
    ranked = sorted(success, key=lambda x: _safe_float(x.get("composite_score")), reverse=True)
    top = ranked[0] if ranked else None

    def _rng(key: str) -> str:
        vals = [_safe_float(r.get(key)) for r in success if r.get(key) not in (None, "")]
        return f"{min(vals):.4f}-{max(vals):.4f}" if vals else "-"

    lines = [
        "# Model Candidate Benchmark Summary",
        "",
        "## Tra loi nhanh",
        "",
        f"1. Baseline nhe: `minilm_dense_none` hoac `minilm_hybrid_none`",
        f"2. BGE-M3 chay thanh cong: **{any(r.get('status')=='success' and 'bge' in r.get('config_id','') for r in rows)}**",
        f"3. multilingual-e5 chay thanh cong: **{any(r.get('status')=='success' and 'multilingual' in r.get('config_id','') for r in rows)}**",
        f"4. Config tot nhat: `{top['config_id'] if top else '-'}` (composite={top.get('composite_score') if top else '-'})",
        f"5. Hybrid vs dense: xem bang duoi (retrieval_hit {_rng('retrieval_hit_rate')})",
        f"6. Reranker: so `*_rerank` vs `*_none`",
        f"7. Qdrant: blocked (khong implement trong backbone V6)",
        f"8. RAGAS: chi top configs, max questions tu env",
        "",
        "## Bang ket qua",
        "",
        "| rank | config_id | status | hit | cit | composite | latency | index_build |",
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for i, r in enumerate(ranked, 1):
        lines.append(
            f"| {i} | `{r.get('config_id')}` | {r.get('status')} | {r.get('retrieval_hit_rate')} | "
            f"{r.get('citation_correctness')} | {r.get('composite_score')} | {r.get('latency')} | {r.get('index_build_time')} |"
        )
    for r in rows:
        if r.get("status") != "success":
            lines.append(
                f"| - | `{r.get('config_id')}` | **{r.get('status')}** | - | - | - | {r.get('latency','')} | - |"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_dashboard(path: Path, rows: List[Dict[str, Any]]) -> None:
    from run_benchmark_matrix import _write_html_dashboard

    _write_html_dashboard(path, rows)


def _apply_ragas_phase(
    runs: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    lane_cfg: Dict[str, Any],
    cfg: Dict[str, Any],
    base_dir: Path,
    *,
    ragas_enabled: bool,
    has_key: bool,
    ragas_top_n: int,
    max_q: int,
) -> None:
    if ragas_enabled and has_key:
        pending = [
            r
            for r in runs
            if r.get("status") == "success" and (r.get("ragas_status") or "skipped") == "skipped"
        ]
        if not pending:
            return
        ranked = sorted(
            pending,
            key=lambda x: _safe_float(x.get("composite_score")),
            reverse=True,
        )[: max(1, ragas_top_n)]
        print(f"RAGAS on top {len(ranked)} configs, max {max_q} questions each...")
        for r in ranked:
            cand = next(c for c in candidates if c["config_id"] == r["config_id"])
            p2 = _run_case(
                base_dir,
                cand,
                lane_cfg,
                cfg,
                str(r.get("run_id", "ragas")) + "_ragas",
                reuse_index=True,
                timeout_sec=1800,
                enable_ragas=True,
                ragas_max_questions=max_q,
            )
            r["ragas_status"] = p2.get("ragas_status")
            r["ragas_reason"] = p2.get("ragas_reason")
            for k in ("faithfulness", "answer_relevancy", "context_precision", "context_recall"):
                r[k] = p2.get(k)
    else:
        for r in runs:
            r.setdefault("ragas_status", "disabled")
            r.setdefault(
                "ragas_reason",
                "OPENAI_API_KEY_missing" if not has_key else "RAGAS_ENABLED_false",
            )


def _results_paths(base_dir: Path, cfg: Dict[str, Any]) -> Dict[str, Path]:
    reports = base_dir / "reports"
    benchmark_id = str(cfg.get("benchmark_id") or "model_candidate")
    return {
        "csv": reports / f"{benchmark_id}_results.csv",
        "summary": reports / f"{benchmark_id}_summary.md",
        "audit": reports / f"{benchmark_id}_failure_audit.md",
        "dashboard": reports / f"{benchmark_id}_dashboard.html",
    }


def _finalize_reports(
    base_dir: Path,
    runs: List[Dict[str, Any]],
    cfg: Dict[str, Any],
    prefetch: Dict[str, str],
    *,
    ragas_enabled: bool,
    has_key: bool,
) -> Path:
    reports = base_dir / "reports"
    paths = _results_paths(base_dir, cfg)
    cand_csv = paths["csv"]
    _write_csv(cand_csv, runs, CANDIDATE_CSV_FIELDS)
    _merge_into_benchmark_csv(base_dir, runs)
    _write_candidate_summary(paths["summary"], runs, prefetch)
    _write_failure_audit(paths["audit"], runs, prefetch)
    _write_dashboard(paths["dashboard"], runs)

    top = max(
        [r for r in runs if r.get("status") == "success"],
        key=lambda x: _safe_float(x.get("composite_score")),
        default=None,
    )
    brief = reports / "notebooklm-brief-latest.md"
    brief.write_text(
        "\n".join(
            [
                "# NotebookLM Brief - Model Candidate Overnight",
                "",
                f"- lane: `{cfg['lane']}`",
                f"- cases: {len(runs)}",
                f"- top: `{top.get('config_id') if top else '-'}`",
                f"- RAGAS: {ragas_enabled and has_key}",
                "",
                f"Xem `{paths['summary'].relative_to(base_dir)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    summary = reports / "benchmark_summary.md"
    summary.write_text(
        "\n".join(
            [
                "# Benchmark Summary (model candidate overnight)",
                "",
                f"Lane: `{cfg['lane']}` | Cases: {len(runs)} | Top: `{top.get('config_id') if top else '-'}`",
                "",
                f"Chi tiet: `{paths['summary'].name}`, `{paths['audit'].name}`.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return cand_csv


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/benchmark_model_candidates_company_public_v1.yaml")
    parser.add_argument("--lane", default="company_public_dev")
    parser.add_argument("--timeout-sec", type=int, default=0)
    parser.add_argument("--reuse-index", default="true")
    parser.add_argument("--enable-ragas", default="false")
    parser.add_argument("--ragas-top-n", type=int, default=3)
    parser.add_argument("--ragas-max-questions", type=int, default=0)
    parser.add_argument("--prefetch-only", action="store_true")
    parser.add_argument(
        "--prefetch-mode",
        choices=["skip", "local", "download"],
        default="local",
        help="skip=khong prefetch; local=chi check cache local; download=cho phep tai model.",
    )
    parser.add_argument(
        "--ragas-only",
        action="store_true",
        help="Chi chay RAGAS tren top configs tu model_candidate_results.csv (khong lap 9 case).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Giu case success trong CSV, chi chay lai failed/timeout.",
    )
    args = parser.parse_args(argv)

    base_dir = Path(__file__).resolve().parent.parent
    _load_dotenv(base_dir)
    cfg = _load_yaml(base_dir / args.config)
    weights = cfg["scoring"]
    lane_cfg = cfg["lane_config"]
    candidates = cfg["candidates"]

    models = sorted({c["embedding_model"] for c in candidates})
    if args.ragas_only or args.prefetch_mode == "skip":
        prefetch = {}
    else:
        prefetch = _prefetch_models(models, local_only=(args.prefetch_mode == "local"))
    if not args.ragas_only:
        print(f"Prefetching embedding models (mode={args.prefetch_mode})...")
        for m, st in prefetch.items():
            print(f"  {m}: {st[:60]}")
    if args.prefetch_only:
        return 0

    ragas_enabled = os.getenv("RAGAS_ENABLED", "false").lower() in ("1", "true", "yes") or (
        str(args.enable_ragas).lower() in ("1", "true", "yes")
    )
    has_key = bool(os.getenv("OPENAI_API_KEY", "").strip())
    max_q = int(args.ragas_max_questions or os.getenv("RAGAS_MAX_QUESTIONS", "10"))

    if args.ragas_only:
        cand_csv = _results_paths(base_dir, cfg)["csv"]
        if not cand_csv.exists():
            print(f"ERROR: missing {cand_csv} — chay phase 1 truoc.", file=sys.stderr)
            return 1
        with cand_csv.open(encoding="utf-8", newline="") as f:
            runs = list(csv.DictReader(f))
        if not runs:
            print("ERROR: model_candidate_results.csv trong.", file=sys.stderr)
            return 1
        _compute_composite(runs, weights)
        _apply_ragas_phase(
            runs,
            candidates,
            lane_cfg,
            cfg,
            base_dir,
            ragas_enabled=ragas_enabled,
            has_key=has_key,
            ragas_top_n=args.ragas_top_n,
            max_q=max_q,
        )
        out = _finalize_reports(
            base_dir, runs, cfg, prefetch, ragas_enabled=ragas_enabled, has_key=has_key
        )
        print(json.dumps({"csv": str(out), "ragas_only": True}, indent=2))
        return 0

    reuse = str(args.reuse_index).lower() in ("1", "true", "yes")
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    runs: List[Dict[str, Any]] = []
    audit_blob: List[Dict[str, Any]] = []
    existing_by_id: Dict[str, Dict[str, Any]] = {}
    existing_order: List[str] = []
    cand_csv_path = base_dir / "reports" / "model_candidate_results.csv"
    cand_csv_path = _results_paths(base_dir, cfg)["csv"]
    if args.resume and cand_csv_path.exists():
        with cand_csv_path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                cid = row.get("config_id", "")
                existing_by_id[cid] = row
                existing_order.append(cid)
        print(f"Resume: loaded {len(existing_by_id)} rows from {cand_csv_path.name}")

    for i, cand in enumerate(candidates, 1):
        cid = cand["config_id"]
        prev = existing_by_id.get(cid)
        if args.resume and prev:
            if prev.get("status") == "success":
                runs.append(dict(prev))
                print(f"[{i}/{len(candidates)}] {cid} skip (success)")
                continue
        timeout = _case_timeout_sec(cand, cfg, args.timeout_sec)
        run_id = f"mc_{ts}_{i:03d}"
        print(f"[{i}/{len(candidates)}] {cid} (timeout={timeout}s)...")
        payload = _run_case(
            base_dir,
            cand,
            lane_cfg,
            cfg,
            run_id,
            reuse_index=reuse,
            timeout_sec=timeout,
            enable_ragas=ragas_enabled,
            ragas_max_questions=max_q,
        )
        payload.setdefault("benchmark_kind", "model_candidate")
        payload.setdefault("config_id", cand["config_id"])
        payload.setdefault("dataset_lane", cfg["lane"])
        payload.setdefault("chunking", cand.get("chunking_profile") or lane_cfg["chunking_profile"])
        payload.setdefault("candidate_pool", cand.get("candidate_pool"))
        payload.setdefault("vector_store", cand.get("vector_store", "chroma"))
        if cand.get("vector_store") == "qdrant":
            payload.setdefault("qdrant_status", payload.get("qdrant_status", "blocked"))
        samples = payload.pop("failure_audit_samples", None)
        if samples:
            audit_blob.append({"config_id": cand["config_id"], "samples": samples})
            payload["failure_audit_samples"] = json.dumps(samples, ensure_ascii=False)
        runs.append(payload)
        _compute_composite(runs, weights)
        _finalize_reports(
            base_dir,
            runs,
            cfg,
            prefetch,
            ragas_enabled=False,
            has_key=has_key,
        )
        print(f"  -> {payload.get('status')} hit={payload.get('retrieval_hit_rate')} composite={payload.get('composite_score')}")

    if args.resume and existing_by_id:
        merged = dict(existing_by_id)
        for r in runs:
            merged[r.get("config_id", "")] = r
        order = existing_order or list(merged.keys())
        extra = [k for k in merged if k not in order]
        runs = [merged[cid] for cid in order + extra]

    _compute_composite(runs, weights)
    _apply_ragas_phase(
        runs,
        candidates,
        lane_cfg,
        cfg,
        base_dir,
        ragas_enabled=ragas_enabled,
        has_key=has_key,
        ragas_top_n=args.ragas_top_n,
        max_q=max_q,
    )
    cand_csv = _finalize_reports(
        base_dir, runs, cfg, prefetch, ragas_enabled=ragas_enabled, has_key=has_key
    )
    print(json.dumps({"csv": str(cand_csv), "cases": len(runs)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
