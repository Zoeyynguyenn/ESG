# Musinsa metric GT audit — disability employment rate & parental leave

**Date:** 2026-06-11  
**Package:** `무신사_dataset_package_20260608T092823` / `splits/full.jsonl`  
**Method:** Direct file scan (no retrieve API)

---

## Summary

| Metric query | Classification | Musinsa-specific GT? |
|--------------|----------------|---------------------|
| `장애인 고용률` (% ) | **not_present** (weak national noise only) | No |
| `육아휴직 대상자 수` (count) | **not_present** (policy text only) | No |

Both should **abstain** under metric-intent gate.

---

## 1. 장애인 고용률 (`해당 기업의 장애인 고용률은 몇 %인가요?`)

### Package scan

| Pattern | Hits in `full.jsonl` | Musinsa workforce rate? |
|---------|----------------------|-------------------------|
| `장애인` (any) | 80+ rows | Mostly national policy / CSR / mss.go.kr |
| `장애인 고용률` + `%` | 1 row (`rec_6e3a25d516794aef`) | **No** — national stats |
| `무신사` + `장애인` + `고용률` + `%` | **0** | — |

### Canonical false-positive snippet

**record:** `rec_6e3a25d516794aef`  
**source:** `mss.go.kr` PDF (not ETNews / company report)  
**text:** *우리나라 장애인은 2024년 말… 장애인 고용률은 **34.5%**로 전체 인구 63.3%…*

This is **national aggregate statistics**, not Musinsa company disability employment rate.

### Other `장애인` mentions

- `장애인기업제품` public procurement tables
- CSR: “장애인을 위한 정형 신발” (무신사 ESG narrative)
- Press: “장애인고용공단 MOU” (partnership, no rate)

**Classification:** `weak_or_derived_only` at best; for API purposes **`not_present`** as answerable company metric.

---

## 2. 육아휴직 대상자 수 (`해당 기업의 육아휴직 대상자 수는 몇 명인가요?`)

### Package scan

| Pattern | Hits | Numeric 대상자 count? |
|---------|------|------------------------|
| `육아휴직` | 1 row (`rec_75fb5d7b5cf54826`) | **No number** |
| `육아휴직` + `대상자` + digit | **0** | — |

### Snippet (policy only)

**record:** `rec_75fb5d7b5cf54826`  
**source:** `mss.go.kr` (embedded in Musinsa package noise)  
**text:** *다자녀 직원 대상 육아휴직 호봉 인정 기준을 확대하고, 5세 이하 육아기 단축근무 제도를 운영…*

Describes **HR policy**, not “대상자 수 = N명”.

**Classification:** **`not_present`**

---

## Gate implication

| Metric | Expected API behavior |
|--------|----------------------|
| 장애인 고용률 | `abstain_recommended=true`, `items=[]` |
| 육아휴직 대상자 수 | `abstain_recommended=true`, `items=[]` |
| Headcount (1891명) | **No abstain** — separate bypass |

No corpus changes required.
