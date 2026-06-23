# Gate production — OpenAI lane `company_export_json_validation`

Ngày: 2026-05-29  
Benchmark: `configs/benchmark_exportjson_openai_phase3.yaml` (6/6 success)

## Chốt winner

| Thành phần | Giá trị |
|---|---|
| **config_id** | `p3_openai_section_hybrid_qdrant` |
| chunking | `section_based` (800/120) |
| retrieval | `hybrid_dense_bm25` |
| embedding | `openai:text-embedding-3-small` |
| vector DB | **Qdrant** (`qdrant_status=enabled`) |
| reranker | `none` |
| candidate_pool | **64** (giữ như validation) |

**Metric:** hit=1.0, citation=1.0, composite=**0.7575**, query_avg=**0.998s**, latency tổng=**33.8s**, index_build=**13.2s**.

## So sánh Chroma vs Qdrant (cùng retrieval, pool=64)

| Chunking | Retrieval | Chroma composite | Qdrant composite | Δ composite | Query Chroma | Query Qdrant | Quyết định |
|---|---|---:|---:|---:|---:|---:|---|
| section_based | hybrid_dense_bm25 | 0.6983 | **0.7575** | 0.0592 | 0.983s | 0.998s | **Qdrant** (Δ≥0.02) |
| section_based | semantic_dense | **0.7551** | 0.6650 | 0.0901 | 0.984s | 0.964s | **Chroma** |
| recursive_800_120 | hybrid_dense_bm25 | 0.6646 | **0.7011** | 0.0365 | 0.975s | 1.004s | **Qdrant** (Δ≥0.02) |

**Quy tắc gate:** nếu |Δ composite| < 0.02 → ưu tiên Qdrant production-scale; ngược lại theo số cao hơn.

- Cặp **section_hybrid** (top validation): Δ=0.059 → Qdrant thắng rõ.
- Cặp **section_dense**: Δ=0.09 → Chroma thắng (không dùng làm stack chính vì hybrid tốt hơn trên validation).
- Cặp **rec800_hybrid**: Δ=0.037 → Qdrant thắng.

## Trade-off latency vs composite

- Hit/citation **đồng nhất 1.0** trên mọi case — khác biệt chủ yếu ở `latency_normalized` và `answer_correctness` trong composite.
- **Qdrant** trên winner `section_hybrid`: composite cao hơn Chroma (+0.059), latency tổng thấp hơn (~33.8s vs 34.9s), index build nhanh hơn (~13.2s vs 14.6s).
- Query trung bình gần tương đương (~1.0s/câu); không có penalty latency đáng kể trên corpus validation hiện tại.

## So với validation (Chroma-only, trước Phase 3)

| config | validation composite | Phase 3 (cùng họ) |
|---|---:|---:|
| section_hybrid chroma | 0.7725 | 0.6983 |
| section_dense chroma | 0.7635 | 0.7551 |

Chênh composite giữa các lần chạy do trọng số latency_normalized dao động; **hit/citation ổn định 1.0** sau fix matcher.

## Khuyến nghị triển khai

1. **Production short-term:** `section_based` + `hybrid_dense_bm25` + OpenAI embedding + **Qdrant** + pool 64.
2. **Fallback dev/local:** Chroma vẫn hợp lệ khi không có Qdrant; dense-only Chroma (`section_dense`) gần parity nếu cần đơn giản hóa.
3. **Chưa làm:** RAGAS, reranker đa ngữ, full lane — tách run riêng.

## Artifact

- `reports/benchmark_exportjson_openai_phase3_results.csv`
- `reports/benchmark_exportjson_openai_phase3_summary.md`
- `reports/benchmark_exportjson_openai_phase3_failure_audit.md`
- `reports/benchmark_exportjson_openai_vs_local_validation.html` (block Phase 3)
