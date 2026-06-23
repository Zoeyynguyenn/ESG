# Tham khảo vận hành C2, handoff team, và hướng C2′ (chưa áp dụng)

**Trạng thái:** Tài liệu tham khảo từ thảo luận nội bộ (2026-06). **Chưa thay đổi production.**  
**Quyết định hiện tại:** Tiếp tục test và chốt trên **stack C2 frozen** (`configs/c2_runpod_stack.yaml`, gate PASS `mc_20260604-024822`).

**Liên quan:**

- Hướng dẫn làm theo pod: `reports/c2-runpod-huong-dan-lam-theo.md`
- Kết quả benchmark gate: `reports/c2-gpu-benchmark-summary.md`
- Stack frozen: `configs/c2_runpod_stack.yaml`

---

## 1. Stack C2 đang test (baseline)

| Thành phần | C2 hiện tại |
|---|---|
| GPU | RunPod RTX 4090 24GB (~$0.69/h tham chiếu) |
| LLM | Qwen2.5-14B-Instruct AWQ, vLLM Tab 1 |
| Rerank | `BAAI/bge-reranker-v2-m3` trên **cùng GPU** |
| Embed | OpenAI `text-embedding-3-small` |
| Retrieve | hybrid_dense_bm25, Qdrant, pool 64, top_k 4 |
| Gate (15 câu KO) | hit/cit ≥ 0.85, answer ≥ 0.70, composite ≥ 0.72 — **PASS** |

**Lưu ý vận hành gate trên pod:** benchmark Tab 2 dùng `OPENAI_BASE_URL=http://127.0.0.1:8000/v1`, `C2_POD_LOCAL_VLLM=1`; test từ PC dùng proxy RunPod trong `.env.c2`.

---

## 2. Git vs zip — khi nào phải upload/clone lại?

| Tình huống | Zip | Git |
|---|---|---|
| Lần đầu trên pod/volume mới | Upload bundle / unzip | `git clone` |
| Sửa code/config (volume còn) | Upload file đổi hoặc zip phần nhỏ | `git pull` trên pod |
| Index cache mới | Upload `c2_index_cache_only.zip` / rsync | Không commit (gitignore) |
| Stop/Start pod, volume giữ | Thường **không** upload lại | `git pull` nếu có commit mới |
| Pod/volume mới | Upload lại hoặc migrate volume | Clone lại nếu mất thư mục repo |

**Tóm lại:** Mỗi lần thay đổi chỉ sync **phần đổi**; không bắt buộc zip/clone toàn bộ nếu volume còn.

---

## 3. Ba team: Dataset → RAG → LangGraph

### Vai trò

| Team | Output | Không làm |
|---|---|---|
| **Dataset** | Dataset chuẩn hóa + manifest (PR Git) | Benchmark, LLM |
| **RAG** | Index, cache, benchmark CSV/summary, gate PASS | Báo cáo định tính cuối |
| **LangGraph** | Báo cáo, định hướng từ artifact RAG + LLM | Reindex, rerank GPU, chốt metric |

### Luồng đề xuất

1. Dataset → PR vào `data/` (+ eval nếu có).
2. RAG → merge → reindex PC → sync cache pod → benchmark → **publish artifact** (xem mục 4).
3. LangGraph → pull tag/release → đọc CSV/summary/evidence → gọi **proxy LLM** (không cần RunPod account).

### Ai cần RunPod?

| Thành phần | Team RAG (pod) | LangGraph |
|---|---|---|
| Rerank GPU (gate C2) | **Có** | Không |
| vLLM Qwen | RAG vận hành | Gọi **proxy OpenAI-compatible** |
| Benchmark | RAG | Không (dùng artifact đã publish) |

**Proxy Tab 1 = chỉ LLM**, không kèm retrieve/rerank. Full RAG end-to-end cần **RAG API** do team RAG expose.

---

## 4. Publish artifact (pod → team khác)

**Luồng chuẩn:** pod ghi `reports/` → **SCP về PC** → `git commit` + push (+ tag nếu PASS).

Script PC: `scripts/fetch_c2_results_from_pod.ps1` (sửa `$PodHost`, `$PodPort` theo pod).

**Nên commit:** CSV, summary, audit, manifest (run_id, commit hash).  
**Không commit:** cache index, model weights, `.env.c2`.

Không khuyến khích `git push` trực tiếp từ pod (token, pod ephemeral).

---

## 5. Benchmark pod vs production

| | Benchmark / gate | Production (khách dùng) |
|---|---|---|
| Pod | Start → chạy eval → có thể **Stop** | **Luôn sẵn sàng** (hoặc scale) |
| Chi phí | Theo giờ chạy | GPU **24/7 ≈ $504/tháng** (4090 @ $0.69/h) nếu pod chạy liên tục |
| LangGraph | Đọc artifact Git | Gọi proxy LLM khi pod prod **Running** |

Benchmark và prod nên **tách tư duy** (có thể tách pod sau này).

---

## 6. Concurrent user (5–10) trên pod C2 hiện tại

- **Full pipeline** (retrieve + rerank GPU + generate): **1–3** request song song ổn; **5–10** dễ queue, OOM rerank, latency cao.
- **Chỉ LLM** qua proxy: **2–5** request có thể; **10** vẫn khó trên một 4090.
- Prod nhiều user: **queue (job_id)**, giới hạn concurrent, hoặc scale ngang (n pod).

---

## 7. Rerank có thực sự cần thiết?

**Trên eval gate 15 câu KO (cùng retrieve/embed):**

| Metric | OpenAI baseline (`rerank=none`) | C2 (`bge` GPU) |
|---|---:|---:|
| hit / citation | 0.8667 | 0.8667 |
| answer | 0.7333 | 0.7333 |
| groundedness | 0.60 | **0.7333** |
| composite | 0.7533 | **0.7667** |

→ Rerank **không** kéo hit/answer trên tập này; giúp **groundedness** và composite nhẹ.  
→ Eval khó hơn (50 câu V3): hybrid + rerank từng giúp citation rõ hơn không rerank.

**Kết luận tham khảo:** Rerank không luôn bắt buộc mọi metric; với C2 frozen vẫn giữ bge cho gate đã PASS. Mở rộng eval trước khi bỏ rerank prod.

---

## 8. GPU vs OpenAI vs Rerank API

- **OpenAI:** mạnh embed + chat; **không có Rerank API** → không all-in OpenAI cho RAG gate hiện tại.
- **C2 hybrid:** embed OpenAI + rerank local + Qwen local.
- **Nghẽn prod:** rerank + vLLM **cùng GPU** (vLLM cap `gpu-memory-utilization 0.68`).

**Rerank API** (Cohere, Jina, Voyage, Mixedbread): bỏ rerank khỏi VRAM pod → vLLM dùng ~0.90–0.95 VRAM → concurrent LLM tốt hơn. Chi phí rerank API thường **nhỏ** so với bill GPU 24/7; **phải ablation** trước khi đổi spec.

---

## 9. Rerank API — gợi ý tham khảo (chưa benchmark trong repo)

Giả định: pool 64 chunk, ~450 token/chunk, query ~80 token → ~33k token/request (Voyage/Jina).

| Nhà cung cấp | Model gợi ý | Giá tham chiếu | ~$/1k query | Ghi chú |
|---|---|---|---:|---|
| **Voyage** | `rerank-2.5-lite` | $0.02 / 1M token | **~$0.7** | 200M token free/account |
| **Jina** | `jina-reranker-v2-base-multilingual` | ~$0.02 / 1M token | **~$0.7** | KO/multilingual; 10M token free key mới |
| **Cohere** | `rerank-v3.5` / multilingual | $2 / 1.000 search | **~$2** | 1 search ≤100 doc; doc dài có thể split billing |
| **Mixedbread** | `mxbai-rerank-large-v2` | ~$7.50 / 1k query | **~$7.5** | Đắt; có instruction rerank |

Verify giá tại trang chính thức trước khi budget.

### So với chi phí C2 GPU (chỉ rerank)

| Query/tháng | bge trên pod* | Rerank API (Voyage/Jina) | Cohere |
|---:|---:|---:|---:|
| 1.000 | (trong GPU) | ~$0.7 | ~$2 |
| 10.000 | (trong GPU) | ~$7 | ~$20 |
| 100.000 | (trong GPU) | ~$74 | ~$200 |

\* bge không tính riêng — nằm trong **~$504/tháng** (4090 24/7 @ $0.69/h).

---

## 10. Hướng C2′ — tham khảo cost ≤ C2, chất lượng giữ (chưa áp dụng)

**Mục tiêu:** Chi phí ≤ C2, không tụt metric gate rõ.

### Phương án A (ưu tiên tham khảo)

```text
Embed / retrieve  → giữ nguyên C2
Rerank            → Voyage rerank-2.5-lite hoặc Jina multilingual (API)
LLM               → Qwen2.5-14B AWQ (giữ nguyên)
GPU               → RTX 3090 24GB hoặc NVIDIA L4 24GB (không cần 4090)
vLLM              → gpu-memory-utilization 0.90–0.95
```

**Ước tính:** GPU ~$290–350/tháng + rerank API vài USD–vài chục USD/tháng (volume vừa) → **thấp hơn C2 ~30–45%**.  
**Chất lượng:** Giữ nếu ablation PASS cùng gate; **latency** chậm hơn 4090, không đổi token LLM.

### Phương án B (dự phòng)

3090/L4 + Qwen 14B + **`rerank=none`** — hit/answer giống trên 15 câu; groundedness có thể giảm. Chỉ cân nhắc sau eval mở rộng.

### GPU rẻ hơn — tốc độ

| GPU | VRAM | Qwen 14B AWQ | Tốc độ vs 4090 |
|---|---|---|---|
| RTX 4090 | 24GB | ✅ C2 hiện tại | Baseline |
| RTX 3090 / L4 | 24GB | ✅ Đủ | Chậm hơn ~40–80% decode |
| RTX A5000 | 24GB | ✅ Đủ | Chậm; thường kém 3090/$ trên RunPod |

**Cùng model AWQ → output quality giống; chỉ khác thời gian chờ.**

### Ablation đề xuất (khi rảnh, sau C2)

1. C2 baseline (bge GPU, 4090)  
2. Voyage lite API + Qwen  
3. Jina multilingual API + Qwen  
4. (Optional) rerank none + Qwen  

Chọn config **rẻ nhất** vẫn ≥ gate → ghi spec `c2_prime` riêng, **không ghi đè** C2 frozen.

---

## 11. Checklist handoff LangGraph (tóm tắt)

- [ ] RAG push đủ repo (kể cả `scripts/runpod/*`)
- [ ] Tag release sau benchmark PASS
- [ ] LangGraph nhận: CSV/summary + proxy URL + model id (không cần RunPod login)
- [ ] Document: benchmark gate chạy pod; LangGraph prod gọi API
- [ ] Pod schedule / health check khi prod 24/7

---

## 12. Quyết định tạm thời

| Hạng mục | Trạng thái |
|---|---|
| Stack test / gate | **C2 frozen** (4090 + bge + Qwen + OpenAI embed) |
| C2′ / rerank API / GPU 3090-L4 | **Chỉ tham khảo** — chưa config, chưa đổi production YAML |
| Ablation rerank API | **Chưa chạy** — làm sau khi C2 ổn định |
| Production YAML | Chưa đổi — chờ xác nhận sau test C2 |

---

*Tài liệu này có thể cập nhật khi có kết quả ablation hoặc thay đổi quyết định chính thức trong `.rag/rag-pipeline-practice/decisions.md`.*
