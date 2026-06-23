# Headcount KO retrieval — holdout gate report

**Date:** 2026-06-05  
**Scope:** Musinsa, noise corpus unchanged, headcount class only  
**Artifact:** `reports/korean_headcount_gate_results.json`

---

## Changes this round

### `korean_metric_retrieval_hints.py`

| Layer | Change |
|-------|--------|
| **Guard** | `_NON_HEADCOUNT_GUARD` blocks synonym/boost when query mentions `사외이사`, `이사회`, `임원진`, `위원회`, `기부금`, … |
| **Strong trigger** | Added `고용 규모`, `총/전체 인력` to strong headcount intent |
| **Soft trigger** | `(workforce noun) + 규모` e.g. `사람 규모`, `인원 규모`, `종업원 규모` — not bare `규모` |
| **Synonyms** | Added `종업원`, `인력규모`, `고용인원` to BM25 expansion set |

### `query_rewrite.py` (minimal)

- `_METRIC_HINT` extended with `종업원`, `인력`, `고용` for generic-company prepend fallback.

No hardcode `1891` / `musinsa` / `record_id`. No corpus changes.

---

## Gate results

| Suite | Before | After |
|-------|--------|-------|
| Regression 16 | 16/16 top-1 | **16/16** top-1, **16/16** top-3 |
| Holdout 6 (original) | 4/6 top-1 | **6/6** top-1, **6/6** top-3 |
| Holdout extended 8 | (new) | **8/8** top-1, **8/8** top-3 |

### Holdout 6 — previously failing (now pass)

- `무신사의 총 고용 규모는 몇 명인가요?` — strong trigger `고용 규모` + synonym expansion
- `해당 기업의 사람 규모는 어느 정도인가요?` — soft trigger `사람 규모` + expansion

---

## Non-headcount leakage sanity (4 queries)

| Query | Headcount path triggered? |
|-------|---------------------------|
| `무신사의 사외이사 수는 몇 명인가요?` | **No** |
| `무신사의 이사회 규모는 어느 정도인가요?` | **No** |
| `무신사의 임원진 규모는 어느 정도인가요?` | **No** |
| `이 회사 사외이사 인원은?` | **No** |

**Leakage: 0/4** — guard blocks prior false activation on `사외이사 인원`.

Sanity top-1 (not a pass criterion): 2/4 — non-headcount retrieval quality not in scope.

---

## Answers to gate questions

1. **Regression 16 still 16/16?** — Yes.
2. **Holdout old 4/6 → ?** — **6/6**.
3. **Holdout extended?** — **8/8** top-1.
4. **Leakage to non-headcount?** — **No** on sanity set (0/4 triggered).
5. **Freeze as headcount patch?** — **Yes, tentatively.** Meets proposed gate: regression 16/16, holdout ≥5/6, extended holdout strong, no leakage on sanity. Still scoped to **headcount class / Musinsa GT** — not general metric KO retrieval.

---

## Reproduce

```bash
python scripts/eval_korean_headcount_gate.py --json-out reports/korean_headcount_gate_results.json
python scripts/eval_korean_metric_retrieval_regression.py --company musinsa
```

---

## Freeze recommendation

| Criterion | Status |
|-----------|--------|
| Regression 16/16 | ✓ |
| Holdout ≥5/6 | ✓ (6/6) |
| Extended holdout stable | ✓ (8/8) |
| No non-headcount leakage (sanity) | ✓ |
| No hardcode / no corpus change | ✓ |

**Propose:** freeze as **`headcount retrieval patch`** with CI gate script `eval_korean_headcount_gate.py`.  
**Not frozen:** general metric KO retrieval, Hanssem/Rayshion, other metric families.
