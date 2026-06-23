# Handover Swagger Retrieve cho Team LangGraph

Ngay cap nhat: 2026-06-12

## 1. Muc dich

Tai lieu nay dung de gui cho team LangGraph khi team chi dung Swagger de goi API `POST /retrieve`.

Muc tieu:

1. Giai thich API hien tra ve gi.
2. Giai thich cach doc dung ket qua retrieve.
3. Giai thich khi nao phai xem ket qua la **khong dang tin**.
4. Giai thich neu team muon generate answer bang LLM thi can them guard nao.

## 2. Trang thai hien tai

API `retrieve` hien da co 3 lop bao ve:

1. Index/runtime parity da dong bo lai.
2. Retrieve response co them cac co `reliability`.
3. Da co module `generation_guard` de chan LLM tra loi sai khi evidence khong dang tin.

Luu y:

- Swagger chi giup team goi `POST /retrieve`.
- Swagger **khong tu dong** goi `generation_guard`.
- Neu team tu doc raw JSON va dua thang `items` vao LLM, LLM van co the tra loi sai.

## 3. Endpoint can dung

Swagger:

- `http://127.0.0.1:8787/docs`

Endpoint chinh:

- `POST /retrieve`

Body toi thieu:

```json
{
  "query": "해당 기업의 총 구성원 수는 몇 명인가요?",
  "company_id": "musinsa",
  "top_k": 8
}
```

## 4. Response moi can doc nhu the nao

Response hien co:

```json
{
  "items": [...],
  "company_id": "musinsa",
  "query": "...",
  "abstain_recommended": false,
  "no_relevant_evidence": false,
  "retrieval_confidence": "high",
  "reliability_reason": null,
  "reliability_flags": [],
  "abstain_reason": null
}
```

Moi `item` co them:

```json
{
  "text": "...",
  "source": "...",
  "score": 0.92,
  "confidence": "high",
  "metric_name": "...",
  "value": "...",
  "unit": "...",
  "record_id": "...",
  "answerable_candidate": false,
  "candidate_confidence": "low",
  "candidate_flags": [
    "metric_anchor_missing",
    "domain_mismatch"
  ]
}
```

## 5. Cach doc dung response

### 5.1 `score` khong dong nghia voi "dap an dung"

`score` chi la retrieval/rerank score.

`score` **khong** co nghia:

- chunk do la ground truth
- chunk do dung metric
- chunk do dung cong ty

Vi vay, khong duoc chi nhin `score` cao de ket luan LLM co the tra loi.

### 5.2 Chi can quan tam 3 field o response level

1. `abstain_recommended`
2. `no_relevant_evidence`
3. `retrieval_confidence`

Neu:

- `abstain_recommended=true`
- hoac `no_relevant_evidence=true`
- hoac `retrieval_confidence=low`

thi phai hieu la:

- retrieve co the da tim ra mot so chunk lien quan be mat
- nhung **khong co evidence dang tin de tra loi**

### 5.3 O item level, chi tin item nao co:

- `answerable_candidate=true`

Neu `answerable_candidate=false`, thi item do chi la candidate retrieve, khong nen dung de sinh answer so.

## 6. Cac tinh huong can hieu dung

### Truong hop A: Co evidence dung

Vi du:

- query: `해당 기업의 총 구성원 수는 몇 명인가요?`

Ky vong:

- `abstain_recommended=false`
- co it nhat 1 item `answerable_candidate=true`
- top evidence co `1891명`

### Truong hop B: Khong co evidence dung trong indexed corpus

Vi du:

- `해당 기업의 남성 비율은 몇 %인가요?`
- `해당 기업의 여성 비율은 몇 %인가요?`
- `해당 기업의 장애인 고용률은 몇 %인가요?`
- `해당 기업의 육아휴직 대상자 수는 몇 명인가요?`

Ky vong:

- `abstain_recommended=true`
- `no_relevant_evidence=true`
- `retrieval_confidence=low`

Luu y:

- API van co the tra ve `items`
- nhung day **khong** phai la evidence co the tin de tra loi

## 7. Team LangGraph can lam gi neu chi dung Swagger

Neu team chi test bang Swagger, hay dung quy tac sau:

### Quy tac 1

Neu `abstain_recommended=true` thi xem nhu:

- "Corpus hien tai khong co evidence dang tin cho cau hoi nay"

Khong duoc coi top-1 la dap an.

### Quy tac 2

Neu tat ca `items[].answerable_candidate=false` thi xem nhu:

- "Khong co evidence co the dung de answer"

### Quy tac 3

Khong duoc dua:

- `score`
- `confidence`
- `value`
- `metric_name`

cua item `answerable_candidate=false` vao LLM de sinh answer.

## 8. Neu team muon generate answer bang LLM

Team can them guard o generation layer.

Module da co san:

Duong dan that:

- [src/evidence_api/generation_guard.py](E:/Documents/rag-pipeline-workflow/src/evidence_api/generation_guard.py)

Ham can dung:

- `resolve_answer(resp, query, company_display=..., llm_generate=...)`

Logic:

1. Neu `abstain_recommended=true` -> khong goi LLM, tra template abstain.
2. Neu khong co item `answerable_candidate=true` -> khong goi LLM, tra template abstain.
3. Neu co answerable items -> chi dua cac item do vao context cho LLM.

## 9. Template abstain hien tai

```text
{query}에 대한 신뢰할 수 있는 수치 근거를 찾지 못했습니다.
```

## 10. Snippet tich hop toi thieu

```python
from evidence_api.generation_guard import resolve_answer

resp = retrieve_resp  # JSON da parse thanh object/schema

out = resolve_answer(
    resp,
    query,
    company_display="무신사",
    llm_generate=your_llm_fn,
)

if out.abstained:
    return out.answer

return out.answer
```

## 11. Cach phan loai loi khi test

Khi team LangGraph test, de nghi ghi lai theo 4 nhom:

1. `pass_dung`
2. `correct_abstain`
3. `should_answer_but_abstained`
4. `should_abstain_but_returned_noise`

## 12. 4 query mau de test nhanh

### Query nen answer

```json
{
  "query": "해당 기업의 총 구성원 수는 몇 명인가요?",
  "company_id": "musinsa",
  "top_k": 8
}
```

### Query nen abstain

```json
{
  "query": "해당 기업의 남성 비율은 몇 %인가요?",
  "company_id": "musinsa",
  "top_k": 8
}
```

```json
{
  "query": "해당 기업의 여성 비율은 몇 %인가요?",
  "company_id": "musinsa",
  "top_k": 8
}
```

```json
{
  "query": "해당 기업의 장애인 고용률은 몇 %인가요?",
  "company_id": "musinsa",
  "top_k": 8
}
```

## 13. Dieu can nho nhat

`items` la ket qua retrieve.

`items` **khong tu dong co nghia** la:

- answerable evidence
- ground truth
- co the dua vao LLM de tra loi

Quyet dinh dung/khong dung de answer phai dua tren:

- `abstain_recommended`
- `no_relevant_evidence`
- `retrieval_confidence`
- `answerable_candidate`

## 14. Trang thai handoff

Retrieve layer hien co the xem la tam on cho:

1. Query co GT that su trong indexed corpus
2. Query khong co GT, nhung can bao abstain

Phan team LangGraph can bo sung them:

1. Goi `resolve_answer()` sau `/retrieve`
2. Khong cho LLM doc item noise
3. Tuan thu cac co `abstain` va `answerable_candidate`
