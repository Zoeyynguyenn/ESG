"""Multi-format document transformation audit for enterprise internal-doc lane."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from enterprise_docs.parsers import detect_source_type, read_text, split_markdown_sections

ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = ROOT / "data/enterprise_docs/file_inventory.json"

# Parser capability model (system-level, not per-case tuned)
_FORMAT_CAPABILITIES: dict[str, dict[str, Any]] = {
    "markdown": {
        "parser_status": "implemented",
        "parse_success_expected": 1.0,
        "section_preservation": 0.9,
        "table_preservation": 0.85,
        "metadata_preservation": 0.7,
        "unit_value_preservation": 0.8,
        "structured_extraction_readiness": "strong",
        "notes": "split_markdown_sections + table rows preserved in text",
    },
    "csv": {
        "parser_status": "implemented",
        "parse_success_expected": 1.0,
        "section_preservation": 0.3,
        "table_preservation": 0.75,
        "metadata_preservation": 0.4,
        "unit_value_preservation": 0.7,
        "structured_extraction_readiness": "adequate",
        "notes": "pipe-delimited rows; no typed schema",
    },
    "json": {
        "parser_status": "implemented",
        "parse_success_expected": 0.95,
        "section_preservation": 0.2,
        "table_preservation": 0.5,
        "metadata_preservation": 0.6,
        "unit_value_preservation": 0.65,
        "structured_extraction_readiness": "adequate",
        "notes": "pretty-print to text; structure flattened",
    },
    "jsonl": {
        "parser_status": "partial",
        "parse_success_expected": 0.9,
        "section_preservation": 0.2,
        "table_preservation": 0.4,
        "metadata_preservation": 0.5,
        "unit_value_preservation": 0.5,
        "structured_extraction_readiness": "weak",
        "notes": "line-by-line not specialized in ingest_path",
    },
    "html": {
        "parser_status": "implemented",
        "parser_version": "1.1.0",
        "parse_success_expected": 0.9,
        "section_preservation": 0.55,
        "table_preservation": 0.6,
        "metadata_preservation": 0.45,
        "unit_value_preservation": 0.55,
        "structured_extraction_readiness": "adequate",
        "notes": "HTMLParser table rows + heading blocks (v1.1 hardening)",
    },
    "xml": {
        "parser_status": "implemented",
        "parser_version": "1.1.0",
        "parse_success_expected": 0.85,
        "section_preservation": 0.5,
        "table_preservation": 0.35,
        "metadata_preservation": 0.55,
        "unit_value_preservation": 0.5,
        "structured_extraction_readiness": "adequate",
        "notes": "ElementTree text walk for DART/KIPRIS-style XML (v1.1)",
    },
    "pdf": {
        "parser_status": "implemented",
        "parser_version": "1.1.0",
        "parse_success_expected": 0.75,
        "section_preservation": 0.35,
        "table_preservation": 0.4,
        "metadata_preservation": 0.3,
        "unit_value_preservation": 0.45,
        "structured_extraction_readiness": "adequate",
        "notes": "Page sections + table-line pipe join (v1.1)",
    },
    "text": {
        "parser_status": "implemented",
        "parse_success_expected": 1.0,
        "section_preservation": 0.1,
        "table_preservation": 0.1,
        "metadata_preservation": 0.2,
        "unit_value_preservation": 0.3,
        "structured_extraction_readiness": "weak",
        "notes": "plain text chunk only",
    },
    "word": {
        "parser_status": "planned",
        "parse_success_expected": 0.0,
        "section_preservation": 0.0,
        "table_preservation": 0.0,
        "metadata_preservation": 0.0,
        "unit_value_preservation": 0.0,
        "structured_extraction_readiness": "not_implemented",
        "notes": "framework slot for .docx — not in supported_extensions",
    },
    "ppt": {
        "parser_status": "planned",
        "parse_success_expected": 0.0,
        "section_preservation": 0.0,
        "table_preservation": 0.0,
        "metadata_preservation": 0.0,
        "unit_value_preservation": 0.0,
        "structured_extraction_readiness": "not_implemented",
        "notes": "framework slot for .pptx — not in supported_extensions",
    },
    "image_ocr": {
        "parser_status": "planned",
        "parse_success_expected": 0.0,
        "section_preservation": 0.0,
        "table_preservation": 0.0,
        "metadata_preservation": 0.0,
        "unit_value_preservation": 0.0,
        "structured_extraction_readiness": "not_implemented",
        "notes": "framework slot for image OCR pipeline",
    },
}

_PACKAGE_LABEL_MAP = {
    "demo_company": "demo_company",
    "한샘": "hanssem",
    "무신사": "musinsa",
}


def _has_table_markers(text: str) -> bool:
    return bool(re.search(r"\|.+\|", text)) or "|" in text and text.count("|") >= 4


def _probe_sample_file(path: Path) -> dict[str, Any]:
    """Live probe one file if accessible."""
    out: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        out["parse_success"] = False
        return out
    try:
        st = detect_source_type(path)
        text = read_text(path)
        out["source_type"] = st
        out["parse_success"] = bool(text and text.strip())
        out["char_count"] = len(text or "")
        out["has_sections"] = (
            len(split_markdown_sections(text)) > 1 if st == "markdown" else False
        )
        out["has_table_markers"] = _has_table_markers(text or "")
        out["has_year"] = bool(re.search(r"\b20\d{2}\b", text or ""))
        out["has_numeric"] = bool(re.search(r"\d[\d,.]*", text or ""))
    except Exception as exc:  # noqa: BLE001
        out["parse_success"] = False
        out["error"] = str(exc)
    return out


def audit_format_transformation(*, sample_probe: bool = True) -> dict[str, Any]:
    """Audit format coverage from inventory + parser capabilities."""
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8")) if INVENTORY_PATH.exists() else {}
    packages = inventory.get("packages") or []

    by_format: dict[str, dict[str, Any]] = {}
    by_company_format: dict[str, dict[str, int]] = {}
    live_probes: list[dict[str, Any]] = []

    for pkg in packages:
        label = str(pkg.get("label") or "")
        company_id = _PACKAGE_LABEL_MAP.get(label, label)
        by_type = pkg.get("by_source_type") or {}
        by_company_format[company_id] = dict(by_type)
        for fmt, count in by_type.items():
            entry = by_format.setdefault(fmt, {
                "format": fmt,
                "document_count": 0,
                "companies": [],
                **_FORMAT_CAPABILITIES.get(fmt, _FORMAT_CAPABILITIES.get("text", {})),
            })
            entry["document_count"] += int(count)
            if company_id not in entry["companies"]:
                entry["companies"].append(company_id)

    # Add planned formats with zero count
    for fmt in ("word", "ppt", "image_ocr"):
        if fmt not in by_format:
            by_format[fmt] = {"format": fmt, "document_count": 0, "companies": [], **_FORMAT_CAPABILITIES[fmt]}

    if sample_probe:
        for pkg in packages[:3]:
            docs = (pkg.get("documents") or [])[:2]
            for doc in docs:
                p = Path(str(doc.get("source_path") or ""))
                if p.suffix.lower() in {".md", ".csv", ".json", ".html", ".xml", ".pdf"}:
                    live_probes.append(_probe_sample_file(p))

    # Readiness score per format (heuristic composite)
    format_rows: list[dict[str, Any]] = []
    for fmt, row in sorted(by_format.items()):
        caps = _FORMAT_CAPABILITIES.get(fmt, {})
        composite = round(
            (
                float(caps.get("parse_success_expected") or 0)
                + float(caps.get("section_preservation") or 0)
                + float(caps.get("table_preservation") or 0)
                + float(caps.get("metadata_preservation") or 0)
                + float(caps.get("unit_value_preservation") or 0)
            )
            / 5,
            3,
        )
        format_rows.append({
            **row,
            "transformation_readiness_score": composite,
            "readiness_tier": (
                "strong" if composite >= 0.7 else "adequate" if composite >= 0.45 else "weak"
            ),
        })

    format_rows.sort(key=lambda r: (-r.get("transformation_readiness_score", 0), -r.get("document_count", 0)))

    priority_strengthen = [r["format"] for r in format_rows if r.get("document_count", 0) > 0 and r.get("readiness_tier") == "weak"]
    priority_maintain = [r["format"] for r in format_rows if r.get("readiness_tier") in ("strong", "adequate") and r.get("document_count", 0) > 0]

    return {
        "version": "1.0.0",
        "audit_type": "multi_format_transformation",
        "by_format": {r["format"]: r for r in format_rows},
        "format_priority_list": {
            "strengthen_next": priority_strengthen,
            "maintain": priority_maintain,
            "planned_not_in_corpus": ["word", "ppt", "image_ocr"],
        },
        "by_company_format": by_company_format,
        "live_sample_probes": live_probes,
        "metric_types": {
            "exact": ["document_count per format from inventory"],
            "heuristic": ["transformation_readiness_score", "readiness_tier"],
            "proxy": ["live_sample_probes when file path accessible"],
        },
    }
