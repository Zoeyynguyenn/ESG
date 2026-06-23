"""Pre-build vector index once per embedding (tranh lap lai ingest o benchmark)."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", default="company_public_dev")
    parser.add_argument("--embedding-model", default="")
    parser.add_argument("--embedding-list", default="")
    parser.add_argument("--chunking-profile", default="recursive_800_120")
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--chunk-overlap", type=int, default=120)
    parser.add_argument("--corpus-version", default="company_public_v1")
    parser.add_argument("--parser-version", default="v1")
    parser.add_argument("--cache-root", default="artifacts/benchmark_cache")
    parser.add_argument("--vector-store", default="chroma", choices=["chroma", "qdrant"])
    parser.add_argument("--company-filter", default="")
    args = parser.parse_args(argv)

    base_dir = Path(__file__).resolve().parent.parent
    cache_root = base_dir / args.cache_root
    chunk_key = f"{args.chunking_profile}_{args.chunk_size}_{args.chunk_overlap}"
    company_filter = args.company_filter.strip()
    models: list[str] = []
    if args.embedding_list.strip():
        models.extend([m.strip() for m in args.embedding_list.split(",") if m.strip()])
    if args.embedding_model.strip():
        models.append(args.embedding_model.strip())
    if not models:
        print("ERROR: can truyen --embedding-model hoac --embedding-list", file=sys.stderr)
        return 2

    from ingest import ingest_lexical_fallback
    from rag_stack import ingest_corpus_files

    failed = 0
    for model in models:
        emb_key = model.replace("/", "_")
        cache_key = (
            f"p={args.parser_version}__c={chunk_key}__e={emb_key}"
            f"__d={args.corpus_version}__lane={args.lane}__vs={args.vector_store}"
        )
        if company_filter:
            cache_key += f"__company={company_filter}"
        chroma_dir = cache_root / "index_cache" / cache_key / "chroma_db"
        qdrant_dir = cache_root / "index_cache" / cache_key / "qdrant_db"
        bm25_path = cache_root / "index_cache" / cache_key / "bm25_corpus.json"
        store_dir = qdrant_dir if args.vector_store == "qdrant" else chroma_dir
        marker = store_dir.parent / ".index_complete"
        if marker.exists() and store_dir.exists() and any(store_dir.rglob("*")) and bm25_path.exists():
            print(f"SKIP: index da co tai {cache_key}")
            continue

        os.environ["RAG_BENCHMARK_LANE"] = args.lane
        os.environ["RAG_CHUNKING_PROFILE"] = args.chunking_profile
        os.environ["RAG_CHUNK_SIZE"] = str(args.chunk_size)
        os.environ["RAG_CHUNK_OVERLAP"] = str(args.chunk_overlap)
        os.environ["RAG_EMBEDDING_MODEL"] = model
        os.environ["RAG_CHROMA_DIR"] = str(chroma_dir)
        os.environ["RAG_BM25_INDEX_PATH"] = str(bm25_path)
        os.environ["RAG_VECTOR_STORE"] = args.vector_store
        if company_filter:
            manifest_dir = cache_root / "manifests"
            manifest_dir.mkdir(parents=True, exist_ok=True)
            manifest_path = manifest_dir / f"corpus_{args.lane}_{company_filter}.json"
            from rag_common import iter_corpus_files

            os.environ["RAG_BENCHMARK_LANE"] = args.lane
            files = [
                str(p.relative_to(base_dir)).replace("\\", "/")
                for p in iter_corpus_files()
                if str(p.relative_to(base_dir)).replace("\\", "/").startswith(
                    f"data/rag_dataset/04_company_public_curated/{company_filter}/"
                )
            ]
            import json

            manifest_path.write_text(
                json.dumps(
                    {"lane": args.lane, "company_filter": company_filter, "files": files},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            os.environ["RAG_BENCHMARK_CORPUS_MANIFEST"] = str(manifest_path)
            os.environ["RAG_COMPANY_FILTER"] = company_filter
        if args.vector_store == "qdrant":
            os.environ["RAG_QDRANT_PATH"] = str(qdrant_dir)

        print(f"Building index: {model} -> {cache_key}")
        t0 = time.perf_counter()
        try:
            ingest_corpus_files()
        except Exception as exc:
            print(f"ingest_corpus_files failed ({model}): {exc}", file=sys.stderr)
            try:
                ingest_lexical_fallback()
            except Exception as exc2:
                print(f"lexical fallback failed ({model}): {exc2}", file=sys.stderr)
                failed += 1
                continue
        elapsed = round(time.perf_counter() - t0, 1)
        print(f"OK: index built in {elapsed}s at {store_dir}")
    if failed:
        print(f"DONE_WITH_ERRORS: failed_models={failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
