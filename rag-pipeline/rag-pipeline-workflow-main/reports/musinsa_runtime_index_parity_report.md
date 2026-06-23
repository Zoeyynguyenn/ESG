# Musinsa runtime / index / package parity report

**Date:** 2026-06-11  
**Scope:** Index parity only — no ranking heuristic changes  
**Machine JSON:** `reports/musinsa_runtime_index_parity.json` (post-fix snapshot)

---

## Executive summary

| | Before fix | After fix |
|---|------------|-----------|
| Cached BM25 chunks | **739** | **3501** |
| `1891명` in runtime index | **No** | **Yes** |
| `rec_27e2235c5c45f84a` in index text | **No** | **Yes** |
| Parity with `build_chunks()` | **Mismatch** | **Match** |

**Root cause:** `ingest_corpus_files()` used `load_file_text()` on `full.jsonl`, which **truncates at 500,000 characters** (`rag_common.py` line 162). GT record (`rec_27e2235c5c45f84a` / ETNews `1891명`) lies **after** that cutoff. Prebuild then marked index ready (`.index_complete`) and **skipped** future rebuilds.

**Fix:** Ingest for `company_export_json` lane now uses `build_chunks()` (same as retrieval). Prebuild detects `chunk_count` mismatch and auto-rebuilds.

---

## Part 1 — Runtime vs expected (Musinsa)

### API runtime paths (`company_id=musinsa`)

| Field | Value |
|-------|--------|
| **package** | `무신사_dataset_package_20260608T092823` |
| **package full.jsonl** | `data/rag_dataset/05_company_export_json/…/splits/full.jsonl` |
| **manifest** | `artifacts/benchmark_cache/manifests/corpus_company_export_json_full_company_efb99cde07.json` |
| **cache_key** | `p=jsonl_v1__c=section_based_800_120__e=openai_text-embedding-3-small__d=langgraph_staging_20260608__lane=company_export_json_full__vs=qdrant__company=efb99cde07` |
| **index_dir** | `artifacts/benchmark_cache/index_cache/<cache_key>/` |
| **BM25** | `…/bm25_corpus.json` |
| **Qdrant** | `…/qdrant_db/` |

### Before fix (cached runtime index)

| Signal | Value |
|--------|--------|
| chunk_count | 739 |
| `1891` | false |
| `1891명` | false |
| `rec_27e2235c5c45f84a` | false |
| `.index_complete` marker | `chunks=739` |

### Expected (`build_chunks()` under same env)

| Signal | Value |
|--------|--------|
| chunk_count | 3501 |
| `1891명` | true |
| `rec_27e2235c5c45f84a` | true |

### After fix (rebuild + API restart)

Cached runtime index **matches** expected on all signals (see JSON).

---

## Part 2 — Why runtime ≠ fresh rebuild

### Verified causes (data-backed)

1. **Different chunking pipelines**
   - **Prebuild / ingest:** `load_file_text(jsonl)` → join all records → `[:500000]` → `section_based` split → **739 chunks**
   - **Retrieval audit / `build_chunks`:** per-row `_chunks_from_export_jsonl` → **3501 chunks**

2. **500k truncation** (`rag_common.load_file_text`, jsonl branch)
   - Simulated ingest path: `len(full.jsonl loaded text)=500000`, **`1891명` absent**
   - `build_chunks`: **`1891명` present** in 4 chunks

3. **Stale cache not rebuilt**
   - `index_ready()` only checks marker + files exist
   - `prebuild_langgraph_staging_index.py` **SKIP** when marker present — kept 739-chunk index

4. **Not the primary cause**
   - Cache key mismatch: **same key** before/after
   - Config path stale at import: mitigated by `sync_runtime_config_paths()` but index content was still wrong
   - Wrong package: **same** `full.jsonl` in manifest

### Code locations

| File | Role |
|------|------|
| `src/rag_common.py:162` | `[:500000]` truncation on jsonl ingest text |
| `src/rag_stack.py` `ingest_corpus_files` | Used truncated path for export-json |
| `src/rag_common.py` `build_chunks` | Correct per-record chunking |
| `src/retrieval_v3.py` `get_corpus_chunks` | Loads BM25 written by ingest |
| `scripts/prebuild_langgraph_staging_index.py` | SKIP on `index_ready` without parity |

---

## Part 3 — Parity fix (no ranking changes)

### Changes

1. **`rag_stack.ingest_corpus_files`**
   - For `company_export_json*` lane: chunk via `build_chunks(BASE_DIR)` (aligned with retrieval).

2. **`production_config.index_chunk_parity_mismatch`**
   - Compares cached BM25 count vs `expected_bm25_chunk_count()`.

3. **`scripts/prebuild_langgraph_staging_index.py`**
   - Auto-rebuild when parity mismatch (even without `--force`).

### Rebuild executed

```text
REBUILD: musinsa index parity stale (chunk_count_mismatch:cached=739,expected=3501)
BUILD: musinsa
OK: musinsa files_loaded=2 chunks=3501
```

---

## Part 4 — Verification after parity

| Step | Result |
|------|--------|
| Rebuild Musinsa index | OK, 3501 chunks |
| Restart API (`8787`) | OK |
| Parity audit | cached == expected (3501, `1891명` true) |
| `POST /retrieve` headcount | See below |

### Retrieve after parity (HTTP 200, `company_id=musinsa`)

| Query | top-1 `1891명` | top-1 `mss.go.kr` | score |
|-------|----------------|-------------------|-------|
| `해당 기업의 총 구성원 수는 몇 명인가요?` | **Yes** | No | 1.38 |
| `무신사의 직원 수는 몇 명인가요?` | **Yes** | No | 1.45 |

Top-1 snippet (both): *총직원 수는1891명으로 정규직 1745명…*

**Note:** `record_id` in API item may still be `null` (catalog resolve) while chunk text contains GT anchor — parity/retrieve text goal met.

### Two-layer conclusion

| Layer | Status |
|-------|--------|
| **Parity fixed?** | **Yes** |
| **Retrieval after parity?** | **Top-1 contains `1891명`** for both test queries — no longer blocked by missing index |

Ranking/heuristic tuning **not** required to explain prior API miss; index parity was the blocker.

---

## Six answers

1. **API runtime before fix read which index?**  
   `artifacts/benchmark_cache/index_cache/p=jsonl_v1__…__company=efb99cde07/bm25_corpus.json` (+ matching `qdrant_db`).

2. **Fresh rebuild expected path?**  
   **Same cache key/path** — content should match `build_chunks()` (3501 chunks), not a separate `artifacts/bm25_corpus.json`.

3. **Why mismatch?**  
   Ingest truncated `full.jsonl` at 500k chars + different chunking; stale 739-chunk cache kept by `index_ready` SKIP.

4. **Parity fix how?**  
   Ingest uses `build_chunks` for export-json; prebuild auto-rebuild on chunk-count mismatch; Musinsa index rebuilt.

5. **After fix, runtime has `1891명` + `rec_27…`?**  
   **Yes** (BM25 scan: both true).

6. **Headcount retrieve after parity?**  
   Both test queries return top-1 with **`1891명`** (ETNews workforce anchor), not `mss.go.kr` noise.

---

## Constraints honored

- No `mss.go.kr` penalty
- No ranking/boost heuristic changes
- No corpus cleanup
- Gate headcount scripts unchanged
