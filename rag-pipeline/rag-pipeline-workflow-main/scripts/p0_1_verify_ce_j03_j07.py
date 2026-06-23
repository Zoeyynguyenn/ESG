"""Quick retrieval check for CE-J03..J07 after P0.1 field boost."""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))

QUESTIONS = {
    "CE-J03": "Dart corp code trong ho so la gi?",
    "CE-J04": "Cong ty niem yet tren san nao?",
    "CE-J05": "Trang web chinh thuc cua cong ty la gi?",
    "CE-J06": "Export type cua bo du lieu nay la gi?",
    "CE-J07": "Version cua file export la bao nhieu?",
}


def _setup() -> None:
    cache_root = BASE / "artifacts" / "benchmark_cache"
    lane = "company_export_json_full"
    company_filter = "넥스트아이_dataset_package_20260528T091409"
    cache_key = (
        "p=jsonl_v1__c=section_based_800_120__e=openai_text-embedding-3-small__d=nexteye_esg_v1_1_1_openai_full_e2e"
        f"__lane={lane}__vs=qdrant__company={hashlib.md5(company_filter.encode()).hexdigest()[:10]}"
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
            "RAG_VECTOR_STORE": "qdrant",
            "RAG_QDRANT_PATH": str(index_dir / "qdrant_db"),
            "RAG_BM25_INDEX_PATH": str(index_dir / "bm25_corpus.json"),
            "RAG_TOP_K": "4",
            "RAG_FINAL_TOP_K": "4",
            "RAG_CANDIDATE_POOL_SIZE": "64",
            "RAG_RERANK_ENABLED": "false",
        }
    )


def main() -> None:
    _setup()
    from retrieval_v3 import query_v3

    for qid, question in QUESTIONS.items():
        r = query_v3(question, retrieval_mode="hybrid_dense_bm25", top_k=4, pool=64)
        top = (r.get("evidence") or [{}])[0]
        text = (top.get("text") or "")[:220].replace("\n", " ")
        boost = (top.get("score_breakdown") or {}).get("field_boost")
        print(f"\n{qid}: score={top.get('score')} boost={boost}")
        print(f"  src: {top.get('source', '')[-80:]}")
        print(f"  text: {text}")


if __name__ == "__main__":
    main()
