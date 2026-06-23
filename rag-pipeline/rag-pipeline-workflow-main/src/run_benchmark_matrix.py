"""Benchmark matrix runner voi stage-wise + dataset lanes + cache reuse."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _load_yaml(path: Path) -> Dict[str, Any]:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _build_full_cases(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    dims = cfg["dimensions"]
    cases = []
    for chunking, embedding, retrieval, reranker in itertools.product(
        dims["chunking"], dims["embedding"], dims["retrieval"], dims["reranker"]
    ):
        cid = f"{chunking['id']}__{embedding['id']}__{retrieval['id']}__{reranker['id']}"
        mode = retrieval["mode"]
        if reranker["enabled"] and retrieval["id"] == "hybrid_bm25_dense":
            mode = reranker["retrieval_mode_override"] or mode
        cases.append(
            {
                "config_id": cid,
                "chunking": chunking["id"],
                "chunking_profile": chunking["profile"],
                "chunk_size": chunking["chunk_size"],
                "chunk_overlap": chunking["chunk_overlap"],
                "embedding_model": embedding["model"],
                "retrieval_mode": mode,
                "retrieval_id": retrieval["id"],
                "reranker": reranker["id"],
                "reranker_model": reranker.get("reranker_model") or "",
            }
        )
    return cases


def _default_case(cfg: Dict[str, Any]) -> Dict[str, Any]:
    dims = cfg["dimensions"]
    c = dims["chunking"][0]
    e = dims["embedding"][0]
    r = dims["retrieval"][0]
    rr = dims["reranker"][0]
    return {
        "chunking": c["id"],
        "chunking_profile": c["profile"],
        "chunk_size": c["chunk_size"],
        "chunk_overlap": c["chunk_overlap"],
        "embedding_model": e["model"],
        "retrieval_mode": r["mode"],
        "retrieval_id": r["id"],
        "reranker": rr["id"],
        "reranker_model": rr.get("reranker_model") or "",
    }


def _stagewise_cases(cfg: Dict[str, Any], lane: str = "dev") -> List[Dict[str, Any]]:
    from benchmark_utils import stagewise_chunking_dims

    dims = cfg["dimensions"]
    base = _default_case(cfg)
    out: List[Dict[str, Any]] = []
    chunking_list = stagewise_chunking_dims(cfg, "stagewise", lane)

    for c in chunking_list:
        out.append(
            {
                **base,
                "config_id": f"stageA_chunking__{c['id']}",
                "chunking": c["id"],
                "chunking_profile": c["profile"],
                "chunk_size": c["chunk_size"],
                "chunk_overlap": c["chunk_overlap"],
            }
        )
    for e in dims["embedding"]:
        out.append(
            {
                **base,
                "config_id": f"stageA_embedding__{e['id']}",
                "embedding_model": e["model"],
            }
        )
    for r in dims["retrieval"]:
        out.append(
            {
                **base,
                "config_id": f"stageA_retrieval__{r['id']}",
                "retrieval_id": r["id"],
                "retrieval_mode": r["mode"],
            }
        )
    for rr in dims["reranker"]:
        # Reranker stage A phai chay tren hybrid (neu khong thi gan nhu vo nghia).
        # Dua retrieval base ve hybrid_bm25_dense, va neu reranker enabled thi dung override rerank mode.
        retrieval_id = "hybrid_bm25_dense"
        retrieval_mode = "hybrid_dense_bm25"
        if rr["enabled"]:
            retrieval_mode = rr.get("retrieval_mode_override") or retrieval_mode
        pool_override = max(int(cfg.get("fixed", {}).get("pool", 24)), 64)
        out.append(
            {
                **base,
                "config_id": f"stageA_reranker__{rr['id']}",
                "reranker": rr["id"],
                "reranker_model": rr.get("reranker_model") or "",
                "retrieval_id": retrieval_id,
                "retrieval_mode": retrieval_mode,
                "pool_override": pool_override,
            }
        )
    return out


def _focused_cases(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    full = _build_full_cases(cfg)
    # deterministic sampled focused set ~12
    sorted_full = sorted(full, key=lambda x: hashlib.md5(x["config_id"].encode("utf-8")).hexdigest())
    return sorted(sorted_full[:12], key=lambda x: x["config_id"])


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
    lats = [_safe_float(r.get("latency"), 0.0) for r in success]
    lat_min, lat_max = min(lats), max(lats)
    for r in rows:
        if r.get("status") != "success":
            r["composite_score"] = 0.0
            r["latency_normalized"] = ""
            continue
        lat = _safe_float(r.get("latency"), lat_max)
        latency_norm = 1.0 if lat_max - lat_min < 1e-9 else 1 - ((lat - lat_min) / (lat_max - lat_min))
        score = (
            weights["retrieval_hit_rate"] * _safe_float(r.get("retrieval_hit_rate"))
            + weights["citation_correctness"] * _safe_float(r.get("citation_correctness"))
            + weights["verified_rate"] * _safe_float(r.get("verified_rate"))
            + weights["priority_field_completion"] * _safe_float(r.get("priority_field_completion"))
            + weights["one_minus_insufficient_rate"] * (1 - _safe_float(r.get("insufficient_rate")))
            + weights["one_minus_conflict_rate"] * (1 - _safe_float(r.get("conflict_rate")))
            + weights["latency_normalized"] * latency_norm
        )
        r["latency_normalized"] = round(latency_norm, 4)
        r["composite_score"] = round(score, 4)


CSV_FIELDS = [
    "run_id",
    "config_id",
    "dataset_lane",
    "benchmark_mode",
    "benchmark_kind",
    "matrix_hash",
    "chunking",
    "embedding_model",
    "embedding_model_effective",
    "retrieval_mode",
    "retrieval_mode_effective",
    "reranker",
    "reranker_effective",
    "extraction_mode",
    "verification_mode",
    "retrieval_hit_rate",
    "citation_correctness",
    "field_coverage",
    "verified_rate",
    "insufficient_rate",
    "conflict_rate",
    "priority_field_completion",
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
    "latency",
    "latency_normalized",
    "composite_score",
    "status",
    "error_code",
    "error_reason",
    "started_at",
    "ended_at",
    "ingest_status",
    "resume_action",
]


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fields = CSV_FIELDS
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fields})


def _render_summary(
    rows: List[Dict[str, Any]],
    weights: Dict[str, float],
    mode: str,
    lane: str,
    *,
    recovery_notes: str = "",
    ragas_policy: str = "",
) -> str:
    total = len(rows)
    success = [r for r in rows if r.get("status") == "success"]
    planned = [r for r in rows if r.get("status") == "planned"]
    failed = [r for r in rows if r.get("status") not in ("success", "planned")]
    ranked = sorted(success, key=lambda x: _safe_float(x.get("composite_score"), 0.0), reverse=True)

    by_lane: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        by_lane.setdefault(r.get("dataset_lane", "unknown"), []).append(r)

    lines = [
        "# Benchmark Summary",
        "",
        f"- mode: `{mode}`",
        f"- lane: `{lane}`",
        f"- tong run: **{total}**",
        f"- thanh cong: **{len(success)}**",
        f"- planned: **{len(planned)}**",
        f"- that bai: **{len(failed)}**",
        "",
        "## So run theo lane",
        "",
        "| lane | total | success | planned | failed |",
        "|---|---:|---:|---:|---:|",
    ]
    for ln, items in sorted(by_lane.items()):
        s = sum(1 for x in items if x.get("status") == "success")
        p = sum(1 for x in items if x.get("status") == "planned")
        f = len(items) - s - p
        lines.append(f"| {ln} | {len(items)} | {s} | {p} | {f} |")

    lines.extend(
        [
            "",
            "## Top config moi lane",
            "",
            "| lane | top_config | composite_score | latency |",
            "|---|---|---:|---:|",
        ]
    )
    for ln, items in sorted(by_lane.items()):
        sitems = sorted(
            [x for x in items if x.get("status") == "success"],
            key=lambda x: _safe_float(x.get("composite_score"), 0.0),
            reverse=True,
        )
        if sitems:
            top = sitems[0]
            lines.append(f"| {ln} | `{top['config_id']}` | {top.get('composite_score')} | {top.get('latency')} |")
        else:
            lines.append(f"| {ln} | - | - | - |")

    lines.extend(
        [
            "",
            "## Top 5 overall",
            "",
            "| rank | config_id | lane | score | retrieval_hit | citation | verified | latency |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for i, r in enumerate(ranked[:5], 1):
        lines.append(
            f"| {i} | `{r['config_id']}` | {r.get('dataset_lane')} | {r.get('composite_score')} | "
            f"{r.get('retrieval_hit_rate')} | {r.get('citation_correctness')} | {r.get('verified_rate')} | {r.get('latency')} |"
        )

    lines.extend(["", "## De xuat config final", ""])
    if ranked:
        lines.append(f"- De xuat tam thoi: `{ranked[0]['config_id']}` (lane={ranked[0].get('dataset_lane')}).")
    else:
        lines.append("- Chua de xuat duoc vi chua co run success.")

    if success:
        avg_lat = statistics.mean(_safe_float(x.get("latency")) for x in success)
        avg_score = statistics.mean(_safe_float(x.get("composite_score")) for x in success)
        lines.extend(["", "## Trade-off chat luong vs thoi gian", "", f"- latency TB: {avg_lat:.2f}s", f"- composite TB: {avg_score:.4f}"])

    if recovery_notes:
        lines.extend(["", "## Recovery / resume", "", recovery_notes, ""])
    if ragas_policy:
        lines.extend(["", "## RAGAS policy", "", ragas_policy, ""])
    cmp = _lane_comparison_section(rows)
    if cmp:
        lines.append(cmp)
    lines.extend(["", "## Cong thuc composite", "", "```json", json.dumps(weights, indent=2), "```", ""])
    return "\n".join(lines)


def _ragas_policy_text(mode: str, enable_ragas: bool) -> str:
    has_key = bool(__import__("os").getenv("OPENAI_API_KEY", "").strip())
    if mode == "stagewise":
        return (
            "- Stagewise dev: metric noi bo; RAGAS **khong bat** (`--enable-ragas` mac dinh false).\n"
            f"- OPENAI_API_KEY: {'co' if has_key else 'khong co'} (khong anh huong stagewise dev)."
        )
    if enable_ragas and has_key:
        return (
            "- RAGAS: **enabled** khi co key (tich hop day du chua co — co the fallback).\n"
            f"- model_judge: `{__import__('os').getenv('OPENAI_MODEL', 'gpt-4o-mini')}`"
        )
    if enable_ragas and not has_key:
        return "- RAGAS: **disabled** — `OPENAI_API_KEY_missing`."
    return "- RAGAS: **disabled** — `--enable-ragas` false."


def _run_case_subprocess(
    cmd: List[str],
    *,
    cwd: str,
    timeout_sec: int,
) -> tuple[Dict[str, Any], str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout_sec)
    except subprocess.TimeoutExpired as exc:
        partial = (exc.stdout or "").strip().splitlines() if exc.stdout else []
        return (
            {
                "status": "timeout",
                "error_reason": "case_timeout_dev_lane:subprocess exceeded limit",
                "error_code": "case_timeout_dev_lane",
            },
            "timeout",
        )
    stdout = (proc.stdout or "").strip().splitlines()
    payload: Dict[str, Any] = {}
    if stdout:
        try:
            payload = json.loads(stdout[-1])
        except Exception:
            payload = {}
    if not payload:
        payload = {
            "status": "failed",
            "error_reason": f"invalid_case_output:{(proc.stderr or proc.stdout or '')[:200]}",
        }
    return payload, "ran"


def _enrich_row(
    payload: Dict[str, Any],
    c: Dict[str, Any],
    cfg: Dict[str, Any],
    args: argparse.Namespace,
    matrix_hash: str,
    resume_action: str,
) -> Dict[str, Any]:
    from benchmark_utils import normalize_error_code

    payload.setdefault("dataset_lane", args.lane)
    payload.setdefault("config_id", c["config_id"])
    payload.setdefault("chunking", c["chunking"])
    payload.setdefault("embedding_model", c["embedding_model"])
    payload.setdefault("retrieval_mode", c["retrieval_mode"])
    payload.setdefault("reranker", c["reranker"])
    payload.setdefault("extraction_mode", cfg["fixed"]["extraction_mode"])
    payload.setdefault("verification_mode", cfg["fixed"]["verification_mode"])
    payload.setdefault("benchmark_mode", args.mode)
    payload.setdefault("benchmark_kind", args.benchmark_kind)
    payload.setdefault("matrix_hash", matrix_hash)
    payload.setdefault("resume_action", resume_action)
    status = str(payload.get("status", ""))
    payload["error_code"] = normalize_error_code(str(payload.get("error_reason", "")), status)
    return payload


def _write_dryrun_validation(
    path: Path,
    cases: List[Dict[str, Any]],
    args: argparse.Namespace,
    matrix_hash: str,
    existing_index: Dict[Any, Any],
    resume_plan: List[Dict[str, str]],
) -> None:
    lines = [
        "# Benchmark Dry-run Validation",
        "",
        f"- mode: `{args.mode}`",
        f"- lane: `{args.lane}`",
        f"- benchmark_kind: `{args.benchmark_kind}`",
        f"- matrix_hash: `{matrix_hash}`",
        f"- stagewise_dev_expected_cases: **{len(cases)}**",
        f"- case_timeout_sec: **{args.case_timeout_sec}**",
        f"- resume: **{args.resume}**",
        f"- force_rerun: **{args.force_rerun}**",
        f"- enable_ragas: **{args.enable_ragas}**",
        "",
        "## Cases planned",
        "",
        "| # | config_id | resume_action |",
        "|---:|---|---|",
    ]
    for i, item in enumerate(resume_plan, 1):
        lines.append(f"| {i} | `{item['config_id']}` | {item['resume_action']} |")
    lines.extend(
        [
            "",
            "## Resume index (existing CSV)",
            "",
            f"- So key da index: **{len(existing_index)}**",
            "",
            "## Schema CSV",
            "",
            f"- Cot: {', '.join(CSV_FIELDS)}",
            "",
            "## Ghi chu",
            "",
            "- Dry-run **khong** ghi de `benchmark_results.csv`.",
            "- Chay that: `python src/run_benchmark.py --mode stagewise --lane dev --benchmark-kind retrieval_only --reuse-index true --resume true`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_html_dashboard(path: Path, rows: List[Dict[str, Any]]) -> None:
    rows_json = json.dumps(rows, ensure_ascii=False)
    html = f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"/><title>Benchmark Dashboard</title>
<style>body{{font-family:Arial,sans-serif;margin:20px}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{border:1px solid #ddd;padding:6px}}th{{cursor:pointer;background:#f5f5f5}}.top{{background:#eaf7ea}}.fail{{background:#fdecec}}</style>
</head><body><h1>Benchmark Dashboard</h1>
<input id="f" placeholder="filter lane/config/model..." style="width:360px"/><button onclick="render()">Apply</button>
<table id="t"></table><h2>Fail logs</h2><ul id="fails"></ul>
<script>
const rows={rows_json}; let sortKey="composite_score", sortDir="desc";
const cols=["run_id","dataset_lane","config_id","chunking","embedding_model","retrieval_mode","reranker","retrieval_hit_rate","citation_correctness","field_coverage","verified_rate","insufficient_rate","conflict_rate","priority_field_completion","latency","composite_score","status","error_reason"];
function sorted(a){{return [...a].sort((x,y)=>{{const av=x[sortKey]??"",bv=y[sortKey]??"";const an=parseFloat(av),bn=parseFloat(bv);let c=(!Number.isNaN(an)&&!Number.isNaN(bn))?(an-bn):String(av).localeCompare(String(bv));return sortDir==="asc"?c:-c;}})}}
function render(){{const q=document.getElementById("f").value.toLowerCase().trim();const filtered=rows.filter(r=>!q||JSON.stringify(r).toLowerCase().includes(q));const data=sorted(filtered);const top=data.find(r=>r.status==="success")?.config_id;const t=document.getElementById("t");t.innerHTML="";const h=document.createElement("tr");cols.forEach(c=>{{const th=document.createElement("th");th.textContent=c;th.onclick=()=>{{if(sortKey===c)sortDir=sortDir==="asc"?"desc":"asc";else{{sortKey=c;sortDir="desc";}}render();}};h.appendChild(th);}});const thead=document.createElement("thead");thead.appendChild(h);t.appendChild(thead);const tb=document.createElement("tbody");data.forEach(r=>{{const tr=document.createElement("tr");if(r.status!=="success"&&r.status!=="planned")tr.classList.add("fail");if(r.config_id===top)tr.classList.add("top");cols.forEach(c=>{{const td=document.createElement("td");td.textContent=r[c]??"";tr.appendChild(td);}});tb.appendChild(tr);}});t.appendChild(tb);const fails=document.getElementById("fails");fails.innerHTML="";data.filter(r=>r.status!=="success"&&r.status!=="planned").forEach(r=>{{const li=document.createElement("li");li.textContent=`${{r.config_id}}: ${{r.error_reason||"unknown"}}`;fails.appendChild(li);}});}}
render();
</script></body></html>"""
    path.write_text(html, encoding="utf-8")


def _write_notebooklm_brief(path: Path, rows: List[Dict[str, Any]], mode: str, lane: str) -> None:
    success = [r for r in rows if r.get("status") == "success"]
    ranked = sorted(success, key=lambda x: _safe_float(x.get("composite_score"), 0.0), reverse=True)
    top = ranked[0] if ranked else None
    lines = [
        "# NotebookLM Brief - Benchmark RAG",
        "",
        "## Muc tieu",
        "- Benchmark co kiem soat de chon cau hinh tot nhat, tiet kiem thoi gian bang stage-wise + lane.",
        "",
        "## Lane strategy",
        "- dev_subset: scan ung vien nhanh.",
        "- validation_subset: xac nhan shortlist.",
        "- full_subset: confirm top 2-3.",
        "",
        f"## Dot chay hien tai",
        f"- mode: `{mode}`",
        f"- lane: `{lane}`",
        f"- so run: {len(rows)}",
        "",
    ]
    if top:
        lines.extend(
            [
                "## Top config",
                f"- config_id: `{top['config_id']}`",
                f"- score: {top.get('composite_score')}",
                f"- retrieval_hit_rate: {top.get('retrieval_hit_rate')}",
                f"- citation_correctness: {top.get('citation_correctness')}",
                f"- verified_rate: {top.get('verified_rate')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Rui ro con lai",
            "- RAGAS co the disabled/fallback neu thieu runtime API.",
            "- Mot so model embedding/reranker co the fail neu chua cache local.",
            "",
            "## Buoc tiep theo",
            "1. Chay tiep mode stagewise lane dev.",
            "2. Lay shortlist sang focused lane validation.",
            "3. Chot top 2-3 roi final lane full.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _merge_lane_results(
    existing: List[Dict[str, Any]],
    new_runs: List[Dict[str, Any]],
    lane: str,
    mode: str,
    benchmark_kind: str,
) -> List[Dict[str, Any]]:
    """Giu ket qua lane khac, thay the dong cung lane+mode+kind."""
    kept = [
        r
        for r in existing
        if not (
            r.get("dataset_lane") == lane
            and (r.get("benchmark_mode") or mode) == mode
            and (r.get("benchmark_kind") or benchmark_kind) == benchmark_kind
        )
    ]
    return kept + new_runs


def _lane_comparison_section(rows: List[Dict[str, Any]]) -> str:
    lanes = sorted({r.get("dataset_lane", "") for r in rows if r.get("dataset_lane")})
    if len(lanes) < 2:
        return ""
    lines = [
        "",
        "## So sanh lane (metric spread)",
        "",
        "| lane | success | retrieval_hit min | retrieval_hit max | composite min | composite max |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    def _sf(v: Any) -> float:
        try:
            return float(v) if v not in (None, "") else float("nan")
        except Exception:
            return float("nan")

    for ln in lanes:
        succ = [r for r in rows if r.get("dataset_lane") == ln and r.get("status") == "success"]
        if not succ:
            lines.append(f"| {ln} | 0 | - | - | - | - |")
            continue
        hits = [_sf(r.get("retrieval_hit_rate")) for r in succ]
        comps = [_sf(r.get("composite_score")) for r in succ]
        hits = [h for h in hits if h == h]
        comps = [c for c in comps if c == c]
        lines.append(
            f"| {ln} | {len(succ)} | {min(hits) if hits else '-'} | {max(hits) if hits else '-'} | "
            f"{min(comps) if comps else '-'} | {max(comps) if comps else '-'} |"
        )
    return "\n".join(lines)


def _select_cases(cfg: Dict[str, Any], mode: str, top_n: int, lane: str = "dev") -> List[Dict[str, Any]]:
    if mode == "stagewise":
        return _stagewise_cases(cfg, lane)
    if mode == "focused":
        return _focused_cases(cfg)
    full = _build_full_cases(cfg)
    return full[: max(1, top_n)]


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", default="configs/benchmark_matrix_v1.yaml")
    parser.add_argument("--mode", choices=["stagewise", "focused", "final"], default="stagewise")
    parser.add_argument(
        "--lane",
        choices=["dev", "validation", "full", "company_public_dev", "company_export_json_dev"],
        default="dev",
    )
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument("--benchmark-kind", choices=["retrieval_only", "full_pipeline"], default="retrieval_only")
    parser.add_argument("--reuse-index", default="true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", default="true")
    parser.add_argument("--force-rerun", action="store_true")
    parser.add_argument("--case-timeout-sec", type=int, default=1200)
    parser.add_argument("--enable-ragas", action="store_true")
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument("--vector-store", choices=["chroma", "qdrant"], default="chroma")
    parser.add_argument("--embed-local-only", default="auto", choices=["auto", "true", "false"])
    parser.add_argument("--pdf-parser", default="auto", choices=["auto", "pypdf", "docling"])
    args = parser.parse_args(argv)

    args.resume = str(args.resume).lower() in ("1", "true", "yes")

    from benchmark_utils import (
        archive_csv,
        case_match_key,
        index_results_by_key,
        matrix_fingerprint,
        should_skip_case,
    )

    base_dir = Path(__file__).resolve().parent.parent
    cfg = _load_yaml(base_dir / args.matrix)
    weights = cfg["scoring"]["composite"]
    lane_cfg = cfg["dataset_lanes"][f"{args.lane}_subset"]
    corpus_version = lane_cfg.get("corpus_version") or cfg["cache"]["corpus_version"]
    eval_set_path = lane_cfg.get("eval_set_path") or cfg.get("eval_set_path")
    cases = _select_cases(cfg, args.mode, args.top_n, args.lane)
    matrix_hash = matrix_fingerprint(cfg, args.mode, args.lane)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")

    reports_dir = base_dir / "reports"
    csv_path = reports_dir / "benchmark_results.csv"
    existing_rows = []
    existing_index: Dict[Any, Any] = {}
    if csv_path.exists():
        from benchmark_utils import load_results_csv

        existing_rows = load_results_csv(csv_path)
        existing_index = index_results_by_key(
            existing_rows, args.benchmark_kind, args.mode, matrix_hash
        )

    runs: List[Dict[str, Any]] = []
    resume_plan: List[Dict[str, str]] = []
    recovery_lines: List[str] = []

    if args.dry_run:
        for c in cases:
            key = case_match_key(c["config_id"], args.lane, args.benchmark_kind, args.mode, matrix_hash)
            prev = existing_index.get(key)
            if should_skip_case(prev, resume=args.resume, force_rerun=args.force_rerun):
                action = "skip_reuse_success"
            else:
                action = "run_new"
            resume_plan.append({"config_id": c["config_id"], "resume_action": action})
        dry_path = reports_dir / "benchmark_dryrun_validation.md"
        _write_dryrun_validation(dry_path, cases, args, matrix_hash, existing_index, resume_plan)
        print(
            json.dumps(
                {
                    "mode": args.mode,
                    "lane": args.lane,
                    "cases": len(cases),
                    "matrix_hash": matrix_hash,
                    "dry_run": True,
                    "dryrun_report": str(dry_path),
                    "production_csv_preserved": str(csv_path),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.resume and csv_path.exists():
        archived = archive_csv(csv_path)
        if archived:
            recovery_lines.append(f"- Da archive CSV cu: `{archived.name}`")

    for i, c in enumerate(cases, 1):
        key = case_match_key(c["config_id"], args.lane, args.benchmark_kind, args.mode, matrix_hash)
        prev = existing_index.get(key)
        if should_skip_case(prev, resume=args.resume, force_rerun=args.force_rerun):
            reused = dict(prev)
            reused["resume_action"] = "reused_success"
            runs.append(reused)
            recovery_lines.append(f"- Reuse: `{c['config_id']}` tu `{prev.get('run_id')}`")
            print(f"[{i}/{len(cases)}] {c['config_id']} -> reused (success)")
            continue

        run_id = f"bench_{ts}_{i:03d}"
        index_key = hashlib.md5(
            f"{cfg['cache']['parser_version']}|{c['chunking_profile']}|{c['embedding_model']}|{corpus_version}|{args.lane}".encode("utf-8")
        ).hexdigest()[:16]
        enable_ragas = args.enable_ragas and args.mode in ("focused", "final")
        cmd = [
            args.python_bin,
            str(base_dir / "src" / "run_benchmark_case.py"),
            "--run-id", run_id,
            "--config-id", c["config_id"],
            "--dataset-lane", args.lane,
            "--benchmark-mode", args.benchmark_kind,
            "--chunking-profile", c["chunking_profile"],
            "--chunk-size", str(c["chunk_size"]),
            "--chunk-overlap", str(c["chunk_overlap"]),
            "--embedding-model", c["embedding_model"],
            "--retrieval-mode", c["retrieval_mode"],
            "--reranker", c["reranker"],
            "--reranker-model", c["reranker_model"],
            "--top-k", str(cfg["fixed"]["top_k"]),
            "--pool", str(cfg["fixed"]["pool"]),
            "--index-key", index_key,
            "--parser-version", cfg["cache"]["parser_version"],
            "--corpus-version", corpus_version,
            "--corpus-ratio", str(lane_cfg["corpus_ratio"]),
            "--eval-max-questions", str(lane_cfg["eval_questions"]),
            "--reuse-index", str(args.reuse_index),
            "--cache-root", cfg["cache"]["cache_root"],
            "--benchmark-lane", args.lane,
            "--vector-store", args.vector_store,
            "--embed-local-only", args.embed_local_only,
            "--pdf-parser", args.pdf_parser,
        ]
        if c.get("pool_override"):
            cmd[cmd.index("--pool") + 1] = str(c["pool_override"])
        if eval_set_path:
            cmd.extend(["--eval-set-path", str(base_dir / eval_set_path)])
        if enable_ragas:
            cmd.append("--enable-ragas")
        payload, _ = _run_case_subprocess(cmd, cwd=str(base_dir), timeout_sec=args.case_timeout_sec)
        payload.setdefault("run_id", run_id)
        payload = _enrich_row(payload, c, cfg, args, matrix_hash, "ran_new")
        runs.append(payload)
        print(f"[{i}/{len(cases)}] {c['config_id']} -> {payload.get('status')}")

    _compute_composite(runs, weights)
    md_path = reports_dir / "benchmark_summary.md"
    html_path = reports_dir / "benchmark_dashboard.html"
    brief_path = reports_dir / "notebooklm-brief-latest.md"

    recovery_notes = "\n".join(recovery_lines) if recovery_lines else "- Khong co reuse trong lan chay nay."
    ragas_txt = _ragas_policy_text(args.mode, args.enable_ragas)

    merged_rows = _merge_lane_results(existing_rows, runs, args.lane, args.mode, args.benchmark_kind)
    _write_csv(csv_path, merged_rows)
    md_path.write_text(
        _render_summary(
            merged_rows,
            weights,
            args.mode,
            args.lane,
            recovery_notes=recovery_notes,
            ragas_policy=ragas_txt,
        ),
        encoding="utf-8",
    )
    _write_html_dashboard(html_path, merged_rows)
    _write_notebooklm_brief(brief_path, merged_rows, args.mode, args.lane)

    print(
        json.dumps(
            {
                "mode": args.mode,
                "lane": args.lane,
                "benchmark_kind": args.benchmark_kind,
                "matrix_hash": matrix_hash,
                "runs": len(runs),
                "dry_run": False,
                "resume": args.resume,
                "csv": str(csv_path),
                "summary_md": str(md_path),
                "dashboard_html": str(html_path),
                "notebooklm_brief": str(brief_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
