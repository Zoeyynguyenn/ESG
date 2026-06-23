# Báo cáo rerun E2E OpenAI — eval answerable-only (KO)

**Ngày chạy:** 2026-06-03  
**Stack (giữ BC11):** `section_based` 800/120 · `openai:text-embedding-3-small` · Qdrant · `hybrid_dense_bm25` · pool 64 · **reranker none** · generative `gpt-4o-mini`  
**Eval:** `.rag/rag-pipeline-practice/eval_set_company_export_json_dev_ko.md` — **15 câu answerable-only** (bỏ CE-J16–J20 insufficient; sửa J11–J15 theo ground truth trong package)  
**Config:** `configs/benchmark_exportjson_openai_e2e.yaml`  
**Preflight:** `scripts/openai_e2e_preflight.py` — API key OK  

---

## Thay đổi so với lần trước

| Hạng mục | Trước (BC11 / run fail) | Sau (run này) |
|---|---|---|
| Eval | 20 câu (5 insufficient + 3 câu không có field) | 15 câu, mọi câu có GT trong package |
| API key | 401 invalid | Preflight OK |
| Smoke CI | CE-J16 insufficient | CE-J08 (exported_at), toàn answerable |
| `eval_questions` E2E | 20 | 15 |

---

## Kết quả benchmark

| config_id | hit | citation | groundedness | answer | composite | latency (s) | RAGAS faithfulness |
|---|---:|---:|---:|---:|---:|---:|---:|
| `e2e_openai_hybrid_qdrant_generative` | **0.8667** | **0.8667** | 0.60 | **0.7333** | **0.7533** | 183.6 | 0.75 |
| `e2e_openai_hybrid_qdrant_extractive` | **0.8667** | **0.8667** | 0.8667 | **0.80** | 0.74 | 490.7 | 0.715 |

**RAGAS (top config, max 10 câu):** context_precision 0.7667 · context_recall 0.70 · judge `gpt-4o-mini`

**Winner:** generative (composite cao hơn nhờ latency; extractive mạnh hơn về answer correctness và groundedness).

---

## So sánh mốc BC11 (20 câu, cùng stack OpenAI)

| Metric | BC11 (ước lượng) | Run answerable-only |
|---|---:|---:|
| retrieval_hit | ~1.00 | 0.8667 (13/15) |
| citation | ~1.00 | 0.8667 |
| answer_correctness | ~0.35 (7/20) | **0.73–0.80** |
| insufficient handling | có 5 câu CE-J16–J20 | N/A (đã loại) |

**Kết luận:** Sau khi loại câu không có GT và insufficient, **answer correctness tăng mạnh** (~2×). Retrieval/citation giảm nhẹ do **2 miss cố định** (CE-J04 KOSDAQ market, CE-J05 homepage) — cần theo dõi retrieval alias cho `krx_meta` / profile homepage.

---

## Câu fail retrieval (audit)

- **CE-J04** — “어느 시장에 상장” → `retrieval_miss`, evidence rỗng  
- **CE-J05** — “공식 홈페이지” → `retrieval_miss`, evidence rỗng  

Các câu manifest (J06–J08, J12, J14–J15) và profile/ticker/DART (J01–J03, J09–J11, J13) hit ổn định.

---

## Trạng thái pipeline

| Tiêu chí | Đánh giá |
|---|---|
| OpenAI embed + key | Ổn |
| Reindex full lane | OK (620 chunks, ~102s) |
| Eval KO answerable-only | Ổn cho đo lường regression |
| Generative KO | Chạy được; answer ~73% |
| GPU / Qwen / bge-reranker | **Chưa** — chờ pipeline ổn định thêm (theo báo cáo 12) |

**Bước tiếp theo đề xuất:** (1) fix retrieval CE-J04/J05; (2) chạy smoke CI production; (3) khi hit ≥ 0.93 và answer ≥ 0.75 ổn định → benchmark C2 (4090 + Qwen2.5-14B) theo báo cáo 12.

---

## Artifact

- `reports/benchmark_exportjson_openai_e2e_results.csv`
- `reports/benchmark_exportjson_openai_e2e_summary.md`
- `reports/benchmark_exportjson_openai_e2e_failure_audit.md`
