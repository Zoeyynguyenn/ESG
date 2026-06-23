"""Ingest ESG dataset: LangChain+Chroma (uu tien), fallback lexical."""

from __future__ import annotations

import json
from datetime import datetime

from config import BASE_DIR, DATA_DIR, LEXICAL_INDEX_PATH
from rag_common import build_chunks, save_lexical_index
from rag_stack import detect_environment, ingest_corpus_files, write_ingest_report


def ingest_lexical_fallback():
    chunks = build_chunks(BASE_DIR)
    save_lexical_index(chunks, LEXICAL_INDEX_PATH)
    return {"mode": "lexical_fallback", "chunk_count": len(chunks)}


def main():
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Khong tim thay dataset: {DATA_DIR}")

    env = detect_environment()
    print(json.dumps({"environment": env}, ensure_ascii=False, indent=2))

    try:
        rows, total_chunks = ingest_corpus_files()
        report = write_ingest_report(
            rows,
            total_chunks,
            mode="langchain_chroma",
            notes=f"Python {env.get('python')}; chromadb={env.get('chromadb_version', 'n/a')}",
        )
        print("=== Ingest: LangChain + Chroma (full corpus) ===")
        print(f"total_chunks: {total_chunks}")
        print(f"files: {len(rows)}")
        print(f"report: {report}")
        pdf = [r for r in rows if "ESG-X02" in r.file]
        if pdf:
            print(f"ESG-X02: status={pdf[0].status}, chunks={pdf[0].chunks}")
        return
    except Exception as exc:
        print(f"Chroma ingest failed: {exc}")
        fb = ingest_lexical_fallback()
        from rag_common import iter_corpus_files, load_file_text
        from rag_stack import FileIngestRow

        rows_fb = []
        for f in iter_corpus_files():
            rel = str(f.relative_to(BASE_DIR)).replace("\\", "/")
            text = load_file_text(f)
            rows_fb.append(
                FileIngestRow(
                    rel,
                    f.suffix.lstrip(".") or "unknown",
                    "loaded" if text else "skipped",
                    0,
                    str(exc)[:80],
                )
            )
        report = write_ingest_report(
            rows_fb,
            fb["chunk_count"],
            mode="lexical_fallback",
            notes=str(exc),
        )
        print("=== Ingest: Lexical fallback ===")
        print(json.dumps(fb, indent=2))
        print(f"report: {report}")


if __name__ == "__main__":
    main()
