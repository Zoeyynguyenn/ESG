"""Tai lieu, chunking va retrieval lexical cho baseline V1."""

from __future__ import annotations

import html
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from config import (
    BASE_DIR,
    COMPANY_EXPORT_JSON_BUCKET,
    COMPANY_PUBLIC_BUCKET,
    DATA_BUCKETS,
    LEXICAL_CHUNK_OVERLAP,
    LEXICAL_CHUNK_SIZE,
    LEXICAL_INDEX_PATH,
    META_MD_FILES,
    PDF_PARSER,
    RTX_REFERENCES_BUCKET,
)


@dataclass
class ChunkRecord:
    source: str
    text: str
    chunk_id: int = 0


_TOKEN_RE = re.compile(r"[\uac00-\ud7a3]+|[a-zA-Z0-9_]+")


def tokenize(text: str) -> List[str]:
    """Lexical tokens: Hangul syllable runs + Latin/number (lowercased)."""
    out: List[str] = []
    for piece in _TOKEN_RE.findall(text or ""):
        if piece.isascii():
            out.append(piece.lower())
        else:
            out.append(piece)
    return out


def strip_html(raw: str) -> str:
    cleaned = re.sub(r"<script.*?>.*?</script>", " ", raw, flags=re.S | re.I)
    cleaned = re.sub(r"<style.*?>.*?</style>", " ", cleaned, flags=re.S | re.I)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = html.unescape(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def split_chunks(text: str, size: int = LEXICAL_CHUNK_SIZE, overlap: int = LEXICAL_CHUNK_OVERLAP) -> List[str]:
    chunks: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        chunk = text[i : i + size]
        if chunk.strip():
            chunks.append(chunk.strip())
        if i + size >= n:
            break
        i += max(1, size - overlap)
    return chunks


def _read_pdf(path: Path) -> Optional[str]:
    if PDF_PARSER in {"auto", "docling"}:
        text = _read_pdf_docling(path)
        if text:
            return text
        if PDF_PARSER == "docling":
            return None
    if PDF_PARSER not in {"auto", "pypdf"}:
        return None
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        reader = PdfReader(str(path))
        pages = [p.extract_text() or "" for p in reader.pages[:80]]
        text = "\n".join(pages).strip()
        return text if text else None
    except Exception:
        return None


def _read_pdf_docling(path: Path) -> Optional[str]:
    try:
        # Optional parser: docling-project/docling
        from docling.document_converter import DocumentConverter
    except Exception:
        return None
    try:
        converter = DocumentConverter()
        result = converter.convert(str(path))
        doc = getattr(result, "document", None)
        if doc is not None:
            if hasattr(doc, "export_to_markdown"):
                text = doc.export_to_markdown() or ""
            elif hasattr(doc, "export_to_text"):
                text = doc.export_to_text() or ""
            else:
                text = str(doc)
        else:
            text = str(result)
        text = re.sub(r"\s+\n", "\n", text).strip()
        return text if text else None
    except Exception:
        return None


def load_file_text(path: Path) -> Optional[str]:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix in {".html", ".htm"}:
        return strip_html(path.read_text(encoding="utf-8", errors="ignore"))
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            if isinstance(data, dict):
                return json.dumps(data, ensure_ascii=False)[:50000]
            if isinstance(data, list):
                return json.dumps(data[:50], ensure_ascii=False)[:50000]
        except Exception:
            return None
    if suffix == ".jsonl":
        blocks: List[str] = []
        try:
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                if not line.strip():
                    continue
                item = json.loads(line)
                if not isinstance(item, dict):
                    continue
                text = str(item.get("text") or "").strip()
                if not text:
                    continue
                header = [
                    f"record_id: {item.get('record_id', '')}",
                    f"doc_id: {item.get('doc_id', '')}",
                    f"company: {item.get('company', '')}",
                    f"year: {item.get('year', '')}",
                    f"source_type: {item.get('source_type', '')}",
                    f"title: {item.get('title', '')}",
                    f"section_path: {item.get('section_path', '')}",
                    f"page: {item.get('page', '')}",
                    f"record_role: {item.get('record_role', '')}",
                    f"source_system: {item.get('source_system', '')}",
                    f"source_url: {item.get('source_url', '')}",
                    f"esg_tags: {', '.join(item.get('esg_tags') or [])}",
                ]
                blocks.append("\n".join(header + ["", text]))
        except Exception:
            return None
        return "\n\n--- record ---\n\n".join(blocks)[:500000] if blocks else None
    return None


def rtx_chunked_corpus_path(base_dir: Path | None = None) -> Path:
    root = base_dir or BASE_DIR
    lane_id = os.getenv("RAG_COMPANY_FILTER", "06_rtx_references_raw").strip().strip("/")
    if not lane_id:
        lane_id = "06_rtx_references_raw"
    return root / "data" / "rag_dataset" / lane_id / "chunks" / "rtx_chunked_corpus.jsonl"


def _chunks_from_rtx_jsonl(f: Path, base_dir: Path) -> List[ChunkRecord]:
    """Pre-chunked RTX lane: one JSONL row = one retrieval chunk."""
    rel = str(f.relative_to(base_dir)).replace("\\", "/")
    out: List[ChunkRecord] = []
    try:
        lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return out
    for line_no, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        year_hint = meta.get("year_hint") or item.get("year") or ""
        header = "\n".join(
            [
                f"record_id: {item.get('chunk_id', '')}",
                f"chunk_id: {item.get('chunk_id', '')}",
                f"company: {item.get('company', '')}",
                f"year: {year_hint}",
                f"source_type: {item.get('source_type', '')}",
                f"document_title: {item.get('document_title', '')}",
                f"section_path: {item.get('section_hint', '')}",
                f"source_path: {item.get('source_path', '')}",
            ]
        )
        full = f"{header}\n\n{text}"
        out.append(ChunkRecord(source=rel, text=full, chunk_id=line_no))
    return out


def active_data_buckets() -> List[Path]:
    lane = os.getenv("RAG_BENCHMARK_LANE", "").strip()
    if lane == "company_public_dev":
        if COMPANY_PUBLIC_BUCKET.exists():
            return [COMPANY_PUBLIC_BUCKET]
        return []
    if lane.startswith("company_export_json"):
        if COMPANY_EXPORT_JSON_BUCKET.exists():
            return [COMPANY_EXPORT_JSON_BUCKET]
        return []
    if lane.startswith("rtx_references"):
        if RTX_REFERENCES_BUCKET.exists():
            return [RTX_REFERENCES_BUCKET]
        return []
    return [b for b in DATA_BUCKETS if b.exists()]


def iter_corpus_files() -> Iterable[Path]:
    allow_set: Optional[set[str]] = None
    manifest = os.getenv("RAG_BENCHMARK_CORPUS_MANIFEST", "").strip()
    if manifest:
        try:
            data = json.loads(Path(manifest).read_text(encoding="utf-8"))
            allow_set = set((x or "").replace("\\", "/") for x in data.get("files", []))
        except Exception:
            allow_set = None
    seen: set[str] = set()
    lane = os.getenv("RAG_BENCHMARK_LANE", "").strip()
    if lane != "company_public_dev":
        for meta in META_MD_FILES:
            if meta.is_file():
                key = str(meta.resolve())
                if key not in seen:
                    rel = str(meta.relative_to(BASE_DIR)).replace("\\", "/")
                    if allow_set is None or rel in allow_set:
                        seen.add(key)
                        yield meta
    for bucket in active_data_buckets():
        if not bucket.exists():
            continue
        for f in sorted(bucket.rglob("*")):
            if not f.is_file():
                continue
            if f.name.lower() == "readme.md":
                continue
            if f.suffix.lower() not in {".md", ".html", ".htm", ".pdf", ".txt", ".json", ".jsonl"}:
                continue
            if f.name == "manifest.csv":
                continue
            key = str(f.resolve())
            if key in seen:
                continue
            rel = str(f.relative_to(BASE_DIR)).replace("\\", "/")
            if allow_set is not None and rel not in allow_set:
                continue
            seen.add(key)
            yield f


def _chunks_from_export_jsonl(f: Path, base_dir: Path) -> List[ChunkRecord]:
    """One JSONL row = one evidence record; chunk inside the row (not across the whole file)."""
    rel = str(f.relative_to(base_dir)).replace("\\", "/")
    out: List[ChunkRecord] = []
    try:
        lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return out
    for line_no, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        header = "\n".join(
            [
                f"record_id: {item.get('record_id', '')}",
                f"doc_id: {item.get('doc_id', '')}",
                f"company: {item.get('company', '')}",
                f"year: {item.get('year', '')}",
                f"source_type: {item.get('source_type', '')}",
                f"title: {item.get('title', '')}",
                f"section_path: {item.get('section_path', '')}",
                f"record_role: {item.get('record_role', '')}",
            ]
        )
        full = f"{header}\n\n{text}"
        for i, c in enumerate(split_chunks(full)):
            out.append(ChunkRecord(source=rel, text=c, chunk_id=line_no * 1000 + i))
    return out


def build_chunks(base_dir: Path) -> List[ChunkRecord]:
    lane = os.getenv("RAG_BENCHMARK_LANE", "").strip()
    if lane.startswith("rtx_references"):
        rtx_path = rtx_chunked_corpus_path(base_dir)
        if rtx_path.is_file():
            return _chunks_from_rtx_jsonl(rtx_path, base_dir)
        return []

    records: List[ChunkRecord] = []
    for f in iter_corpus_files():
        rel = str(f.relative_to(base_dir)).replace("\\", "/")
        if "06_rtx_references_raw/" in rel and rel.endswith("rtx_chunked_corpus.jsonl"):
            records.extend(_chunks_from_rtx_jsonl(f, base_dir))
            continue
        if (
            f.suffix.lower() == ".jsonl"
            and "05_company_export_json/" in rel
            and "/splits/" in rel
        ):
            records.extend(_chunks_from_export_jsonl(f, base_dir))
            continue
        text = load_file_text(f)
        if not text or not text.strip():
            continue
        for i, c in enumerate(split_chunks(text)):
            records.append(ChunkRecord(source=rel, text=c, chunk_id=i))
    return records


def overlap_score(question: str, chunk_text: str) -> float:
    q = set(tokenize(question))
    c = set(tokenize(chunk_text))
    if not q or not c:
        return 0.0
    common = q.intersection(c)
    coverage = len(common) / max(1, len(q))
    density = len(common) / max(10, len(c) ** 0.5)
    return 0.75 * coverage + 0.25 * density


def save_lexical_index(chunks: List[ChunkRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "chunk_count": len(chunks),
        "chunks": [asdict(c) for c in chunks],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_lexical_index(path: Path) -> List[ChunkRecord]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [ChunkRecord(**item) for item in data.get("chunks", [])]
