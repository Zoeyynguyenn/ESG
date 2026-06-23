# So sánh Local (MiniLM) vs OpenAI

Tạo lúc: 2026-05-29T10:45:42

## Lưu ý khi đọc

| Khía cạnh | Local | OpenAI |
|---|---|---|
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` (local CPU) | `openai:text-embedding-3-small` (API) |
| Lane corpus | `company_export_json_dev` → `splits/dev.jsonl` | `company_export_json_validation` → `splits/validation.jsonl` |
| Eval | Cùng file `.rag/.../eval_set_company_export_json_dev.md` (20 câu trên validation; dev thường ít hơn tùy `eval_questions`) |
| Pool | 24 (Pha 1) | 64 (validation / Phase 3) |
| Vector store | Chroma | Chroma (validation) / Qdrant (Phase 3 winner) |

**Tốc độ:** `query_s` = giây trung bình mỗi câu; `index_build_s` = thời gian build index; `latency_s` = tổng thời gian chạy eval case.

## Bảng chính (cùng chunking + retrieval)

| Chunking | Retrieval | Hit L | Hit O | Cit L | Cit O | Composite L | Composite O | Query L (s) | Query O (s) | O/L query | Index L (s) | Index O (s) | Latency L (s) | Latency O (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| recursive_800_120 | semantic_dense | 1.0 | 1.0 | 1.0 | 1.0 | 0.765 | 0.665 | 0.167 | 1.043 | 6.2x | 16.815 | 21.471 | 26.859 | 43.02 |
| recursive_800_120 | hybrid_dense_bm25 | 1.0 | 1.0 | 1.0 | 1.0 | 0.7638 | 0.7401 | 0.176 | 1.007 | 5.7x | 20.144 | 15.332 | 31.558 | 36.101 |
| section_based | semantic_dense | 1.0 | 1.0 | 1.0 | 1.0 | 0.7644 | 0.7635 | 0.167 | 1.004 | 6.0x | 18.663 | 14.103 | 29.109 | 34.767 |
| section_based | hybrid_dense_bm25 | 1.0 | 1.0 | 1.0 | 1.0 | 0.764 | 0.7725 | 0.205 | 1.026 | 5.0x | 19.074 | 13.514 | 30.807 | 34.642 |
| section_based | hybrid_dense_bm25 | 1.0 | 1.0 | 1.0 | 1.0 | 0.764 | 0.7575 | 0.205 | 0.998 | 4.9x | 19.074 | 13.212 | 30.807 | 33.785 |

## OpenAI smoke trên dev lane (cùng lane với Local)

| Config | Hit | Cit | Composite | Query (s) | Index (s) | Latency (s) |
|---|---:|---:|---:|---:|---:|---:|
| `smoke_openai_rec800_dense_chroma` | 1.0 | 1.0 | 0.83 | 0.938 | 13.429 | 18.712 |
| `smoke_openai_rec800_hybrid_chroma` | 1.0 | 1.0 | 0.7 | 1.003 | 13.436 | 19.009 |

## Nguồn

- `reports/benchmark_exportjson_phase1_results.csv`
- `reports/benchmark_exportjson_openai_validation_results.csv`
- `reports/benchmark_exportjson_openai_phase3_results.csv`
- CSV bảng này: `benchmark_local_vs_openai_comparison.csv`
