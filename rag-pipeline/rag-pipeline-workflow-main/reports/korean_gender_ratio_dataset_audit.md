# Musinsa gender-ratio — direct dataset audit

**Date:** 2026-06-05  
**Method:** Direct search on package files — **not** retrieve API output  
**Package:** `data/rag_dataset/05_company_export_json/무신사_dataset_package_20260608T092823`  
**Indexed corpus for LangGraph:** `splits/full.jsonl` only (`company_evidence`, 1604 records)

---

## Executive classification

| Question | Classification |
|----------|----------------|
| Male/female **workforce ratio %** answer in indexed corpus? | **`not_present` (C)** |
| Any clean GT in package at all? | **`weak_or_derived_only` (B)** — taxonomy/AI lane only, no numeric value |
| API retrieve “wrong” vs “no answer exists”? | **No correct answer exists in indexed data** → API returning top-1 noise is **misleading**, not “correct retrieval miss” |

---

## Files audited

| Path | Role | Gender-ratio workforce GT? |
|------|------|---------------------------|
| `splits/full.jsonl` | **Indexed** (staging prebuild) | **No clean GT** |
| `lanes/company_evidence.jsonl` | Same records as full | **No clean GT** |
| `lanes/ai_extracted_response.jsonl` | Derived, **not indexed** | Taxonomy labels only, `value=null` |
| `lanes/requirement_taxonomy.jsonl` | Requirement definitions | Not evidence |
| `records/*.jsonl` | Mirrors lanes | Same as above |
| `_sources/*.pdf` | Raw sources | Large file = `mss.go.kr` SME annual report; no Musinsa HR gender % found in extract |
| `manifest.json` | `full` = 1604 `company_evidence` only | Confirms AI lane not in index |

---

## Search results — indexed (`splits/full.jsonl`)

| Pattern | Hits | Usable GT? |
|---------|------|------------|
| `남성 비율` | **0** | — |
| `여성 비율` | **1** | **No** — `rec_b4abdc1b60ee637c`, national table `여성비율(47.0)(46.3)…`, `mss.go.kr` |
| `여성 구성원` / `남성 구성원` | **0** | — |
| `구성원 현황` + gender % | **0** | — |
| `여성 임직원` + % | **1** | **No** — `rec_f6039aa0310e470b`, **IBK기업은행** 여성임직원 비율, `mss.go.kr` PDF |
| `여성 패션` + 50% | **2** | **No** — customer GMV segment, not workforce |

**Indexed split composition:** 1113 `mss.go.kr` chunks / 491 non-mss — heavy government PDF noise.

---

## False positives (must not treat as GT)

| record_id | Snippet / reason | Class |
|-----------|------------------|-------|
| `rec_b4abdc1b60ee637c` | `여성비율(47.0)…` national tech-industry stats | Policy / national stats |
| `rec_f6039aa0310e470b` | `디지털·IT 등 분야 여성임직원 비율` — **IBK bank**, not 무신사 | Wrong entity |
| `rec_8baa5d754675ed1b` | `여성 패션 잡화 거래액 50%` | Customer segment |
| `rec_86c5365947ea0354` | UI form text `여성 남성` comment fields | UI noise |
| Various | `여성기업`, procurement policy | Government SME policy |

---

## Derived lane (`ai_extracted_response.jsonl`) — class B only

52+ records mention gender / `구성원 현황 / 성별`:

| Example record_id | Requirement | Value in record | Supporting evidence |
|-------------------|-------------|-----------------|---------------------|
| `rec_3edb9ead915e3a91` | `구성원 현황 / 성별 / 남성` | **None** (`metric: null`) | Points to `rec_310f5fbc91f32137` → **mss 방역물품 table**, not HR gender |
| `rec_68b7a2ba38c86c6a` | `구성원 현황 / 성별 / 여성` | **None** | Same wrong mss chunks |
| `rec_56d542f92d7498b0` | `다양성 / 여성 구성원 비율` | **None** (metadata scores only) | `supporting_evidence` → mss.go.kr, not Impact Report body |

**Conclusion:** Derived lane is **requirement/taxonomy scaffolding**, not verified source evidence with answer values. **Not indexed** by LangGraph staging.

---

## Golden set (repo cross-check)

`data/golden_set/golden_answer_fill_preliminary_ko_20260609.csv` — 무신사 **QT-002** (여성 구성원 비율):

> `fill_status=dataset_issue` — sustainability pages not usable as gold-answer evidence.

---

## Answers (Part 2)

### 1. Hai câu `남성 비율 / 여성 비율` có đáp án thật trong package hiện tại không?

**Không** — trong **indexed corpus** không có evidence Musinsa workforce male/female % có thể dùng làm GT.

### 2. Nếu có, ở đâu?

**N/A.** Không có `clean_gt_present`. Chỉ có:
- **(B)** `ai_extracted_response.jsonl` — label không số, supporting evidence sai domain
- False positives trong indexed noise (mss, IBK, UI, GMV segment)

### 3. API hiện tại có “đúng theo dữ liệu” không?

**Một nửa đúng, một nửa sai:**

| Khía cạnh | Đánh giá |
|-----------|----------|
| Không thể trả **đáp án đúng** | **Đúng** — vì GT không tồn tại trong indexed evidence |
| Trả **top-1 như evidence tốt** (UI form, noise) | **Sai UX** — thiếu abstain; gây hiểu nhầm là có evidence |

→ Vấn đề chính sau audit: **`abstain / no-relevant-evidence gate`**, không phải retrieval tuning cho gender-ratio.

---

## Distinction summary

```
A. clean_gt_present          → 0 records
B. weak_or_derived_only      → ai_extracted + taxonomy (no values, wrong supporting refs)
C. not_present (indexed)     → workforce gender % for Musinsa
```
