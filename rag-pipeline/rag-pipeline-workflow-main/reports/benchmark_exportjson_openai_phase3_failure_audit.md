# Model Candidate Failure Audit

Ngay: 2026-05-29T10:39:35

## Model prefetch

| model | status |
|---|---|
| `openai:text-embedding-3-small` | api_model_skip_prefetch |

## Case status

| config_id | status | error_code | error_reason |
|---|---|---|---|
| `p3_openai_section_hybrid_chroma` | success |  |  |
| `p3_openai_section_hybrid_qdrant` | success |  |  |
| `p3_openai_section_dense_chroma` | success |  |  |
| `p3_openai_section_dense_qdrant` | success |  |  |
| `p3_openai_rec800_hybrid_chroma` | success |  |  |
| `p3_openai_rec800_hybrid_qdrant` | success |  |  |

## Sample questions (per config)

### `p3_openai_section_hybrid_chroma`

- **CE-J01**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J02**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J03**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J04**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J05**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok

### `p3_openai_section_hybrid_qdrant`

- **CE-J01**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J02**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J03**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J04**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J05**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok

### `p3_openai_section_dense_chroma`

- **CE-J01**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl']
  - diagnosis: ok
- **CE-J02**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl']
  - diagnosis: ok
- **CE-J03**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl']
  - diagnosis: ok
- **CE-J04**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl']
  - diagnosis: ok
- **CE-J05**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl']
  - diagnosis: ok

### `p3_openai_section_dense_qdrant`

- **CE-J01**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl']
  - diagnosis: ok
- **CE-J02**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl']
  - diagnosis: ok
- **CE-J03**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl']
  - diagnosis: ok
- **CE-J04**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl']
  - diagnosis: ok
- **CE-J05**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl']
  - diagnosis: ok

### `p3_openai_rec800_hybrid_chroma`

- **CE-J01**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J02**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J03**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J04**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J05**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok

### `p3_openai_rec800_hybrid_qdrant`

- **CE-J01**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J02**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J03**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J04**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
- **CE-J05**: hit=True cit=True
  - expected: `data/rag_dataset/05_company_export_json/ë„¥ìŠ¤íŠ¸ì•„ì´_dataset_package_20260528`
  - normalized_expected: `data/rag_dataset/05_company_export_json/ë„¥ìš¤íš ̧ì•„ì ́_dataset_package_202605`
  - normalized_top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl', 'data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528t091409/splits/validation.jsonl']
  - match_reason: `package_split_match` | fail_kind: `ok`
  - top: ['data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409/splits/validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl', 'data\\rag_dataset\\05_company_export_json\\넥스트아이_dataset_package_20260528T091409\\splits\\validation.jsonl']
  - diagnosis: ok
