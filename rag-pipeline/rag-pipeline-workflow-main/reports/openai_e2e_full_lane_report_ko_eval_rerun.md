# Báo cáo E2E OpenAI — eval tiếng Hàn + RAGAS (rerun)

**Trạng thái run:** **THẤT BẠI** — không chạy được benchmark do `OPENAI_API_KEY` trong repo không hợp lệ.  
**Ngày ghi nhận:** 2026-06-02  
**Config:** `configs/benchmark_exportjson_openai_e2e.yaml`  
**Eval mới:** `.rag/rag-pipeline-practice/eval_set_company_export_json_dev_ko.md`

---

## 1. Stack dự kiến (không đổi production)

| Thành phần | Giá trị |
|---|---|
| Lane | `company_export_json_full` |
| Package | `넥스트아이_dataset_package_20260528T091409` |
| Chunking | `section_based` 800/120 |
| Embedding | `openai:text-embedding-3-small` |
| Retrieval | `hybrid_dense_bm25`, pool 64, top_k 4 |
| Vector DB | Qdrant |
| LLM generative | `gpt-4o-mini` |
| RAGAS | bật, max 10 câu/case, judge `gpt-4o-mini` |

---

## 2. Môi trường thực tế đã kiểm tra

| Kiểm tra | Kết quả |
|---|---|
| `OPENAI_API_KEY` trong shell Cursor (không load `.env`) | **Không có** → preflight cũ báo nhầm `ollama` |
| Nguồn key khi chạy script Python | File **`E:\Documents\rag-pipeline-workflow\.env`** (đã load qua `setdefault`, không sửa file) |
| `OPENAI_API_KEY` sau load `.env` | **Có** (độ dài 164, suffix `jVsA`) |
| `OPENAI_BASE_URL` | Mặc định `api.openai.com` (không set trong `.env`) |
| User/Machine env `OPENAI_API_KEY` | **Không set** |
| `.env.local` | **Không tồn tại** |
| Provider khi `RAG_BENCHMARK_LLM_PROVIDER=openai_api` | `openai_api` (sau load `.env`) |
| Embedding model | `text-embedding-3-small` |
| Judge / answer model | `gpt-4o-mini` |
| Kiểm tra API `GET /v1/models` | **HTTP 401** — `invalid_api_key` / Incorrect API key |

**Kết luận env:** Key trong `.env` **không usable**. Cần thay bằng key hợp lệ từ [OpenAI API keys](https://platform.openai.com/account/api-keys) (hoặc set biến môi trường User-level), **không** commit key mới.

**Sửa repo (preflight):** Thêm `scripts/openai_e2e_preflight.py` và cập nhật `scripts/run_openai_e2e_full.ps1` để load `.env` + fail sớm khi key sai — tránh nhảy sang Ollama khi chưa có key trong process.

---

## 3. Các bước đã chạy

### 3.1. Re-index full lane

```text
python scripts/p0_1_reindex_full_lane.py
```

| Mục | Kết quả |
|---|---|
| Corpus manifest | **OK** — `full.jsonl`, `manifest.json`, `README.md` |
| Ingest / embed | **FAIL** tại batch Qdrant + OpenAI embed |
| Root cause | **401 AuthenticationError** — API key không hợp lệ |
| Qdrant / encoding | Không tới bước kiểm tra (fail trước embed) |

### 3.2. E2E + RAGAS

```text
powershell -ExecutionPolicy Bypass -File scripts/run_openai_e2e_full.ps1 -SkipInstall -RagasMaxQuestions 10
```

| Case | Trạng thái | Ghi chú |
|---|---|---|
| `e2e_openai_hybrid_qdrant_extractive` | **failed** | `ingest_failed` 401 |
| `e2e_openai_hybrid_qdrant_generative` | **failed** | `ingest_failed` 401 |
| RAGAS | **Không chạy** | Không có index / không có eval rows |

**Preflight cũ (trước patch):** In `llm ready ollama` vì process chưa load `.env` — **sai lane**, không phản ánh OpenAI E2E.

---

## 4. Artifact tạo ra

| File | Nội dung |
|---|---|
| `reports/benchmark_exportjson_openai_e2e_results.csv` | 2 dòng `failed` — run `mc_20260602-095303_*` |
| `reports/benchmark_exportjson_openai_e2e_summary.md` | Tóm tắt failed |
| `reports/benchmark_exportjson_openai_e2e_failure_audit.md` | (nếu có) audit ingest |
| `scripts/openai_e2e_preflight.py` | Preflight mới (chưa pass do key) |

**Không có** metric KO eval mới — run chưa qua ingest.

---

## 5. So sánh Before vs After

### 5.1. Điều kiện so sánh (quan trọng)

| | Mốc cũ (Before) | Run mới (After) — dự kiến |
|---|---|---|
| Eval set | `eval_set_company_export_json_dev.md` (câu hỏi **tiếng Việt**) | `eval_set_company_export_json_dev_ko.md` (câu hỏi **tiếng Hàn**) |
| Lane benchmark | `company_export_json_full` (20 câu) | Cùng lane + stack |
| Run cũ tham chiếu | `mc_20260529-112245_*` (thành công) | **Chưa chạy** |
| Nguồn số cũ | `reports/openai_e2e_full_lane_report.md`, `openai_generative_results_summary.md` | — |

→ So sánh metric **chỉ có ý nghĩa sau khi rerun thành công** với key hợp lệ. Hiện tại **không kết luận được** cải thiện retrieval hay answer do ngôn ngữ.

### 5.2. Bảng metric — generative (production mode)

| Metric | Before (VI eval, run OK) | After (KO eval) | Δ | Ghi chú |
|---|---:|---:|---:|---|
| retrieval_hit_rate | 1.0 | — | — | After: N/A |
| citation_correctness | 1.0 | — | — | |
| answer_correctness | 0.35 | — | — | Rule scoring; cũ 12/20 câu |
| groundedness | 0.85 | — | — | |
| insufficient_information_handling | 1.0 | — | — | |
| composite_score | 0.7875 | — | — | |
| query_time_avg (s) | 2.052 | — | — | |
| faithfulness (RAGAS) | 0.40 | — | — | 10 câu mẫu |
| context_precision (RAGAS) | 0.2583 | — | — | |
| context_recall (RAGAS) | 0.50 | — | — | |
| answer_relevancy (RAGAS) | — | — | — | Không ghi trong báo cáo cũ |

### 5.3. Bảng metric — extractive (tham chiếu)

| Metric | Before | After | Δ |
|---|---:|---:|---:|
| retrieval_hit_rate | 1.0 | — | — |
| citation_correctness | 1.0 | — | — |
| answer_correctness | 0.0 | — | — |
| composite_score | 0.65 | — | — |
| faithfulness (RAGAS) | 0.8944 | — | — |

### 5.4. Phân tích khi có số liệu KO (hướng dẫn đọc)

Khi rerun thành công, cần tách:

| Loại thay đổi | Metric thường bị ảnh hưởng |
|---|---|
| Đổi ngôn ngữ câu hỏi / expected notes (KO) | `answer_correctness`, `faithfulness`, `answer_relevancy` — có thể tăng/giảm **không** do retrieval |
| Cải thiện retrieval thật | `retrieval_hit_rate`, `citation_correctness`, `context_recall` |
| Đổi prompt insufficient KO | `insufficient_information_handling`, `faithfulness` |
| Stack không đổi | `index_build_time`, embedding model giữ nguyên |

---

## 6. Kết luận cuối

**Không cải thiện / chưa kết luận được.**

Lý do:

1. Benchmark **không hoàn thành** — chặn tại OpenAI embedding ingest (`401 invalid_api_key`).
2. Không có số liệu eval tiếng Hàn + RAGAS để so với mốc cũ.
3. Mốc cũ dùng eval **tiếng Việt**; run mới cần eval **tiếng Hàn** — ngay cả khi chạy được cũng phải đọc delta theo bảng mục 5.4, không so thẳng `answer_correctness` như cải thiện retrieval.

**Hành động tiếp theo (người vận hành):**

1. Cập nhật `OPENAI_API_KEY` hợp lệ trong `.env` (local only) hoặc User env.
2. Chạy: `python scripts/openai_e2e_preflight.py` → phải in `openai_api_check: ok`.
3. Chạy: `python scripts/p0_1_reindex_full_lane.py`.
4. Chạy: `.\scripts\run_openai_e2e_full.ps1 -SkipInstall -RagasMaxQuestions 10`.
5. Cập nhật lại file báo cáo này với bảng Before/After đầy đủ.

**Production stack:** **Không đổi** — chưa có số liệu mới đủ để đổi `configs/production_openai_hybrid_qdrant_generative.yaml`.

---

## 7. Tham chiếu mốc cũ

- `reports/openai_e2e_full_lane_report.md`
- `reports/openai_generative_results_summary.md` (generative **12/20** rule, eval VI)
- `reports/benchmark_exportjson_openai_e2e_results.csv` (hiện chỉ chứa run failed 2026-06-02)
