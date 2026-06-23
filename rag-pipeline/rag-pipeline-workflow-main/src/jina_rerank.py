"""Jina AI Rerank API client (https://api.jina.ai/v1/rerank)."""



from __future__ import annotations



import os

import time

from typing import List, Optional



JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"

DEFAULT_JINA_RERANK_MODEL = "jina-reranker-v3"



_jina_last_call_ts: float = 0.0





def jina_api_key() -> str:

    return (os.getenv("JINA_API_KEY") or "").strip()





def jina_max_chars() -> int:

    try:

        return max(128, int(os.getenv("RAG_JINA_MAX_CHARS", "400")))

    except ValueError:

        return 400





def _throttle() -> None:

    global _jina_last_call_ts

    min_interval = float(os.getenv("JINA_RERANK_MIN_INTERVAL_SEC", "2"))

    elapsed = time.time() - _jina_last_call_ts

    if elapsed < min_interval:

        time.sleep(min_interval - elapsed)

    _jina_last_call_ts = time.time()





def _is_retryable_status(code: int) -> bool:

    return code in (429, 500, 502, 503, 504)





def rerank_scores(

    query: str,

    documents: List[str],

    *,

    model: Optional[str] = None,

    top_n: Optional[int] = None,

) -> List[float]:

    """Return relevance scores aligned with input document order."""

    key = jina_api_key()

    if not key:

        raise RuntimeError("jina_api_key_missing")

    if not documents:

        return []



    import httpx



    model_name = (model or os.getenv("JINA_RERANK_MODEL") or DEFAULT_JINA_RERANK_MODEL).strip()

    max_chars = jina_max_chars()

    payload = {

        "model": model_name,

        "query": query,

        "documents": [d[:max_chars] for d in documents],

        "return_documents": False,

    }

    if top_n is not None:

        payload["top_n"] = int(top_n)



    max_retries = max(0, int(os.getenv("JINA_RERANK_MAX_RETRIES", "3")))

    backoff = float(os.getenv("JINA_RERANK_RETRY_BACKOFF_SEC", "12"))

    timeout = float(os.getenv("JINA_RERANK_TIMEOUT_SEC", "60"))



    last_err = ""

    for attempt in range(max_retries + 1):

        _throttle()

        resp = httpx.post(

            JINA_RERANK_URL,

            headers={

                "Authorization": f"Bearer {key}",

                "Content-Type": "application/json",

                "Accept": "application/json",

            },

            json=payload,

            timeout=timeout,

        )

        if resp.status_code == 200:

            body = resp.json()

            results = body.get("results") or []

            scores = [0.0] * len(documents)

            for item in results:

                idx = int(item.get("index", -1))

                if 0 <= idx < len(scores):

                    scores[idx] = float(item.get("relevance_score", 0.0))

            return scores



        last_err = f"jina_rerank_http_{resp.status_code}:{resp.text[:300]}"

        if _is_retryable_status(resp.status_code) and attempt < max_retries:

            time.sleep(backoff * (attempt + 1))

            continue

        raise RuntimeError(last_err)



    raise RuntimeError(last_err or "jina_rerank_failed")


