"""Dump extractive vs generative answers for OpenAI E2E full lane."""

from __future__ import annotations

import hashlib
import os
import sys
from datetime import datetime
from pathlib import Path

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


def _setup_e2e_env() -> None:
    cache_root = BASE / "artifacts" / "benchmark_cache"
    lane = "company_export_json_full"
    company_filter = "넥스트아이_dataset_package_20260528T091409"
    parser_key = "jsonl_v1"
    chunk_key = "section_based_800_120"
    emb_key = "openai_text-embedding-3-small"
    corpus_key = "nexteye_esg_v1_1_1_openai_full_e2e"
    vs = "qdrant"
    cache_key = (
        f"p={parser_key}__c={chunk_key}__e={emb_key}__d={corpus_key}"
        f"__lane={lane}__vs={vs}__company={hashlib.md5(company_filter.encode()).hexdigest()[:10]}"
    )
    index_dir = cache_root / "index_cache" / cache_key
    os.environ.update(
        {
            "RAG_BENCHMARK_LANE": lane,
            "RAG_COMPANY_FILTER": company_filter,
            "RAG_CHUNKING_PROFILE": "section_based",
            "RAG_CHUNK_SIZE": "800",
            "RAG_CHUNK_OVERLAP": "120",
            "RAG_EMBEDDING_MODEL": "openai:text-embedding-3-small",
            "RAG_VECTOR_STORE": vs,
            "RAG_QDRANT_PATH": str(index_dir / "qdrant_db"),
            "RAG_BM25_INDEX_PATH": str(index_dir / "bm25_corpus.json"),
            "RAG_TOP_K": "4",
            "RAG_FINAL_TOP_K": "4",
            "RAG_CANDIDATE_POOL_SIZE": "64",
            "RAG_BENCHMARK_LANGUAGE": "ko",
            "RAG_RERANK_ENABLED": "false",
            "RAG_BENCHMARK_LLM_PROVIDER": "openai_api",
        }
    )
    from run_benchmark_case import _prepare_corpus_manifest

    manifest = _prepare_corpus_manifest(BASE, lane, 1.0, cache_root, company_filter=company_filter)
    os.environ["RAG_BENCHMARK_CORPUS_MANIFEST"] = str(manifest)


def _clip(s: str, n: int = 500) -> str:
    s = (s or "").replace("\r", "").strip()
    return s if len(s) <= n else s[: n - 3] + "..."


def main() -> None:
    _load_dotenv()
    _setup_e2e_env()

    from eval_scoring_v2 import score_result_v2
    from eval_set_io import parse_eval_set
    from llm_runtime import detect_llm_runtime
    from retrieval_v3 import query_v3

    eval_path = BASE / ".rag/rag-pipeline-practice/eval_set_company_export_json_dev_ko.md"
    rows = parse_eval_set(eval_path)
    if rows and hasattr(rows[0], "to_dict"):
        rows = [r.to_dict() for r in rows]
    llm = detect_llm_runtime()
    if llm.status != "ready":
        raise SystemExit(f"LLM blocked: {llm.blocker_reason}")

    samples: list[dict] = []
    for row in rows:
        ext = query_v3(
            row["question"],
            retrieval_mode="hybrid_dense_bm25",
            top_k=4,
            pool=64,
            answer_mode="extractive",
            llm_runtime=None,
        )
        gen = query_v3(
            row["question"],
            retrieval_mode="hybrid_dense_bm25",
            top_k=4,
            pool=64,
            answer_mode="generative",
            llm_runtime=llm,
        )
        m_ext = score_result_v2(row, ext)
        m_gen = score_result_v2(row, gen)
        samples.append(
            {
                "row": row,
                "ext": ext,
                "gen": gen,
                "m_ext": m_ext,
                "m_gen": m_gen,
            }
        )

    ext_ok = sum(1 for s in samples if s["m_ext"].get("answer_correct"))
    gen_ok = sum(1 for s in samples if s["m_gen"].get("answer_correct"))

    summary_lines = [
        "# Tóm tắt kết quả Generative GPT-4o-mini",
        "",
        f"Tạo lúc: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "| Mục | Giá trị |",
        "|---|---|",
        "| Lane | `company_export_json_full` |",
        "| Embedding | `openai:text-embedding-3-small` |",
        "| Retrieval | hybrid_dense_bm25, pool 64, Qdrant |",
        f"| Generative LLM | `{llm.model_name}` |",
        f"| answer_correct (rule) | Extractive **{ext_ok}/20** → Generative **{gen_ok}/20** |",
        "",
        "Chi tiết: [openai_generative_results_full.md](openai_generative_results_full.md)",
        "",
        "| ID | Category | Ext OK | Gen OK | Câu trả lời Generative (rút gọn) |",
        "|---|---|---:|---:|---|",
    ]
    for s in samples:
        row = s["row"]
        gen_ans = _clip(s["gen"].get("answer", ""), 120).replace("|", "\\|").replace("\n", " ")
        summary_lines.append(
            f"| {row['id']} | {row.get('category','')} | "
            f"{'✓' if s['m_ext'].get('answer_correct') else '✗'} | "
            f"{'✓' if s['m_gen'].get('answer_correct') else '✗'} | {gen_ans} |"
        )

    detail_lines = [
        "# Kết quả Generative vs Extractive — chi tiết 20 câu",
        "",
        f"LLM generative: `{llm.model_name}` | Lane: full",
        "",
    ]
    for s in samples:
        row, ext, gen = s["row"], s["ext"], s["gen"]
        m_ext, m_gen = s["m_ext"], s["m_gen"]
        top_src = (gen.get("evidence") or [{}])[0].get("source", "")
        detail_lines.extend(
            [
                f"## {row['id']} — {row['question']}",
                "",
                f"**Expected:** {row.get('expected_answer', '')}",
                "",
                f"**Top source:** `{top_src}`",
                "",
                "| Metric | Extractive | Generative |",
                "|---|---|---|",
                f"| retrieval_hit | {m_ext.get('retrieval_hit')} | {m_gen.get('retrieval_hit')} |",
                f"| citation | {m_ext.get('citation_correct')} | {m_gen.get('citation_correct')} |",
                f"| answer_correct | {m_ext.get('answer_correct')} | {m_gen.get('answer_correct')} |",
                f"| insufficient_ok | {m_ext.get('insufficient_ok')} | {m_gen.get('insufficient_ok')} |",
                "",
                "### Extractive",
                "",
                "```",
                _clip(ext.get("answer", ""), 900),
                "```",
                "",
                "### Generative (GPT-4o-mini)",
                "",
                "```",
                _clip(gen.get("answer", ""), 900),
                "```",
                "",
                "---",
                "",
            ]
        )

    summary_path = BASE / "reports" / "openai_generative_results_summary.md"
    detail_path = BASE / "reports" / "openai_generative_results_full.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    detail_path.write_text("\n".join(detail_lines), encoding="utf-8")
    print(summary_path)
    print(detail_path)


if __name__ == "__main__":
    main()
