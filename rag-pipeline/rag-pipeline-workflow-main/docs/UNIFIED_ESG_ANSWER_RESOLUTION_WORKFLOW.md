# Unified ESG answer resolution — Workflow

Một bài toán ESG: **dataset/public source** và **internal-doc/company documents** là hai nguồn đầu vào; lớp hợp nhất chọn **best answer** có evidence và readiness/conflict rõ ràng.

## Phạm vi

- **Làm:** merge output hiện có, resolution policy, unified schema, review workbook/JSONL
- **Không làm:** rebuild RAG hoặc internal-doc pipeline; LangGraph; synthesis; tune case lẻ

## Input

| Nguồn | Artifact mặc định |
|---|---|
| Dataset / RAG eval | `reports/goldns_emni_rag_eval_20260618-100003/results.jsonl` |
| Internal-doc structured | `reports/enterprise_docs_structured_esg_hardening_20260619-090700/structured_esg_records.jsonl` |
| Partition enrichment | `data/dataset_excel_eval_ready/20260617_goldns_emni/*/answerable_gold.csv` |

## Identity / business key

1. **Primary:** `question_id` khi cả hai nguồn có cùng id
2. **Fallback:** `company_id::family_id::metric_name_norm::year`

Dataset `question_family` map sang `family_id` nội bộ qua `FAMILY_ALIASES`.

## Resolution status

| Status | Ý nghĩa |
|---|---|
| `MATCH_CONFIRMED` | Cả hai có answer và khớp |
| `BACKFILL_FROM_INTERNAL` | Chỉ internal-doc (hoặc dataset abstain) |
| `BACKFILL_FROM_DATASET` | Chỉ dataset/public source |
| `CONFLICT_REVIEW_REQUIRED` | Cả hai có nhưng conflict |
| `NO_ANSWER_FOUND` | Không nguồn nào resolved |
| `INSUFFICIENT_EVIDENCE` | Signal một phần, chưa đủ confirm |

## Decision policy (tóm tắt)

### Auto-confirm

- `MATCH_CONFIRMED`
- `BACKFILL_FROM_DATASET` khi `answer_correct`
- `BACKFILL_FROM_INTERNAL` khi `confidence >= 0.85` và sufficiency resolved

### SME review

- `CONFLICT_REVIEW_REQUIRED`
- `INSUFFICIENT_EVIDENCE`
- `BACKFILL_FROM_INTERNAL` candidate (confidence thấp)

### Ưu tiên nguồn

- **Internal-doc:** metric SR công ty, `multi_source_confirmed`, dataset absent
- **Dataset:** filing công khai (DART), internal extraction fail, canonical gold alignment khi MATCH

## Chạy

```bash
python scripts/run_unified_esg_answer_resolution.py
```

Output: `reports/unified_esg_answer_resolution_<timestamp>/`

| File | Mục đích |
|---|---|
| `unified_answers.jsonl` | Unified layer — dùng chung |
| `unified_esg_review.xlsx` | Review workbook — **không ghi đè Excel gốc** |
| `resolution_policy.json` | Policy đầy đủ |
| `status_breakdown.json` | Thống kê theo status |
| `review_workbook_plan.md` | Hướng dẫn review từng sheet |

## Module

| File | Vai trò |
|---|---|
| `src/unified_esg_resolution_policy.py` | Rules + value equivalence |
| `src/unified_esg_answer_resolution.py` | Merge + export |
| `data/unified_esg/unified_answer_schema.json` | Schema output |

## Bước tiếp theo

Khi cùng `company_id` xuất hiện ở cả hai lane: chạy resolution → SME review `CONFLICT` sheet → publish unified layer cho báo cáo ESG.
