#!/usr/bin/env python3
"""Build holdout re-ingested corpus units (parser v1.1) from file inventory packages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.holdout_reingest import reingest_holdout_companies  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--companies",
        default="hanssem,musinsa",
        help="Comma-separated holdout company ids",
    )
    args = parser.parse_args()
    company_ids = [c.strip() for c in args.companies.split(",") if c.strip()]
    summary = reingest_holdout_companies(company_ids)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if any(v.get("status") != "ok" for v in summary.values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
