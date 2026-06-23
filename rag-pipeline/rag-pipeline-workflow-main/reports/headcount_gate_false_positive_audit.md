# Headcount gate / regression false-positive audit

**Date:** 2026-06-11  
**Scope:** Scoring logic only — no new heuristics

---

## Pass rule (exact bug surface)

All headcount eval/gate scripts share:

```python
def _has_answer(text: str, snippet: str) -> bool:
    return snippet in (text or "")
```

**Expected snippet in cases:** `"1891"` (not `"1891명"`, not `rec_27e2235c5c45f84a`).

**Pass condition (gate):** `top1 = bool(resp.items) and _has_answer(resp.items[0].text, "1891")`  
(`scripts/eval_korean_metric_ablation.py`, used by `eval_korean_headcount_gate.py`)

### Why `"1891"` is unsafe

| Match type | Example in corpus | Valid GT? |
|------------|-------------------|-----------|
| Workforce anchor | `총직원 수는1891명` | **Yes** |
| Table digit run | `…851891,337한국…` | **No** |
| record_id hash | `rec_e501a7f818919beb` | **No** |
| Date/phone substrings | `2026-06-08`, `89191825` | **No** |

Substring `"1891"` can pass without `1891명` or `rec_27e2235c5c45f84a`.

**Eval cases also list `expected_record_id: rec_27e2235c5c45f84a` but never assert it** — record_id is informational only.

---

## False positive mechanism #1 — wrong BM25 path (primary)

`config.py` binds `BM25_INDEX_PATH` at **import time**. If `retrieval_v3` / eval runs before `apply_company_env()`, or `config` is not re-synced, eval reads:

- `artifacts/bm25_corpus.json` → **3,501 chunks, 4× `1891명`** (fresh)

API after correct env reads:

- `artifacts/benchmark_cache/index_cache/…/bm25_corpus.json` → **739 chunks, 0× `1891명`** (stale)

**Measured today:**

| Run | Index file | `무신사의 직원 수는 몇 명인가요?` |
|-----|------------|-----------------------------------|
| Saved gate `korean_headcount_gate_results_live.json` | (stale run) | `top1: true`, `pool: true` |
| Re-run `eval_suite` now (same code) | correct cache path | `top1: false`, `pool: false`, `failure: answerable_chunk_not_in_top_pool` |

Earlier **16/16** headline is **not reproducible** on the index API actually serves.

`sync_runtime_config_paths()` was added to `production_config` / `staging_config` but **does not replace a stale cache** — only fixes path binding.

---

## False positive mechanism #2 — substring scoring

Even on `artifacts/bm25_corpus.json`, `_has_answer(..., "1891")` matches:

- **4** true `1891명` workforce chunks
- **2** unrelated substrings (company table + record_id)

Gate can report **pass** without retrieving the canonical record.

---

## Scripts / artifacts — validity status

| Artifact | Verdict |
|----------|---------|
| `reports/korean_headcount_gate_results.json` | **Invalidate** 16/16 headline for current API index |
| `reports/korean_headcount_gate_results_live.json` | **Invalidate** — same scoring, non-reproducible on live cache |
| `reports/korean_metric_regression_musinsa.json` | **Invalidate** pass rows — used `"1891"` + likely wrong index path at run time |
| `reports/korean_metric_regression_ablation_report.md` | **Partially invalid** — ablation deltas assumed GT reachable in pool |
| `scripts/eval_korean_headcount_gate.py` | **Keep script** — fix scoring + require index parity check |
| `scripts/eval_korean_metric_retrieval_regression.py` | **Keep script** — fix `expected_snippet` → `1891명`, assert `record_id` |
| `scripts/verify_musinsa_headcount_retrieval.py` | **Unsafe** — `EXPECTED_SNIPPET = "1891"` |

### What remains usable

- Case **query paraphrase lists** (16 + holdout queries)
- **Ablation harness** structure (`ablation_patches`, suite runner)
- **Non-headcount leakage** checks (separate regex guards)
- Gender-ratio abstain workstream (orthogonal)

---

## Reproduction commands (audit)

```bash
# Package GT
python scripts/audit_musinsa_headcount_gt.py

# Single gate case — fails on current API cache
python -c "… eval_suite('full_fix','now',[EvalCase('무신사의 직원 수는 몇 명인가요?','1891',…)], …)"
```

---

## Five answers (gate / eval)

1. **`1891명` in package?** → **Yes** (`rec_27e2235c5c45f84a`).
2. **`1891명` in API index?** → **No**.
3. **API miss = retrieval or index?** → **Index miss** (GT not in cache); ranking not proven broken.
4. **Prior gate false positive?** → **Yes** — (a) wrong/stale BM25 path vs API, (b) `"1891"` substring rule, (c) no `record_id` assertion.
5. **`mss.go.kr` penalty now?** → **No** — fix **index rebuild + eval contract** first; do not patch ranking to fake pass.

---

## Recommended eval contract (future, not implemented here)

- `expected_snippet`: `1891명` (or regex workforce anchor)
- `expected_record_id`: must match top-1 when set
- Pre-flight: `index chunk_count` ≈ fresh `build_chunks()` count; fail gate if drift
- Separate **index-ready** from **corpus-parity-ready**
