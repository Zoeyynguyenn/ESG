# Korean metric retrieval — audit, ablation, holdout

**Date:** 2026-06-05  
**Scope:** Musinsa package, noise corpus unchanged, no retrieval code changed during this audit.  
**Artifacts:** `reports/korean_metric_ablation_results.json`

---

## Part 1 — Code audit

### Hardcode check (`query_rewrite.py`, `korean_metric_retrieval_hints.py`, `retrieval_v3.py`)

| Target | Found? |
|--------|--------|
| `1891` | **No** |
| `rec_27e2235c5c45f84a` | **No** |
| `musinsa` / Musinsa package name | **No** (rewrite uses `display_name` from registry config) |

**Conclusion:** No answer- or company-specific hardcode in retrieval logic. Ground truth `1891` appears only in eval scripts, not in `src/`.

### Heuristic scope

| Layer | Scope | Risk |
|-------|--------|------|
| Rewrite | Generic KO company references → registry `display_name` | Low overfit; company-agnostic |
| BM25 synonym expansion | Triggers on `_HEADCOUNT_QUERY` regex (인원, 직원, 구성원, …) | **Token-list sensitive** — wording outside list gets no expansion |
| `숫자+명` boost | Only when `is_headcount_metric_query()` | Does **not** run on bare `사외이사` / `임원진` queries; **does** run if query contains `인원` (e.g. `사외이사 인원`) |
| Blend alpha | Lower Jina weight only for headcount-class queries | Isolated to matched queries |

### Side-effect risk for non-headcount metrics

- Boost is gated on headcount query regex, not on every `명` in corpus.
- **Leakage path:** queries that mention `인원` for a non-headcount metric (e.g. `사외이사 인원`) incorrectly enter headcount path — observed in other-metric suite (`이 회사 사외이사 인원은?` passed top-1; may be coincidental ranking, not proof of correctness).
- `숫자+명` boost can still favour any chunk with large `N명` near headcount phrases — on non-headcount tasks, wrong numeric chunks are possible if the query accidentally triggers headcount class.

---

## Part 2 — Ablation (regression 16)

| Config | top-1 | top-3 | Δ top-1 vs full |
|--------|-------|-------|-----------------|
| **A. full_fix** | **16/16 (100%)** | **16/16** | — |
| B. no_rewrite | 16/16 (100%) | 16/16 | 0 |
| C. no_synonym_expansion | 10/16 (62.5%) | 11/16 | **−6** |
| D. no_headcount_boost | 14/16 (87.5%) | 16/16 | −2 |
| E. no_jina | 16/16 (100%) | 16/16 | 0 |

### Interpretation

1. **BM25 synonym expansion** — largest contributor (−6 top-1 when removed). Fixes recall for `인원`, short forms, and synonym mismatch vs evidence `총직원`.
2. **Headcount ranking boost** — secondary (−2 top-1): disambiguates competing `1891명` vs `1604명` when chunk is already in pool.
3. **Query rewrite** — **0 delta** on regression 16 (company filter + synonyms sufficient for this set). Still fixes `rewrite_miss` wording and is required for generic-company UX; holdout uses patterns rewrite handles.
4. **Jina rerank** — **0 delta** on regression 16 with current boost+synonym stack (rerank runs but outcome unchanged vs overlap path for these cases).

---

## Part 3 — Holdout (6 new queries, no code tuning)

**full_fix results: top-1 4/6 (66.7%), top-3 4/6**

| Result | Query | Failure mode |
|--------|-------|--------------|
| PASS | 무신사의 인력 규모는 어느 정도인가요? | — |
| PASS | 이 회사 전체 임직원 규모를 알려주세요 | — |
| PASS | 해당 회사 고용 인원은 몇 명입니까? | — |
| PASS | 이 기업 종업원 수는 몇 명인가요? | — |
| **FAIL** | 무신사의 총 **고용 규모**는 몇 명인가요? | `answerable_chunk_not_in_top_pool` — `고용 규모` not in trigger regex (`고용 인원` only) |
| **FAIL** | 해당 기업의 **사람 규모**는 어느 정도인가요? | `answerable_chunk_not_in_top_pool` — `사람 규모` not in trigger regex (`사람 수` only) |

Holdout failures are **lexical recall / trigger coverage**, not rerank wiring. Same 2 queries fail under `no_jina` and `no_headcount_boost` — not fixable by rerank alone.

---

## Part 4 — Other metric family (5 queries, GT from package)

Metrics tested without corpus changes:

| Metric | GT snippet | full_fix top-1 |
|--------|------------|----------------|
| External directors | `사외이사 3` | 1/3 |
| Executive count | `임원진 7명` | 0/2 |

**Overall other-metric: top-1 1/5 (20%), top-3 4/5 (80%)**

Pipeline is **not** general metric-KO retrieval today — it is **headcount-class specialized**. Non-headcount counts pass only sporadically; headcount boost does not transfer (and should not be expected to without separate metric classes).

GT quality note: `사외이사 3` appears in ~10 chunks (including headcount article); executive GT is cleaner (`임원진 7명` in 2 chunks) but recall still weak.

---

## Part 5 — Answers to five questions

### 1. Hardcode / overfit ngầm?

- **Không** hardcode `1891` / `musinsa` / `record_id` trong `src/`.
- **Có** over-specialization theo **lớp headcount**: regex trigger + synonym list + `명` boost. Regression 16 có thể “đẹp” trong khi holdout và metric khác chưa theo.

### 2. Thành phần ablation đóng góp nhiều nhất?

1. **BM25 synonym expansion** (chính)  
2. **Headcount ranking boost** (phụ, ranking giữa số cạnh tranh)  
3. Rewrite và Jina: **không đổi top-1** trên regression 16 (với stack hiện tại)

### 3. Holdout ngoài bộ 16?

- **4/6 top-1** — chưa robust.  
- Fail do **trigger lexical** (`고용 규모`, `사람 규모` ngoài regex), không phải rerank.

### 4. Generalize ngoài headcount?

- **Chưa.** Other-metric 1/5 top-1.  
- Đúng nghĩa hiện tại: **PASS headcount class (có điều kiện)**, chưa PASS metric KO chung.

### 5. Freeze ngay?

- **Không nên freeze** như retrieval metric KO tổng quát.  
- **Có thể** ghi nhận: *headcount KO regression 16 = gate tạm*, kèm thêm gate holdout (≥5/6 hoặc 6/6) trước khi coi lớp headcount ổn định.  
- Cần thêm: mở rộng trigger/synonym có kiểm soát (sau khi đo), metric-class riêng cho board/donation, GT đa công ty.

---

## Reproduce

```bash
python scripts/eval_korean_metric_ablation.py --json-out reports/korean_metric_ablation_results.json
python scripts/eval_korean_metric_retrieval_regression.py --company musinsa --json-out reports/korean_metric_regression_musinsa.json
```
