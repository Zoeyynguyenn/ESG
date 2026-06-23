# Unified ESG answer resolution

Artifact: `reports/unified_esg_answer_resolution_20260619-144820`

## Câu trả lời bắt buộc

{
  "1_business_key_mapping": {
    "answer": "Ưu tiên join theo question_id khi cả hai nguồn có; fallback business_key = company_id::family_id::metric_name_norm::year. Dataset family map qua FAMILY_ALIASES (employee_status→employee_headcount).",
    "primary_key": "question_id",
    "fallback_key": [
      "company_id",
      "family_id",
      "metric_name",
      "year"
    ]
  },
  "2_best_answer_rules": {
    "answer": "MATCH_CONFIRMED khi giá trị khớp; BACKFILL_FROM_DATASET khi chỉ RAG có; BACKFILL_FROM_INTERNAL khi chỉ internal-doc có; CONFLICT_REVIEW_REQUIRED khi cả hai khác; NO_ANSWER_FOUND / INSUFFICIENT_EVIDENCE khi không đủ signal.",
    "policy_file": "resolution_policy.json"
  },
  "3_auto_confirm_vs_review": {
    "auto_confirm": [
      "MATCH_CONFIRMED",
      "BACKFILL_FROM_DATASET (answer_correct)",
      "BACKFILL_FROM_INTERNAL (conf>=0.85+sufficiency)"
    ],
    "review_required": [
      "CONFLICT_REVIEW_REQUIRED",
      "INSUFFICIENT_EVIDENCE",
      "BACKFILL_FROM_INTERNAL candidate"
    ],
    "status_counts": {
      "NO_ANSWER_FOUND": 480,
      "BACKFILL_FROM_DATASET": 67,
      "BACKFILL_FROM_INTERNAL": 19
    }
  },
  "4_unified_output_fields": {
    "answer": "identity, best_answer, best_answer_origin, resolution_status, confidence, readiness_state, conflict_status, sources{dataset,internal_doc}, supporting_evidence, auto_confirm, review_required",
    "schema": "data/unified_esg/unified_answer_schema.json"
  },
  "5_review_artifact_without_touching_excel": {
    "answer": "Có — workbook/JSONL riêng (unified_answers.jsonl, unified_esg_review.xlsx); không ghi đè Excel gốc hay results.jsonl frozen.",
    "artifacts": [
      "unified_answers.jsonl",
      "unified_esg_review.xlsx",
      "review_workbook_plan.md"
    ]
  },
  "6_next_step": {
    "answer": "Khi có công ty overlap cả dataset + internal-doc: chạy resolution trên cùng company_id; SME review sheet CONFLICT; publish unified layer cho báo cáo ESG; không mở LangGraph/synthesis."
  }
}

## Status breakdown

{
  "NO_ANSWER_FOUND": 480,
  "BACKFILL_FROM_DATASET": 67,
  "BACKFILL_FROM_INTERNAL": 19
}

## Inputs

{
  "dataset_results_path": "reports/goldns_emni_rag_eval_20260618-100003/results.jsonl",
  "internal_records_path": "reports/enterprise_docs_structured_esg_hardening_20260619-090700/structured_esg_records.jsonl",
  "dataset_row_count": 530,
  "internal_row_count": 36,
  "unified_row_count": 566,
  "join_by_question_id": 566,
  "join_by_business_key_only": 0
}
