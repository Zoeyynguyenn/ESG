"""Ingest mixed-format enterprise documents into normalized evidence units."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterator

from enterprise_docs.models import DocumentDescriptor, EvidenceUnit, SourceType
from enterprise_docs.parsers import (
    detect_source_type,
    infer_year,
    read_text,
    split_markdown_sections,
    split_structured_sections,
)
from enterprise_docs.registries import ingest_profile

try:
    from rag_common import split_chunks
except ImportError:  # pragma: no cover
    def split_chunks(text: str, size: int = 900, overlap: int = 150) -> list[str]:
        return [text[i : i + size] for i in range(0, len(text), max(1, size - overlap))]


def _profile(company_id: str) -> dict[str, Any]:
    return ingest_profile(company_id)


def _document_id_from_path(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    stem = re.sub(r"[^0-9a-zA-Z가-힣_]+", "_", rel)
    return stem.strip("_")[:120] or "document"


def scan_documents(root: Path, *, company_id: str) -> list[DocumentDescriptor]:
    profile = _profile(company_id)
    supported = {ext.lower() for ext in profile["supported_extensions"]}
    descriptors: list[DocumentDescriptor] = []
    if not root.exists():
        return descriptors
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in supported:
            continue
        source_type = detect_source_type(path)
        title = path.stem
        descriptors.append(
            DocumentDescriptor(
                document_id=_document_id_from_path(path, root),
                source_path=str(path),
                source_type=source_type,
                title=title,
                byte_size=path.stat().st_size,
            )
        )
    return descriptors


def ingest_path(
    path: Path,
    *,
    company_id: str,
    root: Path,
    esg_domain: str | None = None,
) -> Iterator[EvidenceUnit]:
    profile = _profile(company_id)
    chunk_size = int(profile["chunk_size"])
    chunk_overlap = int(profile["chunk_overlap"])
    source_type = detect_source_type(path)
    text = read_text(path)
    if not text.strip():
        return
    document_id = _document_id_from_path(path, root)
    year = infer_year(text)

    if source_type == "markdown":
        sections = split_markdown_sections(text)
    elif source_type in ("html", "xml"):
        sections = split_structured_sections(text, source_type)
    else:
        sections = [("root", text)]

    unit_idx = 0
    for section, section_text in sections:
        if not section_text.strip():
            continue
        for chunk in split_chunks(section_text, size=chunk_size, overlap=chunk_overlap):
            if not chunk.strip():
                continue
            unit_idx += 1
            unit_id = f"{company_id}::{document_id}::{unit_idx:04d}"
            yield EvidenceUnit(
                unit_id=unit_id,
                company_id=company_id,
                document_id=document_id,
                source_path=str(path),
                source_type=source_type,
                text=chunk,
                search_text=chunk,
                evidence_text=chunk,
                section=section,
                topic=section,
                year=year,
                esg_domain=esg_domain,
                metadata={
                    "source_path_rel": path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path),
                    "ingest_profile": profile,
                },
            )


def ingest_tree(root: Path, *, company_id: str) -> list[EvidenceUnit]:
    profile = _profile(company_id)
    supported = {ext.lower() for ext in profile["supported_extensions"]}
    units: list[EvidenceUnit] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in supported:
            units.extend(ingest_path(path, company_id=company_id, root=root))
    return units


def units_to_jsonl_rows(units: list[EvidenceUnit]) -> list[dict[str, Any]]:
    return [u.to_dict() for u in units]
