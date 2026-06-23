#!/usr/bin/env python3
"""Prebuild Qdrant+BM25 index cho cả 3 công ty (registry companies_3cty)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import yaml

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))


def _load_embed_env() -> None:
    """Chỉ .env / .env.local — embed OpenAI, không ghi đè bởi .env.c2 (hallmdr LLM)."""
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


def _load_registry(path: Path) -> List[Dict[str, Any]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    companies = raw.get("companies") or {}
    rows: List[Dict[str, Any]] = []
    for key, meta in companies.items():
        if not isinstance(meta, dict):
            continue
        rows.append(
            {
                "registry_key": key,
                "package": str(meta["package"]).strip(),
                "corpus_version": str(meta["corpus_version"]).strip(),
                "display_name": meta.get("display_name") or key,
            }
        )
    return rows


def _reindex_one(*, package: str, corpus_version: str, display_name: str) -> Dict[str, Any]:
    cache_root = BASE / "artifacts" / "benchmark_cache"
    lane = "company_export_json_full"
    parser_key = "jsonl_v1"
    chunk_key = "section_based_800_120"
    emb_key = "openai_text-embedding-3-small"
    vs = "qdrant"
    cache_key = (
        f"p={parser_key}__c={chunk_key}__e={emb_key}__d={corpus_version}"
        f"__lane={lane}__vs={vs}__company={hashlib.md5(package.encode()).hexdigest()[:10]}"
    )
    index_dir = cache_root / "index_cache" / cache_key

    os.environ.update(
        {
            "RAG_BENCHMARK_LANE": lane,
            "RAG_COMPANY_FILTER": package,
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
    from rag_stack import ingest_corpus_files

    manifest_path = _prepare_corpus_manifest(BASE, lane, 1.0, cache_root, company_filter=package)
    os.environ["RAG_BENCHMARK_CORPUS_MANIFEST"] = str(manifest_path)
    corpus_files = json.loads(manifest_path.read_text(encoding="utf-8")).get("files", [])
    if not any("manifest.json" in f for f in corpus_files):
        raise RuntimeError(f"{display_name}: manifest.json missing from corpus manifest")

    marker = index_dir / ".index_complete"
    for p in (index_dir / "qdrant_db", index_dir / "bm25_corpus.json", marker):
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        elif p.is_file():
            p.unlink(missing_ok=True)

    t0 = time.perf_counter()
    _, n_chunks = ingest_corpus_files()
    elapsed = round(time.perf_counter() - t0, 1)
    bm25 = json.loads((index_dir / "bm25_corpus.json").read_text(encoding="utf-8"))
    sources = {c.get("source", "") for c in bm25.get("chunks", [])}
    return {
        "company": display_name,
        "package": package,
        "corpus_version": corpus_version,
        "cache_key": cache_key,
        "chunks": n_chunks,
        "elapsed_sec": elapsed,
        "manifest_in_bm25": any("manifest.json" in s for s in sources),
        "index_dir": str(index_dir),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--registry",
        default="configs/companies_3cty_registry.yaml",
        help="Registry YAML (default: configs/companies_3cty_registry.yaml)",
    )
    parser.add_argument(
        "--company",
        default="",
        help="Chỉ build 1 công ty (registry key: raysolution|hanssem|musinsa)",
    )
    args = parser.parse_args()

    _load_embed_env()
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        print("ERROR: OPENAI_API_KEY missing — cần key OpenAI thật trong .env (embed).", file=sys.stderr)
        return 1

    registry_path = BASE / args.registry
    rows = _load_registry(registry_path)
    if args.company.strip():
        rows = [r for r in rows if r["registry_key"] == args.company.strip()]
        if not rows:
            print(f"ERROR: unknown company key {args.company!r}", file=sys.stderr)
            return 1

    print(f"Prebuild {len(rows)} company index(es) from {registry_path.name}...")
    results = []
    for row in rows:
        print(f"\n==> {row['display_name']} ({row['package']})")
        try:
            out = _reindex_one(
                package=row["package"],
                corpus_version=row["corpus_version"],
                display_name=row["display_name"],
            )
            results.append(out)
            print(
                f"OK: {out['chunks']} chunks in {out['elapsed_sec']}s | "
                f"manifest_in_bm25={out['manifest_in_bm25']}"
            )
        except Exception as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1

    summary = BASE / "reports" / "prebuild_3cty_index_summary.json"
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
