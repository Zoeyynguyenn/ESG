#!/usr/bin/env python3
"""Verify Musinsa headcount retrieval: 1891명 for generic KO metric query (noise corpus kept)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

MUSINSA_QUERY = "해당 기업의 총 구성원 수는 몇 명인가요?"
EXPECTED_RECORD = "rec_27e2235c5c45f84a"
EXPECTED_SNIPPET = "1891"


def _bootstrap() -> None:
    from evidence_api.env_bootstrap import load_repo_dotenv

    load_repo_dotenv()


def _check_tokenize() -> bool:
    from rag_common import tokenize

    tokens = tokenize(MUSINSA_QUERY)
    need = {"구성원", "몇", "명인가요"}
    missing = need - set(tokens)
    if missing:
        print(f"FAIL tokenize: missing {missing} in {tokens}")
        return False
    if not tokenize("무신사 1891명"):
        print("FAIL tokenize: empty for 무신사 1891명")
        return False
    print(f"OK tokenize: {tokens}")
    return True


def _check_rewrite() -> bool:
    from evidence_api.query_rewrite import rewrite_query_for_company
    from evidence_api.staging_config import company_registry, load_staging_config

    cfg = load_staging_config()
    entry = company_registry(cfg)["musinsa"]
    rewritten = rewrite_query_for_company(MUSINSA_QUERY, "musinsa", entry)
    if "무신사" not in rewritten:
        print(f"FAIL rewrite: {rewritten!r}")
        return False
    if "해당 기업" in rewritten:
        print(f"FAIL rewrite still generic: {rewritten!r}")
        return False
    print(f"OK rewrite: {rewritten!r}")
    return True


def _check_bm25_signal() -> bool:
    from evidence_api.staging_config import apply_company_env, load_staging_config, reset_retrieval_runtime_caches
    from production_config import repo_root
    from retrieval_v3 import retrieve_bm25_lexical

    import retrieval_v3 as r3

    cfg = load_staging_config()
    apply_company_env(cfg, "musinsa", base_dir=repo_root())
    reset_retrieval_runtime_caches()
    r3._bm25_index = None

    from evidence_api.query_rewrite import rewrite_query_for_company
    from evidence_api.staging_config import company_registry

    q = rewrite_query_for_company(
        MUSINSA_QUERY, "musinsa", company_registry(cfg)["musinsa"]
    )
    hits, note = retrieve_bm25_lexical(q, 64, 64)
    if note == "empty_query":
        print("FAIL bm25: empty_query (Korean tokens not reaching BM25)")
        return False
    if not hits:
        print(f"FAIL bm25: no hits note={note}")
        return False
    top = hits[0]
    tag = "1891" if EXPECTED_SNIPPET in top.text else "other"
    print(f"OK bm25: hits={len(hits)} note={note} top={tag} score={top.score}")
    return True


def _jina_key_present() -> bool:
    from jina_rerank import jina_api_key

    return bool(jina_api_key())


def _check_runtime_retrieve() -> tuple[str, bool]:
    """Returns (status, passed): pass | fail | skipped."""
    from evidence_api.schemas import RetrieveRequest
    from evidence_api.service import EvidenceRetrievalService
    from evidence_api.staging_config import load_staging_config

    cfg = load_staging_config()
    svc = EvidenceRetrievalService()
    if not svc.is_indexed("musinsa"):
        print("SKIP runtime: musinsa index not ready — run prebuild --company musinsa --force")
        return "skipped", False

    jina = _jina_key_present()
    print(f"JINA_API_KEY: {'set' if jina else 'missing (rerank may use overlap fallback)'}")

    from retrieval_v3 import retrieve as r3_retrieve

    import retrieval_v3 as r3

    from evidence_api.query_rewrite import rewrite_query_for_company
    from evidence_api.staging_config import apply_company_env, company_registry, reset_retrieval_runtime_caches

    apply_company_env(cfg, "musinsa", base_dir=ROOT)
    reset_retrieval_runtime_caches()
    r3._bm25_index = None

    entry = company_registry(cfg)["musinsa"]
    search_q = rewrite_query_for_company(MUSINSA_QUERY, "musinsa", entry)
    mode = svc._stack_retrieval_mode(cfg["stack"])
    pool = int(cfg["stack"].get("candidate_pool", 64))
    hits, note = r3_retrieve(search_q, mode, pool, pool)
    print(f"retrieve note: {note}")
    if "jina_api" in note:
        print("rerank: Jina API")
    elif "fallback" in note:
        print(f"rerank: FALLBACK ({note})")
    else:
        print(f"rerank: {note}")

    resp = svc.retrieve(
        RetrieveRequest(query=MUSINSA_QUERY, company_id="musinsa", top_k=8)
    )
    if not resp.items:
        print("FAIL runtime: items empty")
        return "fail", False

    for i, item in enumerate(resp.items[:3]):
        has_1891 = EXPECTED_SNIPPET in (item.text or "")
        rid = item.record_id or ""
        print(
            f"  top{i+1} record_id={rid} 1891={has_1891} "
            f"preview={(item.text or '')[:90].replace(chr(10), ' ')}"
        )

    first = resp.items[0]
    top_ok = EXPECTED_SNIPPET in (first.text or "")
    rid_ok = first.record_id == EXPECTED_RECORD if first.record_id else top_ok
    if top_ok:
        print(f"OK runtime: top-1 contains {EXPECTED_SNIPPET}명")
        if first.record_id:
            print(f"  record_id={first.record_id}")
        return "pass", True
    print("FAIL runtime: top-1 missing 1891 — likely recall (chunk not in pool) or rerank rank")
    return "fail", False


def main() -> int:
    _bootstrap()
    ok = True
    ok &= _check_tokenize()
    ok &= _check_rewrite()
    ok &= _check_bm25_signal()
    status, runtime_ok = _check_runtime_retrieve()
    if status == "pass":
        pass
    elif status == "fail":
        ok = False
    print(f"\nSummary: unit={'pass' if ok else 'fail'} runtime={status}")
    if status == "fail":
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
