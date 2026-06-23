import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "rag_dataset"
SAMPLE_DOCS_DIR = BASE_DIR / "data" / "sample_docs"

DATA_BUCKETS = [
    DATA_DIR / "01_synthetic_controlled",
    DATA_DIR / "02_esg_public_core",
    DATA_DIR / "03_esg_public_complex",
]
COMPANY_PUBLIC_BUCKET = DATA_DIR / "04_company_public_curated"
COMPANY_EXPORT_JSON_BUCKET = DATA_DIR / "05_company_export_json"
RTX_REFERENCES_BUCKET = DATA_DIR / "06_rtx_references_raw"
META_MD_FILES = [
    DATA_DIR / "sources.md",
    DATA_DIR / "dataset_readme.md",
    DATA_DIR / "esg_eval_guidelines.md",
]

CHROMA_DIR = Path(os.getenv("RAG_CHROMA_DIR", str(BASE_DIR / "artifacts" / "chroma_db")))
LEXICAL_INDEX_PATH = Path(
    os.getenv("RAG_LEXICAL_INDEX_PATH", str(BASE_DIR / "artifacts" / "lexical_index.json"))
)
EVAL_SET_PATH = BASE_DIR / ".rag" / "rag-pipeline-practice" / "eval_set.md"

EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
TOP_K = int(os.getenv("RAG_TOP_K", "4"))

CHUNKING_PROFILE = os.getenv("RAG_CHUNKING_PROFILE", "recursive_800_120")
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "120"))

# LLM: ollama | openai_api | extractive (sau retrieval Chroma, khong can LLM)
LLM_MODE = os.getenv("RAG_LLM_MODE", "auto")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = (os.getenv("OPENAI_BASE_URL") or "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
BENCHMARK_LANGUAGE = os.getenv("RAG_BENCHMARK_LANGUAGE", "ko").strip().lower()

# Lexical fallback
LEXICAL_CHUNK_SIZE = 900
LEXICAL_CHUNK_OVERLAP = 150
INSUFFICIENT_SCORE_THRESHOLD = 0.23
SOURCE_LINE_SCORE_THRESHOLD = 0.18

# Version 3 — retrieval
RETRIEVAL_MODE = os.getenv(
    "RAG_RETRIEVAL_MODE", "hybrid_dense_bm25"
)  # semantic_dense | bm25_lexical | hybrid_dense_bm25 | hybrid_dense_bm25_rerank
HYBRID_ALPHA = float(os.getenv("RAG_HYBRID_ALPHA", "0.55"))  # trong so dense (0-1)
CANDIDATE_POOL_SIZE = int(os.getenv("RAG_CANDIDATE_POOL_SIZE", "24"))
FINAL_TOP_K = int(os.getenv("RAG_FINAL_TOP_K", str(TOP_K)))
RERANK_ENABLED = os.getenv("RAG_RERANK_ENABLED", "false").lower() in ("1", "true", "yes")
RERANK_BACKEND = os.getenv("RAG_RERANK_BACKEND", "auto").strip().lower()
RERANK_MODEL = os.getenv("RAG_RERANK_MODEL", "ms-marco-MultiBERT-L-12")
BM25_INDEX_PATH = Path(os.getenv("RAG_BM25_INDEX_PATH", str(BASE_DIR / "artifacts" / "bm25_corpus.json")))

# Parsing & retrieval controls (benchmark/hardening)
PDF_PARSER = os.getenv("RAG_PDF_PARSER", "auto").strip().lower()  # auto | pypdf | docling
METADATA_AWARE_RETRIEVAL = os.getenv("RAG_METADATA_AWARE_RETRIEVAL", "false").lower() in (
    "1",
    "true",
    "yes",
)
VECTOR_STORE = os.getenv("RAG_VECTOR_STORE", "chroma").strip().lower()  # chroma | qdrant
QDRANT_PATH = Path(os.getenv("RAG_QDRANT_PATH", str(BASE_DIR / "artifacts" / "qdrant_db")))
QDRANT_COLLECTION = os.getenv("RAG_QDRANT_COLLECTION", "rag_chunks")

V21_BASELINE_METRICS = {
    "retrieval_hit_rate": 0.72,
    "citation_correctness": 0.46,
    "groundedness": 1.0,
    "answer_correctness": 0.52,
    "insufficient_information_handling": 1.0,
}

RETRIEVAL_MODES_V3 = [
    "semantic_dense",
    "bm25_lexical",
    "hybrid_dense_bm25",
    "hybrid_dense_bm25_rerank",
]
