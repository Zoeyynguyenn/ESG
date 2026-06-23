"""Debug reranker regression on company_public_dev without full benchmark."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from eval_scoring_v2 import source_aliases
from eval_set_io import parse_eval_set


def _norm_path(s: str) -> str:
    return (s or "").replace("\\", "/").lower()


def _is_company_public_source(src: str) -> bool:
    return _norm_path(src).startswith("data/rag_dataset/04_company_public_curated/")


def _rank_of_expected(hits: List[Dict[str, Any]], expected: str) -> int | None:
    aliases = source_aliases(expected)
    for i, h in enumerate(hits, 1):
        src = _norm_path(h.get("source", ""))
        if any(a in src for a in aliases):
            return i
    return None


def _to_hit_dict(h: Any) -> Dict[str, Any]:
    return {
        "source": h.source,
        "chunk_id": h.chunk_id,
        "score": round(float(h.score), 6),
        "score_breakdown": h.score_breakdown,
        "text_preview": h.text[:180].replace("\n", " "),
    }


def _load_rows(eval_path: Path, limit: int) -> List[Dict[str, str]]:
    rows = parse_eval_set(eval_path)
    rows = sorted(rows, key=lambda r: r["id"])
    return rows[:limit]


def _write_leak_report(path: Path, samples: List[Dict[str, Any]]) -> None:
    lines = [
        "# Reranker Diagnostic - Corpus Leak",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Kiem tra 10 query dau: truoc/sau rerank co source ngoai lane `04_company_public_curated` hay khong.",
        "",
        "| qid | leak_before | leak_after | outside_before | outside_after |",
        "|---|---:|---:|---:|---:|",
    ]
    for s in samples[:10]:
        lines.append(
            f"| `{s['id']}` | {s['leak_before']} | {s['leak_after']} | "
            f"{len(s['outside_before'])} | {len(s['outside_after'])} |"
        )
    lines.extend(["", "## Vi du source ngoai lane (neu co)", ""])
    for s in samples[:10]:
        if s["outside_before"] or s["outside_after"]:
            lines.append(f"### `{s['id']}` {s['question'][:100]}")
            if s["outside_before"]:
                lines.append("- before:")
                lines.extend([f"  - `{x}`" for x in s["outside_before"][:5]])
            if s["outside_after"]:
                lines.append("- after:")
                lines.extend([f"  - `{x}`" for x in s["outside_after"][:5]])
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_regression_report(path: Path, rows: List[Dict[str, Any]], reranker_model: str) -> None:
    lines = [
        "# Reranker Regression Report (12 queries)",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"- reranker_effective_model: `{reranker_model}`",
        "",
        "| qid | expected_in_before | expected_in_after | rank_before | rank_after | sorted_desc_after | mapping_ok |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['id']}` | {r['expected_in_before']} | {r['expected_in_after']} | "
            f"{r['rank_before'] if r['rank_before'] is not None else '-'} | "
            f"{r['rank_after'] if r['rank_after'] is not None else '-'} | "
            f"{r['sorted_desc_after']} | {r['mapping_ok']} |"
        )
    lines.extend(["", "## Chi tiet 10 query fail/thoai hoa", ""])
    degraded = [r for r in rows if r["expected_in_before"] and not r["expected_in_after"]]
    if len(degraded) < 10:
        degraded.extend([r for r in rows if not r["expected_in_after"] and r not in degraded])
    for r in degraded[:10]:
        lines.append(f"### `{r['id']}` - {r['question'][:120]}")
        lines.append(f"- expected_source: `{r['expected_source']}`")
        lines.append(f"- expected rank before: `{r['rank_before']}`")
        lines.append(f"- expected rank after: `{r['rank_after']}`")
        lines.append(f"- sorted_desc_after: `{r['sorted_desc_after']}`")
        lines.append(f"- mapping_ok: `{r['mapping_ok']}`")
        lines.append("- top10 before:")
        for h in r["top_before"]:
            lines.append(
                f"  - `{h['source']}`#{h['chunk_id']} score={h['score']} "
                f"(hybrid={h['score_breakdown'].get('hybrid')})"
            )
        lines.append("- top10 after:")
        for h in r["top_after"]:
            lines.append(
                f"  - `{h['source']}`#{h['chunk_id']} score={h['score']} "
                f"(rerank={h['score_breakdown'].get('rerank')})"
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", default="company_public_dev")
    parser.add_argument(
        "--eval-set-path",
        default=".rag/rag-pipeline-practice/eval_set_company_public_dev.md",
    )
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--pool", type=int, default=64)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument(
        "--embedding-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
    )
    parser.add_argument(
        "--reranker-model",
        default="BAAI/bge-reranker-base",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    eval_path = base_dir / args.eval_set_path

    cache_key = (
        "p=v1__c=recursive_800_120_800_120__e=sentence-transformers_all-MiniLM-L6-v2"
        "__d=company_public_v1__lane=company_public_dev__vs=chroma"
    )
    os.environ["RAG_BENCHMARK_LANE"] = args.lane
    os.environ["RAG_CHROMA_DIR"] = str(base_dir / "artifacts/benchmark_cache/index_cache" / cache_key / "chroma_db")
    os.environ["RAG_BM25_INDEX_PATH"] = str(
        base_dir / "artifacts/benchmark_cache/index_cache" / cache_key / "bm25_corpus.json"
    )
    os.environ["RAG_EMBEDDING_MODEL"] = args.embedding_model
    os.environ["RAG_RERANK_ENABLED"] = "true"
    os.environ["RAG_RERANK_MODEL"] = args.reranker_model
    from retrieval_v3 import _rerank_candidates, retrieve_hybrid_dense_bm25

    rows = _load_rows(eval_path, args.limit)
    diagnostics: List[Dict[str, Any]] = []
    reranker_effective_model = args.reranker_model

    for row in rows:
        before_hits, _ = retrieve_hybrid_dense_bm25(row["question"], args.pool, args.pool)
        before_top = before_hits[: args.top_k]
        reranked_all, rstatus = _rerank_candidates(row["question"], before_hits[:])
        after_top = reranked_all[: args.top_k]
        if rstatus.startswith("fallback"):
            reranker_effective_model = rstatus

        before_dict = [_to_hit_dict(h) for h in before_top]
        after_dict = [_to_hit_dict(h) for h in after_top]
        before_keys = {(h["source"], h["chunk_id"], h["text_preview"]) for h in before_dict}
        after_keys = {(h["source"], h["chunk_id"], h["text_preview"]) for h in after_dict}
        mapping_ok = after_keys.issubset(before_keys | {(h["source"], h["chunk_id"], h["text_preview"]) for h in [_to_hit_dict(x) for x in reranked_all]})
        sorted_desc_after = all(after_dict[i]["score"] >= after_dict[i + 1]["score"] for i in range(len(after_dict) - 1))
        rank_before = _rank_of_expected(before_dict, row["expected_source"])
        rank_after = _rank_of_expected(after_dict, row["expected_source"])
        outside_before = [h["source"] for h in before_dict if not _is_company_public_source(h["source"])]
        outside_after = [h["source"] for h in after_dict if not _is_company_public_source(h["source"])]

        diagnostics.append(
            {
                "id": row["id"],
                "question": row["question"],
                "expected_source": row["expected_source"],
                "expected_in_before": rank_before is not None,
                "expected_in_after": rank_after is not None,
                "rank_before": rank_before,
                "rank_after": rank_after,
                "sorted_desc_after": sorted_desc_after,
                "mapping_ok": mapping_ok,
                "leak_before": len(outside_before) > 0,
                "leak_after": len(outside_after) > 0,
                "outside_before": outside_before,
                "outside_after": outside_after,
                "top_before": before_dict,
                "top_after": after_dict,
            }
        )

    reports = base_dir / "reports"
    reports.mkdir(exist_ok=True)
    _write_leak_report(reports / "reranker_diagnostic_leak.md", diagnostics)
    _write_regression_report(reports / "reranker_regression_report.md", diagnostics, reranker_effective_model)
    print(
        json.dumps(
            {
                "queries": len(diagnostics),
                "leak_before": sum(1 for d in diagnostics if d["leak_before"]),
                "leak_after": sum(1 for d in diagnostics if d["leak_after"]),
                "report_leak": str(reports / "reranker_diagnostic_leak.md"),
                "report_regression": str(reports / "reranker_regression_report.md"),
                "reranker_effective_model": reranker_effective_model,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
