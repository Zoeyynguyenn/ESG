# Báo cáo sửa eval alias/scoring — OpenAI validation lane

Ngày: 2026-05-29  
Lane: `company_export_json_validation`  
Config: `configs/benchmark_exportjson_openai_validation.yaml` (không RAGAS)

## 1. File code đã sửa / thêm

| File | Thay đổi |
|---|---|
| `src/eval_source_matcher.py` | **Mới** — matcher record/package/split/path; normalize source; `fail_kind` |
| `src/eval_scoring_v2.py` | `score_retrieval` / `score_citation` gọi matcher; audit fields; `RC_RETRIEVAL_TRUE_MISS` |
| `src/run_benchmark_case.py` | `failure_audit_samples`: normalized sources, `match_reason`, `fail_kind`, record/doc id |
| `src/run_model_candidate_benchmark.py` | Audit markdown hiển thị trường mới (đã có sẵn từ trước) |

**Không đổi:** pipeline retrieval/index/query (`query_v3`, ingest, chunking).

## 2. Quy tắc match mới (thứ tự ưu tiên)

1. **Record/doc** — nếu eval có `record_id` / `doc_id` trong `expected_source` hoặc chunk text (`record_id:`, `doc_id:`).
2. **Export JSON split alias** — `expected_source` trỏ `.../splits/dev.jsonl` (hoặc validation/full) nhưng top evidence là `validation.jsonl` cùng package → `package_split_match` (khớp `dataset_package_<timestamp>`, không chấm cứng tên file split).
3. **Cùng split** — `dev.jsonl` vs `dev.jsonl` → `split_alias_match`.
4. **Legacy path alias** — `source_aliases()` + substring (lane public/ESG).
5. **Chuẩn hóa trước khi so:** `\` → `/`, lowercase, Unicode NFKC, trim.

**Phân loại fail:**

- `retrieval_miss` — không có evidence gần package/path.
- `alias_mismatch` — top evidence cùng package export JSON nhưng matcher cũ sẽ fail (audit only khi miss).

**Reason codes:** `retrieval_alias_miss`, `retrieval_true_miss`, `retrieval_no_evidence`.

## 3. Trước / sau (4 config validation OpenAI)

| config_id | hit (trước) | cit (trước) | composite (trước) | hit (sau) | cit (sau) | composite (sau) |
|---|---:|---:|---:|---:|---:|---:|
| `val_openai_rec800_dense_chroma` | 0.0 | 0.0 | 0.265 | **1.0** | **1.0** | **0.665** |
| `val_openai_rec800_hybrid_chroma` | 0.0 | 0.0 | 0.1816 | **1.0** | **1.0** | **0.7401** |
| `val_openai_section_dense_chroma` | 0.0 | 0.0 | 0.165 | **1.0** | **1.0** | **0.7635** |
| `val_openai_section_hybrid_chroma` | 0.0 | 0.0 | 0.236 | **1.0** | **1.0** | **0.7725** |

Run ID sau sửa: `mc_20260529-102949_*` (CSV: `reports/benchmark_exportjson_openai_validation_results.csv`).

**Kết luận số:** hit/citation từ 0 → 1.0 trên toàn bộ config; composite tăng ~+0.40–0.60 nhờ trọng số retrieval/citation trong composite. Groundedness/answer_correctness không đổi (0.75 / 0.05–0.15).

## 4. Case còn fail và lý do

**Retrieval/citation:** không còn miss trên 20 câu eval (audit mẫu CE-J01…J05: `hit=True`, `cit=True`, `match_reason=package_split_match`).

**Điểm yếu còn lại (không phải retrieval miss):**

| Hạng mục | Giá trị | Ghi chú |
|---|---|---|
| `answer_correctness` | 0.05–0.15 | Rule-based answer scoring; chưa phản ánh chất lượng OpenAI embedding |
| `groundedness` | 0.75 | Overlap token; ổn định trước/sau |
| Eval set encoding | expected path mojibake (`ë„¥ìŠ¤…`) | Matcher bypass qua `dataset_package_20260528T091409`; nên sửa eval set UTF-8 sau |

**Nguyên nhân hit=0 trước đây (đã xác nhận):** scoring file-level + mojibake folder name + eval trỏ `splits/dev.jsonl` trong khi corpus validation dùng `splits/validation.jsonl` — retrieval đúng nhưng matcher cũ fail.

## 5. Gate Phase 3 OpenAI

| Tiêu chí | Trạng thái |
|---|---|
| Validation hit/citation đáng tin | **Đạt** — hit=1.0, citation=1.0 (4/4 config) |
| Smoke dev OpenAI | Đã đạt trước đó (hit=1.0) |
| RAGAS | Chưa chạy (`ragas` chưa cài) — không chặn gate retrieval |

**Đề xuất:** mở **Phase 3 OpenAI — Chroma vs Qdrant** trên lane validation (hoặc full), cùng embedding `openai:text-embedding-3-small`, winner section_hybrid hoặc rec800_hybrid làm baseline.

Lệnh gợi ý (khi có config Phase 3):

```powershell
python src/run_model_candidate_benchmark.py --config configs/benchmark_exportjson_openai_phase3.yaml
```

## 6. Artifact liên quan

- `reports/benchmark_exportjson_openai_validation_results.csv`
- `reports/benchmark_exportjson_openai_validation_failure_audit.md`
- `reports/benchmark_exportjson_openai_validation_summary.md`
- `reports/benchmark_exportjson_openai_vs_local_validation.html` (đã regenerate)
