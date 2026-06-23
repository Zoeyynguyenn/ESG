"""Re-ingest holdout company packages into parser v1.1 evidence units."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from enterprise_docs.ingest import ingest_tree, units_to_jsonl_rows

ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = ROOT / "data/enterprise_docs/file_inventory.json"

COMPANY_PACKAGE_LABEL: dict[str, str] = {
    "hanssem": "hanssem_mixed",
    "musinsa": "musinsa_mixed",
}


def _load_inventory() -> dict[str, Any]:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def package_path_for_company(company_id: str) -> Path | None:
    label = COMPANY_PACKAGE_LABEL.get(company_id)
    if not label:
        return None
    for pkg in _load_inventory().get("packages") or []:
        if pkg.get("label") == label and pkg.get("exists"):
            return Path(str(pkg.get("path") or ""))
    return None


def reingest_company(
    company_id: str,
    *,
    output: Path | None = None,
    max_documents: int | None = None,
) -> dict[str, Any]:
    """Ingest raw html/xml/pdf package into corpus_units_reingested.jsonl."""
    source_root = package_path_for_company(company_id)
    if not source_root or not source_root.exists():
        return {
            "company_id": company_id,
            "status": "source_missing",
            "source_root": str(source_root or ""),
        }

    units = ingest_tree(source_root, company_id=company_id)
    if max_documents:
        seen: set[str] = set()
        limited: list[Any] = []
        for u in units:
            if u.document_id not in seen:
                if len(seen) >= max_documents:
                    break
                seen.add(u.document_id)
            if u.document_id in seen:
                limited.append(u)
        units = limited

    rows = units_to_jsonl_rows(units)
    out = output or (ROOT / f"data/enterprise_docs/{company_id}/corpus_units_reingested.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    by_doc = Counter(r["document_id"] for r in rows)
    by_type = Counter(r["source_type"] for r in rows)
    summary = {
        "company_id": company_id,
        "status": "ok",
        "parser_version": "1.1.0",
        "source_root": str(source_root),
        "output": str(out.relative_to(ROOT)).replace("\\", "/"),
        "unit_count": len(rows),
        "document_count": len(by_doc),
        "by_source_type": dict(by_type),
        "by_document_sample": dict(list(by_doc.most_common(12))),
    }
    (out.parent / "reingest_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def reingest_holdout_companies(
    company_ids: list[str] | None = None,
) -> dict[str, Any]:
    ids = company_ids or ["hanssem", "musinsa"]
    return {cid: reingest_company(cid) for cid in ids}
