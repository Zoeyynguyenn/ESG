# Model Candidate Failure Audit

Ngay: 2026-05-29T10:04:07

## Model prefetch

| model | status |
|---|---|
| `openai:text-embedding-3-small` | api_model_skip_prefetch |

## Case status

| config_id | status | error_code | error_reason |
|---|---|---|---|
| `smoke_openai_rec800_dense_chroma` | success |  |  |
| `smoke_openai_rec800_hybrid_chroma` | success |  |  |

## Sample questions (per config)

### `smoke_openai_rec800_dense_chroma`

- **CE-J01**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl']
  - diagnosis: ok
- **CE-J02**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl']
  - diagnosis: ok
- **CE-J03**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl']
  - diagnosis: ok
- **CE-J04**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl']
  - diagnosis: ok
- **CE-J05**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl']
  - diagnosis: ok

### `smoke_openai_rec800_hybrid_chroma`

- **CE-J01**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J02**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J03**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J04**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J05**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
