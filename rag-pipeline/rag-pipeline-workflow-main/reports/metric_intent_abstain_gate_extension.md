# Metric-intent abstain gate extension

**Date:** 2026-06-11  
**Scope:** API layer only — no retrieval ranking changes, no corpus cleanup  
**Eval artifact:** `reports/metric_intent_abstain_eval.json`

---

## Before / after

| Query class | Before (gender-ratio gate only) | After (metric-intent gate) |
|-------------|--------------------------------|----------------------------|
| Gender-ratio (no GT) | abstain ✓ | abstain ✓ |
| Headcount (1891명 GT) | no abstain ✓ | no abstain ✓ |
| `장애인 고용률` | **top-1 noise** (national mss.go.kr %) | **abstain**, `items=[]` |
| `육아휴직 대상자 수` | **top-1 noise** (policy / unrelated headcount-ish text) | **abstain**, `items=[]` |
| Other blocked metrics (여성기업 비율, etc.) | noise | abstain |

---

## Design

### Gate applies when

1. Query is **quantitative metric intent** (percentage or count)
2. **NOT** generic headcount (`is_headcount_metric_query` bypass)
3. **Unless** query has **specific metric topic** (`육아휴직`, `장애인`, `고용률`, …) that overrides generic `인원` headcount trigger

### Intent classes

| Kind | Triggers | Anchor required |
|------|----------|-----------------|
| **percentage** | `%`, `비율`, `고용률`, `비중`, gender-ratio | topic term + `\d+%` (gender subset uses gender anchor) |
| **count** | `몇 명`, `대상자 수`, `인원` (non-headcount) | topic term + `\d+명/수/건` |

### Signals

| Signal | Meaning |
|--------|---------|
| `metric_anchor_missing` | Top-k lacks numeric anchor matching intent + topic |
| `domain_mismatch` | mss.go.kr without company, national stats, UI/policy noise |
| `no_answerable_evidence` | Anchor may exist but not answerable (domain fail) |

### Headcount bypass

Uses existing `korean_metric_retrieval_hints.is_headcount_metric_query()` **unless** `_SPECIFIC_METRIC` topic present (prevents `육아휴직 … 인원` false bypass).

---

## Files changed

| File | Change |
|------|--------|
| `src/evidence_api/abstain.py` | Generalized `parse_metric_intent`, percentage/count anchors, extended domain mismatch |
| `scripts/verify_retrieve_abstain_gate.py` | Updated unit tests |
| `scripts/eval_metric_intent_abstain.py` | **New** — 11-case eval suite |

---

## Test results (11/11)

| Suite | Result |
|-------|--------|
| Headcount should answer (3) | 3/3 — no false abstain |
| Gender-ratio should abstain (3) | 3/3 |
| Blocked metrics should abstain (5) | 5/5 |

Gender-ratio baseline (`eval_korean_gender_ratio_baseline.py`): **10/10 abstain_ok** (after fix: gender-ratio intent checked **before** headcount bypass so `남성 직원 비율` no longer false-passes).

### Regression fix (2026-06-11)

Queries like `무신사의 남성 직원 비율은 몇 %인가요?` contain `직원`, which triggered headcount bypass before gender-ratio was evaluated. **Fix:** `parse_metric_intent()` now checks `is_gender_ratio_query()` first, then headcount bypass.

---

## What should abstain vs answer

| Should **answer** (no abstain) | Should **abstain** |
|-------------------------------|-------------------|
| Headcount: `직원/구성원/임직원 … 몇 명` with GT in index | Gender-ratio without GT |
| (Future) metrics with clean GT + answerable anchor in top-k | `장애인 고용률` (national noise only) |
| | `육아휴직 대상자 수` (policy, no count) |
| | Ad-hoc % / count queries without company-specific evidence |

---

## Regression

- **Headcount:** no abstain on 3 pass queries ✓
- **Gender-ratio:** abstain unchanged ✓
- **No ranking/heuristic changes** ✓

---

## API contract (unchanged shape)

When abstaining:

```json
{
  "items": [],
  "abstain_recommended": true,
  "no_relevant_evidence": true,
  "retrieval_confidence": "low",
  "abstain_reason": "metric_anchor_missing | domain_mismatch | no_answerable_evidence"
}
```
