"""Prebuild index theo cap (chunking, embedding) doc tu benchmark matrix YAML.

Mac dinh tao dung 6 cap:
- chunking: stagewise.dev_chunking_ids (thuong 3)
- embedding: lay N dau tu dimensions.embedding, voi N = stagewise.round_a.keep_top.embedding (thuong 2)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _load_yaml(path: Path) -> dict[str, Any]:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _chunking_stagewise(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    dims = cfg.get("dimensions", {}).get("chunking", [])
    by_id = {c.get("id"): c for c in dims}
    ids = cfg.get("stagewise", {}).get("dev_chunking_ids") or [c.get("id") for c in dims]
    out = []
    for cid in ids:
        c = by_id.get(cid)
        if c:
            out.append(c)
    return out


def _embeddings_for_pairs(cfg: dict[str, Any], limit_override: int | None) -> list[dict[str, Any]]:
    emb = cfg.get("dimensions", {}).get("embedding", [])
    if limit_override and limit_override > 0:
        return emb[:limit_override]
    n = (
        cfg.get("stagewise", {})
        .get("round_a", {})
        .get("keep_top", {})
        .get("embedding", 2)
    )
    try:
        n = int(n)
    except Exception:
        n = 2
    n = max(1, min(n, len(emb)))
    return emb[:n]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", default="configs/benchmark_matrix_v1.yaml")
    parser.add_argument("--lane", default="company_public_dev")
    parser.add_argument("--vector-store", choices=["chroma", "qdrant"], default="chroma")
    parser.add_argument("--embedding-limit", type=int, default=0)
    parser.add_argument("--parser-version", default="")
    parser.add_argument("--corpus-version", default="")
    parser.add_argument("--cache-root", default="")
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    base_dir = Path(__file__).resolve().parent.parent
    cfg = _load_yaml(base_dir / args.matrix)

    chunkings = _chunking_stagewise(cfg)
    embeddings = _embeddings_for_pairs(cfg, args.embedding_limit if args.embedding_limit > 0 else None)
    parser_version = args.parser_version or cfg.get("cache", {}).get("parser_version", "v1")
    if args.corpus_version:
        corpus_version = args.corpus_version
    else:
        lane_cfg = cfg.get("dataset_lanes", {}).get(f"{args.lane}_subset", {})
        corpus_version = lane_cfg.get("corpus_version") or cfg.get("cache", {}).get("corpus_version", "esg_core_v1")
    cache_root = args.cache_root or cfg.get("cache", {}).get("cache_root", "artifacts/benchmark_cache")

    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for c in chunkings:
        for e in embeddings:
            pairs.append((c, e))

    summary = {
        "matrix": args.matrix,
        "lane": args.lane,
        "vector_store": args.vector_store,
        "pair_count": len(pairs),
        "chunking_ids": [c.get("id") for c in chunkings],
        "embedding_ids": [e.get("id") for e in embeddings],
        "parser_version": parser_version,
        "corpus_version": corpus_version,
        "cache_root": cache_root,
        "dry_run": args.dry_run,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.dry_run:
        return 0

    failed = 0
    for idx, (c, e) in enumerate(pairs, 1):
        cmd = [
            args.python_bin,
            str(base_dir / "src" / "prebuild_benchmark_index.py"),
            "--lane",
            args.lane,
            "--vector-store",
            args.vector_store,
            "--embedding-model",
            str(e.get("model")),
            "--chunking-profile",
            str(c.get("profile")),
            "--chunk-size",
            str(c.get("chunk_size")),
            "--chunk-overlap",
            str(c.get("chunk_overlap")),
            "--corpus-version",
            str(corpus_version),
            "--parser-version",
            str(parser_version),
            "--cache-root",
            str(cache_root),
        ]
        print(f"[{idx}/{len(pairs)}] prebuild {c.get('id')} x {e.get('id')}")
        rc = subprocess.run(cmd, cwd=str(base_dir)).returncode
        if rc != 0:
            failed += 1
            print(f"  -> FAIL rc={rc}")
        else:
            print("  -> OK")

    if failed:
        print(f"DONE_WITH_ERRORS: failed_pairs={failed}/{len(pairs)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

