# Báo cáo 12: Chốt embedding OpenAI và đề xuất 3 cặp GPU + LLM

**Ngày:** 2026-06-02 · **Nối tiếp:** [Báo cáo 11](bao-cao-11-chot-pipeline-openai-20260529.md)  
**Dataset:** `넥스트아이_dataset_package_20260528T091409` · eval tiếng Hàn

---

## 1. Tóm tắt


| Hạng mục            | Quyết định                                                          |
| ------------------- | ------------------------------------------------------------------- |
| **Embed**           | `**openai:text-embedding-3-small`** — giữ                           |
| **bge-m3 embed**    | Chỉ khi privacy / retrieval tốt hơn rõ / chi phí API embed vượt GPU |
| **Retrieve (BC11)** | `section_based` 800/120 · Qdrant · hybrid pool 64                   |
| **GPU pod**         | Rerank + LLM only — **không** embed trên GPU                        |
| **Cặp ưu tiên**     | **C2 — RTX 4090 + Qwen2.5-14B Q4** (+ bge-reranker-v2-m3)           |


Production YAML (`configs/production_openai_hybrid_qdrant_generative.yaml`) **chưa đổi** cho đến khi triển khai GPU xác nhận ổn.

---

## 2. Phần đầu pipeline — đã chốt

```text
package → section_based 800/120 → OpenAI embed → Qdrant hybrid (pool 64)
        → [GPU] bge-reranker-v2-m3 → Qwen generative
```


| Thành phần        | Giá trị                                      | GPU pod? |
| ----------------- | -------------------------------------------- | -------- |
| Chunking          | section_based **800/120**                    | Không    |
| Embedding         | **text-embedding-3-small**                   | Không    |
| Vector + retrieve | Qdrant · **hybrid_dense_bm25** · pool **64** | Không    |
| Rerank + LLM      | bge-reranker-v2-m3 · Qwen2.5-Instruct        | **Có**   |


**BC11 đã đo:** hit/citation **1.0** · generative composite **0.7875** · index 1 cty **~58–64 s** (OpenAI embed).

---

## 3. Khi nào dùng bge-m3 (embed)?

**Mặc định: không.** Giữ OpenAI embed.


| Chỉ chuyển bge-m3 khi                                | Không chuyển khi                                                |
| ---------------------------------------------------- | --------------------------------------------------------------- |
| Data **không được** ra API ngoài                     | Chỉ muốn giảm bill **LLM** → dùng GPU + Qwen                    |
| A/B chứng minh retrieval **+2–3%** composite         | Chỉ thiếu rerank → thêm **bge-reranker**, giữ OpenAI embed      |
| Chi phí token embed/tháng **>** chi phí GPU re-index | Scale 10–100 cty (~$0.1–1.2/tháng embed) — vẫn rẻ hơn GPU embed |


---

## 4. Chi phí embed: OpenAI vs bge-m3 GPU

Giá OpenAI: **$0.02 / 1M token** · ước ~200K token mới/ngày (10 cty).


| Quy mô  | OpenAI/tháng | bge-m3 GPU/tháng* |
| ------- | ------------ | ----------------- |
| 10 cty  | **~$0.12**   | ~$0.5–2           |
| 100 cty | **~$1.20**   | ~$1–4             |


 2–4 h re-index × $0.27–0.69/hr GPU. **Kết luận: OpenAI embed rẻ hơn ở quy mô hiện tại.**

---

## 5. Ba cặp GPU + LLM

**Chung:** embed OpenAI · rerank **bge-reranker-v2-m3** · volume **~50GB** cache model · Stop pod khi không dùng.

### 5.1. Tổng quan


| ID     | GPU           | LLM                   | Vai trò           | Ưu tiên          |
| ------ | ------------- | --------------------- | ----------------- | ---------------- |
| C1     | A5000 24GB    | Qwen2.5-**7B** Q4     | Rẻ · POC          | Dự phòng         |
| **C2** | **4090 24GB** | Qwen2.5-**14B** Q4    | **Cân bằng 24GB** | **★ Chọn trước** |
| C3     | L40S 48GB     | Qwen2.5-**14B** 8-bit | Headroom · scale  | Khi C2 OOM       |


### 5.2. Giá RunPod (tham chiếu)


| GPU         | VRAM  | ~$/giờ         | vs A5000 |
| ----------- | ----- | -------------- | -------- |
| A5000       | 24 GB | **$0.27**      | 1×       |
| **4090**    | 24 GB | **$0.69**      | ~2.5×    |
| L40S        | 48 GB | **$0.67–0.79** | ~2.5–3×  |
| Volume 50GB | —     | **$3.5/tháng** | cố định  |


### 5.3. So sánh 3 cặp (một bảng)


| Tiêu chí          | C1 A5000+7B   | **C2 4090+14B** ★ | C3 L40S+14B |
| ----------------- | ------------- | ----------------- | ----------- |
| ~$/giờ GPU        | **Thấp nhất** | Cao               | TB          |
| ~$/4h chạy        | **~$1.1**     | ~$2.8             | ~$2.7–3.2   |
| Tốc độ LLM (ước)  | 100%          | **130–160%**      | 120–150%    |
| query E2E (ước)   | 1.5–2.5 s     | **1.2–2.0 s**     | 1.2–2.0 s   |
| VRAM (rerank+LLM) | ~7–8 GB       | **~10–12 GB**     | ~16–18 GB   |
| Chất lượng answer | ★★★           | **★★★★**          | ★★★★☆       |
| Ổn định 24GB      | Dư VRAM       | **Vừa**           | —           |


```text
Tốc độ LLM (tương đối):  C1 ████████░░   C2 ██████████████   C3 █████████████░
Chi phí/giờ:             C1 ██░░░░░░░░   C2 ██████░░░░░░   C3 ██████░░░░░░
Chất lượng (ước):        C1 ███░░░░░░░   C2 ████████░░░░   C3 █████████░░░
```

### 5.4. Vì sao ưu tiên **C2**


| Lý do                                   | Giải thích ngắn                                                                    |
| --------------------------------------- | ---------------------------------------------------------------------------------- |
| **Cùng giá giờ 4090, model lớn hơn 7B** | 14B Q4 + rerank vừa 24GB — tận dụng GPU hơn 4090+7B                                |
| **Chất lượng**                          | 14B phù hợp ESG Hàn / governance hơn 7B; BC11 answer mới 12/20                     |
| **Tốc độ**                              | Nhanh hơn A5000+7B; gần mốc OpenAI ~2.05 s/câu                                     |
| **Chi phí hợp lý**                      | Đắt hơn C1 ~2.5×/giờ nhưng một cặp đủ production 24GB — không cần L40S trừ khi OOM |


**C1:** chỉ khi budget cực thấp hoặc region không có 4090.  
**C3:** khi C2 OOM hoặc nhiều user đồng thời.  
**4090+7B:** không ưu tiên — cùng giá C2 nhưng model nhỏ hơn.

### 5.5. Vì sao chọn **Qwen2.5-Instruct** (không chọn LLM khác)

Bài toán: **QA RAG ESG tiếng Hàn** — đọc context ngắn, trả lời có căn cứ, metadata (ticker, corp code, insufficient).


| LLM / hướng                | Tiếng Hàn                             | QA + instruction | Self-host 4090 (7–14B) | Phù hợp RAG ESG | Ghi chú                                                  |
| -------------------------- | ------------------------------------- | ---------------- | ---------------------- | --------------- | -------------------------------------------------------- |
| **Qwen2.5-Instruct** ★     | **Tốt** (train đa ngôn ngữ, CJK mạnh) | **Tốt**          | **7B / 14B Q4**        | **Cao**         | vLLM/Ollama phổ biến; bản Instruct sẵn                   |
| Llama 3.1 Instruct         | TB                                    | Tốt (EN)         | 8B / 70B               | TB              | Hàn không phải thế mạnh; 70B không vừa 4090              |
| Mistral / Mixtral Instruct | Yếu–TB                                | Tốt (EN/EU)      | 7B ok                  | TB              | Ít tối ưu cho corpus KO + thuật ngữ Hàn                  |
| Nemotron / diffusion 8B    | TB                                    | Khác mục tiêu    | 8B                     | **Thấp**        | Hướng reasoning/diffusion — không phải Instruct QA chuẩn |
| Gemma 2 Instruct           | TB                                    | Tốt              | 9B / 27B               | TB              | 27B chật 24GB; Hàn kém Qwen trong thực hành đa ngôn ngữ  |
| **gpt-4o-mini (API)**      | Tốt                                   | Tốt              | Không self-host        | Cao (BC11)      | **Tốn token tích lũy** — lý do chuyển GPU                |


**Chọn Qwen vì:**

1. **Ngôn ngữ:** export JSON Nexteye + eval KO — cần hiểu **Hàn + số/metadata**; Qwen2.5 thường ổn hơn Llama/Mistral cùng size trên task đa ngôn ngữ.
2. **Dạng model:** **Instruct** — sẵn cho “đọc context → trả lời / nói insufficient”, khớp layer generative trong repo.
3. **VRAM thực tế:** **7B và 14B quant** chạy được trên 4090 **cùng reranker** — không cần model 32B+ trên 24GB.
4. **Hệ sinh thái:** weights Hugging Face, AWQ/GPTQ, **vLLM** — dễ cache trên RunPod volume, API kiểu OpenAI (gần cách repo đang gọi LLM).
5. **Chi phí vận hành:** thay **gpt-4o-mini trả theo token** bằng **trả theo giờ GPU** — Qwen 14B là điểm cân bằng chất lượng/chi phí trên C2.

**Không chọn làm mặc định:** Llama/Mistral (Hàn yếu hơn cùng size) · Nemotron diffusion (sai use case) · model >32B trên 4090 (OOM hoặc quant quá nặng).

---

## 6. RunPod — lưu ý ngắn


| #   | Việc                                                    |
| --- | ------------------------------------------------------- |
| 1   | Volume **cùng region** pod (ví dụ `rag-models-ko` 50GB) |
| 2   | **Running** = trả GPU · **Stop** = hết tiền GPU         |
| 3   | Model cache trên volume — không tải lại mỗi lần bật     |
| 4   | Embed vẫn gọi OpenAI từ máy/VPS                         |


---

## 7. Kết luận

1. **Chốt phần đầu:** OpenAI embed + Qdrant hybrid (BC11).
2. **bge-m3 embed:** chưa dùng — xem mục 3.
3. **GPU + LLM:** ưu tiên **C2 (4090 + Qwen2.5-14B Q4 + bge-reranker-v2-m3)** — LLM **Qwen2.5-Instruct** vì phù hợp Hàn/ESG và self-host 24GB (mục 5.5).
4. **YAML production:** chưa cập nhật — triển khai C2 đang theo `reports/c2-gpu-setup-test-journal.md`.

---

*Báo cáo đề xuất kỹ thuật — C2 đã chốt triển khai 2026-06-03.*