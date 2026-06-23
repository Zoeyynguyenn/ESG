"""Production smoke CI — 5 cau, frozen stack, monitoring thresholds."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))


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
    if not os.environ.get("OPENAI_BASE_URL", "").strip():
        os.environ.pop("OPENAI_BASE_URL", None)


def _require_keys(cfg: Dict[str, Any]) -> None:
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        raise SystemExit("OPENAI_API_KEY missing — set in .env or CI secrets")
    reranker = (cfg.get("stack", {}).get("reranker") or "none").strip().lower()
    if reranker == "jina_api" and not os.environ.get("JINA_API_KEY", "").strip():
        raise SystemExit("JINA_API_KEY missing — required for production Jina rerank")


def _check_metric(name: str, value: float, minimum: float) -> Dict[str, Any]:
    ok = value >= minimum
    return {"metric": name, "value": value, "min": minimum, "pass": ok}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Production smoke CI gate")
    from production_config import DEFAULT_PRODUCTION_CONFIG

    parser.add_argument("--config", default=DEFAULT_PRODUCTION_CONFIG)
    parser.add_argument("--require-index", default="true", choices=["true", "false"])
    parser.add_argument("--output-dir", default="artifacts/smoke_ci")
    args = parser.parse_args(argv)

    _load_dotenv()
    from eval_scoring_v2 import score_result_v2
    from eval_set_io import parse_eval_set
    from llm_runtime import detect_llm_runtime
    from production_config import (
        apply_production_env,
        index_ready,
        load_production_config,
        monitoring_thresholds,
        smoke_question_ids,
    )
    from retrieval_v3 import query_v3

    cfg = load_production_config(BASE / args.config)
    _require_keys(cfg)

    if str(args.require_index).lower() == "true" and not index_ready(cfg):
        idx = BASE / "artifacts/benchmark_cache/index_cache"
        raise SystemExit(
            f"Production index chua san sang. Chay: python scripts/p0_1_reindex_full_lane.py\n"
            f"Expected cache under index_cache/"
        )

    apply_production_env(cfg, base_dir=BASE)
    stack = cfg["stack"]
    smoke_cfg = cfg.get("smoke_ci") or {}
    per_q = smoke_cfg.get("per_question") or {}
    thresholds = monitoring_thresholds(cfg)
    smoke_ids = set(smoke_question_ids(cfg))

    eval_path = BASE / cfg["eval"]["smoke_set_path"]
    rows = parse_eval_set(eval_path)
    if rows and hasattr(rows[0], "to_dict"):
        rows = [r.to_dict() for r in rows]
    rows = [r for r in rows if r["id"] in smoke_ids]
    if len(rows) != len(smoke_ids):
        missing = smoke_ids - {r["id"] for r in rows}
        raise SystemExit(f"Smoke eval thieu cau: {sorted(missing)}")

    llm = detect_llm_runtime()
    if llm.status != "ready":
        raise SystemExit(f"LLM blocked: {llm.blocker_reason}")

    results: List[Dict[str, Any]] = []
    query_times: List[float] = []

    for row in rows:
        t0 = time.perf_counter()
        out = query_v3(
            row["question"],
            retrieval_mode=stack["retrieval_mode"],
            top_k=stack["top_k"],
            pool=stack["candidate_pool"],
            answer_mode=stack.get("answer_mode", "generative"),
            llm_runtime=llm,
        )
        elapsed = round(time.perf_counter() - t0, 3)
        query_times.append(elapsed)
        metrics = score_result_v2(row, out)
        qid = row["id"]
        req = list((per_q.get(qid) or {}).get("require") or [])
        waive_answer = bool((per_q.get(qid) or {}).get("waive_answer"))
        checks: Dict[str, bool] = {}
        for key in req:
            if key == "retrieval_hit":
                checks[key] = bool(metrics.get("retrieval_hit"))
            elif key == "citation_correct":
                checks[key] = bool(metrics.get("citation_correct"))
            elif key == "answer_correct":
                checks[key] = bool(metrics.get("answer_correct"))
            elif key == "insufficient_ok":
                checks[key] = bool(metrics.get("insufficient_ok"))
        q_pass = all(checks.values()) if checks else True
        results.append(
            {
                "id": qid,
                "category": row.get("category"),
                "query_time_sec": elapsed,
                "metrics": metrics,
                "checks": checks,
                "waive_answer": waive_answer,
                "pass": q_pass,
                "answer_preview": (out.get("answer") or "")[:200],
                "top_source": ((out.get("evidence") or [{}])[0].get("source", "")),
            }
        )

    n = len(results)
    hit_rate = sum(1 for r in results if r["metrics"].get("retrieval_hit")) / n
    cit_rate = sum(1 for r in results if r["metrics"].get("citation_correct")) / n
    waived = set(thresholds.get("answer_correctness_waived_ids") or [])
    ans_scored = [r for r in results if r["id"] not in waived]
    ans_rate = (
        sum(1 for r in ans_scored if r["metrics"].get("answer_correct")) / len(ans_scored)
        if ans_scored
        else 1.0
    )
    insuf_rows = [r for r in results if r.get("category") == "insufficient"]
    insuf_rate = (
        sum(1 for r in insuf_rows if r["metrics"].get("insufficient_ok")) / len(insuf_rows)
        if insuf_rows
        else 1.0
    )
    avg_q = sum(query_times) / len(query_times) if query_times else 0.0

    aggregate_checks = [
        _check_metric("retrieval_hit_rate", hit_rate, float(thresholds["retrieval_hit_rate_min"])),
        _check_metric("citation_correctness", cit_rate, float(thresholds["citation_correctness_min"])),
        _check_metric("insufficient_smoke", insuf_rate, float(thresholds["insufficient_smoke_min"])),
        _check_metric("answer_correctness", ans_rate, float(thresholds["answer_correctness_min"])),
    ]
    aggregate_checks.append(
        {
            "metric": "query_time_avg_sec",
            "value": round(avg_q, 3),
            "max": float(thresholds["query_time_avg_max_sec"]),
            "pass": avg_q <= float(thresholds["query_time_avg_max_sec"]),
        }
    )

    per_q_pass = all(r["pass"] for r in results)
    agg_pass = all(c["pass"] for c in aggregate_checks)
    overall = per_q_pass and agg_pass

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = BASE / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "production_id": cfg["production_id"],
        "frozen_at": cfg.get("frozen_at"),
        "overall_pass": overall,
        "per_question_pass": per_q_pass,
        "aggregate_pass": agg_pass,
        "aggregate_checks": aggregate_checks,
        "results": results,
        "llm": llm.model_name,
    }
    json_path = out_dir / f"smoke_ci_{ts}.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        f"# Smoke CI — {cfg['production_id']}",
        "",
        f"Thoi gian: {report['timestamp']}",
        f"Ket qua: **{'PASS' if overall else 'FAIL'}**",
        "",
        "## Aggregate",
        "",
        "| Metric | Value | Threshold | Pass |",
        "|---|---:|---:|---|",
    ]
    for c in aggregate_checks:
        thr = c.get("min", c.get("max"))
        op = ">=" if "min" in c else "<="
        md_lines.append(
            f"| {c['metric']} | {c['value']} | {op} {thr} | {'OK' if c['pass'] else 'FAIL'} |"
        )
    md_lines.extend(["", "## Per question", ""])
    for r in results:
        status = "OK" if r["pass"] else "FAIL"
        md_lines.append(f"- **{r['id']}** ({status}): {r['checks']}")
    md_path = out_dir / f"smoke_ci_{ts}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(json.dumps({"pass": overall, "json": str(json_path), "md": str(md_path)}, indent=2))
    if not overall:
        print("SMOKE CI FAILED", file=sys.stderr)
        for r in results:
            if not r["pass"]:
                print(f"  FAIL {r['id']}: {r['checks']}", file=sys.stderr)
        for c in aggregate_checks:
            if not c["pass"]:
                print(f"  FAIL aggregate {c['metric']}", file=sys.stderr)
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
