# Model Candidate Failure Audit

Ngay: 2026-06-10T10:14:13

## Model prefetch

| model | status |
|---|---|

## Case status

| config_id | status | error_code | error_reason |
|---|---|---|---|
| `openai_hybrid_qdrant_none_gate` | success |  |  |
| `openai_hybrid_qdrant_flashrank_gate` | success |  |  |

## Sample questions (per config)

### `openai_hybrid_qdrant_none_gate`

- **CE-HS01**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manif`
  - normalized_expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manif`
  - normalized_top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manifest.json', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manifest.json', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/splits/full.jsonl', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\manifest.json', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\manifest.json', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl']
  - diagnosis: ok
- **CE-HS02**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/recor`
  - normalized_expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/recor`
  - normalized_top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manifest.json']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/splits/full.jsonl', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\manifest.json']
  - diagnosis: ok
- **CE-HS03**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/recor`
  - normalized_expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/recor`
  - normalized_top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/splits/full.jsonl']
  - diagnosis: ok
- **CE-HS04**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manif`
  - normalized_expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manif`
  - normalized_top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manifest.json', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manifest.json', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manifest.json', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\manifest.json', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/splits/full.jsonl', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl']
  - diagnosis: ok
- **CE-HS05**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manif`
  - normalized_expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manif`
  - normalized_top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manifest.json', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manifest.json', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/splits/full.jsonl', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\manifest.json', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\manifest.json', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl']
  - diagnosis: ok

### `openai_hybrid_qdrant_flashrank_gate`

- **CE-HS01**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manif`
  - normalized_expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manif`
  - normalized_top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl']
  - diagnosis: ok
- **CE-HS02**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/recor`
  - normalized_expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/recor`
  - normalized_top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/splits/full.jsonl', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl']
  - diagnosis: ok
- **CE-HS03**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/recor`
  - normalized_expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/recor`
  - normalized_top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/splits/full.jsonl']
  - diagnosis: ok
- **CE-HS04**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manif`
  - normalized_expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manif`
  - normalized_top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manifest.json', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manifest.json', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manifest.json', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\manifest.json', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/splits/full.jsonl', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl']
  - diagnosis: ok
- **CE-HS05**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/manif`
  - normalized_expected: `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manif`
  - normalized_top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/manifest.json', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl', 'data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608t042739/splits/full.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/splits/full.jsonl', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\manifest.json', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl', 'data\\rag_dataset\\05_company_export_json\\한샘_dataset_package_20260608T042739\\splits\\full.jsonl']
  - diagnosis: ok
