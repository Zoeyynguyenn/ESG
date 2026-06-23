# Báo cáo 11: Chốt pipeline OpenAI

**Ngày:** 2026-05-29 · **Nối tiếp:** [Báo cáo 10](bao-cao-10-ket-luan-benchmark-local-vs-production-20260529.md)  
**Dataset:** `넥스트아이_dataset_package_20260528T091409` (lane `company_export_json_*`)  
**Production ID:** `e2e_openai_hybrid_qdrant_generative`  
**Config freeze:** `configs/production_openai_hybrid_qdrant_generative.yaml`

---

## 1. Kết luận

| | Local (BC10) | OpenAI (đã chốt) |
|---|---|---|
| Vai trò | So chunking, embedding, hybrid, vector DB trên CPU | Stack vận hành + eval end-to-end |
| Benchmark | 3 pha · 30/30 case · `retrieval_only` | Validation · Phase 3 · E2E 20q · smoke 5q |
| LLM | Extractive / rule (không GPT) | **gpt-4o-mini** generative |
| Smoke CI | — | **PASS** (hit/cit 5/5) |

**Luồng production:**

`jsonl package` → **section_based 800/120** → **text-embedding-3-small** → **Qdrant** → **hybrid_dense_bm25** (pool **64**, top_k **4**, reranker **none**) → **gpt-4o-mini**.

- **Embedding:** `text-embedding-3-small` — không mở benchmark OpenRouter thêm.  
- **RAGAS:** đã chạy 1 lần E2E (tham khảo); **không** dùng làm gate release.

---

## 2. Đã test gì (tóm tắt)

**Local (BC10)** — package cùng Nexteye, máy CPU:

| Pha | Nội dung | Kết quả rút gọn |
|---|---|---|
| 1 | 3 chunking × 3 embedding (MiniLM, BGE-M3, e5) × dense/hybrid | 18/18 OK; hit 1.0 dev; hybrid ≈ dense |
| 2 | Reranker `none` vs `ms-marco-MiniLM` | Reranker EN chậm ~15×, composite thấp hơn → **không dùng** |
| 3 | Chroma vs Qdrant (MiniLM) | 6/6 OK; kiến trúc cả hai chạy được |

**OpenAI** — sau khi sửa eval matcher (`package_split_match`):

| Bước | Lane / eval | Ghi chú |
|---|---|---|
| Validation | 20 câu, 4 config | hit/cit **1.0** |
| Phase 3 | `section_hybrid` × Chroma/Qdrant, pool 64 | Winner **Qdrant**, composite **0.7575** |
| E2E | `company_export_json_full`, 20 câu | Generative vs extractive |
| P0.1 | Generative sau field boost + manifest inject | **12/20** answer_correct |
| Smoke CI | CE-J02, J03, J06, J07, J16 | Production gate PASS |

**Không làm:** raw data Downloads; so sánh embedding OpenRouter; RAGAS làm tiêu chí chính.

---

## 3. Bảng chốt: Local CPU vs OpenAI

| Thành phần | Local CPU (đã đo) | OpenAI (chốt) |
|---|---|---|
| Chunking | `section_based`, `recursive_800_120` | **`section_based` 800/120** |
| Embedding | MiniLM; BGE-M3; e5-base | **`openai:text-embedding-3-small`** |
| Vector DB | Chroma + Qdrant | **Qdrant** |
| Retrieval | `hybrid_dense_bm25`, pool 64 | Giống |
| Reranker | `none` (ms-marco loại) | **`none`** |
| LLM | Rule / extractive | **gpt-4o-mini** |
| Hit / citation | 1.0 (Pha 1 dev) | **1.0** validation, full, smoke |
| Answer (rule) | Thấp (không generative) | **12/20** full; smoke 4/4 scored (J06 waive) |
| Query / câu | ~0.15s retrieval only | **~2.05s** full 20q gen.; **~4.2s** smoke 5q |
| Index build | MiniLM **~17–20s**; BGE **~287–356s** | OpenAI **~58–64s** (batch 32) |
| GPU (sau này) | Gợi ý: bge-m3, bge-reranker-v2-m3 | Giữ API embed/LLM tạm thời |

---

## 4. Kết quả OpenAI (số liệu)

**Phase 3 — validation, config `p3_openai_section_hybrid_qdrant`:**

| Metric | Giá trị |
|---|---:|
| retrieval_hit_rate | 1.0 |
| citation_correctness | 1.0 |
| composite_score | 0.7575 |
| query_time_avg | 0.998 s |
| index_build_time | 13.2 s |

Qdrant thắng Chroma cùng hybrid (+0.059 composite, ngưỡng gate ≥ 0.02).

**E2E full lane — 20 câu (`company_export_json_full`):**

| Metric | Extractive | Generative (production) |
|---|---:|---:|
| hit / citation | 1.0 / 1.0 | 1.0 / 1.0 |
| answer_correctness | 0.0 | **0.35** |
| insufficient_handling | 0.75 | **1.0** |
| composite | 0.65 | **0.7875** |
| query_time_avg (s) | 0.94 | **2.05** |

**Smoke CI (5 câu):** hit/cit **1.0**; J16 insufficient OK; ngưỡng answer ≥ 0.6 (J06 waived).

**RAGAS (10 câu E2E, không gate):** faithfulness 0.89 extractive / 0.40 generative — lệch định nghĩa paraphrase vs rule metric, không đổi quyết định stack.

---

## 5. Giải thích tham số stack

| Thuật ngữ | Ý nghĩa ngắn |
|---|---|
| **section_based 800/120** | Cắt theo section/record JSON; chunk tối đa **800** ký tự; **120** ký tự chồng lấn giữa hai chunk liền kề. |
| **hybrid_dense_bm25** | Retrieval **gộp** vector (dense/Qdrant) + từ khóa (BM25): tốt cho nghĩa + mã số/ticker/corp code. |
| **pool 64** | Mỗi câu hỏi lấy **64** chunk ứng viên từ hybrid, sau đó chọn **top_k = 4** đưa vào context LLM. |
| **~2s full** | Trung bình **~2.05 s/câu** trên eval **20 câu** generative (retrieval + gọi GPT), không gồm index. |
| **~4s smoke 5q** | Trung bình **~4.2 s/câu** trên **5 câu** smoke CI — cùng stack, mẫu ít hơn / câu metadata có thể nặng hơn. |
| **MiniLM ~20s** | Index local bằng `all-MiniLM-L6-v2` trên CPU — nhanh, dùng benchmark laptop. |
| **BGE ~300s+** | Index local `BAAI/bge-m3` trên CPU — model lớn, **~5–6 phút** cùng corpus; không phản ánh tốc độ GPU production. |

---

## 6. Tham chiếu chi tiết

- Báo cáo 10 (local): `reports/bao-cao-10-ket-luan-benchmark-local-vs-production-20260529.md`  
- Phase 3 gate: `reports/benchmark_exportjson_openai_phase3_production_gate.md`  
- E2E: `reports/openai_e2e_full_lane_report.md`  
- Generative 12/20: `reports/openai_generative_results_summary.md`
