# Korean metric headcount regression — before / after

**Date:** 2026-06-05  
**Company:** musinsa (noise corpus unchanged)  
**Cases:** 16 paraphrase / synonym / generic-company queries  
**Ground truth:** chunk containing `1891` (etnews headcount article)

## Summary

| Metric | Baseline | After fix |
|--------|----------|-----------|
| top-1 correct | 5/16 (31.2%) | **16/16 (100%)** |
| top-3 contains answer | 11/16 (68.8%) | **16/16 (100%)** |
| Jina rerank (`jina_api`) | 16/16 | 16/16 |

## Changes applied

1. **Query rewrite** (`query_rewrite.py`): possessive-safe replacement for `이 기업`, `이 회사`, `해당 기업/회사` → `무신사` / `무신사의` (no `무신사 이 기업의…`).
2. **BM25 synonym expansion** (`korean_metric_retrieval_hints.py`): conditional append of headcount synonyms (`인원`, `직원`, `구성원`, `임직원`, `근로자`, `총직원`, …) when query is a headcount metric question.
3. **Metric-aware hybrid ranking** (`korean_metric_retrieval_hints.py` + `retrieval_v3.py`):
   - Pre-rerank boost for chunks with `\d{2,5}명` near headcount phrases (extra weight for `총직원`).
   - Light penalty for decimal-table noise (e.g. SME PDF grids).
   - Slightly lower Jina blend alpha for headcount queries; post-rerank tie-break boost.

## Failure classes — baseline vs after

| fail_kind | Baseline | After |
|-----------|----------|-------|
| `answerable_chunk_not_in_top_pool` | 4 | 0 |
| `rerank_failed_to_promote` | 6 | 0 |
| `rewrite_miss` | 1 | 0 |
| `pass` | 5 | 16 |

## Remaining risks (not covered by this regression)

- All 16 cases share one company and one numeric answer (`1891`); Hanssem/Rayshion not tested (no clean GT in package).
- Other metric types (board size, donations, ESG) not in scope of this set.
- Chunks with multiple headcount numbers in one text can still confuse ranking on unseen wordings.

## Reproduce

```bash
python scripts/prebuild_langgraph_staging_index.py --company musinsa --force
python scripts/eval_korean_metric_retrieval_regression.py --company musinsa --json-out reports/korean_metric_regression_musinsa.json
```
