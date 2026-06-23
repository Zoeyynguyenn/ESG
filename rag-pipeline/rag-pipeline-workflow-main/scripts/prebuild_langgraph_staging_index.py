#!/usr/bin/env python3
"""Pre-index corpus cho LangGraph staging.

Ví dụ:
  python scripts/prebuild_langgraph_staging_index.py
  python scripts/prebuild_langgraph_staging_index.py --company musinsa
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _bootstrap_env() -> None:
    from evidence_api.env_bootstrap import load_repo_dotenv

    load_repo_dotenv()


def main(argv: list[str] | None = None) -> int:
    _bootstrap_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="", help="Path configs/langgraph_staging.yaml")
    parser.add_argument("--company", default="", help="Chi build mot company_id (vd. musinsa)")
    parser.add_argument("--force", action="store_true", help="Rebuild index neu da co")
    args = parser.parse_args(argv)

    import os

    from evidence_api.staging_config import (
        apply_company_env,
        company_cfg,
        company_registry,
        load_staging_config,
        reset_retrieval_runtime_caches,
    )
    from production_config import index_chunk_parity_mismatch, index_ready, repo_root

    cfg = load_staging_config(args.config or None)
    companies = [args.company] if args.company else sorted(company_registry(cfg))
    if not companies:
        print("ERROR: registry trong trong", file=sys.stderr)
        return 2

    reg = company_registry(cfg)
    failed = 0
    for company_id in companies:
        if company_id not in reg:
            print(f"SKIP: company_id khong co trong registry: {company_id}")
            failed += 1
            continue
        entry = reg[company_id]
        ccfg = company_cfg(cfg, company_id)
        if entry.get("legacy_cache_only") and not args.force:
            print(
                f"SKIP: {company_id} legacy_cache_only — khong rebuild (cache thieu thi restore cache cu)",
                file=sys.stderr,
            )
            if not index_ready(ccfg):
                failed += 1
            continue

        apply_company_env(cfg, company_id, base_dir=repo_root())
        parity = index_chunk_parity_mismatch(ccfg, base_dir=repo_root())
        force_rebuild = args.force or bool(parity)
        if parity and not args.force:
            print(f"REBUILD: {company_id} index parity stale ({parity})")
        elif index_ready(ccfg) and not force_rebuild:
            print(f"SKIP: index san sang cho {company_id}")
            continue

        print(f"BUILD: {company_id}")
        reset_retrieval_runtime_caches()
        from rag_stack import ingest_corpus_files

        if force_rebuild:
            os.environ["RAG_FORCE_REBUILD"] = "true"
        try:
            rows, n_chunks = ingest_corpus_files()
            loaded = sum(1 for r in rows if r.status == "loaded")
            print(f"OK: {company_id} files_loaded={loaded} chunks={n_chunks}")
        except Exception as exc:
            print(f"FAIL: {company_id} {exc}", file=sys.stderr)
            failed += 1
        finally:
            os.environ.pop("RAG_FORCE_REBUILD", None)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
