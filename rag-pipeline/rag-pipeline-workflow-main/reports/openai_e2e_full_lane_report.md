# Báo cáo E2E OpenAI — full lane + RAGAS + generative

Ngày: 2026-05-29  
Config: `configs/benchmark_exportjson_openai_e2e.yaml`  
Run: `mc_20260529-112245_*` (2/2 success, ~10.2 phút)

## Stack

| Thành phần | Giá trị |
|---|---|
| Lane | `company_export_json_full` → `splits/full.jsonl` |
| Embedding | `openai:text-embedding-3-small` |
| Vector DB | Qdrant |
| Chunking | `section_based` 800/120 |
| Retrieval | `hybrid_dense_bm25`, pool 64 |
| LLM generative | `gpt-4o-mini` (`openai_api`) |
| RAGAS | 10 câu/case, judge `gpt-4o-mini` |

## Kết quả số — extractive vs generative

| Metric | Extractive | Generative | Δ (G − E) |
|---|---:|---:|---:|
| retrieval_hit_rate | 1.0 | 1.0 | 0 |
| citation_correctness | 1.0 | 1.0 | 0 |
| **answer_correctness** | **0.0** | **0.35** | **+0.35** |
| groundedness (rule) | 0.75 | 0.85 | +0.10 |
| insufficient_handling | 0.75 | **1.0** | +0.25 |
| **composite** | 0.65 | **0.7875** | **+0.1375** |
| query_time_avg (s) | 0.944 | 2.052 | +1.1s |
| index_build (s) | 64.3 | 58.0 | −6.3s |
| latency tổng (s) | 349.6 | 256.6 | −93s* |

\*Case 2 reuse index cache nên latency tổng thấp hơn dù query chậm hơn.

### RAGAS (10 câu mẫu)

| Metric | Extractive | Generative |
|---|---:|---:|
| faithfulness | **0.8944** | 0.40 |
| answer_relevancy | — | — |
| context_precision | 0.2583 | 0.2583 |
| context_recall | 0.40 | 0.50 |
| ragas_status | success | success |

## Kết luận

1. **Retrieval/citation:** Cả hai mode đạt **hit=1.0, citation=1.0** trên full lane (20 câu) — matcher `package_split_match` hoạt động (expected `dev.jsonl` vs corpus `full.jsonl`).

2. **Generative tốt hơn extractive về trả lời:**
   - `answer_correctness`: 0 → **0.35** (rule-based scoring)
   - `insufficient_handling`: 0.75 → **1.0** (5 câu insufficient xử lý đúng hơn)
   - `composite`: 0.65 → **0.7875**

3. **RAGAS faithfulness** extractive cao hơn (0.89 vs 0.40) — có thể do extractive trả lời ngắn/sát chunk; generative diễn đạt lại nên judge strict hơn. Cần đọc mẫu câu fail RAGAS trước khi kết luận “hallucination”.

4. **Tốc độ:** Generative ~**2.05 s/câu** vs extractive ~**0.94 s/câu** (~2.2× chậm hơn do gọi GPT-4o mini).

5. **Full lane index:** ~**58–64 s** embed batch 32 chunk (fix vượt 300k token/request).

## Khuyến nghị production

- **Retrieval stack:** giữ `section_hybrid + OpenAI embed + Qdrant`
- **Answer layer:** dùng **generative (gpt-4o-mini)** khi cần câu trả lời tự nhiên + insufficient handling; giữ extractive cho debug/audit nhanh
- **Monitoring:** theo dõi RAGAS faithfulness live; rule composite và RAGAS có thể lệch hướng

## Artifact

- `reports/benchmark_exportjson_openai_e2e_results.csv`
- `reports/benchmark_exportjson_openai_e2e_summary.md`
- `reports/benchmark_exportjson_openai_e2e_failure_audit.md`
- `reports/openai_e2e_prep_checklist.md`

## 5 to-do — trạng thái

| # | Việc | Trạng thái |
|---|---|---|
| 1 | Sửa eval UTF-8 | Done |
| 2 | Tích hợp RAGAS (`ragas_eval.py`) | Done + **ragas_status=success** |
| 3 | `--answer-mode generative` | Done |
| 4 | Config/script E2E full lane | Done |
| 5 | Chạy E2E + báo cáo | **Done (2/2 success)** |
