"""Version 2: Evaluated Evidence RAG — validate eval set + chay eval theo mode."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from config import BASE_DIR, DATA_DIR, EMBEDDING_MODEL, TOP_K
from eval_scoring_v2 import aggregate_metrics_v2, score_result_v2, top_error_patterns
from eval_set_io import validate_eval_set, write_validation_report
from evidence_rag import get_chunks, run_query
from rag_stack import detect_environment, query_chroma, resolve_llm_mode, stack_available


def get_chunk_count() -> int:
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(BASE_DIR / "artifacts" / "chroma_db"))
        col = client.list_collections()
        if col:
            return col[0].count()
    except Exception:
        pass
    return len(get_chunks())


def dataset_snapshot() -> Dict[str, Any]:
    from rag_common import iter_corpus_files

    files = list(iter_corpus_files())
    return {
        "data_dir": str(DATA_DIR),
        "file_count": len(files),
        "has_esg_x02_pdf": any("ESG-X02" in str(f) and f.suffix.lower() == ".pdf" for f in files),
    }


def make_query_fn(mode: str) -> tuple[Callable[[str], Dict[str, Any]], Dict[str, Any]]:
    meta: Dict[str, Any] = {
        "eval_mode": mode,
        "embedding_model": EMBEDDING_MODEL,
        "top_k": TOP_K,
        "environment": detect_environment(),
    }
    if stack_available():
        meta["stack"] = "langchain_chroma"
        meta["retrieval_mode"] = "semantic"
        override = "extractive" if mode == "extractive" else None
        if mode == "generative":
            resolved = resolve_llm_mode()
            if resolved in ("ollama", "openai_api"):
                override = resolved
            else:
                meta["generative_blocker"] = "ollama_va_openai_api_khong_san_sang"
                override = "extractive"
                meta["eval_mode"] = "extractive_forced"
        meta["llm_mode"] = override or "extractive"
        return lambda q: query_chroma(q, top_k=TOP_K, llm_mode_override=override), meta

    chunks = get_chunks()
    meta["stack"] = "lexical_fallback"
    meta["retrieval_mode"] = "lexical"
    meta["llm_mode"] = "rule_based"
    return lambda q: run_query(q, chunks, top_k=TOP_K), meta


def run_eval(rows: List[Dict[str, str]], query_fn: Callable) -> List[Dict[str, Any]]:
    out = []
    for row in rows:
        result = query_fn(row["question"])
        metrics = score_result_v2(row, result)
        out.append({"row": row, "result": result, "metrics": metrics})
    return out


def decide_v2_status(metrics: Dict[str, float], mode: str, generative_ran: bool) -> tuple[str, str, str]:
    """status, advance_v3, reason"""
    rhr = metrics["retrieval_hit_rate"]
    cit = metrics["citation_correctness"]
    ans = metrics["answer_correctness"]
    ins = metrics["insufficient_information_handling"]
    pr = metrics["pass_rate"]

    if rhr >= 0.75 and cit >= 0.55 and ans >= 0.65 and ins >= 0.95 and pr >= 0.45:
        status = "pass"
    elif rhr >= 0.65 and ins >= 0.9 and pr >= 0.35:
        status = "pass_with_limits"
    else:
        status = "pass_with_limits" if pr >= 0.3 else "not_pass"

    reasons = [
        f"retrieval_hit_rate={rhr}",
        f"citation_correctness={cit}",
        f"answer_correctness={ans}",
        f"insufficient_handling={ins}",
        f"pass_rate={pr}",
        f"mode={mode}",
    ]
    if not generative_ran:
        reasons.append("generative_chua_chay")

    # V3 = retrieval improvements — advance only if V2 eval pipeline stable
    advance = "chua"
    if status in ("pass", "pass_with_limits") and ins >= 0.9:
        advance = "co_the" if rhr < 0.8 or cit < 0.6 else "nen"
    reason = "; ".join(reasons)
    return status, advance, reason


def write_v2_report(
    title: str,
    prefix: str,
    evaluated: List[Dict[str, Any]],
    run_meta: Dict[str, Any],
    chunk_count: int,
    v2_status: str,
    advance_v3: str,
    status_reason: str,
) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = BASE_DIR / "reports" / f"{prefix}-{ts}.md"
    metrics = aggregate_metrics_v2([e["metrics"] for e in evaluated])
    patterns = top_error_patterns(evaluated)
    pass_n = sum(1 for e in evaluated if e["metrics"]["overall"] == "pass")
    partial_n = sum(1 for e in evaluated if e["metrics"]["overall"] == "partial")
    fail_n = sum(1 for e in evaluated if e["metrics"]["overall"] == "fail")

    lines = [
        f"# {title}",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Version 2 ket luan",
        "",
        f"- **Version 2 status:** `{v2_status}`",
        f"- **Advance V3:** `{advance_v3}`",
        f"- **Ly do:** {status_reason}",
        "",
        "## Stack config",
        "",
        "```json",
        json.dumps(
            {**run_meta, "chunk_count": chunk_count, "dataset": dataset_snapshot()},
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## Metrics (5 chinh)",
        "",
        "```json",
        json.dumps(metrics, indent=2),
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
        "## Per-question (chi tiet)",
        "",
    ]
    for item in evaluated:
        row = item["row"]
        r = item["result"]
        m = item["metrics"]
        lines.append(f"### {row['id']} — **{m['overall']}**")
        lines.append("")
        lines.append(f"**Q:** {row['question']}")
        lines.append("")
        lines.append(f"- expected_source: `{row['expected_source']}`")
        lines.append(f"- expected_answer: {row['expected_answer']}")
        lines.append(f"- reasons: {', '.join(m.get('reasons') or []) or '-'}")
        lines.append("")
        lines.append(
            "| retrieval | citation_top1 | citation_topk | grounded | answer | insufficient |"
        )
        lines.append("|---|---|---|---|---|---|")
        lines.append(
            f"| {m['retrieval_hit']} | {m['citation_correct']} | {m.get('citation_topk_any')} | "
            f"{m['groundedness']} | {m['answer_correct']} | {m['insufficient_ok']} |"
        )
        ans = (r.get("answer") or "")[:180].replace("|", "/")
        lines.append("")
        lines.append(f"answer: {ans}")
        if r.get("evidence"):
            lines.append(f"evidence_top1: `{r['evidence'][0].get('source')}`")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_compare_report(
    results: Dict[str, Dict[str, Any]],
) -> Optional[Path]:
    if len(results) < 2:
        return None
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = BASE_DIR / "reports" / f"v2-compare-modes-{ts}.md"
    lines = [
        "# V2 Compare Modes",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "| Mode | retrieval_hit | citation | grounded | answer | insufficient | pass | partial | fail |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode, data in results.items():
        m = data["metrics"]
        s = data["summary"]
        lines.append(
            f"| {mode} | {m['retrieval_hit_rate']} | {m['citation_correctness']} | "
            f"{m['groundedness']} | {m['answer_correctness']} | "
            f"{m['insufficient_information_handling']} | {s['pass']} | {s['partial']} | {s['fail']} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description="V2 Evaluated Evidence RAG")
    parser.add_argument("--skip-validate", action="store_true")
    args = parser.parse_args()

    if not args.skip_validate:
        vr = validate_eval_set()
        vp = write_validation_report(vr)
        print(f"Validation: valid={vr.valid} rows={vr.row_count} -> {vp}")
        if not vr.valid:
            print("WARN: eval set co loi nhung van tiep tuc eval")

    from eval_set_io import parse_eval_set

    rows = parse_eval_set()
    chunk_count = get_chunk_count()
    mode_results: Dict[str, Dict[str, Any]] = {}
    report_paths: List[str] = []

    # Mode 1: extractive
    qfn, meta = make_query_fn("extractive")
    ev = run_eval(rows, qfn)
    metrics = aggregate_metrics_v2([e["metrics"] for e in ev])
    st, adv, reason = decide_v2_status(metrics, meta["eval_mode"], False)
    p = write_v2_report(
        "V2 Eval — Extractive",
        "v2-eval-extractive",
        ev,
        meta,
        chunk_count,
        st,
        adv,
        reason,
    )
    report_paths.append(str(p))
    mode_results["extractive"] = {
        "metrics": metrics,
        "summary": {
            "pass": sum(1 for e in ev if e["metrics"]["overall"] == "pass"),
            "partial": sum(1 for e in ev if e["metrics"]["overall"] == "partial"),
            "fail": sum(1 for e in ev if e["metrics"]["overall"] == "fail"),
        },
        "status": st,
    }
    print(f"Extractive: {p} status={st}")

    # Mode 2: generative (neu co)
    env = detect_environment()
    gen_available = env.get("ollama") or env.get("openai_api_key_set")
    if gen_available:
        qfn_g, meta_g = make_query_fn("generative")
        if meta_g.get("eval_mode") != "extractive_forced":
            ev_g = run_eval(rows, qfn_g)
            metrics_g = aggregate_metrics_v2([e["metrics"] for e in ev_g])
            st_g, adv_g, reason_g = decide_v2_status(metrics_g, "generative", True)
            p_g = write_v2_report(
                "V2 Eval — Generative",
                "v2-eval-generative",
                ev_g,
                meta_g,
                chunk_count,
                st_g,
                adv_g,
                reason_g,
            )
            report_paths.append(str(p_g))
            mode_results["generative"] = {
                "metrics": metrics_g,
                "summary": {
                    "pass": sum(1 for e in ev_g if e["metrics"]["overall"] == "pass"),
                    "partial": sum(1 for e in ev_g if e["metrics"]["overall"] == "partial"),
                    "fail": sum(1 for e in ev_g if e["metrics"]["overall"] == "fail"),
                },
                "status": st_g,
            }
            print(f"Generative: {p_g} status={st_g}")
        else:
            print(f"Generative skipped: {meta_g.get('generative_blocker')}")
    else:
        print("Generative skipped: ollama/API khong san sang")

    cp = write_compare_report(mode_results)
    if cp:
        report_paths.append(str(cp))
        print(f"Compare: {cp}")

    # Final status file sidecar
    final_status = mode_results.get("extractive", {}).get("status", "not_pass")
    print(json.dumps({"reports": report_paths, "v2_status": final_status}, indent=2))


if __name__ == "__main__":
    main()
