"""Re-index OpenAI E2E full lane with manifest.json + README in corpus."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
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


def _setup() -> tuple[Path, Path]:
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
            "RAG_CHROMA_COLLECTION": f"bench_{hashlib.md5(cache_key.encode('utf-8')).hexdigest()[:16]}",
            "RAG_OPENAI_EMBED_BATCH": "32",
            "RAG_FORCE_REBUILD": "true",
        }
    )
    from run_benchmark_case import _prepare_corpus_manifest

    manifest = _prepare_corpus_manifest(BASE, lane, 1.0, cache_root, company_filter=company_filter)
    os.environ["RAG_BENCHMARK_CORPUS_MANIFEST"] = str(manifest)
    return manifest, index_dir


def main() -> None:
    _load_dotenv()
    manifest_path, index_dir = _setup()
    corpus_files = json.loads(manifest_path.read_text(encoding="utf-8")).get("files", [])
    print("Corpus files:", corpus_files)
    if not any("manifest.json" in f for f in corpus_files):
        raise SystemExit("manifest.json missing from corpus manifest")

    marker = index_dir / ".index_complete"
    for p in (index_dir / "qdrant_db", index_dir / "bm25_corpus.json", marker):
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        elif p.is_file():
            p.unlink(missing_ok=True)

    from rag_stack import ingest_corpus_files

    t0 = time.perf_counter()
    rows, n_chunks = ingest_corpus_files()
    elapsed = round(time.perf_counter() - t0, 1)
    print(f"Ingest OK: {n_chunks} chunks in {elapsed}s")

    bm25 = json.loads((index_dir / "bm25_corpus.json").read_text(encoding="utf-8"))
    sources = {c.get("source", "") for c in bm25.get("chunks", [])}
    has_manifest = any("manifest.json" in s for s in sources)
    print(f"BM25 sources with manifest.json: {has_manifest}")
    print(f"Total BM25 chunk sources: {len(sources)}")


if __name__ == "__main__":
    main()
