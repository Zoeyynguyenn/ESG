# Báo cáo 10: Kết luận benchmark local, sai lệch kết quả và hướng production ESG

**Ngày:** 2026-05-29  
**Phạm vi:** Benchmark 3 pha trên lane `company_export_json`, dataset Nexteye package `091409`  
**Mục đích:** Tổng hợp ý nghĩa kết quả đã chạy xong, nguyên nhân metric bị lệch trên môi trường local CPU-only, và khung chọn stack cho production.

---

## 1. Tóm tắt điều hành

Ba pha benchmark **đã chạy xong**. Kết quả chính thức nằm tại:

| Pha | File kết quả |
|---|---|
| Pha 1 | `reports/benchmark_exportjson_phase1_results.csv` |
| Pha 2 | `reports/benchmark_exportjson_phase2_results.csv` |
| Pha 3 | `reports/benchmark_exportjson_phase3_results.csv` |

**Kết luận tổng quát:** Benchmark **có giá trị** để chốt **kiến trúc pipeline** (chunking, hybrid retrieval, loại trừ reranker không phù hợp ngôn ngữ), nhưng **chưa đủ** để chốt winner production chỉ dựa trên máy local CPU-only — đặc biệt khi Pha 2/3 trên lane validation/full cho `retrieval_hit_rate = 0` (cần rà eval trước khi tin metric đó).

Ba nguyên nhân làm kết quả **khó dùng trực tiếp cho production**:

1. **Chưa có GPT / generation thật** — mọi run đều `retrieval_only`, RAGAS `skipped`; chưa đo chất lượng câu trả lời end-to-end.
2. **Reranker tiếng Anh trên corpus đa ngôn ngữ** — `cross-encoder/ms-marco-MiniLM-L-6-v2` không phù hợp dữ liệu Hàn/ESG; đây là lỗi **chọn model**, không chứng minh reranker vô ích.
3. **CPU bottleneck với embedding lớn** — BGE-M3 index ~287–356s/case trên CPU trong khi MiniLM ~17–20s; thứ hạng composite bị ảnh hưởng bởi latency, không chỉ chất lượng retrieval.

**Vector store:** Trên cùng config MiniLM + dense, Pha 3 full lane Chroma composite cao hơn Qdrant một chút (~0.26 vs ~0.16–0.22). Ở quy mô lớn vẫn nên hướng **Qdrant** (hybrid native, metadata filter, scale ngang) theo thực hành open source phổ biến cho RAG production.

**Bước tiếp theo không bắt buộc GPU:** Đã có OpenAI API key — có thể chạy benchmark ngắn với `text-embedding-3-small`, GPT-4o-mini và RAGAS trước khi xin GPU.

---

## 2. Ba pha đã chạy — tổng quan kết quả

### 2.1. Pha 1 — So sánh chunking × embedding × retrieval (dev lane)

**Lane:** `company_export_json_dev`  
**Ma trận:** 3 chunking × 3 embedding × 2 retrieval (dense / hybrid), Chroma, reranker = none  
**Trạng thái:** **18/18 success**

| Nhóm | Số case | retrieval_hit_rate | composite_score (khoảng) | index_build_time (khoảng) |
|---|---|---|---|---|
| MiniLM (6 case) | 6 | 1.0 | **0.764 – 0.765** | ~17–20s |
| BGE-M3 (6 case) | 6 | 1.0 | 0.673 – 0.692 | ~287–356s |
| multilingual-e5-base (6 case) | 6 | 1.0 | 0.734 – 0.743 | ~78–89s |

**Điểm nổi bật Pha 1:**

- Dense và hybrid **cùng hit_rate 1.0** trên dev; composite gần nhau — hybrid không vượt trội rõ trên lane dev nhỏ.
- **MiniLM** composite cao nhất chủ yếu do **latency_normalized** tốt (index/query nhanh), không đồng nghĩa embedding tốt nhất cho production đa ngôn ngữ.
- **BGE-M3** và **e5** chạy thành công sau khi xử lý xung đột dimension Chroma (collection tách theo embedding).

### 2.2. Pha 2 — So sánh reranker (validation lane)

**Lane:** `company_export_json_validation`  
**Nội dung:** 3 top config từ Pha 1 × none vs rerank (`semantic_dense` / `semantic_dense_rerank`, pool = 64)  
**Trạng thái:** **6/6 success**

| config_id (rút gọn) | reranker | hit_rate | citation | composite | query_time_avg |
|---|---|---|---|---|---|
| rec800 dense none | none | 0.0 | 0.0 | 0.2449 | ~0.16s |
| rec800 dense rerank | ms-marco | 0.0 | 0.0 | 0.1843 | ~2.67s |
| rec512 dense none | none | 0.0 | 0.0 | 0.2468 | ~0.15s |
| rec512 dense rerank | ms-marco | 0.0 | 0.0 | 0.1725 | ~3.03s |
| section dense none | none | 0.0 | 0.0 | **0.2500** | ~0.14s |
| section dense rerank | ms-marco | 0.0 | 0.0 | 0.1833 | ~2.70s |

**Đọc Pha 2:**

- So sánh none vs rerank đã **cùng retrieval mode gốc** (dense) và **cùng pool = 64** — công bằng hơn các run trước.
- Reranker vẫn **composite thấp hơn** và **query chậm hơn ~15–20×** — phù hợp giả thuyết model MS MARCO không phù hợp ngôn ngữ corpus.
- **hit_rate / citation = 0 trên toàn Pha 2** — metric eval validation lane có vấn đề (alias ground truth, record-level vs split-level); **không dùng Pha 2 để chốt hit_rate production** cho đến khi sửa eval.

### 2.3. Pha 3 — So sánh Chroma vs Qdrant (full lane)

**Lane:** `company_export_json_full`  
**Nội dung:** Top config × Chroma vs Qdrant, dense, pool = 64  
**Trạng thái:** **6/6 success** (Qdrant `enabled`)

| config | vector_store | hit_rate | citation | composite | query_time_avg |
|---|---|---|---|---|---|
| section_based + MiniLM | chroma | 0.0 | 0.0 | **0.2575** | ~0.14s |
| section_based + MiniLM | qdrant | 0.0 | 0.0 | 0.1575 | ~0.18s |
| recursive_512 + MiniLM | chroma | 0.0 | 0.0 | 0.2035 | ~0.16s |
| recursive_512 + MiniLM | qdrant | 0.0 | 0.0 | 0.2213 | ~0.16s |
| recursive_800 + MiniLM | chroma | 0.0 | 0.0 | 0.2256 | ~0.16s |
| recursive_800 + MiniLM | qdrant | 0.0 | 0.0 | 0.2254 | ~0.16s |

**Đọc Pha 3:**

- Cả Chroma và Qdrant đều chạy ổn định; **không có lỗi runtime** so sánh vector DB.
- Trên metric hiện tại (hit/citation = 0), chỉ phân biệt được qua **composite** và **latency** — Chroma nhỉnh hơn một chút ở config `section_based`.
- Giống Pha 2, **hit_rate = 0** trên full lane cần điều tra eval — kết luận kiến trúc vẫn dựa chủ yếu vào **Pha 1 dev**.

---

## 3. Giá trị kết luận được / không được

### 3.1. Kết luận **được phép** rút ra

| Kết luận | Cơ sở |
|---|---|
| Pipeline ingest → index → retrieve chạy ổn định 3 pha | 30/30 case success trong CSV |
| Hybrid và dense tương đương trên dev (hit 1.0) | Pha 1 — 18 case |
| MiniLM phù hợp **benchmark nhanh trên CPU** | Index ~17–20s, composite dev cao nhất |
| BGE-M3 / e5 **chạy được** sau fix Chroma collection | Pha 1 — 12 case success |
| `ms-marco-MiniLM` reranker **không phù hợp** corpus đa ngôn ngữ hiện tại | Pha 2 — composite thấp hơn none, latency cao |
| Chroma và Qdrant **đều feasible** trên local | Pha 3 — 6/6 success |
| Chưa đo được chất lượng generation production | `retrieval_only` + RAGAS skipped |

### 3.2. Kết luận **chưa được** rút ra

| Chưa kết luận | Lý do |
|---|---|
| Winner embedding cho production | BGE/e5 bị penalize latency CPU; chưa có run OpenAI embedding |
| Reranker “vô dụng” nói chung | Chỉ test model tiếng Anh; chưa test reranker đa ngôn ngữ |
| Config tốt nhất trên validation/full | hit_rate = 0 — eval chưa phản ánh đúng |
| Latency production | Số local không map GPU/API |
| Chroma vs Qdrant ở scale lớn | Chỉ test corpus một công ty, metric hit bị 0 |

---

## 4. Nguyên nhân sai lệch kết quả

### 4.1. Không có GPT / generation thật

| Hiện trạng | Hệ quả |
|---|---|
| `benchmark_kind = retrieval_only` | Chỉ đo retrieval + heuristic citation |
| `ragas_status = skipped` | Không có faithfulness, answer relevancy từ judge |
| `answer_correctness` thấp (~0.05–0.15) | Placeholder extractive, không phản ánh GPT-4o-mini |

Benchmark trả lời: *“retrieval có tìm đúng chunk/lane không?”* — chưa trả lời: *“câu trả lời ESG có đủ tin cậy để dùng với khách hàng/đối tác không?”*

### 4.2. Reranker sai ngôn ngữ (không phải lỗi code pipeline)

| Thành phần | Thực tế Pha 2 |
|---|---|
| Model | `cross-encoder/ms-marco-MiniLM-L-6-v2` (MS MARCO, tiếng Anh) |
| Corpus | Export JSON ESG, tiếng Hàn + thuật ngữ chuyên ngành |
| So sánh | Cùng `semantic_dense`, pool = 64 — đã công bằng hơn |

Reranker làm **chậm query** (~2.7–3.0s vs ~0.15s) và **composite thấp hơn** none. Cần thử reranker **đa ngôn ngữ** (ví dụ `BAAI/bge-reranker-v2-m3` hoặc API rerank) trước khi bỏ hẳn bước rerank trong production.

### 4.3. CPU local vs GPU production — embedding

| Model | Index build (Pha 1, CPU) | Ghi chú production |
|---|---|---|
| MiniLM | ~17–20s | Nhanh local; trần chất lượng thấp hơn cho ESG đa ngôn ngữ |
| BGE-M3 | ~287–356s | Trên GPU thường giây/batch — hướng open source production phổ biến |
| e5-base | ~78–89s | Trung gian; cần so sánh thêm với API embedding |

**Lưu ý:** Các run Pha 1 đầu từng fail do Chroma reuse collection 384-dim khi embed 1024-dim; đã xử lý bằng collection tách theo cache key. Số liệu Pha 1 trong CSV hiện tại là sau fix.

### 4.4. Metric hit_rate = 0 trên validation/full (Pha 2 & 3)

Trên dev (Pha 1) hit_rate = 1.0; trên validation/full = 0.0 — chênh lệch này **không hợp lý về mặt retrieval thuần** nếu cùng pipeline. Khả năng cao:

- Ground truth eval trỏ `splits/*.jsonl` thay vì `record_id` / nguồn evidence thực;
- Lane full/validation cần scoring theo **record-level**, không chỉ file split.

**Hành động:** Sửa eval alias trước khi dùng Pha 2/3 để chốt winner; tạm thời **ưu tiên kết luận kiến trúc từ Pha 1**.

---

## 5. Chroma vs Qdrant

### 5.1. Kết quả từ Pha 3 (full lane, cùng embedding MiniLM)

Trên metric hiện tại, Chroma và Qdrant **đều chạy thành công**. Composite cao nhất: `section_based` + Chroma (0.2575). Qdrant không thua về độ ổn định runtime (`qdrant_status = enabled`).

### 5.2. Hướng production (tham khảo thực hành open source)

| Tiêu chí | Chroma | Qdrant |
|---|---|---|
| Mục đích | Dev, prototype, benchmark nhanh trên laptop | Production, multi-tenant, data lớn |
| Hybrid | BM25 file + dense riêng | Dense + sparse native, RRF |
| Metadata | Có, đủ cho dev | Filter mạnh: company, lane, source_type… |
| Scale | Single-node | Replication, horizontal scale |

**Kết luận:** Giữ **Chroma** cho dev/benchmark local; lộ trình production ESG nhiều công ty → **Qdrant**. Kết quả Pha 3 local **không bác bỏ** hướng này — chỉ cho thấy trên corpus nhỏ + metric hiện tại, Chroma không kém.

---

## 6. Đối chiếu với đánh giá AI và thực hành open source

Phần này tổng hợp **hướng dẫn từ đánh giá AI** (tài liệu phân tích pipeline RAG cho ESG) và **pattern phổ biến trong hệ thống RAG open source**, không phải kết quả benchmark trực tiếp.

| Bước | Hướng industry / open source | Benchmark local đã xác nhận | Production (đích) |
|---|---|---|---|
| Parse | pypdf / structured input; OCR khi cần | `pypdf` ổn định cho lane export JSON | pypdf + parser nâng cao có chọn lọc |
| Chunking | Structure-based, parent document | `section_based` tốt trên dev Pha 1 | section_based + parent expansion |
| Embedding | BGE / E5 hoặc API đa ngôn ngữ | MiniLM thắng composite **do CPU** | BGE-M3 (GPU) hoặc OpenAI embedding API |
| Retrieval | Hybrid + metadata filter | Hybrid ≈ dense trên dev | Hybrid RRF + filter company/lane |
| Reranker | Multilingual cross-encoder / API | ms-marco **không phù hợp** | bge-reranker-v2-m3 hoặc API rerank |
| Generation | LLM tiering (mini / full) | Chưa chạy | GPT-4o-mini + GPT-4o khi cần |

Các pattern open source đáng cân nhắc **sau** khi chốt baseline retrieval: query rewrite, kiểm tra evidence thấp (low-evidence), mở rộng parent chunk, metadata filter theo tenant — phù hợp bài toán ESG response readiness (nhiều nguồn, cần trích dẫn).

---

## 7. Khuyến nghị pipeline (tóm tắt)

### 7.1. Dev / benchmark trên laptop (CPU, có OpenAI key)

- Chunking: `section_based` (ưu tiên) hoặc `recursive_800_120`
- Embedding: `text-embedding-3-small` (API) hoặc MiniLM (offline)
- Retrieval: `hybrid_dense_bm25`
- Vector store: Chroma (nhanh) hoặc Qdrant (gần production)
- Reranker: tạm **none**; không dùng ms-marco cho tiếng Hàn
- Generation + eval: GPT-4o-mini + RAGAS

### 7.2. Production có GPU

- Embedding: `BAAI/bge-m3`
- Vector store: Qdrant
- Retrieval: hybrid native (dense + sparse RRF)
- Reranker: `BAAI/bge-reranker-v2-m3`
- Generation: GPT-4o-mini / GPT-4o

### 7.3. Hai pipeline candidate để thử tiếp

| ID | Chunking | Embedding (giai đoạn hiện tại) | Retrieval | Ghi chú |
|---|---|---|---|---|
| **A** | section_based | OpenAI `text-embedding-3-small` | hybrid | Dựa trên Pha 1 dev + hướng production |
| **B** | recursive_800_120 | OpenAI hoặc MiniLM | hybrid | Linh hoạt tài liệu ít cấu trúc |

---

## 8. Bảng lựa chọn stack: Local CPU | Có GPU | OpenAI API key

| Thành phần | Local chỉ CPU | Production có GPU | Giải pháp OpenAI API key (không cần GPU) |
|---|---|---|---|
| **PDF / JSON parse** | `pypdf` | `pypdf` + parser nâng cao khi cần OCR | `pypdf` (lane export JSON đã structured) |
| **Chunking** | `section_based` hoặc `recursive_800_120` | `section_based` + parent/small-to-large | Giống cột CPU |
| **Embedding** | `all-MiniLM-L6-v2` (nhanh, trần chất lượng) | **`BAAI/bge-m3`** | **`text-embedding-3-small`** (API, đa ngôn ngữ) |
| **Vector DB** | **Chroma** (dev nhanh) | **Qdrant** (scale, hybrid native) | **Chroma** (dev) hoặc **Qdrant** |
| **Lexical / sparse** | BM25 file (`bm25_corpus.json`) | Qdrant sparse (BM42/SPLADE) | BM25 file hoặc Qdrant nếu đã deploy |
| **Retrieval** | `hybrid_dense_bm25` | Hybrid RRF trên Qdrant | `hybrid_dense_bm25` |
| **Metadata filter** | `company`, lane, `source_type` | Pre-filter theo tenant | Giống CPU |
| **Reranker** | Không dùng ms-marco; tạm **none** | **`BAAI/bge-reranker-v2-m3`** | API rerank (nếu có) hoặc none |
| **Generation** | Extractive / rule (benchmark hiện tại) | GPT-4o-mini / 4o (API) | **GPT-4o-mini** |
| **Evaluation** | Internal hit/citation (Pha 1 dev tin hơn) | RAGAS + review spot check | **RAGAS** (judge qua OpenAI) |
| **Latency query (ước lượng)** | 25–90s (tùy index/rerank) | ~2–5s | ~2–4s (API embed + gen) |
| **Chi phí** | $0 model, tốn thời gian CPU | CapEx GPU + vận hành | OpEx API (nhỏ với corpus hiện tại) |
| **Phù hợp khi** | Debug kiến trúc, dataset nhỏ | Data lớn, nhiều công ty, SLA | Chốt chất lượng trước khi xin GPU |

---

## 9. Máy local — trả lời trực tiếp

| Câu hỏi | Trả lời |
|---|---|
| Máy CPU cho kết quả **sai** không? | **Không** — đúng với phạm vi đo (kiến trúc, loại reranker). |
| Máy CPU **đủ chốt production model** không? | **Chưa** — thiếu GPT/RAGAS; Pha 2/3 hit = 0 cần sửa eval; embedding lớn bị penalize. |
| Cần xin GPU ngay không? | **Không bắt buộc** nếu có OpenAI key; GPU khi scale lớn hoặc giảm chi phí API dài hạn. |

---

## 10. Bước tiếp theo đề xuất

1. Ghi `OPENAI_API_KEY` vào `.env` (không commit).
2. Sửa eval scoring validation/full (record-level, alias nguồn) — mở khóa Pha 2/3.
3. Chạy benchmark ngắn: 2 pipeline (A/B) × OpenAI embedding × `full_pipeline` + RAGAS.
4. Ghi kết quả vào `experiment_log.md` và `decisions.md`.
5. Proposal GPU chỉ sau khi có số liệu OpenAI run + ước tính chi phí ở quy mô N công ty.

---

## 11. Tài liệu tham chiếu trong repo

| Tài liệu | Đường dẫn |
|---|---|
| Kết quả Pha 1 | `reports/benchmark_exportjson_phase1_results.csv` |
| Kết quả Pha 2 | `reports/benchmark_exportjson_phase2_results.csv` |
| Kết quả Pha 3 | `reports/benchmark_exportjson_phase3_results.csv` |
| Log overnight (nếu cần đối chiếu) | `exportjson_overnight_3phase_20260528-210658.log` |
| Data contract dataset | `data_contract_dataset_team_v1_1.md` |
| Báo cáo benchmark ngày 28 | `reports/bao-cao-09-tong-hop-benchmark-va-dataset-esg-20260528.md` |
| Workflow state | `.rag/rag-pipeline-practice/progress.md`, `decisions.md` |

---

*Báo cáo tổng hợp kết quả 3 pha đã hoàn tất (2026-05-28/29). Số liệu lấy từ CSV kết quả chính thức; không thay thế experiment log chi tiết từng run.*
