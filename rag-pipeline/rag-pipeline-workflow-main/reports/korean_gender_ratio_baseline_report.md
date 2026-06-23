# Gender-ratio KO retrieval — GT audit & baseline

**Date:** 2026-06-05  
**Company:** musinsa  
**Scope:** Audit + baseline only — **no retrieval code changed**

---

## Part 1 — Ground truth audit

### Indexed corpus (`splits/full.jsonl` → LangGraph staging)

| Target | Result |
|--------|--------|
| Musinsa **workforce male %** | **Not found** in non-noise `company_evidence` |
| Musinsa **workforce female %** | **Not found** in non-noise `company_evidence` |
| `여성 구성원` phrase | **0 chunks** |
| K-ESG `구성원 현황 / 성별 / 남성|여성` | In `lanes/ai_extracted_response.jsonl` only — **no numeric value**, **not indexed** |

### False-positive snippets (must not use as GT)

| Snippet | Why wrong |
|---------|-----------|
| `여성 패션 잡화 거래액 50%` | Customer segment GMV, not workforce ratio |
| `여성비율(47.0)(46.3)…` | National SME stats in `mss.go.kr` PDF noise |
| `여성기업` / `여성기업제품` | Government procurement policy, not Musinsa HR |

### Golden set (repo)

`data/golden_set/golden_answer_fill_preliminary_ko_20260609.csv` — **무신사 QT-002** (여성 구성원 비율):

> `dataset_issue` — sustainability_report records are listing pages, not usable gold-answer evidence.

### Conclusion

**GT status: BLOCKED** for male/female workforce ratio on Musinsa indexed package.  
Cannot define `expected value` + `record_id` without inventing answers.

---

## Part 2 — Baseline API retrieve (2 primary queries)

| Query | Rewritten | Headcount path | Rerank | Top-1 quality |
|-------|-----------|----------------|--------|---------------|
| `해당 기업의 남성 비율은 몇 %인가요?` | `무신사의 남성 비율은 몇 %인가요?` | **No** | `jina_api` | **Wrong** — UI/news noise (`rec_86c5365947ea0354`, comment form “여성 남성”) |
| `해당 기업의 여성 비율은 몇 %인가요?` | `무신사의 여성 비율은 몇 %인가요?` | **No** | `jina_api` | **Wrong** — same noise family |

**Verdict:** API does **not** return a verifiable correct gender-ratio answer — but **correct GT is absent**, so this is **data + retrieval under noise**, not a proven fixable regression without GT.

---

## Part 3 — Failure classification (metric class audit)

| Layer | Observation |
|-------|-------------|
| **Rewrite** | OK — generic `해당 기업` → `무신사의` |
| **Headcount leak** | **Partial** — bare `남성/여성 비율` queries: **no** headcount path. Queries with `임직원`/`구성원` + ratio (e.g. `무신사 임직원 여성 비율`) **incorrectly** trigger headcount path → top-1 headcount/executive chunks, not gender ratio. Fix deferred until GT exists. |
| **Lexical recall** | BM25 has tokens `남성`/`여성`/`비율` but hits **wrong domain** (UI strings, national stats) |
| **Pool / rerank** | Promotes high-frequency gender tokens in noise, not workforce disclosure |
| **Metric ambiguity** | **Primary blocker** — no clean Musinsa workforce gender % in indexed evidence |

This is a **separate `gender-ratio metric class`** from headcount. Headcount patch must **not** be reused here.

---

## Part 4 — Mini regression (8 paraphrases)

All cases marked `gt_status=blocked`. Baseline script records retrieval behavior; **pass/fail not scored** without GT.

Run: `python scripts/eval_korean_gender_ratio_baseline.py`

---

## Part 5 — Patch recommendation

| Question | Answer |
|----------|--------|
| Patch retrieval now? | **No** — blocked on GT |
| Next step | (1) Annotate GT from primary source (Impact Report PDF body) or index `ai_extracted` with verified values; (2) then build `gender-ratio class` with own gate (like headcount) |
| Headcount gate impact | None — gender queries do not trigger headcount path |

---

## Answers to four questions

1. **API đúng cho 2 câu ratio chưa?** — **Không** (top-1 là noise). Không thể xác nhận “đúng số X%” vì **không có GT sạch**.

2. **Lỗi ở đâu?** — Chủ yếu **metric ambiguity / no clean GT**; retrieval kéo chunk có token `남성`/`여성` nhưng **sai domain** (UI, mss.go.kr). Rewrite OK; không phải headcount leak.

3. **GT đủ mở workstream ratio class?** — **Chưa** — blocked (`dataset_issue` + không có workforce % trong indexed evidence).

4. **Patch tiếp ngay?** — **Không** — blocked vì data/GT. Cần GT trước, rồi mới baseline có ý nghĩa và mới đề xuất `gender-ratio retrieval patch`.
