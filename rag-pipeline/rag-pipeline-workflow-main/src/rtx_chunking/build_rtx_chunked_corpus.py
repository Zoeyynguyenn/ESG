"""Build chunked corpus + Golden Set corpus units for RTX reference lane."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from config import LEXICAL_CHUNK_OVERLAP, LEXICAL_CHUNK_SIZE
from golden_set.io_utils import write_jsonl
from rag_common import load_file_text, split_chunks, strip_html


def _load_pdf_text(path: Path, max_pages: int = 120) -> Optional[str]:
    """Fast PDF text extraction for RTX lane (pypdf only — avoid docling OCR)."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        reader = PdfReader(str(path))
        pages = [p.extract_text() or "" for p in reader.pages[:max_pages]]
        text = "\n".join(pages).strip()
        return text if text else None
    except Exception:
        return None

COMPANY = "RTX"
ORIGIN_LANE = "06_rtx_references_raw"
MIN_UNIT_CHARS = 80
MAX_UNIT_CHARS = 4000

PDF_KIND_MAP = {
    "eeo-1": "data_table",
    "performance data tables": "data_table",
    "esgappendix": "appendix",
    "cdp": "questionnaire",
}

HTML_KIND_MAP = {
    "rtx_proxy_2025": ("proxy_statement", "2025"),
    "rtx_10k_2025": ("10k", "2025"),
    "rtx_10k_2024": ("10k", "2024"),
    "rtx_data_security_privacy": ("policy_page", ""),
    "rtx_ethics_compliance": ("policy_page", ""),
}

YEAR_RE = re.compile(r"(20\d{2})")


def _token_estimate(text: str) -> int:
    return max(1, len(text) // 4)


def _slug(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()[:48]


def _record_id(source_slug: str, idx: int) -> str:
    return f"rtx_{source_slug}_{idx:04d}"


def _infer_pdf_kind(filename: str) -> str:
    low = filename.lower()
    for key, kind in PDF_KIND_MAP.items():
        if key in low:
            return kind
    return "pdf_document"


def _infer_html_meta(stem: str) -> Tuple[str, str]:
    if stem in HTML_KIND_MAP:
        return HTML_KIND_MAP[stem]
    year_m = YEAR_RE.search(stem)
    year = year_m.group(1) if year_m else ""
    if "proxy" in stem or "def14a" in stem:
        return "proxy_statement", year
    if "10k" in stem:
        return "10k", year
    if "ethics" in stem or "compliance" in stem:
        return "policy_page", year
    if "security" in stem or "privacy" in stem:
        return "policy_page", year
    return "web_page", year


def _load_url_map(source_urls_path: Path) -> Dict[str, str]:
    if not source_urls_path.exists():
        return {}
    data = json.loads(source_urls_path.read_text(encoding="utf-8"))
    out: Dict[str, str] = {}
    for ref in data.get("web_references", []):
        for key in ("local_html", "local_snapshot"):
            rel = ref.get(key) or ""
            if rel:
                out[Path(rel).name] = ref.get("url", "")
    return out


def _extract_html_sections(html: str) -> List[Tuple[str, str]]:
    """Split HTML into (section_hint, text) blocks using headings."""
    parts: List[Tuple[str, str]] = []
    pattern = re.compile(
        r"<(h[1-3])[^>]*>(.*?)</\1>",
        re.IGNORECASE | re.DOTALL,
    )
    matches = list(pattern.finditer(html))
    if not matches:
        text = strip_html(html)
        if text.strip():
            parts.append(("document_body", text))
        return parts

    for i, m in enumerate(matches):
        heading = strip_html(m.group(2))[:120] or f"section_{i+1}"
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        body = strip_html(html[start:end])
        if body.strip():
            parts.append((heading, body))
    return parts


def _load_md_fallback(path: Path) -> Tuple[str, str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    title_m = re.search(r"^#\s+(.+)$", raw, re.M)
    title = title_m.group(1).strip() if title_m else path.stem
    if "## Snapshot" in raw:
        body = raw.split("## Snapshot", 1)[1]
    else:
        body = raw
    body = re.sub(r"^#+\s+.*$", "", body, flags=re.M)
    body = re.sub(r"^-\s+", "", body, flags=re.M)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return title, body


def _company_signal(text: str) -> List[str]:
    signals = []
    for token in ("RTX Corporation", "RTX", "Raytheon", "Collins Aerospace", "Pratt & Whitney"):
        if token.lower() in text.lower():
            signals.append(token)
    return signals or ["RTX"]


def _iter_source_files(lane_root: Path) -> Iterator[Dict[str, Any]]:
    sources_dir = lane_root / "_sources"
    web_dir = lane_root / "web_sources"

    for pdf in sorted(sources_dir.glob("*.pdf")):
        yield {
            "path": pdf,
            "source_type": "pdf",
            "rel_path": str(pdf.relative_to(lane_root)).replace("\\", "/"),
            "file_name": pdf.name,
            "document_kind": _infer_pdf_kind(pdf.name),
            "year_hint": (m.group(1) if (m := YEAR_RE.search(pdf.name)) else ""),
            "url": "",
            "is_fallback_snapshot": False,
            "document_title": pdf.stem,
        }

    url_map = _load_url_map(lane_root / "source_urls.json")

    for html in sorted(web_dir.glob("*.html")):
        kind, year = _infer_html_meta(html.stem)
        yield {
            "path": html,
            "source_type": "html",
            "rel_path": str(html.relative_to(lane_root)).replace("\\", "/"),
            "file_name": html.name,
            "document_kind": kind,
            "year_hint": year or (m.group(1) if (m := YEAR_RE.search(html.stem)) else ""),
            "url": url_map.get(html.name, ""),
            "is_fallback_snapshot": False,
            "document_title": html.stem.replace("_", " ").title(),
        }

    for md in sorted(web_dir.glob("*.md")):
        yield {
            "path": md,
            "source_type": "md_fallback",
            "rel_path": str(md.relative_to(lane_root)).replace("\\", "/"),
            "file_name": md.name,
            "document_kind": "press_release",
            "year_hint": "2024",
            "url": url_map.get(md.name, ""),
            "is_fallback_snapshot": True,
            "document_title": "DOJ Raytheon RTX Resolution Press Release",
        }


def _text_blocks(meta: Dict[str, Any]) -> List[Tuple[str, str]]:
    path: Path = meta["path"]
    st = meta["source_type"]

    if st == "md_fallback":
        title, body = _load_md_fallback(path)
        meta["document_title"] = title
        return [("press_release_body", body)] if body.strip() else []

    if st == "html" and meta["document_kind"] in ("10k", "proxy_statement"):
        raw = path.read_text(encoding="utf-8", errors="replace")
        sections = _extract_html_sections(raw)
        if sections:
            return sections
        text = load_file_text(path)
        return [("document_body", text or "")] if text else []

    if st == "pdf":
        text = _load_pdf_text(path)
    else:
        text = load_file_text(path)
    if not text or not text.strip():
        return []
    return [("document_body", text)]


def build_corpus(
    *,
    lane_root: Path,
    chunks_path: Path,
    units_path: Path,
    report_path: Path,
    summary_path: Path,
) -> Dict[str, Any]:
    parse_warnings: List[str] = []
    all_chunks: List[Dict[str, Any]] = []
    all_units: List[Dict[str, Any]] = []
    file_stats = {"pdf": 0, "html": 0, "md_fallback": 0}

    for meta in _iter_source_files(lane_root):
        file_stats[meta["source_type"]] = file_stats.get(meta["source_type"], 0) + 1
        source_slug = _slug(meta["path"].stem)
        blocks = _text_blocks(meta)

        if not blocks:
            parse_warnings.append(f"empty_or_unreadable:{meta['rel_path']}")
            continue

        chunk_idx = 0
        for section_hint, block_text in blocks:
            if not block_text.strip():
                continue
            for piece in split_chunks(
                block_text,
                size=LEXICAL_CHUNK_SIZE,
                overlap=LEXICAL_CHUNK_OVERLAP,
            ):
                if len(piece.strip()) < 40:
                    continue
                chunk_idx += 1
                rid = _record_id(source_slug, chunk_idx)
                signals = _company_signal(piece)
                metadata = {
                    "origin_lane": ORIGIN_LANE,
                    "file_name": meta["file_name"],
                    "url": meta["url"],
                    "document_kind": meta["document_kind"],
                    "year_hint": meta["year_hint"],
                    "company_signal": signals,
                    "is_fallback_snapshot": meta["is_fallback_snapshot"],
                }
                chunk_row = {
                    "chunk_id": f"rtx-{source_slug}-{chunk_idx:04d}",
                    "company": COMPANY,
                    "source_path": meta["rel_path"],
                    "source_type": meta["source_type"],
                    "document_title": meta["document_title"],
                    "section_hint": section_hint[:120],
                    "text": piece,
                    "char_count": len(piece),
                    "token_estimate": _token_estimate(piece),
                    "metadata": metadata,
                }
                all_chunks.append(chunk_row)

                if len(piece) >= MIN_UNIT_CHARS:
                    unit_text = piece[:MAX_UNIT_CHARS]
                    all_units.append(
                        {
                            "unit_id": f"{ORIGIN_LANE}::{rid}",
                            "company": COMPANY,
                            "record_id": rid,
                            "source_file": meta["rel_path"],
                            "source_type": meta["source_type"],
                            "section_path": section_hint[:120],
                            "text": unit_text,
                            "document_kind": meta["document_kind"],
                            "year_hint": meta["year_hint"],
                            "package_name": ORIGIN_LANE,
                            "origin_lane": ORIGIN_LANE,
                            "url": meta["url"],
                            "is_fallback_snapshot": meta["is_fallback_snapshot"],
                            "chunking_note": f"rtx_lane_{LEXICAL_CHUNK_SIZE}_{LEXICAL_CHUNK_OVERLAP}",
                        }
                    )

        if chunk_idx == 0:
            parse_warnings.append(f"no_chunks_produced:{meta['rel_path']}")

    chunks_path.parent.mkdir(parents=True, exist_ok=True)
    units_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(chunks_path, all_chunks)
    write_jsonl(units_path, all_units)

    by_source = Counter(c["source_type"] for c in all_chunks)
    by_kind = Counter(c["metadata"]["document_kind"] for c in all_chunks)
    input_count = sum(file_stats.values())

    ready_rag = len(all_chunks) >= 20 and input_count >= 8
    ready_gs = len(all_units) >= 15 and any(
        c["metadata"]["document_kind"] in ("10k", "proxy_statement", "appendix", "policy_page")
        for c in all_chunks
    )

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "origin_lane": ORIGIN_LANE,
        "input_file_count": input_count,
        "pdf_count": file_stats.get("pdf", 0),
        "html_count": file_stats.get("html", 0),
        "fallback_md_count": file_stats.get("md_fallback", 0),
        "chunk_count": len(all_chunks),
        "corpus_unit_count": len(all_units),
        "by_source_type": dict(by_source),
        "by_document_kind": dict(by_kind),
        "parse_warnings": parse_warnings,
        "ready_for_rag": ready_rag,
        "ready_for_golden_set": ready_gs,
        "doj_source": "md_fallback",
        "chunk_size": LEXICAL_CHUNK_SIZE,
        "chunk_overlap": LEXICAL_CHUNK_OVERLAP,
        "output_chunks": str(chunks_path),
        "output_units": str(units_path),
    }

    _write_report(summary, report_path)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _write_report(summary: Dict[str, Any], path: Path) -> None:
    lines = [
        "# RTX Reference Lane — Chunking Report",
        "",
        f"Generated: {summary.get('generated_at', '')}",
        "",
        "## Mục tiêu",
        "",
        "Chunk lane `06_rtx_references_raw` thành corpus riêng cho RAG và Golden Set workbook-first.",
        "",
        "## Input đã chunk",
        "",
        f"- PDF: **{summary.get('pdf_count', 0)}** (`_sources/`)",
        f"- HTML: **{summary.get('html_count', 0)}** (`web_sources/`)",
        f"- Fallback MD: **{summary.get('fallback_md_count', 0)}** (DOJ snapshot)",
        "",
        "## Chiến lược chunking",
        "",
        f"- Text extraction: `rag_common.load_file_text` (PDF/HTML); MD snapshot parser riêng.",
        f"- SEC HTML (`10k`, `proxy_statement`): tách theo `<h1-h3>` rồi sliding window.",
        f"- Chunk size/overlap: **{summary.get('chunk_size')}** / **{summary.get('chunk_overlap')}** (cùng lexical default).",
        "- Output tách lane — không trộn `05_company_export_json`.",
        "",
        "## Kết quả",
        "",
        f"- **Tổng chunks:** {summary.get('chunk_count', 0)}",
        f"- **Tổng corpus units:** {summary.get('corpus_unit_count', 0)}",
        "",
        "### Breakdown theo source_type",
        "",
    ]
    for k, v in summary.get("by_source_type", {}).items():
        lines.append(f"- `{k}`: {v}")

    lines.extend(["", "### Breakdown theo document_kind", ""])
    for k, v in summary.get("by_document_kind", {}).items():
        lines.append(f"- `{k}`: {v}")

    lines.extend(
        [
            "",
            "## Lưu ý",
            "",
            f"- **DOJ:** dùng **fallback snapshot `.md`** (`{summary.get('doj_source', '')}`) — không có raw HTML.",
        ]
    )
    warnings = summary.get("parse_warnings") or []
    if warnings:
        lines.append("- **Parse warnings:**")
        for w in warnings:
            lines.append(f"  - `{w}`")
    else:
        lines.append("- Không có file rỗng hoặc unreadable.")

    lines.extend(
        [
            "",
            "## Kết luận",
            "",
            f"- Sẵn sàng cho RAG: **{'Có' if summary.get('ready_for_rag') else 'Chưa'}**",
            f"- Sẵn sàng cho Golden Set workbook-first: **{'Có' if summary.get('ready_for_golden_set') else 'Chưa'}**",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Build RTX chunked corpus")
    parser.add_argument(
        "--lane-root",
        default="data/rag_dataset/06_rtx_references_raw",
    )
    parser.add_argument(
        "--chunks-out",
        default="data/rag_dataset/06_rtx_references_raw/chunks/rtx_chunked_corpus.jsonl",
    )
    parser.add_argument(
        "--units-out",
        default="data/golden_set/v2/rtx_step1_corpus_units/corpus_units_rtx.jsonl",
    )
    parser.add_argument(
        "--report",
        default="reports/rtx_chunking_report.md",
    )
    parser.add_argument(
        "--summary-json",
        default="reports/_rtx_chunking_summary.json",
    )
    args = parser.parse_args(argv)

    summary = build_corpus(
        lane_root=root / args.lane_root,
        chunks_path=root / args.chunks_out,
        units_path=root / args.units_out,
        report_path=root / args.report,
        summary_path=root / args.summary_json,
    )
    print(
        json.dumps(
            {
                k: summary[k]
                for k in (
                    "input_file_count",
                    "chunk_count",
                    "corpus_unit_count",
                    "ready_for_rag",
                    "ready_for_golden_set",
                )
            },
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
