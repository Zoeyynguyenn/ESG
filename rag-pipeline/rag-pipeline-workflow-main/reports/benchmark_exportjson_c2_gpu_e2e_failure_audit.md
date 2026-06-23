# Model Candidate Failure Audit

Ngay: 2026-06-04T08:59:37

## Model prefetch

| model | status |
|---|---|
| `openai:text-embedding-3-small` | api_model_skip_prefetch |

## Case status

| config_id | status | error_code | error_reason |
|---|---|---|---|
| `c2_gpu_hybrid_qdrant_generative` | success |  |  |

## Sample questions (per config)

### `c2_gpu_hybrid_qdrant_generative`

- **CE-J01**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/sp`
  - normalized_expected: `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/sp`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/full.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl']
  - diagnosis: ok
- **CE-J02**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/sp`
  - normalized_expected: `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/sp`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/full.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl']
  - diagnosis: ok
- **CE-J03**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/sp`
  - normalized_expected: `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/sp`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/full.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/full.jsonl']
  - diagnosis: ok
- **CE-J04**: hit=False cit=False
  - expected: `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/sp`
  - normalized_expected: `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/sp`
  - normalized_top: []
  - match_reason: `no_match` | fail_kind: `retrieval_miss`
  - top: []
  - diagnosis: retrieval_miss
- **CE-J05**: hit=False cit=False
  - expected: `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/sp`
  - normalized_expected: `data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/sp`
  - normalized_top: []
  - match_reason: `no_match` | fail_kind: `retrieval_miss`
  - top: []
  - diagnosis: retrieval_miss
