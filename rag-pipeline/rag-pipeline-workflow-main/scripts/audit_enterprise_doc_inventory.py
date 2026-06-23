#!/usr/bin/env python3
"""Scan enterprise document folders and emit file-type inventory."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enterprise_docs.ingest import SUPPORTED_EXTENSIONS, scan_documents  # noqa: E402


def _inventory_for_root(label: str, path: Path, company_id: str) -> dict:
    descriptors = scan_documents(path, company_id=company_id) if path.exists() else []
    by_type = Counter(d.source_type for d in descriptors)
    return {
        "label": label,
        "path": str(path),
        "exists": path.exists(),
        "document_count": len(descriptors),
        "by_source_type": dict(by_type),
        "documents": [
            {
                "document_id": d.document_id,
                "source_type": d.source_type,
                "title": d.title,
                "byte_size": d.byte_size,
                "source_path": d.source_path,
            }
            for d in descriptors
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="data/enterprise_docs/file_inventory.json",
    )
    parser.add_argument(
        "--demo-root",
        default=r"C:\Users\nguye\Downloads\data-company\demo_company",
    )
    parser.add_argument(
        "--hanssem-root",
        default=r"C:\Users\nguye\Downloads\data-company\한샘_일반자료_20260430",
    )
    parser.add_argument(
        "--musinsa-root",
        default=r"C:\Users\nguye\Downloads\data-company\무신사_일반자료_20260430",
    )
    args = parser.parse_args()

    demo_root = Path(args.demo_root)
    payload = {
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        "packages": [
            _inventory_for_root(
                "demo_company",
                demo_root,
                "demo_company",
            ),
            _inventory_for_root(
                "demo_company_rtx_7step",
                demo_root / "rtx_7step_dataset" / "rtx_7step_dataset",
                "demo_company",
            ),
            _inventory_for_root("hanssem_mixed", Path(args.hanssem_root), "hanssem"),
            _inventory_for_root("musinsa_mixed", Path(args.musinsa_root), "musinsa"),
        ],
    }

    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({p["label"]: p["document_count"] for p in payload["packages"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
