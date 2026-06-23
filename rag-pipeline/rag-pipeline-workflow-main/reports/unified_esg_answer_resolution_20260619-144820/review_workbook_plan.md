# Unified ESG review workbook plan

Artifact: `reports/unified_esg_answer_resolution_20260619-144820`

## Nguyên tắc

- **Không ghi đè** Excel workbook gốc (`이엠앤아이_Final_ESG_Data.xlsx`, v.v.)
- **Không sửa** `results.jsonl` frozen RAG eval
- Xuất artifact review riêng: `unified_esg_review.xlsx` + `unified_answers.jsonl`

## Sheets

| Sheet | Nội dung |
|---|---|
| `all_unified` | Toàn bộ records hợp nhất |
| `MATCH_CONFIRMED` | Dataset + internal-doc khớp — auto-confirm |
| `BACKFILL_INTERNAL` | Internal-doc bổ sung khi dataset thiếu |
| `BACKFILL_DATASET` | Dataset/public source khi internal thiếu |
| `CONFLICT_REVIEW` | Conflict — SME review |
| `NO_ANSWER` | Không có đáp án / insufficient evidence |

## Input sources

{
  "dataset_results_path": "reports/goldns_emni_rag_eval_20260618-100003/results.jsonl",
  "internal_records_path": "reports/enterprise_docs_structured_esg_hardening_20260619-090700/structured_esg_records.jsonl",
  "dataset_row_count": 530,
  "internal_row_count": 36,
  "unified_row_count": 566,
  "join_by_question_id": 566,
  "join_by_business_key_only": 0
}

## Status breakdown

{
  "NO_ANSWER_FOUND": 480,
  "BACKFILL_FROM_DATASET": 67,
  "BACKFILL_FROM_INTERNAL": 19
}

## Workflow review

1. Mở sheet `CONFLICT_REVIEW` trước — assign SME
2. `BACKFILL_INTERNAL` với `auto_confirm=false` — RAG/SME xác nhận candidate
3. `MATCH_CONFIRMED` — audit spot-check, không cần sửa Excel gốc
4. `NO_ANSWER` — quyết định bổ sung source (corpus_limited) hay chấp nhận abstain
