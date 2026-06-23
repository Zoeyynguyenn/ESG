"""Step 1: Export corpus units with metadata from company_export_json packages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from golden_set.io_utils import write_jsonl


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def _gri_from_record(rec: Dict[str, Any]) -> str:
    meta = rec.get("metadata") or {}
    row = meta.get("source_row") or {}
    gri = row.get("gri") or ""
    if gri:
        return str(gri)
    text = rec.get("text") or ""
    for token in text.split("\n"):
        if token.strip().startswith("GRI:"):
            return token.split(":", 1)[1].strip()
    return ""


def _unit_from_record(
    rec: Dict[str, Any],
    *,
    package: str,
    short_name: str,
    source_file: str,
) -> Optional[Dict[str, Any]]:
    text = (rec.get("text") or "").strip()
    if len(text) < 80:
        return None
    role = rec.get("record_role") or ""
    source_type = rec.get("source_type") or ""
    section = rec.get("section_path") or ""

    # Ưu tiên evidence báo cáo ESG + taxonomy có GRI
    is_taxonomy = role == "requirement_taxonomy"
    is_reportish = any(
        k in (section + " " + text[:500]).lower()
        for k in ("sustainability", "지속가능", "esg management", "material", "gri")
    )
    is_news = source_type == "news" or "news" in section.lower()
    if is_news and not is_taxonomy:
        return None
    if not is_taxonomy and not is_reportish:
        # Giữ một phần evidence khác có esg_tags mạnh
        tags = rec.get("esg_tags") or []
        if not tags or tags == ["G.other"]:
            return None

    meta = rec.get("metadata") or {}
    row = meta.get("source_row") or {}
    gri = _gri_from_record(rec)
    unit_id = f"{package}::{rec.get('record_id', '')}"

    return {
        "unit_id": unit_id,
        "package_name": package,
        "company": short_name,
        "record_id": rec.get("record_id", ""),
        "record_role": role,
        "source_type": source_type,
        "section_path": section,
        "source_file": source_file,
        "text": text[:4000],
        "gri_code": gri,
        "k_esg": row.get("k_esg") or "",
        "sasb": row.get("sasb") or "",
        "area": row.get("area") or "",
        "category": row.get("category") or "",
        "subcategory": row.get("subcategory") or "",
        "item": row.get("item") or rec.get("title") or "",
        "unit": row.get("unit") or (rec.get("metric") or {}).get("unit") or "",
        "esg_tags": rec.get("esg_tags") or [],
        "chunking_note": "aligned_with_rag_index_section_based_800_120",
    }


def run_step1(
    *,
    dataset_root: Path,
    output_path: Path,
    companies: List[Dict[str, str]],
    max_units_per_company: int = 40,
) -> Dict[str, Any]:
    units: List[Dict[str, Any]] = []
    stats: Dict[str, int] = {}

    for comp in companies:
        pkg = comp["package"]
        short = comp.get("short_name") or pkg
        pkg_dir = dataset_root / pkg
        if not pkg_dir.is_dir():
            stats[f"missing_{pkg}"] = 1
            continue
        n_pkg = 0
        for rel in (
            "records/company_evidence.jsonl",
            "records/requirement_taxonomy.jsonl",
            "lanes/company_evidence.jsonl",
            "lanes/requirement_taxonomy.jsonl",
        ):
            path = pkg_dir / rel
            for rec in _load_jsonl(path):
                u = _unit_from_record(rec, package=pkg, short_name=short, source_file=rel)
                if u is None:
                    continue
                units.append(u)
                n_pkg += 1
                if n_pkg >= max_units_per_company:
                    break
            if n_pkg >= max_units_per_company:
                break
        stats[short] = n_pkg

    # Dedupe by unit_id
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for u in units:
        if u["unit_id"] in seen:
            continue
        seen.add(u["unit_id"])
        deduped.append(u)

    count = write_jsonl(output_path, deduped)
    return {"units_written": count, "by_company": stats, "output": str(output_path)}
