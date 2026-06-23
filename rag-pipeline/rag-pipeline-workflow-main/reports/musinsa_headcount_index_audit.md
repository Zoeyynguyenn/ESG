# Musinsa headcount indexed corpus audit

**Date:** 2026-06-11  
**API stack:** `configs/langgraph_staging.yaml` → `musinsa`  
**Method:** Direct BM25/Qdrant path inspection + fresh `build_chunks()` — no retrieve API for conclusions  
**Machine JSON:** `reports/musinsa_headcount_index_audit.json`

---

## Index path API uses

| Item | Path |
|------|------|
| **cache_key** | `p=jsonl_v1__c=section_based_800_120__e=openai_text-embedding-3-small__d=langgraph_staging_20260608__lane=company_export_json_full__vs=qdrant__company=efb99cde07` |
| **index_dir** | `artifacts/benchmark_cache/index_cache/<cache_key>/` |
| **BM25** | `…/bm25_corpus.json` |
| **Qdrant** | `…/qdrant_db/` |
| **Manifest** | 3 files: `splits/full.jsonl`, `manifest.json`, `README.md` |

Set via `production_config.apply_production_env()` after `apply_company_env(cfg, "musinsa")`.

---

## Package vs cached index (critical gap)

| Metric | Fresh `build_chunks()` today | **Cached API index** |
|--------|------------------------------|----------------------|
| Chunk count | **3,501** | **739** |
| Chunks with `1891명` | **4** | **0** |
| Chunks with `1891` substring | 6 (4 real + 2 noise) | **0** |
| GT URL `…/20250901000141` | present in chunks | **0 chunks** |
| `rec_27e2235c5c45f84a` in chunk text | yes | **0** |

**Conclusion:** The API index is **stale / out of sync** with current `full.jsonl`. GT exists in package but **was not ingested** into the cache the API reads.

`.index_complete` exists on cache dir — marker is **misleading** (ready flag ≠ corpus parity).

---

## Alternate BM25 on disk (not API path)

| File | Chunks | `1891명` | Notes |
|------|--------|----------|-------|
| `artifacts/bm25_corpus.json` (repo default) | 3,501 | 4 | Matches fresh build; **not** the Musinsa staging cache path |

This file explains eval/API divergence when `config.BM25_INDEX_PATH` was bound at import time to the default path (see gate false-positive audit).

---

## Dense (Qdrant) spot check

`similarity_search("무신사 총직원 수 1891명", k=10)` on API Qdrant store:

- **0/10** hits contain `1891명`
- Top hits include `mss.go.kr` policy tables, unrelated numeric tables

Consistent with BM25: **GT vector not in store**.

---

## API runtime miss — root cause

| Layer | Status |
|-------|--------|
| Package `full.jsonl` | GT present |
| Cached BM25/Qdrant | GT **absent** |
| Retrieval ranking | **Secondary** — cannot rank up evidence that is not in the index |

Observed API top-1 (`mss.go.kr`, score ~1.06) is **expected** when GT chunks are missing and headcount boost promotes other `N명` noise.

---

## Answers (index)

1. **`1891명` in package?** → Yes (see GT audit).
2. **`1891명` in indexed corpus API uses?** → **No** (0 chunks).
3. **API miss because?** → **Index does not contain GT** (not proven retrieval miss-with-GT-present).
4. **Rebuild index before any ranking patch?** → **Yes.**
