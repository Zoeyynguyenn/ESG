# Chuẩn bị OpenAI E2E — RAGAS + full lane + generative

Ngày: 2026-05-29

## Đã làm trong repo

| Hạng mục | Chi tiết |
|---|---|
| Eval set UTF-8 | Sửa path `넥스트아이_dataset_package_...` trong `eval_set_company_export_json_dev.md` |
| RAGAS | `src/ragas_eval.py` + tích hợp `run_benchmark_case.py` |
| Generative | `--answer-mode generative` trong benchmark (OpenAI/Ollama qua `llm_runtime`) |
| Config E2E | `configs/benchmark_exportjson_openai_e2e.yaml` — full lane, 2 case extractive vs generative |
| Script | `scripts/run_openai_e2e_full.ps1` |
| Deps | `requirements-ragas.txt` (`ragas`, `datasets`) |

## Điều kiện trước khi chạy

1. `.env` có `OPENAI_API_KEY` hợp lệ (embedding + LLM + RAGAS judge)
2. `OPENAI_BASE_URL` để trống hoặc URL đầy đủ (không `OPENAI_BASE_URL=` rỗng)
3. Qdrant local chạy được (winner stack dùng `vector_store: qdrant`)
4. `pip install -r requirements-ragas.txt`

## Lệnh chạy

```powershell
cd E:\Documents\rag-pipeline-workflow
.\scripts\run_openai_e2e_full.ps1 -RagasMaxQuestions 10
```

Hoặc:

```powershell
python src/run_model_candidate_benchmark.py `
  --config configs/benchmark_exportjson_openai_e2e.yaml `
  --enable-ragas true `
  --ragas-max-questions 10 `
  --timeout-sec 3600
```

## Output mong đợi

- `reports/benchmark_exportjson_openai_e2e_results.csv`
- `reports/benchmark_exportjson_openai_e2e_summary.md`
- `reports/benchmark_exportjson_openai_e2e_failure_audit.md`

Cột so sánh extractive vs generative: `answer_mode`, `answer_correctness`, `groundedness`, `faithfulness`, `answer_relevancy`, `query_time_avg`, `latency`.

## Chi phí / thời gian ước lượng

- Full lane index: lớn hơn validation (~1–3 phút/case tùy corpus)
- Generative: +1 LLM call/câu (~20 câu)
- RAGAS: thêm judge calls trên `RagasMaxQuestions` (mặc định 10)
- Tổng 2 case: ~15–45 phút

## 5 to-do — trạng thái

| # | Việc | Trạng thái |
|---|---|---|
| 1 | Sửa eval UTF-8 | **Done** |
| 2 | Tích hợp RAGAS | **Done** — faithfulness 0.89 (ext) / 0.40 (gen) |
| 3 | Generative benchmark | **Done** — `llm_provider=openai_api` |
| 4 | Config/script E2E | **Done** |
| 5 | Chạy full lane | **Done** — hit/cit 1.0; generative composite 0.7875 |

Chi tiết: `reports/openai_e2e_full_lane_report.md`
