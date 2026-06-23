# Retrieve API — abstain / no-relevant-evidence gate (design)

**Date:** 2026-06-05  
**Trigger:** Gender-ratio audit → no answer in indexed Musinsa corpus  
**Constraint:** Design only — no schema change committed yet; no retrieval patch before GT exists

---

## Problem statement

When no answerable evidence exists, retrieve still returns `items[0..k]` with non-trivial scores. Downstream (LangGraph) may treat top-1 as usable evidence.

**Observed on gender-ratio queries:**
- Top-1: UI comment form (`여성 남성` widgets)
- Top-3: `여성기업` policy (mss.go.kr), unrelated news %

This is **worse than empty**: implies relevance where none exists.

---

## Design goal

Distinguish:

| State | Meaning |
|-------|---------|
| `retrieval_found_on_topic` | Chunks share query tokens / domain |
| `retrieval_found_answerable_evidence` | Chunks contain metric anchor + value matching query intent |

Gate should fire when **on-topic-ish hits exist but answerable evidence does not**.

---

## Option A — Conservative (`items=[]`)

**Behavior:** If gate triggers → `RetrieveResponse.items = []` (same schema).

**Pros:** Simple for LangGraph — empty list = no evidence  
**Cons:** Loses diagnostic chunks; no score/debug trail in response

**When to use:** Production default if downstream only needs binary “có/không evidence”

---

## Option B — Richer (recommended for staging handoff)

**Behavior:** Return items optionally, plus **response-level flags** (requires schema extension):

```json
{
  "items": [...],
  "company_id": "musinsa",
  "query": "...",
  "abstain_recommended": true,
  "no_relevant_evidence": true,
  "retrieval_confidence": "low",
  "abstain_reason": "metric_anchor_missing"
}
```

**Pros:** Debuggable; LangGraph can branch on flag while still inspecting top chunks  
**Cons:** Schema + client update

**Staging compromise (no schema change yet):** Log gate decision server-side; set all `items[].confidence = "low"` + document convention in handoff doc until schema v2.

---

## Proposed gate signals (deterministic, auditable)

### G1 — Metric anchor mismatch (ratio / % queries)

If query matches **ratio intent**:

```regex
(남성|여성|남녀).{0,12}(비율|구성|비중|성비)|%\s*인가|퍼센트
```

Then top-k chunks must contain **both**:
- gender anchor (`남성` or `여성` as query asks)
- `%` or `퍼센트` or `비율` **near** a number in same sentence/window

If top-3 fail → `abstain_reason=metric_anchor_missing`

### G2 — Domain mismatch patterns

Penalize / veto if top-1 source or text matches:

| Pattern | Reason |
|---------|--------|
| `mss.go.kr` + no company name in chunk | National SME noise |
| `여성기업` without workforce context | Procurement policy |
| `여성 패션` / `거래액` | Customer GMV |
| `댓글` / `퀴즈` / `0 / 300 등록` | UI scrape |
| Entity mismatch (e.g. `IBK기업은행` for `musinsa` query) | Wrong company |

### G3 — Score distribution

If `top1.score - top3.score < ε` and no chunk passes G1 → low separation, likely noise pile.

If all hybrid scores below floor **and** G1 fails → abstain.

### G4 — Catalog / record metadata

If `record_id` resolves but:
- `metric` absent
- `source_type` not in trusted set
- `source_url` contains `mss.go.kr` for company-scoped HR metric query

→ contribute to abstain score (not sole trigger).

### G5 — Headcount vs ratio class guard

Do **not** treat headcount path success as ratio success. Ratio queries must pass G1 independently.

---

## Gate decision logic (pseudo)

```
signals = []
if ratio_query(q):
    if not any(chunk_passes_metric_anchor(c, q) for c in top3):
        signals.append("metric_anchor_missing")
if any(domain_mismatch(c) for c in top3):
    signals.append("domain_mismatch")
if top1_confidence == "low" and len(signals) >= 1:
    abstain_recommended = True

# Strong abstain: metric_anchor_missing AND domain_mismatch in top1
if "metric_anchor_missing" in signals and domain_mismatch(top1):
    no_relevant_evidence = True
```

---

## What API should return when no correct evidence (gender-ratio case)

| Approach | Response |
|----------|----------|
| **Minimum viable** | `items=[]` + HTTP 200 |
| **Recommended staging** | `items=[]` OR items with `abstain_recommended=true`, `no_relevant_evidence=true`, `retrieval_confidence=low` |
| **Must not** | Top-1 UI/policy chunk presented as `confidence: medium/high` without flag |

---

## Implementation phasing (no retrieval tuning)

| Phase | Work |
|-------|------|
| **P0** | `abstain_eval` script on gender-ratio + headcount sanity — measure false abstain on headcount gate |
| **P1** | `evidence_api/abstain.py` — deterministic signals G1–G2 |
| **P2** | Wire in `service.retrieve()` after ranking, before response |
| **P3** | Schema v2 optional fields OR handoff doc convention |
| **Blocked** | Gender-ratio **retrieval patch** until GT ingested into indexed lane |

---

## Evaluation plan

| Suite | Expectation after gate |
|-------|------------------------|
| Musinsa gender-ratio 2 primary queries | `abstain` or `items=[]` |
| Musinsa headcount regression 16 | **No abstain** (must not regress headcount patch) |
| Musinsa headcount holdout 14 | **No abstain** |
| Queries with real metric in corpus (future GT) | Gate **open** when G1 passes |

---

## Recommended option

**Option B (richer)** for LangGraph handoff — flags explicit for agent routing.  
**Option A** acceptable if LangGraph already treats `items=[]` as sole signal.

**Priority signals:** G1 (metric anchor) + G2 (domain mismatch) — sufficient for gender-ratio case without hardcoding Musinsa.
