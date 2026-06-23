"""OpenAI / OpenRouter embedding resolution for benchmark runs."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

# Registry: logical id -> metadata for screening & cost
EMBEDDING_CANDIDATES: Dict[str, Dict[str, Any]] = {
    "openai:text-embedding-3-small": {
        "provider": "openai",
        "openrouter_id": "openai/text-embedding-3-small",
        "dimensions": 1536,
        "context_tokens": 8191,
        "price_usd_per_1m_tokens": 0.02,
        "adoption": "Baseline production; high OpenAI/OpenRouter volume",
        "multilingual_ko": "Good; baseline for EN/KO mixed ESG JSON",
    },
    "openai:text-embedding-3-large": {
        "provider": "openai",
        "openrouter_id": "openai/text-embedding-3-large",
        "dimensions": 3072,
        "context_tokens": 8191,
        "price_usd_per_1m_tokens": 0.13,
        "adoption": "OpenAI flagship embedding; same API as baseline",
        "multilingual_ko": "Strong multilingual; higher cost tier",
    },
    "openrouter:openai/text-embedding-3-large": {
        "provider": "openrouter",
        "openrouter_id": "openai/text-embedding-3-large",
        "dimensions": 3072,
        "context_tokens": 8191,
        "price_usd_per_1m_tokens": 0.13,
        "adoption": "OpenAI flagship embedding; strong non-English",
        "multilingual_ko": "Strong multilingual; higher cost tier",
    },
    "openrouter:intfloat/multilingual-e5-large": {
        "provider": "openrouter",
        "openrouter_id": "intfloat/multilingual-e5-large",
        "dimensions": 1024,
        "context_tokens": 512,
        "price_usd_per_1m_tokens": 0.01,
        "adoption": "Widely used open multilingual embed; MTEB staple",
        "multilingual_ko": "90+ languages; short context may truncate long JSON chunks",
    },
    "openrouter:qwen/qwen3-embedding-8b": {
        "provider": "openrouter",
        "openrouter_id": "qwen/qwen3-embedding-8b",
        "dimensions": 4096,
        "context_tokens": 32768,
        "price_usd_per_1m_tokens": 0.01,
        "adoption": "Top MTEB multilingual/code; high OpenRouter embedding traffic",
        "multilingual_ko": "100+ langs incl. Korean; long context fits section chunks",
    },
}


def embedding_api_key(provider: str) -> str:
    if provider == "openrouter":
        return os.getenv("OPENROUTER_API_KEY", "").strip()
    return os.getenv("OPENAI_API_KEY", "").strip()


def embedding_base_url(provider: str) -> Optional[str]:
    if provider == "openrouter":
        return (
            os.getenv("OPENROUTER_BASE_URL", "").strip()
            or "https://openrouter.ai/api/v1"
        )
    base = (os.getenv("OPENAI_BASE_URL") or "").strip()
    return base or None


def resolve_openrouter_model_id(effective: str) -> str:
    if effective.startswith("openrouter:"):
        return effective.split("openrouter:", 1)[1]
    return effective


def is_api_embedding_model(model_name: str) -> bool:
    m = (model_name or "").strip().lower()
    return (
        m.startswith("openai:")
        or m.startswith("openrouter:")
        or m.startswith("text-embedding-")
    )


def api_embedding_available(model_name: str) -> tuple[bool, str]:
    if not is_api_embedding_model(model_name):
        return False, "not_api_embedding"
    meta = EMBEDDING_CANDIDATES.get(model_name, {})
    provider = meta.get("provider") or (
        "openrouter" if model_name.startswith("openrouter:") else "openai"
    )
    key = embedding_api_key(provider)
    if not key:
        return False, f"{provider}_api_key_missing"
    return True, f"{provider}_api_key_ok"


def create_embeddings(model_name: str):
    """Return LangChain Embeddings for openai: or openrouter: models."""
    from langchain_openai import OpenAIEmbeddings

    effective = (model_name or "").strip()
    os.environ["RAG_EFFECTIVE_EMBEDDING_MODEL"] = effective

    if effective.startswith("openrouter:"):
        model_id = resolve_openrouter_model_id(effective)
        provider = "openrouter"
    elif effective.startswith("openai:"):
        model_id = effective.split("openai:", 1)[1]
        provider = "openai"
    elif effective.startswith("text-embedding-"):
        model_id = effective
        provider = "openai"
    else:
        raise ValueError(f"Unsupported API embedding model: {model_name}")

    kwargs: Dict[str, Any] = {
        "model": model_id,
        "api_key": embedding_api_key(provider),
        "chunk_size": int(os.getenv("RAG_OPENAI_EMBED_BATCH", "32")),
    }
    base_url = embedding_base_url(provider)
    if base_url:
        kwargs["base_url"] = base_url
    if provider == "openrouter":
        kwargs["default_headers"] = {
            "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "https://github.com/rag-pipeline-workflow"),
            "X-Title": os.getenv("OPENROUTER_APP_TITLE", "rag-pipeline-workflow"),
        }
    return OpenAIEmbeddings(**kwargs)
