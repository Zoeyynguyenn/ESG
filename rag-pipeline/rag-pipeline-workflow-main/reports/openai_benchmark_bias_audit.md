# OpenAI benchmark bias audit — export JSON lane (Nexteye)

**Ngày:** 2026-05-29  
**Phạm vi:** Lane OpenAI (`openai:text-embedding-3-small`), package `넥스트아이_dataset_package_20260528T091409`  
**Không thực hiện:** đổi `gpt-4o-mini`, đổi RAGAS, benchmark lại local/GPU  
**Stack tham chiếu:** `configs/production_openai_hybrid_qdrant_generative.yaml` (section_based + hybrid + Qdrant pool 64)

**Artifact máy đọc:** `artifacts/openai_benchmark_bias_audit.json`  
**Script tái chạy:** `python scripts/openai_benchmark_bias_audit.py`

---

## Bảng PASS/FAIL tổng hợp

| # | Hạng mục | Kết quả | Ghi chú ngắn |
|---:|---|:---:|---|
| 1 | Lane leakage | **PASS** | 15/15 câu: top-4 source ∈ `05_company_export_json/.../091409/`; không có `04_company_public` hay bucket ESG khác |
| 2 | Eval matcher / alias / UTF-8 | **PASS** (có caveat) | 20/20 `package_split_match` hit+citation trên index full; eval UTF-8 đã sửa; split dev vs corpus validation/full được matcher xử lý có chủ đích |
| 3 | Fairness setup (OpenAI configs) | **PASS** | Mọi candidate OpenAI: `reranker=none`, `pool=64`, không `_rerank` mode |
| 3b | Fairness setup (local cũ) | **INVALID** (lịch sử) | MiniLM phase2 trước 2026-05-28 — không dùng để kết luận |
| 4 | Vector index integrity | **PASS** (caveat vận hành) | Cache key tách embedding+lane+chunking+company; BM25/Qdrant full khớp `full.jsonl`+`manifest.json` |
| 5 | OpenAI embedding safety | **PASS** (thiếu retry) | Batch ingest OK; chưa có retry 429; resume index/case có |

---

## 1) Lane leakage

### Cơ chế bảo vệ (code)

```39:53:src/retrieval_v3.py
def _source_allowed_for_lane(source: str) -> bool:
    lane = os.getenv("RAG_BENCHMARK_LANE", "").strip()
    ...
    if lane.startswith("company_export_json"):
        pkg = os.getenv("RAG_COMPANY_FILTER", "").strip().strip("/").lower()
        if pkg:
            return src.startswith(f"data/rag_dataset/05_company_export_json/{pkg}/")
```

- Corpus manifest + `RAG_COMPANY_FILTER` giới hạn file ingest (`run_benchmark_case._prepare_corpus_manifest`).
- `_filter_hits_by_lane` áp sau dense/BM25.

### Kết quả kiểm tra runtime (15 câu, production stack, index full)

| Metric | Giá trị |
|---|---|
| Câu có leak | **0 / 15** |
| Prefix hợp lệ | `data/.../05_company_export_json/넥스트아이_dataset_package_20260528T091409/` |
| Manifest (J06–J08) | Top-1 có thể là `manifest.json` (đúng lane) |

**Mẫu top source (rút gọn):**

| ID | Top-1 source |
|---|---|
| CE-J01–J05 | `.../splits/full.jsonl` |
| CE-J06–J08 | `.../manifest.json` |
| CE-J09–J15 | `.../splits/full.jsonl` |

**Caveat vận hành:** `config.py` đọc `VECTOR_STORE` / `QDRANT_PATH` lúc **import module**. Nếu set env sau khi đã import `retrieval_v3`/`rag_stack`, query có thể trỏ nhầm store cũ (ví dụ validation). `run_benchmark_case.py` set env **trước** `import ingest` — CSV OpenAI đã chạy qua runner này nên **đáng tin**. Script audit nên `importlib.reload(config)` hoặc chạy subprocess.

---

## 2) Eval matcher / alias / UTF-8

### Sửa đã áp dụng (2026-05-29)

- Module `src/eval_source_matcher.py`: NFKC, `package_split_match`, `split_alias_match`, record/doc.
- Báo cáo trước/sau: `reports/openai_validation_eval_fix_report.md` — hit/citation **0 → 1.0** trên 4 config validation.

### Phân bố `match_reason` (20 câu, retrieval + citation, index full)

| match_reason | retrieval | citation |
|---:|---:|---:|
| `package_split_match` | 20 | 20 |
| `split_alias_match` | 0 | 0 |
| `path_alias_match` | 0 | 0 |
| `no_match` | 0 | 0 |

**Giải thích:** Eval set trỏ `splits/dev.jsonl` trong khi benchmark validation/full ingest `validation.jsonl` / `full.jsonl` — matcher coi cùng `dataset_package_20260528T091409` → **không còn false miss** do tên split.

### UTF-8 / expected_source

| Kiểm tra | Kết quả |
|---|---|
| `eval_set_company_export_json_dev.md` path package Hàn | **UTF-8 đúng** (넥스트아이) |
| Mojibake trong expected_source | **Không phát hiện** trên 20 dòng hiện tại |
| J06–J08 expected → `manifest.json` | **Đã cập nhật** (P0.1) |

**Caveat (không làm lệch hit/citation embedding):**

- Hit/citation **cao có thể do matcher rộng** (package-level), không chứng minh record-level đúng — phù hợp gate retrieval lane, không phù hợp audit answer chất lượng.
- `answer_correctness` vẫn thấp (0.05–0.15) trên CSV validation — **không dùng** để xếp hạng embedding.

---

## 3) Fairness setup

### OpenAI YAML (validation / phase3 / e2e / smoke)

Đã quét: `configs/benchmark_exportjson_openai_*.yaml`

| Tiêu chí | Tất cả candidate OpenAI |
|---|---|
| `reranker` | `none` |
| `candidate_pool` | **64** |
| `retrieval_mode` | Không có cặp none vs rerank trên cùng config |
| So sánh Chroma vs Qdrant | Cùng chunking + retrieval + pool — **hợp lệ** |

**Kết luận OpenAI:** Các run `mc_20260529-102949_*` (validation) và `mc_20260529-103600_*` (phase3) **đủ fair** để so sánh chunking (`section_based` vs `recursive_800_120`) và vector store.

### Lịch sử local — đánh dấu INVALID

| Phạm vi | Trạng thái |
|---|---|
| `benchmark_exportjson` MiniLM **phase2 rerank** trước 2026-05-28 | **INVALID** nếu pool/mode không apples-to-apples (`prepare_exportjson_phase_configs.py` đã sửa `fair_pool=64`) |
| So sánh OpenAI vs local trên lane/corpus khác nhau | Chỉ mang tính **định hướng**, không phải A/B công bằng (`reports/bao-cao-10-...`) |

---

## 4) Vector index integrity

### Cache key (production full)

```
p=jsonl_v1__c=section_based_800_120__e=openai_text-embedding-3-small__d=nexteye_esg_v1_1_1_openai_full_e2e__lane=company_export_json_full__vs=qdrant__company=4321ffd13b
```

| Thành phần | Trạng thái |
|---|---|
| `.index_complete` | Có |
| `bm25_corpus.json` | 620 chunks; sources: `full.jsonl`, `manifest.json` |
| `qdrant_db` | Sample 200 điểm: 199 `full.jsonl`, 1 `manifest` — **không** còn `validation.jsonl` |
| `RAG_CHROMA_COLLECTION` | `bench_{md5(cache_key)[:16]}` trong `run_benchmark_case.py` |
| Dimension mismatch | `rag_stack.py` xóa `CHROMA_DIR` khi embedding dimension lệch (Chroma); Qdrant rebuild qua `RAG_FORCE_REBUILD` |

**Patch tối thiểu (vận hành, không bắt buộc cho kết luận embedding):**

- `production_config.py`: set thêm `os.environ["RAG_QDRANT_COLLECTION"]` tách theo cache key (hiện mặc định `rag_chunks` nhưng path Qdrant đã tách thư mục).

---

## 5) OpenAI embedding request safety

| Kiểm tra | Có? | Chi tiết |
|---|---|---|
| Batch theo document | **Có** | `RAG_OPENAI_EMBED_BATCH` (default 32), `_ingest_batches` trong `rag_stack.ingest_corpus_files` |
| Token budget / tránh 300k/request | **Có** (gián tiếp) | Batch nhỏ; lỗi full lane đã fix bằng batch (E2E) |
| Retry/backoff 429/timeout | **Không** | Không thấy `tenacity`/retry trong `rag_stack.py` |
| Checkpoint / resume job | **Một phần** | `--resume` + `reuse-index` + `.index_complete`; không resume giữa batch embed API |

**Patch tối thiểu nếu FAIL nghiêm ngặt mục 5:**

- File: `src/rag_stack.py` — bọc `add_documents` / `from_documents` với retry (429, 5xx, timeout) 3 lần exponential backoff.

**Đánh giá mục 5:** **PASS** cho benchmark đã chạy xong; retry là hardening ingest tương lai, không invalidate CSV validation/phase3 hiện có.

---

## CSV OpenAI đã chạy (tham chiếu)

| Run | hit | cit | Ghi chú |
|---|---:|---:|---|
| validation (4 config) | 1.0 | 1.0 | Sau matcher fix |
| phase3 (6 config) | 1.0 | 1.0 | Chroma vs Qdrant, cùng pool |
| e2e generative | 1.0 | 1.0 | Full lane; answer layer tách biệt |

Winner embedding comparison trong lane OpenAI: **cùng** `openai:text-embedding-3-small` — thực tế so sánh **chunking + retrieval + vector store**, không phải nhiều model embedding.

---

## Kết luận một dòng

**Benchmark đủ tin cậy để so sánh embedding** trong phạm vi lane OpenAI export JSON (validation/phase3) sau fix matcher 2026-05-29, với điều kiện: chỉ tin hit/citation/composite retrieval-weighted; không dùng run local MiniLM phase2 rerank cũ; bổ sung retry embed nếu chạy ingest dài trên mạng không ổn định.

---

## Phụ lục — tái kiểm tra

```powershell
cd E:\Documents\rag-pipeline-workflow
python scripts/openai_benchmark_bias_audit.py
# Kiểm tra nhanh top source (nên reload config):
python -c "import os,sys,importlib; from pathlib import Path; ..."
```
