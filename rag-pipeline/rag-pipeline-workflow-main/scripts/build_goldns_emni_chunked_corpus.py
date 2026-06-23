#!/usr/bin/env python3
"""Build chunked corpus from goldns/emni web + local raw sources."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))

from rag_common import split_chunks, strip_html  # noqa: E402

YEAR_RE = re.compile(r"(20\d{2})")
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
SANCTION_LANE_BY_DOMAIN = {
    "www.safetykorea.kr": "safetykorea",
    "www.pipc.go.kr": "pipc",
    "case.ftc.go.kr": "ftc",
}


def _sanction_lane(row: dict[str, Any]) -> str | None:
    domain = str(row.get("domain") or "").strip().lower()
    if domain in SANCTION_LANE_BY_DOMAIN:
        return SANCTION_LANE_BY_DOMAIN[domain]
    source_url = str(row.get("source_url") or "").lower()
    for domain_key, lane in SANCTION_LANE_BY_DOMAIN.items():
        if domain_key in source_url:
            return lane
    return None


def _effective_doc_title(doc_title: str, row: dict[str, Any]) -> str:
    if doc_title == "제재이력.json":
        lane = _sanction_lane(row)
        if lane:
            return f"제재이력_{lane}.json"
    return doc_title


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _infer_year(doc_title: str | None, text: str = "") -> int | None:
    if doc_title:
        m = YEAR_RE.search(doc_title)
        if m:
            return int(m.group(1))
    m = YEAR_RE.search(text[:200])
    return int(m.group(1)) if m else None


def _header_metadata(base_meta: dict[str, Any]) -> dict[str, Any]:
    meta = {
        "company_id": base_meta.get("company_id"),
        "company_name": base_meta.get("company_name"),
        "doc_title": base_meta.get("doc_title"),
        "canonical_doc_title": base_meta.get("canonical_doc_title") or base_meta.get("doc_title"),
        "source_url": base_meta.get("source_url"),
        "file_url": base_meta.get("file_url"),
        "source_kind": base_meta.get("source_kind"),
        "year": base_meta.get("year"),
        "schema": base_meta.get("schema"),
        "source_path": base_meta.get("source_path"),
    }
    if base_meta.get("sanction_lane"):
        meta["sanction_lane"] = base_meta.get("sanction_lane")
    return meta


def _strip_extracted_header(text: str) -> str:
    lines = text.splitlines()
    body: list[str] = []
    started = False
    for line in lines:
        if not started and (
            line.startswith("company_id:")
            or line.startswith("company_name:")
            or line.startswith("doc_title:")
            or line.startswith("source_url:")
            or line.startswith("file_url:")
            or line.startswith("source_kind:")
            or line.startswith("year:")
            or line.startswith("schema:")
            or line.startswith("local_path:")
            or line.strip() == ""
        ):
            continue
        if line.startswith("# DART") or line.startswith("## ") or line.strip().startswith("- "):
            started = True
        if started:
            body.append(line)
    return "\n".join(body).strip()


def _make_unit(
    *,
    base_meta: dict[str, Any],
    content: str,
    chunk_idx: int,
    record_id: str | None = None,
) -> dict[str, Any]:
    search_text = content.strip()
    metadata = _header_metadata(base_meta)
    chunk_id = record_id or f"{base_meta['company_id']}::{base_meta.get('doc_title', 'doc')}::{chunk_idx}"
    return {
        "chunk_id": chunk_id,
        **metadata,
        "search_text": search_text,
        "evidence_text": search_text,
        "metadata": metadata,
        # Backward compatibility for any consumer still reading `text`.
        "text": search_text,
    }


def _units_from_records_jsonl(path: Path, base_meta: dict[str, Any]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for idx, row in enumerate(_read_jsonl(path)):
        text = str(row.get("text") or "").strip()
        if not text:
            continue
        record_id = str(row.get("record_id") or f"{base_meta.get('doc_title')}::{idx}")
        units.append(_make_unit(base_meta=base_meta, content=text, chunk_idx=idx, record_id=record_id))
    return units


def _units_from_extracted_txt(path: Path, base_meta: dict[str, Any]) -> list[dict[str, Any]]:
    text = _strip_extracted_header(path.read_text(encoding="utf-8"))
    sections = re.split(r"\n(?=## )", text)
    units: list[dict[str, Any]] = []
    chunk_idx = 0
    for section in sections:
        section = section.strip()
        if not section:
            continue
        for part in split_chunks(section, CHUNK_SIZE, CHUNK_OVERLAP):
            units.append(_make_unit(base_meta=base_meta, content=part, chunk_idx=chunk_idx))
            chunk_idx += 1
    return units


def _units_from_html(path: Path, base_meta: dict[str, Any]) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = strip_html(raw)
    if not text.strip():
        return []
    units: list[dict[str, Any]] = []
    for idx, part in enumerate(split_chunks(text, CHUNK_SIZE, CHUNK_OVERLAP)):
        units.append(_make_unit(base_meta=base_meta, content=part, chunk_idx=idx))
    return units


def _load_local_units(local_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    units: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for row in _read_jsonl(local_root / "collect_status.jsonl"):
        if row.get("collect_status") != "ok":
            skipped.append({**row, "skip_reason": "collect_not_ok"})
            continue
        artifact_dir = Path(row.get("artifact_dir") or "")
        if not artifact_dir.is_dir():
            skipped.append({**row, "skip_reason": "missing_artifact_dir"})
            continue
        base_meta = {
            "company_id": row.get("company_id"),
            "company_name": row.get("company_name"),
            "doc_title": row.get("doc_title"),
            "source_url": row.get("source_url"),
            "file_url": row.get("file_url"),
            "source_kind": row.get("source_kind") or "collector_file_reference",
            "year": _infer_year(row.get("doc_title")),
            "schema": row.get("schema"),
            "source_path": str(artifact_dir / "extracted.txt"),
        }
        records_path = artifact_dir / "records.jsonl"
        extracted_path = artifact_dir / "extracted.txt"
        if records_path.is_file():
            source_units = _units_from_records_jsonl(records_path, base_meta)
        elif extracted_path.is_file():
            source_units = _units_from_extracted_txt(extracted_path, base_meta)
        else:
            skipped.append({**row, "skip_reason": "missing_extracted_or_records"})
            continue
        units.extend(source_units)
    return units, skipped


def _load_web_units(web_root: Path, local_keys: set[tuple[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    units: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for row in _read_jsonl(web_root / "download_status.jsonl"):
        company_id = row.get("company_id") or ""
        raw_doc_title = row.get("doc_title") or ""
        doc_title = _effective_doc_title(raw_doc_title, row)
        key = (company_id, doc_title)
        if key in local_keys:
            skipped.append({**row, "skip_reason": "deduped_by_local_source"})
            continue
        if row.get("download_status") != "ok":
            skipped.append({**row, "skip_reason": row.get("error") or "download_not_ok"})
            continue
        local_path = Path(row.get("local_path") or "")
        if not local_path.is_file():
            skipped.append({**row, "skip_reason": "missing_local_path"})
            continue
        lane = _sanction_lane(row) if raw_doc_title == "제재이력.json" else None
        base_meta = {
            "company_id": company_id,
            "company_name": row.get("company_name"),
            "doc_title": doc_title,
            "canonical_doc_title": raw_doc_title,
            "source_url": row.get("source_url"),
            "file_url": row.get("file_url"),
            "source_kind": row.get("source_kind") or "web_public",
            "year": _infer_year(doc_title, local_path.name),
            "schema": "web_html",
            "source_path": str(local_path),
            "sanction_lane": lane,
        }
        units.extend(_units_from_html(local_path, base_meta))
    return units, skipped


def _summary_markdown(
    units: list[dict[str, Any]],
    local_skipped: list[dict[str, Any]],
    web_skipped: list[dict[str, Any]],
) -> str:
    by_company = Counter(u["company_id"] for u in units)
    by_kind = Counter(u.get("source_kind") or "unknown" for u in units)
    lines = [
        "# Goldns/Emni Chunked Corpus Summary",
        "",
        f"- total_units: {len(units)}",
        f"- local_skipped: {len(local_skipped)}",
        f"- web_skipped: {len(web_skipped)}",
        "",
        "## Theo company",
        "",
        "| Company | Units |",
        "|---|---:|",
    ]
    for company_id, count in sorted(by_company.items()):
        lines.append(f"| {company_id} | {count} |")
    lines.extend(["", "## Theo source_kind", "", "| Source kind | Units |", "|---|---:|"])
    for kind, count in sorted(by_kind.items()):
        lines.append(f"| {kind} | {count} |")
    blocked = [r for r in web_skipped if r.get("skip_reason") != "deduped_by_local_source"]
    if blocked:
        lines.extend(["", "## Web source skipped/blocked", ""])
        for row in blocked:
            lines.append(
                f"- {row.get('company_id')} / {row.get('doc_title')}: {row.get('skip_reason')}"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-root", default="data/source_raw/20260617_goldns_emni")
    parser.add_argument("--local-root", default="data/source_raw/20260617_goldns_emni_local")
    parser.add_argument("--output-root", default="data/corpus/20260617_goldns_emni")
    args = parser.parse_args()

    web_root = ROOT / args.web_root
    local_root = ROOT / args.local_root
    output_root = ROOT / args.output_root

    local_units, local_skipped = _load_local_units(local_root)
    local_keys = {(u["company_id"], u.get("doc_title") or "") for u in local_units}
    local_keys |= {
        (row.get("company_id") or "", row.get("doc_title") or "")
        for row in _read_jsonl(local_root / "collect_status.jsonl")
        if row.get("collect_status") == "ok"
    }
    web_units, web_skipped = _load_web_units(web_root, local_keys)
    units = local_units + web_units

    _write_jsonl(output_root / "corpus_units.jsonl", units)
    _write_jsonl(output_root / "build_skipped.jsonl", local_skipped + web_skipped)
    (output_root / "README.md").write_text(
        _summary_markdown(units, local_skipped, web_skipped),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "total_units": len(units),
                "local_units": len(local_units),
                "web_units": len(web_units),
                "output_root": str(output_root),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
