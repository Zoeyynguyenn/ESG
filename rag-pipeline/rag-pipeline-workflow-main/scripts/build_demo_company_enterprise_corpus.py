#!/usr/bin/env python3
"""Build demo_company enterprise evidence corpus (prototype)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.ingest import ingest_tree, units_to_jsonl_rows  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root",
        default=r"C:\Users\nguye\Downloads\data-company\demo_company\rtx_7step_dataset\rtx_7step_dataset",
    )
    parser.add_argument(
        "--company-id",
        default="demo_company",
    )
    parser.add_argument(
        "--output",
        default="data/enterprise_docs/demo_company/corpus_units.jsonl",
    )
    parser.add_argument(
        "--also-ingest-csv",
        default=r"C:\Users\nguye\Downloads\data-company\demo_company",
        help="Parent folder to also pick up evidence CSV",
    )
    args = parser.parse_args()

    source_root = Path(args.source_root)
    if not source_root.exists():
        raise SystemExit(f"Source not found: {source_root}")

    units = ingest_tree(source_root, company_id=args.company_id)

    parent = Path(args.also_ingest_csv)
    for csv_path in parent.glob("*.csv"):
        from enterprise_docs.ingest import ingest_path

        units.extend(ingest_path(csv_path, company_id=args.company_id, root=parent, esg_domain="mixed"))

    rows = units_to_jsonl_rows(units)
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "company_id": args.company_id,
        "source_root": str(source_root),
        "unit_count": len(rows),
        "by_document": dict(Counter(r["document_id"] for r in rows)),
        "by_source_type": dict(Counter(r["source_type"] for r in rows)),
        "output": str(out.relative_to(ROOT)).replace("\\", "/"),
    }
    (out.parent / "corpus_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
