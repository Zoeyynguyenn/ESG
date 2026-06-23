"""Stack V1: LangChain + Chroma + embedding + LLM (Ollama/OpenAI/extractive)."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import (
    BASE_DIR,
    CHROMA_DIR,
    CHUNKING_PROFILE,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    LLM_MODE,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    QDRANT_COLLECTION,
    QDRANT_PATH,
    TOP_K,
    VECTOR_STORE,
)
from evidence_rag import INSUFFICIENT_ANSWER, build_answer, is_insufficient_question
from rag_common import iter_corpus_files, load_file_text, tokenize

INSUFFICIENT_MSG = INSUFFICIENT_ANSWER
CHROMA_COLLECTION = os.getenv("RAG_CHROMA_COLLECTION", "langchain")


@dataclass
class FileIngestRow:
    file: str
    file_type: str
    status: str
    chunks: int
    notes: str


def _derive_metadata(rel: str, ftype: str) -> Dict[str, str]:
    s = rel.replace("\\", "/")
    parts = s.split("/")
    file_name = Path(s).name.lower()
    company = "unknown"
    doc_group = "general"
    source_tier = "other"
    if "/01_synthetic_controlled/" in s:
        source_tier = "synthetic"
        company = "greenriver"
    elif "/02_esg_public_core/" in s:
        source_tier = "public_core"
    elif "/03_esg_public_complex/" in s:
        source_tier = "public_complex"
    elif "/04_company_public_curated/" in s:
        source_tier = "company_public"
        try:
            idx = parts.index("04_company_public_curated")
            if idx + 1 < len(parts):
                company = parts[idx + 1].lower()
        except ValueError:
            pass

    if any(k in file_name for k in ("governance", "ethics", "board", "compliance")):
        doc_group = "governance"
    elif any(k in file_name for k in ("social", "labor", "dei", "community", "human")):
        doc_group = "social"
    elif any(k in file_name for k in ("environment", "climate", "emission", "energy", "water", "waste")):
        doc_group = "environment"
    elif any(k in file_name for k in ("annual", "sustainability", "esg", "impact", "report")):
        doc_group = "report"

    return {
        "source": s,
        "file_type": ftype,
        "company": company,
        "doc_group": doc_group,
        "source_tier": source_tier,
    }


def detect_environment() -> Dict[str, Any]:
    import sys

    info: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "chromadb": False,
        "langchain": False,
        "ollama": False,
        "openai_api_key_set": bool(OPENAI_API_KEY),
    }
    try:
        import chromadb  # noqa: F401

        info["chromadb"] = True
        info["chromadb_version"] = chromadb.__version__
    except Exception as exc:
        info["chromadb_error"] = str(exc)
    try:
        import langchain  # noqa: F401

        info["langchain"] = True
    except Exception as exc:
        info["langchain_error"] = str(exc)
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=8)
        info["ollama"] = r.returncode == 0
        info["ollama_hint"] = (r.stdout or r.stderr)[:200]
    except Exception as exc:
        info["ollama_error"] = str(exc)
    return info


def resolve_llm_mode() -> str:
    if LLM_MODE and LLM_MODE != "auto":
        return LLM_MODE
    env = detect_environment()
    if env.get("ollama"):
        return "ollama"
    if OPENAI_API_KEY:
        return "openai_api"
    return "extractive"


def _embeddings():
    from langchain_community.embeddings import HuggingFaceEmbeddings

    # IMPORTANT: dung env runtime de tranh mismatch (ghi mot dang, chay mot neo)
    effective = os.getenv("RAG_EMBEDDING_MODEL", "").strip() or EMBEDDING_MODEL
    os.environ["RAG_EFFECTIVE_EMBEDDING_MODEL"] = effective
    if (
        effective.startswith("openai:")
        or effective.startswith("openrouter:")
        or effective.startswith("text-embedding-")
    ):
        from embedding_providers import create_embeddings

        return create_embeddings(effective)
    batch_size = int(os.getenv("RAG_EMBED_BATCH_SIZE", "32"))
    local_only = os.getenv("RAG_EMBED_LOCAL_ONLY", "false").lower() in ("1", "true", "yes")
    model_kwargs: Dict[str, Any] = {}
    if "bge-m3" in effective.lower():
        model_kwargs["trust_remote_code"] = True
    if local_only:
        model_kwargs["local_files_only"] = True
    return HuggingFaceEmbeddings(
        model_name=effective,
        model_kwargs=model_kwargs,
        encode_kwargs={"batch_size": batch_size, "normalize_embeddings": True},
    )


def _split_by_section_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    import re

    blocks = re.split(r"\n(?=#{1,3}\s)", text)
    chunks: List[str] = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if len(block) <= chunk_size:
            chunks.append(block)
            continue
        i = 0
        n = len(block)
        while i < n:
            part = block[i : i + chunk_size].strip()
            if part:
                chunks.append(part)
            if i + chunk_size >= n:
                break
            i += max(1, chunk_size - chunk_overlap)
    return chunks


def _chroma_store():
    from langchain_community.vectorstores import Chroma

    if VECTOR_STORE == "qdrant":
        from langchain_community.vectorstores import Qdrant
        from qdrant_client import QdrantClient

        client = QdrantClient(path=str(QDRANT_PATH))
        return Qdrant(client=client, collection_name=QDRANT_COLLECTION, embeddings=_embeddings())
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=_embeddings(),
        collection_name=CHROMA_COLLECTION,
    )


def ingest_corpus_files() -> tuple[List[FileIngestRow], int]:
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    rows: List[FileIngestRow] = []
    lane = os.getenv("RAG_BENCHMARK_LANE", "").strip()

    # company_export_json: per-record chunking via build_chunks (same as retrieval_v3).
    # Avoid load_file_text jsonl [:500000] truncation that drops tail records (e.g. GT anchors).
    if lane.startswith("company_export_json") or lane.startswith("rtx_references"):
        from rag_common import build_chunks

        chunk_records = build_chunks(BASE_DIR)
        chunks: List[Document] = [
            Document(page_content=rec.text, metadata={"source": rec.source}) for rec in chunk_records
        ]
        per_source: Dict[str, int] = {}
        for rec in chunk_records:
            per_source[rec.source] = per_source.get(rec.source, 0) + 1
        for src, n in sorted(per_source.items()):
            rows.append(FileIngestRow(src, "jsonl", "loaded", n, "ok"))
    else:
        documents: List[Document] = []
        for path in iter_corpus_files():
            rel = str(path.relative_to(BASE_DIR)).replace("\\", "/")
            ftype = path.suffix.lower().lstrip(".") or "unknown"
            try:
                text = load_file_text(path)
                if not text or not text.strip():
                    rows.append(FileIngestRow(rel, ftype, "skipped", 0, "empty_or_unreadable"))
                    continue
                documents.append(Document(page_content=text, metadata=_derive_metadata(rel, ftype)))
                rows.append(FileIngestRow(rel, ftype, "loaded", 0, "ok"))
            except Exception as exc:
                rows.append(FileIngestRow(rel, ftype, "error", 0, str(exc)[:120]))

        if not documents:
            raise ValueError("Khong co tai lieu de ingest")

        profile = (CHUNKING_PROFILE or "").strip().lower()
        if profile == "section_based":
            chunks = []
            for d in documents:
                for part in _split_by_section_text(d.page_content, CHUNK_SIZE, CHUNK_OVERLAP):
                    chunks.append(Document(page_content=part, metadata=d.metadata))
        else:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
            )
            chunks = splitter.split_documents(documents)
        per_source = {}
        for c in chunks:
            src = c.metadata.get("source", "unknown")
            per_source[src] = per_source.get(src, 0) + 1

        for r in rows:
            if r.status == "loaded":
                r.chunks = per_source.get(r.file, 0)

    if not chunks:
        raise ValueError("Khong co tai lieu de ingest")

    from rag_common import ChunkRecord, save_lexical_index

    bm25_path = Path(os.getenv("RAG_BM25_INDEX_PATH", ""))
    if str(bm25_path).strip():
        bm25_path.parent.mkdir(parents=True, exist_ok=True)
        bm25_records: List[ChunkRecord] = []
        per_src_id: Dict[str, int] = {}
        for c in chunks:
            src = c.metadata.get("source", "unknown")
            cid = per_src_id.get(src, 0)
            per_src_id[src] = cid + 1
            bm25_records.append(ChunkRecord(source=src, text=c.page_content, chunk_id=cid))
        save_lexical_index(bm25_records, bm25_path)

    store_dir = QDRANT_PATH if VECTOR_STORE == "qdrant" else CHROMA_DIR
    complete_marker = store_dir.parent / ".index_complete"
    force_rebuild = os.getenv("RAG_FORCE_REBUILD", "").lower() in ("1", "true", "yes")
    if store_dir.exists() and (force_rebuild or not complete_marker.exists()):
        import shutil

        shutil.rmtree(store_dir, ignore_errors=True)
        complete_marker.unlink(missing_ok=True)
    store_dir.mkdir(parents=True, exist_ok=True)
    emb = _embeddings()
    effective = os.getenv("RAG_EFFECTIVE_EMBEDDING_MODEL", EMBEDDING_MODEL)
    is_openai = effective.startswith("openai:") or "text-embedding" in effective.lower()
    doc_batch = int(os.getenv("RAG_OPENAI_EMBED_BATCH", "32")) if is_openai else len(chunks)

    def _ingest_batches(add_fn, create_fn):
        vs = None
        for i in range(0, len(chunks), doc_batch):
            batch = chunks[i : i + doc_batch]
            if vs is None:
                vs = create_fn(batch)
            else:
                add_fn(vs, batch)
        return vs

    if VECTOR_STORE == "qdrant":
        from langchain_community.vectorstores import Qdrant

        if doc_batch >= len(chunks):
            Qdrant.from_documents(
                documents=chunks,
                embedding=emb,
                path=str(QDRANT_PATH),
                collection_name=QDRANT_COLLECTION,
            )
        else:
            _ingest_batches(
                lambda vs, b: vs.add_documents(b),
                lambda b: Qdrant.from_documents(
                    documents=b,
                    embedding=emb,
                    path=str(QDRANT_PATH),
                    collection_name=QDRANT_COLLECTION,
                ),
            )
    else:
        from langchain_community.vectorstores import Chroma

        def _chroma_create(batch):
            return Chroma.from_documents(
                documents=batch,
                embedding=emb,
                persist_directory=str(CHROMA_DIR),
                collection_name=CHROMA_COLLECTION,
            )

        try:
            if doc_batch >= len(chunks):
                _chroma_create(chunks)
            else:
                _ingest_batches(lambda vs, b: vs.add_documents(b), _chroma_create)
        except Exception as exc:
            msg = str(exc).lower()
            if "expecting embedding with dimension" in msg or "embedding dimension" in msg:
                # Recover from stale collection created by a different embedding dimension.
                import shutil

                shutil.rmtree(CHROMA_DIR, ignore_errors=True)
                CHROMA_DIR.mkdir(parents=True, exist_ok=True)
                Chroma.from_documents(
                    documents=chunks,
                    embedding=emb,
                    persist_directory=str(CHROMA_DIR),
                    collection_name=CHROMA_COLLECTION,
                )
            else:
                raise
    complete_marker.write_text(
        f"chunks={len(chunks)}\nmodel={os.getenv('RAG_EFFECTIVE_EMBEDDING_MODEL', '')}\nvector_store={VECTOR_STORE}\n",
        encoding="utf-8",
    )
    return rows, len(chunks)


def write_ingest_report(rows: List[FileIngestRow], total_chunks: int, mode: str, notes: str = "") -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = BASE_DIR / "reports" / f"v1-ingest-report-{ts}.md"
    lines = [
        "# V1 Ingest Report",
        "",
        f"Ngay: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Config",
        "",
        f"- ingest_mode: `{mode}`",
        f"- embedding_model: `{EMBEDDING_MODEL}`",
        f"- chunking_profile: `{CHUNKING_PROFILE}`",
        f"- chunk_size: {CHUNK_SIZE}",
        f"- chunk_overlap: {CHUNK_OVERLAP}",
        f"- total_chunks: {total_chunks}",
        "",
    ]
    if notes:
        lines.extend([f"Notes: {notes}", ""])
    lines.extend(
        [
            "## File ingest",
            "",
            "| File | Type | Status | Chunks | Notes |",
            "|---|---|---|---:|---|",
        ]
    )
    for r in rows:
        lines.append(f"| `{r.file}` | {r.file_type} | {r.status} | {r.chunks} | {r.notes} |")
    pdf_rows = [r for r in rows if "ESG-X02" in r.file and r.file.endswith(".pdf")]
    if pdf_rows:
        lines.extend(["", f"ESG-X02 PDF: **{pdf_rows[0].status}**, chunks={pdf_rows[0].chunks}"])
    else:
        lines.extend(["", "ESG-X02 PDF: **missing** trong corpus scan"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _generate_llm(context: str, question: str, llm_mode: Optional[str] = None) -> tuple[str, str]:
    mode = llm_mode or resolve_llm_mode()
    if mode == "ollama":
        from langchain_ollama import ChatOllama

        llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)
        prompt = _prompt(context, question)
        out = llm.invoke(prompt)
        text = out.content if hasattr(out, "content") else str(out)
        return text, "langchain_chroma_ollama"
    if mode == "openai_api":
        from langchain_openai import ChatOpenAI

        kwargs = {"model": OPENAI_MODEL, "temperature": 0, "api_key": OPENAI_API_KEY}
        if OPENAI_BASE_URL:
            kwargs["base_url"] = OPENAI_BASE_URL
        llm = ChatOpenAI(**kwargs)
        out = llm.invoke(_prompt(context, question))
        text = out.content if hasattr(out, "content") else str(out)
        return text, "langchain_chroma_openai"
    return "", "extractive"


def _prompt(context: str, question: str) -> str:
    return f"""Ban la tro ly RAG evidence-based.
Chi dung context duoi day. Neu khong du, tra loi chinh xac: "{INSUFFICIENT_MSG}"

Context:
{context}

Cau hoi: {question}

Tra loi ngan gon, tieng Viet."""


def _confidence_from_scores(scores: List[Optional[float]]) -> str:
    vals = [s for s in scores if s is not None]
    if not vals:
        return "medium"
    best = max(vals)
    if best >= 0.55:
        return "high"
    if best >= 0.35:
        return "medium"
    return "low"


def query_chroma(
    question: str,
    top_k: int = TOP_K,
    llm_mode_override: Optional[str] = None,
) -> Dict[str, Any]:
    if VECTOR_STORE == "qdrant":
        if not QDRANT_PATH.exists():
            raise FileNotFoundError(f"Qdrant DB chua ingest: {QDRANT_PATH}")
    else:
        if not CHROMA_DIR.exists():
            raise FileNotFoundError(f"Chroma DB chua ingest: {CHROMA_DIR}")

    if is_insufficient_question(question):
        return {
            "question": question,
            "answer": INSUFFICIENT_MSG,
            "confidence": "low",
            "insufficient": True,
            "evidence": [],
            "mode": "langchain_chroma",
            "retrieval_mode": "semantic",
            "llm_mode": llm_mode_override or resolve_llm_mode(),
        }

    store = _chroma_store()
    results = store.similarity_search_with_score(question, k=top_k)
    top_chunks = []
    evidence = []
    for doc, dist in results:
        sim = round(max(0.0, 1.0 - float(dist)), 4) if dist is not None else None
        src = doc.metadata.get("source", "unknown")
        top_chunks.append({"source": src, "citation": src, "score": sim, "text": doc.page_content})
        evidence.append({"source": src, "citation": src, "score": sim, "text": doc.page_content[:500]})

    context = "\n\n".join(
        f"[{i}] source={c['source']}\n{c['text'][:1200]}" for i, c in enumerate(top_chunks, 1)
    )
    llm_mode = llm_mode_override or resolve_llm_mode()
    answer = ""
    mode = "langchain_chroma"
    if llm_mode == "extractive":
        answer = build_answer(question, top_chunks)
        mode = "langchain_chroma_extractive"
    elif llm_mode in ("ollama", "openai_api"):
        try:
            answer, mode = _generate_llm(context, question, llm_mode=llm_mode)
        except Exception:
            llm_mode = "extractive"
            answer = build_answer(question, top_chunks)
            mode = "langchain_chroma_extractive"
    else:
        answer = build_answer(question, top_chunks)
        mode = "langchain_chroma_extractive"
        llm_mode = "extractive"

    if not answer and llm_mode != "extractive":
        answer = build_answer(question, top_chunks)
        mode = "langchain_chroma_extractive"
        llm_mode = "extractive"

    insufficient = INSUFFICIENT_MSG.lower() in (answer or "").lower()
    if not evidence and not insufficient:
        insufficient = True
        answer = INSUFFICIENT_MSG

    return {
        "question": question,
        "answer": answer,
        "confidence": _confidence_from_scores([e.get("score") for e in evidence]),
        "insufficient": insufficient,
        "evidence": evidence,
        "mode": mode,
        "retrieval_mode": "semantic",
        "llm_mode": llm_mode,
    }


def stack_available() -> bool:
    env = detect_environment()
    if VECTOR_STORE == "qdrant":
        return bool(env.get("langchain") and QDRANT_PATH.exists())
    return bool(env.get("chromadb") and env.get("langchain") and CHROMA_DIR.exists())
