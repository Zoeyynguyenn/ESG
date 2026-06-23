# Golden Set v2 — Silver → Gold

Quy trình mới thay thế `golden_set_v1` (thủ công, không có bước Silver/QC).

## Thư mục artifact (tự sinh khi chạy pipeline)

| Bước | Thư mục | File chính |
|------|---------|------------|
| 1 | `step1_corpus_units/` | `corpus_units.jsonl`, `corpus_units_eligible.jsonl` (prefilter R2.1) |
| 2 | `step2_silver/` | `silver_distilled.jsonl` |
| 3 | `step3_silver_evolved/` | `silver_evolved.jsonl` |
| 4 | `step4_silver_qc/` | `silver_qc_pass.jsonl`, `silver_qc_reject.jsonl` |
| 5 | `step5_sme_review/` | `sme_review.csv`, `sme_review.xlsx` |
| 6 | `step6_gold/` | `golden_set.jsonl`, eval markdown |

## Chạy

```powershell
cd E:\Documents\rag-pipeline-workflow

# Bước 1 — không cần API
python scripts/golden_set_pipeline.py --step 1

# Bước 0 — prefilter R2.1 (sau step 1, trước distillation)
python scripts/golden_set_pipeline.py --step 0

# Bước 2–4 — cần OPENAI_API_KEY
python scripts/golden_set_pipeline.py --step 2
python scripts/golden_set_pipeline.py --step 3
python scripts/golden_set_pipeline.py --step 4

# Bước 5 — xuất file SME review
python scripts/golden_set_pipeline.py --step 5

# Sau khi SME điền cột sme_decision=approve trong sme_review.csv:
python scripts/golden_set_pipeline.py --step 6
```

## Legacy

- `data/golden_set/golden_set_v1_*` — **archive tham chiếu**, không dùng cho regression mới.
- Smoke gate nhanh: `eval_set_3cty_*` (metadata).
- Regression chất lượng ESG: `step6_gold/golden_set.jsonl` sau SME.
