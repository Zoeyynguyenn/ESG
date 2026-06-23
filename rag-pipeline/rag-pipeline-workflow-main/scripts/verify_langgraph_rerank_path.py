#!/usr/bin/env python3
"""Verify LangGraph evidence service uses configured retrieval_v3.retrieve mode (Jina rerank)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    from evidence_api.env_bootstrap import load_repo_dotenv
    from evidence_api.schemas import RetrieveRequest
    from evidence_api.service import EvidenceRetrievalService
    from evidence_api.staging_config import load_staging_config

    load_repo_dotenv()
    cfg = load_staging_config()
    stack = cfg["stack"]
    expected_mode = stack.get("retrieval_mode", "")
    if expected_mode != "hybrid_dense_bm25_rerank":
        print(f"FAIL: expected retrieval_mode hybrid_dense_bm25_rerank, got {expected_mode!r}")
        return 1

    svc = EvidenceRetrievalService()
    assert svc._stack_retrieval_mode(stack) == "hybrid_dense_bm25_rerank"

    company_id = "musinsa"
    if not svc.is_indexed(company_id):
        print(f"SKIP live retrieve: {company_id} not indexed — config/mode checks only")
        print("OK: staging config + _stack_retrieval_mode")
        return 0

    fake_hit = MagicMock()
    fake_hit.text = "record_id: rec_test\n\nstub evidence"
    fake_hit.source = "data/rag_dataset/05_company_export_json/test/splits/full.jsonl"
    fake_hit.score = 0.9

    with patch("retrieval_v3.retrieve", return_value=([fake_hit], "ok;rerank_jina_api")) as mock_retrieve:
        resp = svc.retrieve(RetrieveRequest(query="ESG test", company_id=company_id, top_k=3))

    if mock_retrieve.call_count != 1:
        print(f"FAIL: retrieve called {mock_retrieve.call_count} times")
        return 1

    args, kwargs = mock_retrieve.call_args
    called_mode = args[1] if len(args) > 1 else kwargs.get("mode")
    if called_mode != "hybrid_dense_bm25_rerank":
        print(f"FAIL: service called retrieve(mode={called_mode!r})")
        return 1

    print("OK: service -> retrieval_v3.retrieve(..., hybrid_dense_bm25_rerank, ...)")
    print(f"OK: items={len(resp.items)} reranker={stack.get('reranker_model')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
