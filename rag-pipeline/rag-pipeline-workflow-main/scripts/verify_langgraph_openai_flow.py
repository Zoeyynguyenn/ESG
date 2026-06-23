#!/usr/bin/env python3
"""Kiem tra luong LangGraph staging: OpenAI embed + rerank off + retrieve."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    from evidence_api.env_bootstrap import load_repo_dotenv
    from embedding_providers import api_embedding_available
    from fastapi.testclient import TestClient
    from evidence_api.app import app
    from evidence_api.staging_config import load_staging_config, indexed_companies

    load_repo_dotenv()
    ok, reason = api_embedding_available("openai:text-embedding-3-small")
    print(f"OpenAI embed: {ok} ({reason})")
    if not ok:
        return 1

    cfg = load_staging_config()
    ready, pending = indexed_companies(cfg)
    print(f"indexed={ready} pending={pending}")

    client = TestClient(app)
    print("GET /companies", client.get("/companies").json())
    print("GET /health", client.get("/health").json())

    queries = {
        "musinsa": "ESG carbon emissions",
        "rayshion": "governance policy",
        "hanssem": "environment sustainability",
        "nexteye": "ticker DART corp code",
    }
    failed = 0
    print("\n--- POST /retrieve ---")
    for cid, query in queries.items():
        if cid not in ready:
            print(f"{cid}: SKIP (not indexed)")
            failed += 1
            continue
        resp = client.post("/retrieve", json={"query": query, "company_id": cid, "top_k": 5})
        data = resp.json()
        items = data.get("items") or []
        top = items[0] if items else {}
        print(
            f"{cid}: HTTP {resp.status_code} items={len(items)} "
            f"score={top.get('score')} record_id={top.get('record_id')}"
        )
        if resp.status_code != 200:
            failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
