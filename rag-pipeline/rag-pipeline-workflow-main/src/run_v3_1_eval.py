"""V3.1: baseline generative vs extractive (cung hybrid_dense_bm25_rerank)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

from config import (
    BASE_DIR,
    CANDIDATE_POOL_SIZE,
    EMBEDDING_MODEL,
    FINAL_TOP_K,
    HYBRID_ALPHA,
    RERANK_MODEL,
)
from eval_scoring_v2 import aggregate_metrics_v2, score_result_v2, top_error_patterns
from eval_set_io import parse_eval_set
from llm_runtime import detect_llm_runtime
from retrieval_v3 import get_corpus_chunks, query_v3
from run_v2_eval import get_chunk_count

BEST_RETRIEVAL = "hybrid_dense_bm25_rerank"
V3_EXTRACTIVE_REF = {
    "retrieval_hit_rate": 0.8,
    "citation_correctness": 0.6,
    "groundedness": 1.0,
    "answer_correctness": 0.56,
    "insufficient_information_handling": 1.0,
    "pass_rate": 0.52,
}


def run_eval(rows: List[Dict[str, str]], answer_mode: str, llm_runtime) -> List[Dict[str, Any]]:
    out = []
    for row in rows:
        result = query_v3(
            row["question"],
            retrieval_mode=BEST_RETRIEVAL,
            top_k=FINAL_TOP_K,
            pool=CANDIDATE_POOL_SIZE,
            answer_mode=answer_mode,
            llm_runtime=llm_runtime,
        )
        metrics = score_result_v2(row, result)
        out.append({"row": row, "result": result, "metrics": metrics})
    return out


def write_generative_report(
    status: str,
    runtime_info: Dict[str, Any],
    evaluated: List[Dict[str, Any]] | None,
    meta: Dict[str, Any],
) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = BASE_DIR / "reports" / f"v3_1-eval-generative-{ts}.md"
    lines = [
        "# V3.1 Eval — Generative",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        f"**Status:** `{status}`",
        "",
        "## Run config",
        "",
        "```json",
        json.dumps(meta, ensure_ascii=False, indent=2),
        "```",
        "",
        "## LLM runtime",
        "",
        "```json",
        json.dumps(runtime_info, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    if status == "blocked":
        lines.extend(
            [
                "## Blocker",
                "",
                runtime_info.get("blocker_reason", "Unknown"),
                "",
                "### Checklist bat moi truong",
                "",
            ]
        )
        for step in runtime_info.get("setup_checklist") or []:
            lines.append(f"- {step}")
        lines.append("")
    else:
        metrics = aggregate_metrics_v2([e["metrics"] for e in evaluated or []])
        patterns = top_error_patterns(evaluated or [], 5)
        lines.extend(
            [
                "## Metrics (5 chinh)",
                "",
                "```json",
                json.dumps(metrics, indent=2),
                "```",
                "",
                "## Top error patterns",
                "",
                "```json",
                json.dumps(patterns, indent=2),
                "```",
                "",
                "## Per-question summary",
                "",
            ]
        )
        for item in evaluated or []:
            r = item["result"]
            m = item["metrics"]
            lines.append(
                f"- **{item['row']['id']}** ({m['overall']}): "
                f"insuf={r.get('insufficient')} | {', '.join(m.get('reason_codes', [])[:2]) or '-'}"
            )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def write_compare_report(
    ext_metrics: Dict[str, float],
    gen_metrics: Dict[str, float] | None,
    gen_status: str,
    ext_patterns: Dict[str, int],
    gen_patterns: Dict[str, int] | None,
    recommendation: str,
    baseline_status: str,
) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = BASE_DIR / "reports" / f"v3_1-compare-extractive-vs-generative-{ts}.md"

    def delta(a: float, b: float | None) -> str:
        if b is None:
            return "n/a"
        if b > a + 0.02:
            return "generative_tot"
        if b < a - 0.02:
            return "generative_thap"
        return "tuong_duong"

    lines = [
        "# V3.1 Compare — Extractive vs Generative",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        f"Retrieval mode (ca hai): `{BEST_RETRIEVAL}`",
        f"**Baseline generative status:** `{baseline_status}`",
        "",
        "## Metric table",
        "",
        "| Metric | Extractive | Generative | Delta |",
        "|---|---:|---:|---|",
    ]
    keys = [
        "retrieval_hit_rate",
        "citation_correctness",
        "groundedness",
        "answer_correctness",
        "insufficient_information_handling",
        "pass_rate",
    ]
    for k in keys:
        e = ext_metrics.get(k, 0)
        g = gen_metrics.get(k) if gen_metrics else None
        gstr = f"{g:.4f}" if g is not None else "blocked"
        lines.append(f"| {k} | {e:.4f} | {gstr} | {delta(e, g)} |")

    lines.extend(
        [
            "",
            "## Extractive reference",
            "",
            f"V3 run truoc: retrieval 0.80, citation 0.60, answer 0.56 (pass ~26/50)",
            f"V3.1 extractive rerun: pass_rate {ext_metrics.get('pass_rate', 0):.2f}",
            "",
            "## Top error patterns — extractive",
            "",
            "```json",
            json.dumps(ext_patterns, indent=2),
            "```",
            "",
        ]
    )
    if gen_patterns is not None:
        lines.extend(
            [
                "## Top error patterns — generative",
                "",
                "```json",
                json.dumps(gen_patterns, indent=2),
                "```",
                "",
            ]
        )
    else:
        lines.append("## Generative\n\nKhong chay duoc — xem `v3_1-eval-generative-*.md` blocker.\n")

    lines.extend(["## Recommendation", "", recommendation, ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def main():
    get_corpus_chunks()
    rows = parse_eval_set()
    chunk_count = get_chunk_count()
    runtime = detect_llm_runtime()

    meta = {
        "retrieval_mode": BEST_RETRIEVAL,
        "answer_modes": ["extractive", "generative"],
        "embedding_model": EMBEDDING_MODEL,
        "candidate_pool_size": CANDIDATE_POOL_SIZE,
        "final_top_k": FINAL_TOP_K,
        "hybrid_alpha": HYBRID_ALPHA,
        "rerank_model": RERANK_MODEL,
        "chunk_count": chunk_count,
        "temperature": runtime.temperature,
    }

    runtime_info = {
        "status": runtime.status,
        "llm_provider": runtime.provider,
        "model_name": runtime.model_name,
        "temperature": runtime.temperature,
        "blocker_reason": runtime.blocker_reason,
        "setup_checklist": runtime.setup_checklist,
    }
    meta["llm_runtime"] = runtime_info

    print("Running extractive (V3.1 rerun)...")
    ext_eval = run_eval(rows, "extractive", runtime)
    ext_metrics = aggregate_metrics_v2([e["metrics"] for e in ext_eval])
    ext_patterns = top_error_patterns(ext_eval, 5)
    meta["extractive_metrics"] = ext_metrics

    gen_metrics = None
    gen_patterns = None
    gen_status = "blocked"
    baseline_status = "blocked"

    if runtime.status == "ready":
        print(f"Running generative ({runtime.provider})...")
        gen_eval = run_eval(rows, "generative", runtime)
        gen_metrics = aggregate_metrics_v2([e["metrics"] for e in gen_eval])
        gen_patterns = top_error_patterns(gen_eval, 5)
        gen_status = "pass_with_limits"
        baseline_status = "pass_with_limits"
        gp = write_generative_report("pass_with_limits", runtime_info, gen_eval, meta)
        print(f"Generative report: {gp}")

        if (
            gen_metrics["citation_correctness"] >= ext_metrics["citation_correctness"]
            and gen_metrics["answer_correctness"] >= ext_metrics["answer_correctness"]
        ):
            rec = "Uu tien **generative** cho answer quality; giu retrieval V3 hybrid_dense_bm25_rerank."
        elif gen_metrics["groundedness"] < 0.95:
            rec = "Giữ **extractive** — generative groundedness giam; can prompt guard/chat."
        else:
            rec = "**Hybrid strategy**: extractive cho cau numeric/policy on dinh; generative cho multi-hop/synthesis."
    else:
        gp = write_generative_report("blocked", runtime_info, None, meta)
        print(f"Generative blocker report: {gp}")
        rec = (
            "Giữ **extractive** lam mac dinh cho den khi bat Ollama hoac OPENAI_API_KEY. "
            "Chay lai `python src/run_v3_1_eval.py` sau khi LLM san sang."
        )

    cp = write_compare_report(
        ext_metrics,
        gen_metrics,
        gen_status,
        ext_patterns,
        gen_patterns,
        rec,
        baseline_status,
    )
    print(f"Compare: {cp}")
    print(
        json.dumps(
            {
                "llm_runtime": runtime_info,
                "extractive_metrics": ext_metrics,
                "generative_metrics": gen_metrics,
                "baseline_generative_status": baseline_status,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
