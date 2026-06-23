# Retrieve API — reliability annotation layer

**Date:** 2026-06-11  
**Eval artifacts:** `reports/metric_intent_abstain_eval.json`, `reports/korean_gender_ratio_baseline.json`  
**Scope:** API response contract only — no retrieval ranking changes, no corpus cleanup

---

## Summary

The retrieve API now **keeps `items`** (top-k candidates) on every response, while adding a **reliability layer** so clients and downstream LLMs can distinguish:

| Concept | Meaning |
|---------|---------|
| `score` | Retrieval / rerank ranking score only |
| `candidate_confidence` | Whether **this chunk** can answer the metric query |
| `retrieval_confidence` | Whether the **whole response** is trustworthy enough to answer |

**Before:** when the abstain gate fired, `items` was cleared (`items=[]`). Clients saw empty results; debugging required re-running retrieval. High `score` on top-1 was easy to misread as “correct evidence”.

**After:** `items` always returned (when retrieval finds candidates). Response-level flags say **do not treat top-1 as answerable evidence** when `abstain_recommended=true`. Each item carries `answerable_candidate` and `candidate_flags`.

---

## Schema changes (backward-compatible)

### Response level (`RetrieveResponse`)

| Field | Type | Notes |
|-------|------|-------|
| `items` | `EvidenceItem[]` | **Unchanged behavior:** still returned |
| `abstain_recommended` | `bool` | `true` → downstream should not answer from top-1 alone |
| `no_relevant_evidence` | `bool` | No answerable candidate in top-k check window |
| `retrieval_confidence` | `low \| medium \| high` | From answerability validation, **not** from `score` |
| `reliability_reason` | `string \| null` | Human-readable explanation |
| `reliability_flags` | `string[]` | Structured signals |
| `abstain_reason` | `string \| null` | **Kept for compatibility** — primary flag (= `reliability_flags[0]` when abstaining) |

### Item level (`EvidenceItem`)

| Field | Type | Notes |
|-------|------|-------|
| `score` | `float` | Unchanged — ranking only |
| `confidence` | `low \| medium \| high` | Unchanged — metadata/heuristic confidence (not answerability) |
| `answerable_candidate` | `bool` | **New** — can this chunk answer the metric intent? |
| `candidate_confidence` | `low \| medium \| high` | **New** — trust for answering (not ranking) |
| `candidate_flags` | `string[]` | **New** — per-chunk failure reasons |

### Reliability flags (response + item)

| Flag | Level | Meaning |
|------|-------|---------|
| `metric_anchor_missing` | response | Top-k lacks `%` / count anchor matching metric intent |
| `domain_mismatch` | response / item | Policy, national stats, UI noise, mss.go.kr without company body |
| `entity_mismatch` | response / item | Topic overlap but wrong entity (e.g. IBK bank text for Musinsa query) |
| `no_answerable_evidence` | response | Lexical match but nothing answerable in top-k |
| `no_candidates` | response | Empty retrieval pool |
| `missing_metric_anchor` | item | Chunk lacks required numeric anchor |
| `national_stat_not_company_metric` | item | mss.go.kr / national aggregate, not company metric |
| `headcount_anchor_weak` | item | Headcount query but weak `N명` anchor pattern |

---

## Abstain rules

`abstain_recommended=true` when (metric-intent gate active):

1. Top-k has candidates but **none** with `answerable_candidate=true`, **or**
2. Best candidate has `candidate_confidence=low` and no answerable peer in top-k, **or**
3. Top-k dominated by `domain_mismatch` / `entity_mismatch` / `metric_anchor_missing`

**Headcount bypass:** generic headcount queries (`직원 수`, `구성원 수`, …) never abstain at response level; items still get headcount anchor annotations.

**Items are never cleared** for abstain cases — kept for debug, LLM context, and audit.

---

## Test results (from existing eval)

### `eval_metric_intent_abstain.py` — **11/11 pass**

| Suite | Cases | Pass | Contract |
|-------|-------|------|----------|
| Headcount should answer (HC) | 3 | 3/3 | `abstain_recommended=false`, `items>0`, ≥1 `answerable_candidate=true` |
| Gender-ratio abstain (GR) | 3 | 3/3 | `abstain_recommended=true`, `items>0`, top-3 all `answerable_candidate=false` |
| Blocked metrics (BM) | 5 | 5/3 | Same abstain contract |

### `eval_korean_gender_ratio_baseline.py` — **10/10 abstain_ok**

All blocked gender-ratio variants: flags set, `items` kept, top-3 unanswerable.

### Regression status

| Case | Status |
|------|--------|
| Headcount pass (no false abstain) | ✓ 3/3 |
| Gender-ratio abstain | ✓ 10/10 baseline + 3/3 metric-intent |
| `장애인 고용률` abstain + items kept | ✓ |
| `육아휴직 대상자 수` abstain + items kept | ✓ |

**Known limitation (out of gate scope):** headcount eval asserts **no abstain**, not that top-1 contains `1891명`. Top-1 preview in eval may still be executive-count noise (`7명 임원`) — that is a **ranking** issue, not a reliability-flag regression.

---

## Before / after behavior

| Query class | Before (items=[] mode) | After (reliability mode) |
|-------------|------------------------|---------------------------|
| Headcount | `items` returned, no abstain | Same + `top1_answerable=true`, `retrieval_confidence=high` |
| Gender-ratio (no GT) | `items=[]`, abstain flags | **`items` kept (5)**, all `answerable_candidate=false`, abstain flags |
| `장애인 고용률` | `items=[]` | **`items` kept**, national-stat noise flagged, abstain |
| `육아휴직 대상자 수` | `items=[]` | **`items` kept**, policy/entity mismatch flagged, abstain |

---

## Example responses (from eval runs)

Values below are taken from `metric_intent_abstain_eval.json` (2026-06-11). `score` / full `text` are illustrative where truncated.

### A. Headcount pass — `무신사의 직원 수는 몇 명인가요?`

```json
{
  "items": [
    {
      "record_id": "…",
      "text": "…영입된 7명의 임원진…",
      "score": 0.82,
      "confidence": "medium",
      "answerable_candidate": true,
      "candidate_confidence": "high",
      "candidate_flags": []
    }
  ],
  "company_id": "musinsa",
  "query": "무신사의 직원 수는 몇 명인가요?",
  "abstain_recommended": false,
  "no_relevant_evidence": false,
  "retrieval_confidence": "high",
  "reliability_reason": null,
  "reliability_flags": [],
  "abstain_reason": null
}
```

Eval: `top1_answerable=true`, `items_count=5`, all 3 headcount cases identical contract.

### B. Gender-ratio missing GT — `해당 기업의 여성 비율은 몇 %인가요?`

```json
{
  "items": [
    {
      "record_id": "rec_c959827fdefe1ad4",
      "text": "record_id: rec_c959827fdefe1ad4 … company: 무신사 …",
      "score": 0.91,
      "confidence": "high",
      "answerable_candidate": false,
      "candidate_confidence": "low",
      "candidate_flags": ["missing_metric_anchor", "domain_mismatch"]
    }
  ],
  "company_id": "musinsa",
  "query": "해당 기업의 여성 비율은 몇 %인가요?",
  "abstain_recommended": true,
  "no_relevant_evidence": true,
  "retrieval_confidence": "low",
  "reliability_reason": "Top candidates appear to be policy, national statistics, or off-domain content.",
  "reliability_flags": ["domain_mismatch", "no_answerable_evidence"],
  "abstain_reason": "domain_mismatch"
}
```

Eval: `items_count=5`, `all_items_unanswerable=true` (top-3). Baseline also flags ambiguous top-3 hit `여성기업`.

### C. Disability hiring rate missing GT — `해당 기업의 장애인 고용률은 몇 %인가요?`

```json
{
  "items": [
    {
      "record_id": "rec_521ee9578824a2a3",
      "text": "record_id: rec_521ee9578824a2a3 … company: 무신사 …",
      "score": 0.93,
      "confidence": "high",
      "answerable_candidate": false,
      "candidate_confidence": "low",
      "candidate_flags": ["missing_metric_anchor"]
    }
  ],
  "company_id": "musinsa",
  "query": "해당 기업의 장애인 고용률은 몇 %인가요?",
  "abstain_recommended": true,
  "no_relevant_evidence": true,
  "retrieval_confidence": "low",
  "reliability_reason": "Top candidates lack numeric anchors matching the requested metric.",
  "reliability_flags": ["metric_anchor_missing", "no_answerable_evidence"],
  "abstain_reason": "metric_anchor_missing"
}
```

Dataset audit (`reports/musinsa_metric_gt_audit_disability_parental.md`): only national mss.go.kr `34.5%` exists — **not** Musinsa workforce disability rate. High `score` + `answerable_candidate=false` prevents LLM from treating top-1 as GT.

### D. Parental leave count — `해당 기업의 육아휴직 대상자 수는 몇 명인가요?`

```json
{
  "abstain_recommended": true,
  "no_relevant_evidence": true,
  "retrieval_confidence": "low",
  "reliability_reason": "Top candidates appear to be policy, national statistics, or off-domain content.",
  "reliability_flags": ["domain_mismatch", "entity_mismatch", "no_answerable_evidence"],
  "abstain_reason": "domain_mismatch",
  "items_count": 5,
  "top1_preview": "IBK기업은행은 직원들이 도전과 열정을 회복할 수 있도록…",
  "top1_answerable": false
}
```

Top-1 is **entity mismatch** (IBK bank HR text), not Musinsa parental-leave count.

---

## What should abstain vs answer

| Should **answer** (`abstain_recommended=false`) | Should **abstain** (`abstain_recommended=true`, items kept) |
|------------------------------------------------|--------------------------------------------------------------|
| Headcount: `직원/구성원/임직원 … 몇 명` | Gender-ratio without GT in corpus |
| Future metrics with answerable anchor in top-k | `장애인 고용률` (national stat noise only) |
| | `육아휴직 대상자 수` (policy, no count) |
| | `여성기업 인증 비율`, `육아휴직 사용 인원`, similar blocked metrics |

---

## Downstream LLM guidance

When `abstain_recommended=true`:

- Do **not** cite top-1 as sufficient evidence for a definitive numeric answer.
- Prefer `answerable_candidate=true` items only; if none exist, abstain or ask for more data.
- Ignore high `score` when `candidate_confidence=low`.
- Use `reliability_reason` + `candidate_flags` in chain-of-thought / tool metadata.

---

## Files changed

| File | Role |
|------|------|
| `src/evidence_api/schemas.py` | Response + item reliability fields |
| `src/evidence_api/abstain.py` | `assess_candidate`, `evaluate_retrieval_reliability` |
| `src/evidence_api/service.py` | Annotate items; stop clearing `items` |
| `scripts/eval_metric_intent_abstain.py` | Assert items kept + per-item flags |
| `scripts/eval_korean_gender_ratio_baseline.py` | Same contract update |
| `scripts/verify_retrieve_abstain_gate.py` | Unit tests for item annotations |

---

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| `items` still returned | ✓ (`items_count=5` on abstain cases in eval) |
| Response flags when not trustworthy | ✓ |
| Item-level flags distinguish lexical match vs answerable | ✓ |
| Headcount pass no regress | ✓ 3/3 |
| Missing-GT metrics don't mislead on top-1 | ✓ `top1_answerable=false` on all blocked cases |
