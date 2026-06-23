"""Version 3: benchmark retrieval modes tren full eval set."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from typing import Any, Callable, Dict, List

from config import (
    BASE_DIR,
    CANDIDATE_POOL_SIZE,
    EMBEDDING_MODEL,
    FINAL_TOP_K,
    HYBRID_ALPHA,
    RERANK_ENABLED,
    RERANK_MODEL,
    RETRIEVAL_MODES_V3,
    V21_BASELINE_METRICS,
)
from eval_scoring_v2 import aggregate_metrics_v2, score_result_v2, top_error_patterns
from eval_set_io import parse_eval_set
from retrieval_v3 import get_corpus_chunks, query_v3
from run_v2_eval import get_chunk_count


def run_mode_eval(rows: List[Dict[str, str]], mode: str) -> List[Dict[str, Any]]:
    qfn: Callable[[str], Dict[str, Any]] = lambda q: query_v3(q, retrieval_mode=mode)
    out = []
    for row in rows:
        result = qfn(row["question"])
        metrics = score_result_v2(row, result)
        out.append({"row": row, "result": result, "metrics": metrics})
    return out


def write_mode_report(mode: str, evaluated: List[Dict[str, Any]], meta: Dict[str, Any]) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = BASE_DIR / "reports" / f"v3-eval-{mode}-{ts}.md"
    metrics = aggregate_metrics_v2([e["metrics"] for e in evaluated])
    patterns = top_error_patterns(evaluated, 5)
    pass_n = sum(1 for e in evaluated if e["metrics"]["overall"] == "pass")
    partial_n = sum(1 for e in evaluated if e["metrics"]["overall"] == "partial")
    fail_n = sum(1 for e in evaluated if e["metrics"]["overall"] == "fail")

    lines = [
        f"# V3 Eval — {mode}",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Config",
        "",
        "```json",
        json.dumps({**meta, "metrics": metrics}, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Summary",
        "",
        f"- Questions: {len(evaluated)}",
        f"- pass: {pass_n} | partial: {partial_n} | fail: {fail_n}",
        "",
        "## Top error patterns",
        "",
        "```json",
        json.dumps(patterns, indent=2),
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def delta_vs_v21(current: Dict[str, float]) -> Dict[str, str]:
    out = {}
    for k, base in V21_BASELINE_METRICS.items():
        cur = current.get(k, 0)
        if cur > base + 0.02:
            out[k] = "tang"
        elif cur < base - 0.02:
            out[k] = "giam"
        else:
            out[k] = "giu"
    return out


def evaluate_v3_gates(metrics: Dict[str, float], delta: Dict[str, str]) -> Dict[str, Any]:
    g1 = delta.get("retrieval_hit_rate") == "tang" or (
        metrics["retrieval_hit_rate"] >= V21_BASELINE_METRICS["retrieval_hit_rate"]
    )
    g2 = delta.get("citation_correctness") == "tang" or (
        metrics["citation_correctness"] > V21_BASELINE_METRICS["citation_correctness"] + 0.02
    )
    g3 = metrics["groundedness"] >= 0.95
    g4 = metrics["insufficient_information_handling"] >= 0.95

    if (g1 or g2) and g3 and g4 and (
        metrics["citation_correctness"] > V21_BASELINE_METRICS["citation_correctness"]
        or metrics["retrieval_hit_rate"] > V21_BASELINE_METRICS["retrieval_hit_rate"]
    ):
        status = "pass_with_limits"
    elif g3 and g4 and metrics["retrieval_hit_rate"] >= 0.7:
        status = "pass_with_limits"
    else:
        status = "not_pass"

    return {
        "gate1_retrieval_improved": g1,
        "gate2_citation_improved": g2,
        "gate3_groundedness_ok": g3,
        "gate4_insufficient_ok": g4,
        "v3_status": status,
    }


def write_compare_report(
    mode_results: Dict[str, Dict[str, Any]],
    best_mode: str,
    gates: Dict[str, Any],
    advance_v4: str,
) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = BASE_DIR / "reports" / f"v3-compare-retrieval-modes-{ts}.md"
    lines = [
        "# V3 Compare Retrieval Modes",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"**Best mode:** `{best_mode}`",
        f"**V3 status:** `{gates['v3_status']}`",
        f"**Advance V4:** `{advance_v4}`",
        "",
        "## Metrics by mode (50 cau)",
        "",
        "| Mode | retrieval_hit | citation | grounded | answer | insufficient | pass | partial | fail |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode, data in mode_results.items():
        m = data["metrics"]
        s = data["summary"]
        d = data.get("delta", {})
        lines.append(
            f"| {mode} | {m['retrieval_hit_rate']} ({d.get('retrieval_hit_rate','')}) | "
            f"{m['citation_correctness']} ({d.get('citation_correctness','')}) | "
            f"{m['groundedness']} | {m['answer_correctness']} | "
            f"{m['insufficient_information_handling']} | {s['pass']} | {s['partial']} | {s['fail']} |"
        )

    lines.extend(
        [
            "",
            "## Delta vs V2.1 baseline",
            "",
            "V2.1: retrieval 0.72, citation 0.46, grounded 1.0, answer 0.52, insufficient 1.0",
            "",
            "## Acceptance gates",
            "",
            "```json",
            json.dumps(gates, indent=2),
            "```",
            "",
            "## Top error patterns by mode",
            "",
        ]
    )
    for mode, data in mode_results.items():
        lines.append(f"### {mode}")
        lines.append("```json")
        lines.append(json.dumps(data.get("patterns", {}), indent=2))
        lines.append("```")
        lines.append("")

    lines.extend(
        [
            "## Recommendation",
            "",
            f"Mode mac dinh giai doan tiep theo: **{best_mode}**",
            "",
            "Ly do: uu tien citation_correctness va retrieval_hit_rate so voi V2.1, giu groundedness/insufficient.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def pick_best_mode(mode_results: Dict[str, Dict[str, Any]]) -> str:
    best = None
    best_score = -1.0
    for mode, data in mode_results.items():
        m = data["metrics"]
        score = (
            m["citation_correctness"] * 2.0
            + m["retrieval_hit_rate"]
            + m["groundedness"] * 0.5
            + m["insufficient_information_handling"] * 0.5
        )
        if score > best_score:
            best_score = score
            best = mode
    return best or "hybrid_dense_bm25"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--modes",
        nargs="*",
        default=RETRIEVAL_MODES_V3,
        help="Modes to benchmark",
    )
    args = parser.parse_args()

    get_corpus_chunks()
    rows = parse_eval_set()
    chunk_count = get_chunk_count()
    mode_results: Dict[str, Dict[str, Any]] = {}
    report_paths: List[str] = []

    meta_base = {
        "embedding_model": EMBEDDING_MODEL,
        "candidate_pool_size": CANDIDATE_POOL_SIZE,
        "final_top_k": FINAL_TOP_K,
        "hybrid_alpha": HYBRID_ALPHA,
        "rerank_enabled": RERANK_ENABLED,
        "rerank_model": RERANK_MODEL,
        "chunk_count": chunk_count,
        "v21_baseline": V21_BASELINE_METRICS,
    }

    for mode in args.modes:
        print(f"Running mode: {mode} ...")
        meta = {**meta_base, "retrieval_mode": mode}
        try:
            evaluated = run_mode_eval(rows, mode)
        except Exception as exc:
            print(f"Mode {mode} failed: {exc}")
            continue
        metrics = aggregate_metrics_v2([e["metrics"] for e in evaluated])
        delta = delta_vs_v21(metrics)
        p = write_mode_report(mode, evaluated, meta)
        report_paths.append(p)
        mode_results[mode] = {
            "metrics": metrics,
            "delta": delta,
            "summary": {
                "pass": sum(1 for e in evaluated if e["metrics"]["overall"] == "pass"),
                "partial": sum(1 for e in evaluated if e["metrics"]["overall"] == "partial"),
                "fail": sum(1 for e in evaluated if e["metrics"]["overall"] == "fail"),
            },
            "patterns": top_error_patterns(evaluated, 5),
        }
        print(f"  {mode}: cit={metrics['citation_correctness']} ret={metrics['retrieval_hit_rate']} -> {p}")

    if not mode_results:
        print("No modes completed")
        return

    best = pick_best_mode(mode_results)
    gates = evaluate_v3_gates(mode_results[best]["metrics"], mode_results[best]["delta"])
    advance_v4 = "no" if gates["v3_status"] == "not_pass" else "chua"
    if (
        mode_results[best]["metrics"]["citation_correctness"] >= 0.55
        and mode_results[best]["metrics"]["retrieval_hit_rate"] >= 0.75
    ):
        advance_v4 = "co_the"

    cp = write_compare_report(mode_results, best, gates, advance_v4)
    report_paths.append(cp)

    print(json.dumps({"best_mode": best, "gates": gates, "reports": report_paths}, indent=2))


if __name__ == "__main__":
    main()
