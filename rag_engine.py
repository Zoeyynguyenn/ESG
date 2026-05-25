# -*- coding: utf-8 -*-
"""
RAG Engine — Retrieval Augmented Generation
  - Ingest: PDF / TXT  →  chunk  →  embed  →  ChromaDB
  - Query : question   →  embed  →  top-k chunks  →  context string
"""
import os
import hashlib
import re
from pathlib import Path
from typing import Iterator

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

# ── Config ────────────────────────────────────────────────────────────────────
EMBED_MODEL  = "all-MiniLM-L6-v2"   # nhanh, 384-dim, tot cho semantic search
CHUNK_SIZE   = 400                   # so tu moi chunk
CHUNK_OVERLAP = 80                   # so tu overlap giua cac chunk
TOP_K        = 4                     # so chunk lay ve moi query
DB_DIR       = os.path.join(os.path.dirname(__file__), "vector_db")
COLLECTION   = "esg_docs"


class RagEngine:
    """
    Quan ly viec ingest tai lieu va tra ve context cho LLM.
    """

    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)

        # Embedding model (tai lan dau, sau cache local)
        self._embedder = SentenceTransformer(EMBED_MODEL)

        # ChromaDB persistent
        self._client = chromadb.PersistentClient(path=DB_DIR)
        self._col    = self._client.get_or_create_collection(
            name=COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def ingest(self, file_path: str) -> dict:
        """
        Doc file (PDF hoac TXT), chunk, embed, luu vao ChromaDB.
        Tra ve {"source", "chunks", "skipped"} (skipped = da ton tai).
        """
        path   = Path(file_path)
        source = path.name

        # Lay text
        if path.suffix.lower() == ".pdf":
            raw_text = self._read_pdf(path)
        elif path.suffix.lower() in (".txt", ".md"):
            raw_text = path.read_text(encoding="utf-8", errors="replace")
        else:
            raise ValueError(f"Dinh dang khong ho tro: {path.suffix}")

        chunks    = list(self._split(raw_text))

        # File rỗng hoặc không có nội dung
        if not chunks:
            return {"source": source, "chunks": 0, "added": 0, "skipped": 0}

        ids       = [self._chunk_id(source, i, c) for i, c in enumerate(chunks)]
        metadatas = [{"source": source, "chunk_index": i} for i in range(len(chunks))]

        # Kiem tra cac chunk da ton tai
        existing  = set(self._col.get(ids=ids)["ids"])
        new_mask  = [cid not in existing for cid in ids]
        new_chunks = [c for c, ok in zip(chunks, new_mask) if ok]
        new_ids    = [cid for cid, ok in zip(ids, new_mask) if ok]
        new_meta   = [m for m, ok in zip(metadatas, new_mask) if ok]

        if new_chunks:
            embeddings = self._embed(new_chunks)
            self._col.add(
                documents=new_chunks,
                embeddings=embeddings,
                ids=new_ids,
                metadatas=new_meta,
            )

        return {
            "source":  source,
            "chunks":  len(chunks),
            "added":   len(new_chunks),
            "skipped": len(chunks) - len(new_chunks),
        }

    def query(self, question: str, top_k: int = TOP_K) -> str:
        """
        Tim cac doan van ban lien quan den cau hoi.
        Tra ve context string de inject vao system prompt.
        """
        if self._col.count() == 0:
            return ""

        q_embed = self._embed([question])[0]
        results = self._col.query(
            query_embeddings=[q_embed],
            n_results=min(top_k, self._col.count()),
            include=["documents", "metadatas", "distances"],
        )

        docs      = results["documents"][0]
        metas     = results["metadatas"][0]
        distances = results["distances"][0]

        # Chi lay nhung chunk co do tuong dong cao (distance < 0.7 voi cosine)
        relevant = [
            (doc, meta, dist)
            for doc, meta, dist in zip(docs, metas, distances)
            if dist < 0.7
        ]

        if not relevant:
            return ""

        parts = []
        for doc, meta, dist in relevant:
            parts.append(
                f"[Nguon: {meta['source']} | chunk {meta['chunk_index']} "
                f"| do tuong dong: {1-dist:.2f}]\n{doc}"
            )

        return "\n\n---\n\n".join(parts)

    def list_sources(self) -> list[dict]:
        """Liet ke tat ca tai lieu da ingest."""
        if self._col.count() == 0:
            return []
        all_meta = self._col.get(include=["metadatas"])["metadatas"]
        seen, sources = set(), []
        for m in all_meta:
            src = m.get("source", "?")
            if src not in seen:
                seen.add(src)
                sources.append(src)
        # dem so chunk theo tung source
        summary = []
        for src in sources:
            count = sum(1 for m in all_meta if m.get("source") == src)
            summary.append({"source": src, "chunks": count})
        return summary

    def delete_source(self, source_name: str) -> int:
        """Xoa tat ca chunk cua mot tai lieu. Tra ve so chunk da xoa."""
        all_data = self._col.get(include=["metadatas"])
        ids_to_del = [
            cid for cid, meta in zip(all_data["ids"], all_data["metadatas"])
            if meta.get("source") == source_name
        ]
        if ids_to_del:
            self._col.delete(ids=ids_to_del)
        return len(ids_to_del)

    def count(self) -> int:
        return self._col.count()

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _read_pdf(path: Path) -> str:
        reader = PdfReader(str(path))
        pages  = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"[Trang {i+1}]\n{text}")
        return "\n\n".join(pages)

    @staticmethod
    def _split(text: str) -> Iterator[str]:
        """Chia text thanh cac chunk theo so tu, co overlap."""
        words  = text.split()
        start  = 0
        total  = len(words)
        while start < total:
            end   = min(start + CHUNK_SIZE, total)
            chunk = " ".join(words[start:end]).strip()
            if chunk:
                yield chunk
            if end >= total:
                break
            start = end - CHUNK_OVERLAP

    def _embed(self, texts: list[str]) -> list[list[float]]:
        return self._embedder.encode(texts, show_progress_bar=False).tolist()

    @staticmethod
    def _chunk_id(source: str, index: int, content: str) -> str:
        h = hashlib.md5(f"{source}_{index}_{content[:50]}".encode()).hexdigest()[:12]
        return f"{source}_{index}_{h}"
