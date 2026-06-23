# Báo cáo 13: Chốt production C2 và triển khai Git trên RunPod

**Ngày:** 2026-06-04 · **Nối tiếp:** [Báo cáo 12](bao-cao-12-chot-embed-openai-va-de-xuat-gpu-llm-20260602.md)  
**Dataset / eval:** `넥스트아이_dataset_package_20260528T091409` · 15 câu answerable-only (KO)

---

## 1. Tóm tắt

| Hạng mục | Kết quả |
|---|---|
| **Stack production** | **C2** — Qwen2.5-14B AWQ + bge-reranker GPU + OpenAI embed + Qdrant hybrid |
| **Gate benchmark** | **PASS** (hit 0.8667 · answer 0.7333 · composite **0.7667**) |
| **Deploy RunPod** | Git clone + volume cũ (cache/data/model) — **đã verify** |
| **Production YAML** | `production_c2_runpod_hybrid_qdrant_generative.yaml` — **frozen** |
| **Baseline OpenAI** | `production_openai_hybrid_qdrant_generative.yaml` — superseded (giữ so sánh) |

---

## 2. Công việc đã làm

1. **Benchmark C2 trên pod GPU** — vLLM local + rerank CUDA; gate đạt ngưỡng so OpenAI baseline.
2. **Chuẩn bị repo Git-first** — rà soát `data/` / `reports/`, `.gitignore`, docs RunPod; push code + script `scripts/runpod/`.
3. **Pod:** `git clone` → gắn cache/dataset từ volume cũ (`.bak`) → chạy lại benchmark (**run `mc_20260604-085911`**).
4. **Artifact** — kết quả pod → Git push → PC pull.
5. **Chốt production** — default production sang C2; cập nhật báo cáo gate và `decisions.md`.

---

## 3. Kết quả benchmark (eval 15 câu KO)

| Metric | OpenAI baseline | C2 pod | Gate |
|---:|---:|---:|:---:|
| hit / citation | 0.8667 | 0.8667 | ≥ 0.85 ✅ |
| answer | 0.7333 | 0.7333 | ≥ 0.70 ✅ |
| composite | 0.7533 | **0.7667** | ≥ 0.72 ✅ |
| latency | ~184 s | **~24 s** | — |

**Run tham chiếu:** `mc_20260604-024822` (pod chính thức) · `mc_20260604-085911` (xác nhận Git-first).  
**Miss cố định:** CE-J04, CE-J05 (retrieval) — không regression so baseline.

Chi tiết: `reports/c2-gpu-benchmark-summary.md`

---

## 4. Cài đặt

### 4.1 Hạ tầng RunPod (một lần)

| Hạng mục | Cấu hình |
|---|---|
| GPU | RTX **4090 24GB**, region cố định (vd. US-IL-1) |
| Network volume | **40–50 GB**, mount `/workspace` (model + venv + repo) |
| Port expose | **8000** (vLLM); tùy chọn 8888 (upload file) |
| Container disk | ≥ 40 GB |

Lần đầu: `c2_disk_and_venv_setup.sh` (venv `/workspace/venv`) → `c2_bootstrap_pod.sh` (tải Qwen AWQ + bge-reranker vào volume).  
**Lần sau** (volume còn): **không** bootstrap lại — chỉ Start pod.

### 4.2 Code và dữ liệu trên pod

| Thành phần | Cách đưa lên pod |
|---|---|
| **Code** | `git clone` / `git pull` → `bash scripts/runpod/c2_after_git_clone.sh` |
| **Dataset jsonl** | **Không** trên Git — copy từ `.bak`, zip, hoặc upload UI |
| **Index cache** | PC reindex → `c2_index_cache_only.zip` hoặc copy `artifacts/benchmark_cache/` |
| **`.env.c2`** | Copy từ backup hoặc `cp .env.c2.example .env.c2` + `OPENAI_API_KEY` |

GitHub private: mỗi người **PAT riêng** (Contents Read/Write); **không** share PAT trên pod dùng chung.

### 4.3 Biến môi trường (`.env.c2`)

| Biến | Giá trị / ghi chú |
|---|---|
| `OPENAI_API_KEY` | Key embed OpenAI (bắt buộc trên pod) |
| `OPENAI_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` |
| `OPENAI_BASE_URL` / `C2_LLM_BASE_URL` | **PC test:** proxy RunPod `https://<pod-id>-8000.proxy.runpod.net/v1` |
| `RAG_RERANK_ENABLED` | `true` · model `BAAI/bge-reranker-v2-m3` |

**Trên pod khi benchmark (Tab 2):** comment dòng proxy trong `.env.c2`, set `OPENAI_BASE_URL=http://127.0.0.1:8000/v1` và `C2_POD_LOCAL_VLLM=1` — tránh `answer=0` do URL proxy cũ.

---

## 5. Vận hành

### 5.1 Luồng benchmark gate C2 (mỗi lần chạy)

```text
Tab 1: c2_restart_vllm_tab1.sh  (vLLM, gpu-memory-utilization 0.68)
Tab 2: c2_tab2_run_all.sh       (verify → deps → benchmark 15 câu)
```

- **Embed:** gọi OpenAI API từ pod (key trong `.env.c2`).
- **Rerank + LLM:** GPU trên cùng pod; gate **không** hợp lệ nếu chạy full benchmark từ PC (thiếu rerank GPU).

### 5.2 Cập nhật code (không đổi dataset/cache)

```bash
cd /workspace/rag-pipeline-workflow
git pull
bash scripts/runpod/c2_after_git_clone.sh
# Tab 1 restart vLLM nếu cần → Tab 2 benchmark
```

### 5.3 Publish kết quả về PC / team

Pod không SSH: trên pod `git add reports/benchmark_*` → `git push` → PC `git pull`.  
Hoặc tải file qua RunPod File browser.

### 5.4 Pod Stop / Start và chi phí

- **Stop** sau benchmark — tiết kiệm phí GPU; **volume giữ** model, cache, repo.
- **Start** lại: Tab 1 vLLM → sẵn sàng; proxy URL đổi theo pod mới → cập nhật `.env.c2` trên **PC** nếu test từ ngoài.
- **LangGraph / team khác:** gọi **proxy LLM port 8000** khi pod Running — không cần account RunPod nếu RAG cung cấp URL.

### 5.5 Production runtime (frozen)

- Config: `configs/production_c2_runpod_hybrid_qdrant_generative.yaml`
- Runtime load: `src/production_config.py` (rerank bge + Qwen qua `C2_LLM_BASE_URL`)
- Hướng dẫn đầy đủ: `reports/c2-runpod-huong-dan-lam-theo.md`, `docs/RUNPOD_GIT.md`

---

*Báo cáo 13 — chốt C2 production và xác nhận luồng Git trên RunPod.*
