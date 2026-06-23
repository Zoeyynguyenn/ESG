"""Embedding model comparison — smoke then full, OpenAI/OpenRouter, fair stack."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))


def _emb_cache_key(cfg: Dict[str, Any], cand: Dict[str, Any]) -> str:
    lane_cfg = cfg["lane_config"]
    emb_key = (
        cand["embedding_model"]
        .replace("/", "_")
        .replace(":", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )
    chunk_key = f"{lane_cfg['chunking_profile']}_{lane_cfg['chunk_size']}_{lane_cfg['chunk_overlap']}"
    company = str(lane_cfg.get("company_filter", "")).strip()
    key = (
        f"p={cfg['parser_version']}__c={chunk_key}__e={emb_key}"
        f"__d={cfg['corpus_version']}__lane={cfg['lane']}__vs=qdrant"
    )
    if company:
        key += f"__company={hashlib.md5(company.encode()).hexdigest()[:10]}"
    return key


def _index_dir(cfg: Dict[str, Any], cand: Dict[str, Any]) -> Path:
    return BASE / cfg["cache_root"] / "index_cache" / _emb_cache_key(cfg, cand)


def _load_dotenv() -> None:
    for name in (".env.local", ".env"):
        p = BASE / name
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if v:
                os.environ.setdefault(k, v)


def _load_yaml(path: Path) -> Dict[str, Any]:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _compute_composite(row: Dict[str, Any], weights: Dict[str, float]) -> float:
    return round(
        _safe_float(row.get("retrieval_hit_rate")) * weights.get("retrieval_hit_rate", 0.3)
        + _safe_float(row.get("citation_correctness")) * weights.get("citation_correctness", 0.2)
        + _safe_float(row.get("answer_correctness")) * weights.get("answer_correctness", 0.15)
        + _safe_float(row.get("insufficient_information_handling", row.get("insufficient_handling")))
        * weights.get("insufficient_information_handling", 0.1)
        + _safe_float(row.get("groundedness")) * weights.get("groundedness", 0.1)
        + _safe_float(row.get("latency_normalized")) * weights.get("latency_normalized", 0.05)
        - _safe_float(row.get("stability_penalty")) * weights.get("stability_penalty", 0.05),
        4,
    )


def _estimate_embed_tokens(bm25_path: Path) -> int:
    if not bm25_path.exists():
        return 0
    data = json.loads(bm25_path.read_text(encoding="utf-8"))
    chars = sum(len(c.get("text", "")) for c in data.get("chunks", []))
    return int(chars / 4)


def _estimate_cost_usd(model_key: str, tokens: int) -> float:
    from embedding_providers import EMBEDDING_CANDIDATES

    meta = EMBEDDING_CANDIDATES.get(model_key, {})
    price = float(meta.get("price_usd_per_1m_tokens", 0.02))
    return round(tokens / 1_000_000 * price, 4)


def _run_case(
    base_dir: Path,
    cand: Dict[str, Any],
    cfg: Dict[str, Any],
    run_id: str,
    *,
    eval_path: Path,
    eval_max_questions: int,
    reuse_index: bool,
    timeout_sec: int,
) -> Dict[str, Any]:
    lane = cfg["lane"]
    lane_cfg = cfg["lane_config"]
    pool = int(cand.get("candidate_pool", lane_cfg.get("candidate_pool", 64)))
    company_filter = str(lane_cfg.get("company_filter", "")).strip()
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
        lane_cfg["chunking_profile"],
        "--chunk-size",
        str(lane_cfg["chunk_size"]),
        "--chunk-overlap",
        str(lane_cfg["chunk_overlap"]),
        "--embedding-model",
        cand["embedding_model"],
        "--retrieval-mode",
        cand["retrieval_mode"],
        "--reranker",
        cand.get("reranker", "none"),
        "--top-k",
        str(lane_cfg["top_k"]),
        "--pool",
        str(pool),
        "--index-key",
        cand["config_id"],
        "--parser-version",
        cfg["parser_version"],
        "--corpus-version",
        cfg["corpus_version"],
        "--corpus-ratio",
        str(lane_cfg["corpus_ratio"]),
        "--eval-max-questions",
        str(eval_max_questions),
        "--reuse-index",
        "true" if reuse_index else "false",
        "--cache-root",
        cfg["cache_root"],
        "--eval-set-path",
        str(eval_path),
        "--vector-store",
        cand.get("vector_store", "qdrant"),
        "--answer-mode",
        cand.get("answer_mode", "generative"),
        "--collect-failure-audit",
    ]
    if company_filter:
        cmd.extend(["--company-filter", company_filter])
    env = os.environ.copy()
    for key in (
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENROUTER_API_KEY",
        "OPENROUTER_BASE_URL",
        "OPENROUTER_HTTP_REFERER",
        "OPENROUTER_APP_TITLE",
        "RAG_OPENAI_EMBED_BATCH",
    ):
        val = os.environ.get(key)
        if val:
            env[key] = val
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("RAG_BENCHMARK_LLM_PROVIDER", "openai_api")
    env.setdefault("RAG_OPENAI_EMBED_BATCH", "32")
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
            "status": "timeout",
            "error_code": "case_timeout",
            "embedding_model": cand["embedding_model"],
        }
    text = (proc.stdout or "").strip()
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return {
        "config_id": cand["config_id"],
        "status": "failed",
        "error_reason": (proc.stderr or proc.stdout or "")[:800],
        "embedding_model": cand["embedding_model"],
    }


def _screening_table_md() -> str:
    from embedding_providers import EMBEDDING_CANDIDATES

    rejected = [
        ("openrouter:google/gemini-embedding-001", "Loai", "Gia $0.15/M; trung lap tier premium voi 3-large cho JSON text-only"),
        ("openrouter:qwen/qwen3-embedding-4b", "Loai", "Trung gian voi 8B; uu tien 8B cho Korean/ESG"),
        ("openrouter:openai/text-embedding-ada-002", "Loai", "Legacy; kem hon 3-small"),
        ("openrouter:google/gemini-embedding-2-preview", "Loai", "Multimodal preview; ngoai pham vi JSON export"),
    ]
    lines = [
        "## Candidate screening",
        "",
        "| Model | Provider | Dim | Context | $/1M tok | Adoption / signal | Multilingual/KO | Trang thai |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]
    selected = {
        "openai:text-embedding-3-small",
        "openai:text-embedding-3-large",
        "openrouter:openai/text-embedding-3-large",
        "openrouter:intfloat/multilingual-e5-large",
        "openrouter:qwen/qwen3-embedding-8b",
    }
    for key, meta in EMBEDDING_CANDIDATES.items():
        if key not in selected:
            continue
        lines.append(
            f"| `{key}` | {meta['provider']} | {meta['dimensions']} | {meta['context_tokens']} | "
            f"${meta['price_usd_per_1m_tokens']:.2f} | {meta['adoption'][:60]} | {meta['multilingual_ko'][:40]} | **Chon** |"
        )
    for model, status, reason in rejected:
        lines.append(f"| `{model}` | - | - | - | - | - | - | **{status}**: {reason} |")
    lines.append("")
    lines.append("**Dieu kien tien quyet:** `reports/openai_benchmark_bias_audit.md` — benchmark du tin cay.")
    or_key = bool(os.environ.get("OPENROUTER_API_KEY", "").strip())
    lines.append(
        f"**OpenRouter API:** {'co OPENROUTER_API_KEY' if or_key else 'THIEU — cac model openrouter:* se INVALID/skipped'}"
    )
    lines.append("")
    return "\n".join(lines)


def _write_html(path: Path, rows: List[Dict[str, Any]]) -> None:
    ranked = sorted(rows, key=lambda r: _safe_float(r.get("composite_score")), reverse=True)
    trs = []
    for i, r in enumerate(ranked, 1):
        trs.append(
            f"<tr><td>{i}</td><td>{r.get('config_id','')}</td>"
            f"<td>{r.get('embedding_model','')}</td>"
            f"<td>{r.get('retrieval_hit_rate','')}</td><td>{r.get('citation_correctness','')}</td>"
            f"<td>{r.get('answer_correctness','')}</td><td>{r.get('groundedness','')}</td>"
            f"<td>{r.get('insufficient_information_handling','')}</td>"
            f"<td>{r.get('composite_score','')}</td><td>{r.get('query_time_avg','')}</td>"
            f"<td>{r.get('index_build_time','')}</td><td>${r.get('estimated_embed_cost_usd','')}</td>"
            f"<td>{r.get('status','')}</td></tr>"
        )
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Embedding model comparison</title>
<style>
body{{font-family:system-ui,sans-serif;margin:24px}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:8px;text-align:left;font-size:13px}}
th{{background:#f0f4f8}}
tr:nth-child(even){{background:#fafafa}}
</style></head><body>
<h1>OpenAI / OpenRouter embedding comparison</h1>
<p>Generated: {datetime.now().isoformat(timespec='seconds')}</p>
<table>
<thead><tr><th>#</th><th>config</th><th>embedding</th><th>hit</th><th>cit</th><th>ans</th>
<th>grd</th><th>insuf</th><th>composite</th><th>query_avg_s</th><th>index_s</th><th>est.$</th><th>status</th></tr></thead>
<tbody>
{''.join(trs)}
</tbody></table></body></html>"""
    path.write_text(html, encoding="utf-8")


def _conclusions_md(rows: List[Dict[str, Any]]) -> str:
    ok = [r for r in rows if r.get("status") == "success" and r.get("phase") == "full"]
    if not ok:
        return "## Ket luan\n\nKhong co run full thanh cong.\n"
    by_q = sorted(ok, key=lambda r: _safe_float(r.get("composite_score")), reverse=True)
    by_cost = sorted(
        ok,
        key=lambda r: (
            _safe_float(r.get("composite_score")) / max(0.0001, _safe_float(r.get("estimated_embed_cost_usd", 0.001))),
        ),
        reverse=True,
    )
    best_q = by_q[0]
    best_cp = by_cost[0]
    baseline = next((r for r in ok if "3_small" in r.get("embedding_model", "")), ok[0])
    lines = [
        "## Ket luan",
        "",
        f"1. **Chat luong (composite):** `{best_q['config_id']}` — {best_q['embedding_model']} "
        f"(composite={best_q.get('composite_score')}, hit={best_q.get('retrieval_hit_rate')}).",
        "",
        f"2. **Cost/performance:** `{best_cp['config_id']}` — est. ingest ${best_cp.get('estimated_embed_cost_usd')} "
        f"/ composite {best_cp.get('composite_score')}.",
        "",
        f"3. **Production tam thoi:** giu `{baseline['embedding_model']}` (baseline da freeze P1) "
        f"neu chenh lech chat luong vs winner < nguong nghiep vu.",
        f"   **Du phong:** `{best_q['embedding_model']}` neu can nhay multilingual/Korean hon.",
        "",
    ]
    invalid = [r for r in rows if r.get("invalid_reason")]
    if invalid:
        lines.append("### Run INVALID / loai")
        for r in invalid:
            lines.append(f"- `{r.get('config_id')}`: {r.get('invalid_reason')}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/benchmark_exportjson_embedding_compare.yaml")
    parser.add_argument("--phase", choices=["smoke", "full", "all"], default="all")
    parser.add_argument("--timeout-sec", type=int, default=3600)
    parser.add_argument("--skip-report", action="store_true")
    args = parser.parse_args(argv)

    _load_dotenv()
    cfg = _load_yaml(BASE / args.config)
    weights = cfg["scoring"]
    candidates = [c for c in cfg["candidates"] if c.get("screening_status") != "rejected"]
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    results_path = BASE / "reports" / "embedding_compare_runs.json"
    runs: List[Dict[str, Any]] = []
    if results_path.exists():
        runs = json.loads(results_path.read_text(encoding="utf-8"))

    smoke_eval = BASE / cfg["smoke_eval_set_path"]
    full_eval = BASE / cfg["eval_set_path"]

    phases = []
    if args.phase in ("smoke", "all"):
        phases.append(("smoke", smoke_eval, 5))
    if args.phase in ("full", "all"):
        phases.append(("full", full_eval, 20))

    passed_smoke: set[str] = set()
    if args.phase == "full" and results_path.exists():
        for r in runs:
            if r.get("phase") == "smoke" and r.get("status") == "success":
                passed_smoke.add(r.get("config_id", ""))

    from embedding_providers import api_embedding_available

    for phase_name, eval_path, max_q in phases:
        for i, cand in enumerate(candidates, 1):
            cid = cand["config_id"]
            ok, auth_reason = api_embedding_available(cand["embedding_model"])
            if not ok:
                payload = {
                    "run_id": f"emb_{phase_name}_{ts}_{i:02d}",
                    "config_id": cid,
                    "status": "failed",
                    "error_code": auth_reason,
                    "error_reason": f"preflight_skip:{auth_reason}",
                    "embedding_model": cand["embedding_model"],
                    "phase": phase_name,
                    "invalid_reason": "INVALID: thieu OPENROUTER_API_KEY (khong dung OPENAI key lam fallback)",
                }
                runs.append(payload)
                results_path.write_text(
                    json.dumps(runs, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print(f"SKIP {phase_name} {cid} — {auth_reason}")
                continue
            if phase_name == "full" and args.phase == "all":
                if cid not in passed_smoke and not any(
                    r.get("config_id") == cid and r.get("phase") == "smoke" and r.get("status") == "success"
                    for r in runs
                ):
                    print(f"SKIP full {cid} — smoke chua pass")
                    continue
            emb_key = cand["embedding_model"]
            cache_dir = _index_dir(cfg, cand)
            reuse = (cache_dir / ".index_complete").exists() and (cache_dir / "qdrant_db").exists()
            if phase_name == "smoke":
                reuse = False
            run_id = f"emb_{phase_name}_{ts}_{i:02d}"
            print(f"[{phase_name}] {cid} reuse_index={reuse} ...")
            payload = _run_case(
                BASE,
                cand,
                cfg,
                run_id,
                eval_path=eval_path,
                eval_max_questions=max_q,
                reuse_index=reuse,
                timeout_sec=args.timeout_sec,
            )
            payload["phase"] = phase_name
            payload["embedding_model"] = emb_key
            payload["fair_setup"] = json.dumps(cfg.get("fair_setup", {}))
            if payload.get("status") == "success":
                ck = payload.get("cache_key", "") or _emb_cache_key(cfg, cand)
                bm25 = BASE / cfg["cache_root"] / "index_cache" / ck / "bm25_corpus.json"
                tokens = _estimate_embed_tokens(bm25)
                payload["estimated_embed_tokens"] = tokens
                payload["estimated_embed_cost_usd"] = _estimate_cost_usd(emb_key, tokens)
                payload["composite_score"] = _compute_composite(payload, weights)
            else:
                payload["estimated_embed_tokens"] = 0
                payload["estimated_embed_cost_usd"] = 0
            if phase_name == "smoke" and payload.get("status") == "success":
                passed_smoke.add(cid)
            runs.append(payload)
            results_path.write_text(json.dumps(runs, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.skip_report:
        return 0

    full_rows = [r for r in runs if r.get("phase") == "full"]
    fields = [
        "config_id",
        "embedding_model",
        "phase",
        "status",
        "retrieval_hit_rate",
        "citation_correctness",
        "answer_correctness",
        "groundedness",
        "insufficient_information_handling",
        "composite_score",
        "query_time_avg",
        "index_build_time",
        "estimated_embed_tokens",
        "estimated_embed_cost_usd",
        "ingest_status",
        "error_code",
        "error_reason",
        "invalid_reason",
    ]
    csv_path = BASE / "reports" / "openai_embedding_model_comparison.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in full_rows:
            w.writerow({k: r.get(k, "") for k in fields})

    md_parts = [
        "# OpenAI / OpenRouter embedding model comparison",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        "",
        _screening_table_md(),
        "",
        "## Fair setup (co dinh)",
        "",
        "```yaml",
    ]
    import yaml

    md_parts.append(yaml.safe_dump(cfg["fair_setup"], allow_unicode=True, sort_keys=False).strip())
    md_parts.extend(["```", "", "## Ket qua full lane (20 cau)", ""])
    md_parts.append(
        "| Rank | config | embedding | hit | cit | ans | grd | insuf | composite | query_s | index_s | est.$ | status |"
    )
    md_parts.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    ranked = sorted(full_rows, key=lambda r: _safe_float(r.get("composite_score")), reverse=True)
    for rank, r in enumerate(ranked, 1):
        md_parts.append(
            f"| {rank} | `{r.get('config_id')}` | `{r.get('embedding_model','')}` | "
            f"{r.get('retrieval_hit_rate','')} | {r.get('citation_correctness','')} | "
            f"{r.get('answer_correctness','')} | {r.get('groundedness','')} | "
            f"{r.get('insufficient_information_handling','')} | {r.get('composite_score','')} | "
            f"{r.get('query_time_avg','')} | {r.get('index_build_time','')} | "
            f"{r.get('estimated_embed_cost_usd','')} | {r.get('status','')} |"
        )
    md_parts.append("")
    md_parts.append(_conclusions_md(runs))
    md_path = BASE / "reports" / "openai_embedding_model_comparison.md"
    md_path.write_text("\n".join(md_parts), encoding="utf-8")
    _write_html(BASE / "reports" / "openai_embedding_model_comparison.html", full_rows)
    print(csv_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
