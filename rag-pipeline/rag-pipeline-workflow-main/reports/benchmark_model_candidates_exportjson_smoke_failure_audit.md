# Model Candidate Failure Audit

Ngay: 2026-05-28T21:08:16

## Model prefetch

| model | status |
|---|---|
| `sentence-transformers/all-MiniLM-L6-v2` | cached_ok |

## Case status

| config_id | status | error_code | error_reason |
|---|---|---|---|
| `smoke_nexteye_minilm_dense_chroma` | success |  |  |
| `smoke_nexteye_minilm_hybrid_chroma` | success |  |  |

## Sample questions (per config)

### `smoke_nexteye_minilm_dense_chroma`

- **CE-J01**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl']
  - diagnosis: ok
- **CE-J02**: hit=False cit=False
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: []
  - diagnosis: source_alias_issue
- **CE-J03**: hit=False cit=False
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: []
  - diagnosis: source_alias_issue
- **CE-J04**: hit=False cit=False
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: []
  - diagnosis: source_alias_issue
- **CE-J05**: hit=False cit=False
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: []
  - diagnosis: source_alias_issue

### `smoke_nexteye_minilm_hybrid_chroma`

- **CE-J01**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J02**: hit=False cit=False
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: source_alias_issue
- **CE-J03**: hit=False cit=False
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: source_alias_issue
- **CE-J04**: hit=False cit=False
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: source_alias_issue
- **CE-J05**: hit=False cit=False
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - top: ['data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: source_alias_issue
