"""Lightweight parsers for mixed-format enterprise documents (prototype)."""

from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from enterprise_docs.models import SourceType

PARSER_VERSION = "1.1.0"

try:
    from rag_common import strip_html
except ImportError:  # pragma: no cover
    def strip_html(raw: str) -> str:
        return re.sub(r"<[^>]+>", " ", raw or "")


class _HtmlTableExtractor(HTMLParser):
    """Extract headings and tables as structured text blocks."""

    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[str] = []
        self._current_heading = ""
        self._in_table = False
        self._in_row = False
        self._row_cells: list[str] = []
        self._cell_buf: list[str] = []
        self._text_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        if t in ("h1", "h2", "h3", "h4"):
            self._flush_text()
        elif t == "table":
            self._flush_text()
            self._in_table = True
        elif t == "tr" and self._in_table:
            self._in_row = True
            self._row_cells = []
        elif t in ("td", "th") and self._in_row:
            self._cell_buf = []

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in ("h1", "h2", "h3", "h4"):
            title = " ".join(self._text_buf).strip()
            if title:
                self._current_heading = title
                self.blocks.append(f"## {title}")
            self._text_buf = []
        elif t in ("td", "th") and self._in_row:
            self._row_cells.append(" ".join(self._cell_buf).strip())
            self._cell_buf = []
        elif t == "tr" and self._in_row:
            if self._row_cells:
                self.blocks.append(" | ".join(self._row_cells))
            self._in_row = False
        elif t == "table":
            self._in_table = False
        elif t in ("p", "div", "li", "br") and not self._in_table:
            self._text_buf.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_row:
            self._cell_buf.append(data.strip())
        else:
            self._text_buf.append(data.strip())

    def _flush_text(self) -> None:
        text = " ".join(x for x in self._text_buf if x).strip()
        if text and not self._in_table:
            prefix = f"[{self._current_heading}] " if self._current_heading else ""
            self.blocks.append(prefix + text)
        self._text_buf = []

    def get_text(self) -> str:
        self._flush_text()
        return "\n".join(b for b in self.blocks if b.strip())


def _read_html_structured(raw: str) -> str:
    parser = _HtmlTableExtractor()
    try:
        parser.feed(raw)
        structured = parser.get_text()
        if len(structured.strip()) >= 40:
            return structured
    except Exception:  # noqa: BLE001
        pass
    return strip_html(raw)


def _xml_local_tag(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _read_xml_structured(raw: str) -> str:
    lines: list[str] = []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return raw

    def walk(el: ET.Element, depth: int = 0) -> None:
        tag = _xml_local_tag(el.tag)
        text = (el.text or "").strip()
        attrs = " ".join(f"{k}={v}" for k, v in el.attrib.items() if v)
        if text and len(text) > 1:
            prefix = f"{tag}"
            if attrs:
                prefix += f" ({attrs})"
            lines.append(f"{prefix}: {text}")
        for child in list(el):
            walk(child, depth + 1)
            tail = (child.tail or "").strip()
            if tail and len(tail) > 2:
                lines.append(tail)

    walk(root)
    if lines:
        return "\n".join(lines[:500])
    return raw


def _read_pdf_structured(path: Path, max_pages: int = 80) -> str | None:
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        reader = PdfReader(str(path))
        blocks: list[str] = []
        for i, page in enumerate(reader.pages[:max_pages]):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            # Preserve table-like lines (multiple numeric columns)
            page_lines = []
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                if re.search(r"\d[\d,.\s]{3,}\d", line) and len(line.split()) >= 3:
                    page_lines.append(" | ".join(line.split()))
                else:
                    page_lines.append(line)
            blocks.append(f"## Page {i + 1}\n" + "\n".join(page_lines))
        out = "\n\n".join(blocks).strip()
        return out or None
    except Exception:
        return None


def detect_source_type(path: Path) -> SourceType:
    ext = path.suffix.lower()
    mapping: dict[str, SourceType] = {
        ".md": "markdown",
        ".markdown": "markdown",
        ".html": "html",
        ".htm": "html",
        ".json": "json",
        ".jsonl": "jsonl",
        ".xml": "xml",
        ".csv": "csv",
        ".pdf": "pdf",
        ".txt": "text",
    }
    return mapping.get(ext, "unknown")


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return _read_pdf_structured(path) or _read_pdf_text_legacy(path) or ""
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    if path.suffix.lower() in {".html", ".htm"}:
        return _read_html_structured(raw)
    if path.suffix.lower() == ".xml":
        return _read_xml_structured(raw)
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(raw)
            return json.dumps(payload, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            return raw
    if path.suffix.lower() == ".csv":
        return _csv_to_text(path)
    return raw


def _read_pdf_text_legacy(path: Path, max_pages: int = 80) -> str | None:
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        reader = PdfReader(str(path))
        pages = [p.extract_text() or "" for p in reader.pages[:max_pages]]
        text = "\n".join(pages).strip()
        return text or None
    except Exception:
        return None


def _csv_to_text(path: Path) -> str:
    lines: list[str] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            lines.append(" | ".join(row))
    return "\n".join(lines)


def split_markdown_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_title = "root"
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            if current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = line.lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))
    return sections or [("root", text)]


def split_structured_sections(text: str, source_type: SourceType) -> list[tuple[str, str]]:
    """Section split for markdown, html, xml structured text."""
    if source_type == "markdown":
        return split_markdown_sections(text)
    if source_type in ("html", "xml"):
        sections: list[tuple[str, str]] = []
        current = "root"
        buf: list[str] = []
        for line in text.splitlines():
            if line.startswith("## ") or (source_type == "xml" and line.endswith(":") and len(line) < 120):
                if buf:
                    sections.append((current, "\n".join(buf).strip()))
                current = line.lstrip("#").strip().rstrip(":")
                buf = []
            else:
                buf.append(line)
        if buf:
            sections.append((current, "\n".join(buf).strip()))
        return sections or [("root", text)]
    return [("root", text)]


def export_parser_capabilities() -> dict[str, Any]:
    return {
        "version": PARSER_VERSION,
        "html": {"table_preservation": "pipe_rows", "section_preservation": "heading_blocks"},
        "xml": {"structure": "element_text_walk", "dart_filing": "supported_generic"},
        "pdf": {"structure": "page_sections", "table_hint": "whitespace_pipe_join"},
    }


def infer_year(text: str, fallback: int | None = None) -> int | None:
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text or "") if 2015 <= int(y) <= 2035]
    if not years:
        return fallback
    return max(years)
