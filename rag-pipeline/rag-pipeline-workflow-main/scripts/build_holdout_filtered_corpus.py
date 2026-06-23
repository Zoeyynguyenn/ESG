#!/usr/bin/env python3
"""Build scope-filtered holdout corpus from reingested units."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.holdout_harness import load_corpus_for_company  # noqa: E402
from enterprise_docs.retrieval_scope_policy import (  # noqa: E402
    build_scope_policy_matrix,
    load_retrieval_scope_policy,
    write_filtered_corpus,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--companies", default="hanssem,musinsa")
    parser.add_argument(
        "--scope",
        default=None,
        help="Scope name (default from retrieval_scope_policy.json)",
    )
    args = parser.parse_args()

    scope = args.scope or load_retrieval_scope_policy().get("default_scope") or "structured_esg_retrieval_ready"
    company_ids = [c.strip() for c in args.companies.split(",") if c.strip()]
    units_by_company: dict[str, list] = {}
    build_summary: dict[str, object] = {}

    for cid in company_ids:
        units = load_corpus_for_company(cid, holdout_corpus="reingested")
        units_by_company[cid] = units
        build_summary[cid] = write_filtered_corpus(cid, units, scope_name=scope)

    matrix = build_scope_policy_matrix(units_by_company)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(
        json.dumps(
            {"scope": scope, "build": build_summary, "scope_matrix": matrix},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
