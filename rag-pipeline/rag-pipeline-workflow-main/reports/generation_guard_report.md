# Generation guard — downstream deterministic abstain

**Date:** 2026-06-11  
**Scope:** Client/generation layer only — **no retrieve/index changes**  
**Test:** `scripts/verify_generation_guard.py` (unit + integration)

---

## Problem

Retrieve API returns reliability flags, but raw `items` still contain misleading fields (`score`, `confidence`, `value`, `metric_name`) that can make an LLM answer incorrectly (e.g. `80.4%` for `장애인 고용률`).

## Solution

New module `src/evidence_api/generation_guard.py` — call **after** `POST /retrieve`, **before** LLM.

### Flow (before → after)

```
Before:
  /retrieve → pass all items + scores to LLM → risk wrong numeric answer

After:
  /retrieve → resolve_answer(resp, query, llm_generate=...)
                ├─ should_abstain? → Korean template (no LLM)
                └─ else → only answerable_candidate=true items → build_safe_context → LLM
```

### Rules (deterministic)

| Condition | Action |
|-----------|--------|
| `abstain_recommended=true` | Abstain template, **no LLM** |
| No `answerable_candidate=true` in items | Abstain template, **no LLM** |
| Has answerable items | `build_safe_context()` → optional LLM |

### Abstain template

```
{query}에 대한 신뢰할 수 있는 수치 근거를 찾지 못했습니다.
```

Example: `해당 기업의 장애인 고용률은 몇 %인가요?에 대한 신뢰할 수 있는 수치 근거를 찾지 못했습니다.`

### Prompt safety

- Only items with `answerable_candidate=true` enter context
- **Excluded from prompt:** `score`, `confidence`, `evidence_type`
- **Included (answerable only):** `text`, `source`, `record_id`, `page`, `section_path`, `candidate_confidence`, `metric_name`, `value`, `unit`

---

## LangGraph integration (snippet)

```python
from evidence_api.generation_guard import resolve_answer
from evidence_api.schemas import RetrieveRequest
from evidence_api.service import EvidenceRetrievalService

svc = EvidenceRetrievalService()
resp = svc.retrieve(RetrieveRequest(query=query, company_id="musinsa", top_k=8))

out = resolve_answer(
    resp,
    query,
    company_display="무신사",
    llm_generate=your_llm_fn,  # (context, question) -> str
)

if out.abstained:
    return out.answer  # deterministic Korean — do not call LLM elsewhere
return out.answer
```

---

## Test results

| Group | Query | Expected | Result |
|-------|-------|----------|--------|
| **HC** headcount | `무신사의 직원 수는 몇 명인가요?` | Answer path, LLM called once | ✓ |
| **GR** gender-ratio | `해당 기업의 여성 비율은 몇 %인가요?` | Abstain, no LLM | ✓ |
| **BM** disability | `해당 기업의 장애인 고용률은 몇 %인가요?` | Abstain, no `80.4%` | ✓ |
| **BM** parental | `해당 기업의 육아휴직 대상자 수는 몇 명인가요?` | Abstain, no LLM | ✓ |

Unit tests also verify: non-answerable `value`/`score` never reach LLM context.

---

## Files

| File | Change |
|------|--------|
| `src/evidence_api/generation_guard.py` | **New** — guard + safe context builder |
| `scripts/verify_generation_guard.py` | **New** — unit + integration tests |

Retrieve layer unchanged.

---

## Follow-up (optional, not done)

- Rename legacy `confidence` → `record_quality` on `EvidenceItem` to reduce confusion
- Wire `resolve_answer` into LangGraph graph node when generation endpoint is added
