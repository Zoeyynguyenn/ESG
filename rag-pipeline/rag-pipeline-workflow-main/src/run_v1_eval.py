"""V1 eval: smoke (10 cau) + full eval_set; xuat artifact reports/."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from typing import Any, Callable, Dict, List

from config import BASE_DIR, EMBEDDING_MODEL, EVAL_SET_PATH, TOP_K
from eval_metrics import aggregate_metrics, parse_eval_set, score_result
from evidence_rag import get_chunks, run_query
from rag_stack import detect_environment, query_chroma, resolve_llm_mode, stack_available

SMOKE_IDS = [
    "ESG-E01",
    "ESG-E05",
    "ESG-E07",
    "ESG-E08",
    "ESG-E10",
    "ESG-G01",
    "ESG-S01",
    "ESG-E14",
    "ESG-I01",
    "ESG-I02",
]


def make_query_fn() -> tuple[Callable[[str], Dict[str, Any]], Dict[str, Any]]:
    meta = {
        "retrieval_mode": "semantic",
        "embedding_model": EMBEDDING_MODEL,
        "llm_mode": resolve_llm_mode(),
        "top_k": TOP_K,
    }
    if stack_available():
        meta["stack"] = "langchain_chroma"
        return lambda q: query_chroma(q, top_k=TOP_K), meta
    chunks = get_chunks()
    meta["stack"] = "lexical_fallback"
    meta["retrieval_mode"] = "lexical"
    meta["llm_mode"] = "rule_based"
    return lambda q: run_query(q, chunks, top_k=TOP_K), meta


def run_eval(rows: List[Dict[str, str]], query_fn: Callable) -> List[Dict[str, Any]]:
    out = []
    for row in rows:
        result = query_fn(row["question"])
        metrics = score_result(row, result)
        out.append({"row": row, "result": result, "metrics": metrics})
    return out


def write_report(
    title: str,
    filename_prefix: str,
    evaluated: List[Dict[str, Any]],
    run_meta: Dict[str, Any],
    chunk_count: int,
) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = BASE_DIR / "reports" / f"{filename_prefix}-{ts}.md"
    metrics = aggregate_metrics([e["metrics"] for e in evaluated])
    pass_n = sum(1 for e in evaluated if e["metrics"]["overall"] == "pass")
    partial_n = sum(1 for e in evaluated if e["metrics"]["overall"] == "partial")
    fail_n = sum(1 for e in evaluated if e["metrics"]["overall"] == "fail")

    lines = [
        f"# {title}",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Run config",
        "",
        "```json",
        json.dumps({**run_meta, "chunk_count": chunk_count}, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Metrics",
        "",
        "```json",
        json.dumps(metrics, indent=2),
        "```",
        "",
        "## Summary",
        "",
        f"- Questions: {len(evaluated)}",
        f"- pass: {pass_n}",
        f"- partial: {partial_n}",
        f"- fail: {fail_n}",
        "",
        "## Per-question",
        "",
    ]
    for item in evaluated:
        row = item["row"]
        r = item["result"]
        m = item["metrics"]
        lines.append(f"### {row['id']}")
        lines.append("")
        lines.append(f"**Q:** {row['question']}")
        lines.append("")
        lines.append(
            f"| answer | confidence | insufficient | mode | overall | "
            f"retrieval_hit | citation | grounded | answer_ok | insuf_ok |"
        )
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
        ans = (r.get("answer") or "")[:200].replace("|", "/")
        lines.append(
            f"| {ans} | {r.get('confidence')} | {r.get('insufficient')} | {r.get('mode')} | "
            f"{m['overall']} | {m['retrieval_hit']} | {m['citation_correct']} | "
            f"{m['groundedness']} | {m['answer_correct']} | {m['insufficient_ok']} |"
        )
        if r.get("evidence"):
            lines.append("")
            lines.append("Evidence top-1: `" + str(r["evidence"][0].get("source")) + "`")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-only", action="store_true")
    parser.add_argument("--full-only", action="store_true")
    args = parser.parse_args()

    all_rows = parse_eval_set()
    query_fn, run_meta = make_query_fn()
    run_meta["environment"] = detect_environment()
    chunk_count = get_chunk_count()

    do_smoke = not args.full_only
    do_full = not args.smoke_only

    if do_smoke:
        smoke_rows = [r for r in all_rows if r["id"] in SMOKE_IDS]
        ev = run_eval(smoke_rows, query_fn)
        p = write_report(
            "V1 Baseline Smoke Eval",
            "v1-baseline-smoke",
            ev,
            run_meta,
            chunk_count,
        )
        print(f"Smoke report: {p}")

    if do_full:
        ev = run_eval(all_rows, query_fn)
        p = write_report(
            "V1 Baseline Full Eval",
            "v1-baseline-full-eval",
            ev,
            run_meta,
            chunk_count,
        )
        print(f"Full report: {p}")


if __name__ == "__main__":
    main()
