# Golden Set v2 — Runbook Silver → Gold

Thay thế quy trình thủ công `golden_set_v1` (điền tay `gold_answer` không có Silver/QC).

## Timeline thực thi

| Tuần | Bước | Việc | Artifact | Gate |
|------|------|------|----------|------|
| W1 D1 | **1** | Export corpus units từ `05_company_export_json` | `step1_corpus_units/corpus_units.jsonl` | ≥30 units/company |
| W1 D2 | **2** | Distillation (Silver Q&A) | `step2_silver/silver_distilled.jsonl` | Cần `OPENAI_API_KEY` |
| W1 D3 | **3** | Evol-Instruct (~25%) | `step3_silver_evolved/silver_evolved.jsonl` | |
| W1 D4 | **4** | QC: Answerability, Difficulty, Groundedness (CJK bigram overlap) | `step4_silver_qc/silver_qc_pass.jsonl` | pass rate ≥60% |
| W1 D5–W2 | **5** | SME review (human hoặc **AI judge**) | `step5_sme_review/sme_review.csv` | `sme_decision=approve` |
| W2 | **6** | Promote Gold + eval markdown | `step6_gold/golden_set.jsonl` | ≥20 câu Gold |
| W2+ | CI | Benchmark + RAGAS trên Gold | `eval_set_golden_v2_ko.md` | hit/cit regression |

## Lệnh

```powershell
python scripts/golden_set_pipeline.py --step 1
python scripts/golden_set_pipeline.py --step 2 --limit 15   # pilot; bỏ --limit khi chạy full 118 units
python scripts/golden_set_pipeline.py --step 3
python scripts/golden_set_pipeline.py --step 4
python scripts/golden_set_pipeline.py --step 5
# SME human: mở sme_review.xlsx, điền sme_decision=approve
# SME AI (không có chuyên gia): LLM-as-judge
python scripts/golden_set_pipeline.py --step 5 --ai-sme
python scripts/golden_set_pipeline.py --step 6
```

## Phân vai eval

| Tập | Mục đích | Không dùng để |
|-----|----------|----------------|
| `eval_set_3cty_*` | Smoke / gate nhanh (metadata) | Regression ESG narrative |
| `golden_set_v1_*` | **Archive** | Production regression |
| `golden_set v2` (step 6) | **Source of Truth** regression | Smoke latency |

## SME checklist (bước 5)

- [ ] Câu trả lời chỉ từ `context_excerpt` (Groundedness)
- [ ] Không nhầm GRI/disclosure (vd. 405-1-b-i % vs 2-7-b-i 명)
- [ ] `forbidden_rule` phản ánh rủi ro hallucination
- [ ] `sme_decision=approve` hoặc `revise` + sửa cột revised_*

## Sau Gold v2

1. Chạy benchmark: `--eval-set-path .rag/.../eval_set_golden_v2_ko.md`
2. Bật RAGAS trên top configs
3. Gắn smoke CI production (tùy chọn thay 5 câu Nexteye)
