# Nhật ký setup & test — Cặp C2 (RunPod 4090 + Qwen2.5-14B-Instruct Q4)

**Chốt:** 2026-06-03 · **Tham chiếu:** [Báo cáo 12](bao-cao-12-chot-embed-openai-va-de-xuat-gpu-llm-20260602.md) · **Config stack:** `configs/c2_runpod_stack.yaml`

Mọi bước setup → test phải ghi vào file này (checkbox + log có timestamp). Không cập nhật production YAML cho đến khi **Phase 6** đạt gate.

---

## Cặp C2 (đã chốt)

| Thành phần | Giá trị |
|---|---|
| GPU | RunPod **RTX 4090 24GB** (~$0.69/h) |
| LLM | **Qwen2.5-14B-Instruct** · quant **Q4/AWQ** · serve **vLLM** (OpenAI-compatible API) |
| Reranker | **BAAI/bge-reranker-v2-m3** (trên host có CUDA) |
| Embed | **Giữ** `openai:text-embedding-3-small` (máy/VPS, không trên pod) |
| Retrieve | Qdrant · `hybrid_dense_bm25` · pool 64 (BC11) |

**Baseline OpenAI (so sánh):** `reports/openai_e2e_answerable_ko_rerun_report.md` — hit/cit 0.8667 · answer 0.7333 generative · composite 0.7533.

---

## Tiến độ theo phase

| Phase | Nội dung | Trạng thái |
|---:|---|:---:|
| 0 | Chốt phương án C2 + artifact repo | ✅ |
| 1 | RunPod: volume + pod 4090 + region | ✅ |
| 2 | Bootstrap pod: tải model + `c2_bootstrap_pod.sh` | ✅ |
| 3 | vLLM chạy ổn (`/v1/models`, generate thử) | ✅ |
| 4 | Máy/VPS: `.env.c2` + `c2_gpu_preflight.py` | ✅ (PC) |
| 5 | Test reranker isolated (1–2 câu eval) | ⬜ (Tab 2 verify) |
| 6 | E2E benchmark C2 (`benchmark_exportjson_c2_gpu_e2e.yaml`) | ✅ pod `mc_20260604-024822` composite **0.7667** gate PASS |
| 7 | So sánh metric vs OpenAI + quyết định đổi production YAML | ⬜ |

---

## Phase 0 — Chốt & chuẩn bị repo

**Ngày:** 2026-06-03

| Artifact | Mô tả |
|---|---|
| `configs/c2_runpod_stack.yaml` | Định nghĩa stack C2 + gate so với OpenAI |
| `configs/benchmark_exportjson_c2_gpu_e2e.yaml` | Benchmark 15 câu · generative · bge-reranker |
| `.env.c2.example` | Mẫu biến môi trường (copy → `.env.c2`, không commit) |
| `scripts/runpod/c2_bootstrap_pod.sh` | Bootstrap trên pod |
| `scripts/c2_gpu_preflight.py` | Kiểm tra embed + vLLM + CUDA rerank + index cache |
| `scripts/run_c2_gpu_e2e.ps1` | Chạy benchmark C2 từ Windows |

**Kiến trúc vận hành (khuyến nghị):**

```text
[VPS/PC dev]  OpenAI embed + Qdrant index + run_benchmark
       |
       |  HTTP OpenAI-compatible
       v
[RunPod 4090] vLLM (Qwen 14B Q4)  +  CrossEncoder rerank (bge-reranker-v2-m3)
```

Chạy benchmark **trên pod** (SSH) nếu rerank cần GPU; hoặc vLLM trên pod + rerank local (chậm hơn).

---

## Phase 1 — RunPod hạ tầng

**Checklist (ghi kết quả khi xong):**

- [x] Tạo Network Volume `rag-models-ko` **40GB**, **cùng region** với pod (US-IL-1)
- [x] Chọn template/pod **RTX 4090 24GB**
- [x] Gắn volume vào `/workspace`
- [ ] Mở port **8000** (vLLM) — RunPod TCP proxy hoặc HTTP service
- [x] Ghi `RUNPOD_POD_ID`, region, URL proxy vào log bên dưới

**Log:**

| Thời gian | Việc | Kết quả |
|---|---|---|
| 2026-06-03 | Deploy pod | `universal_sapphire_hawk`, Running, 4090 24GB |
| 2026-06-03 | Web Terminal | `df -h /workspace` → mount `mfs#us-il-1...` tại `/workspace`; `ls` → thư mục trống (OK) |
| | SSH (tùy chọn) | `203.57.48.116:10155` |
| | vLLM URL port 8000 | chưa expose |

---

## Phase 2 — Bootstrap model trên pod

**Lỗi CRLF (Windows upload):** nếu thấy `set: pipefail` / `invalid option`, chạy trước:

```bash
sed -i 's/\r$//' /workspace/c2_bootstrap_pod.sh
```

```bash
# Trên pod (SSH)
bash /workspace/rag-pipeline-workflow/scripts/runpod/c2_bootstrap_pod.sh
# hoặc clone repo rồi chạy script tương đương
```

**Checklist:**

- [x] Log `c2_bootstrap.log` — pip xong (cảnh báo pyzmq/Jupyter, bỏ qua)
- [x] Cache HF: `Qwen/Qwen2.5-14B-Instruct-AWQ` 100%
- [x] Cache: `BAAI/bge-reranker-v2-m3` 100%
- [x] File `/workspace/start_c2_vllm.sh` tạo thành công
- [ ] CUDA/vLLM thực tế chạy GPU (script in `cuda False` — xác nhận ở Phase 3)

**Log:**

| Thời gian | Việc | Kết quả |
|---|---|---|
| 2026-06-03 | Bootstrap (sau fix CRLF) | Model tải OK; CUDA check script = False; tiếp Phase 3 vLLM |

---

## Phase 3 — vLLM serve & smoke LLM

**Neu `EngineCore failed` / `cuda False`:** bootstrap da pip ghi de torch CPU. Chay:

```bash
sed -i 's/\r$//' /workspace/c2_fix_torch_cuda.sh
bash /workspace/c2_fix_torch_cuda.sh
```

**Neu `No space left on device`:** pip/vLLM cai vao **o container ~20GB**, khong phai volume 40GB. Lam:

1. RunPod → Edit pod → **Container Disk 40–50GB** → Stop/Start (volume `rag-models-ko` giu model).
2. Tren pod: `pip cache purge`; dung **venv tren /workspace** — script `scripts/runpod/c2_disk_and_venv_setup.sh`.

**Neu `Qwen2Tokenizer has no attribute all_special_tokens_extended`:** transformers 5.x vs vLLM 0.7.3 — trong venv:

```bash
source /workspace/venv/bin/activate
pip install "transformers>=4.45.0,<4.49.0" "tokenizers>=0.20,<0.22"
python -c "import transformers; print(transformers.__version__)"
```

Rồi start vLLM lại; co the dung `--quantization awq_marlin` thay `awq` (nhanh hon).


```bash
# Hoac dan khoi lenh:
python3 -m pip uninstall -y vllm torch torchvision torchaudio
python3 -m pip install "torch==2.4.0" "torchvision==0.19.0" --index-url https://download.pytorch.org/whl/cu124
python3 -m pip install -U "vllm>=0.8.0"
python3 -c "import torch,vllm; print(torch.__version__, torch.cuda.is_available(), vllm.__version__)"
```

```bash
/workspace/start_c2_vllm.sh
# Pod local:
curl -s http://127.0.0.1:8000/v1/models
```

**Lỗi `No such file /workspace/rag-pipeline-workflow`:** pod chỉ có model + vLLM, **chưa upload repo**. Cách nhanh (không SSH):

1. **PC:** `.\scripts\build_c2_pod_bundle.ps1` → `artifacts/c2_pod_bundle.zip` (~4.4 MB)
2. RunPod → pod → **Upload** file zip vào `/workspace`
3. **Tab 2:**

```bash
cd /workspace
apt-get update -qq && apt-get install -y -qq unzip
unzip -o c2_pod_bundle.zip
cd rag-pipeline-workflow
sed -i 's/\r$//' scripts/runpod/*.sh
bash scripts/runpod/c2_tab2_run_all.sh
```

Hoặc **PC có SSH** (lấy IP/port mới từ RunPod → Connect):

```powershell
.\scripts\push_c2_bundle_to_pod.ps1 -PodHost <IP> -PodPort <PORT>
```

```bash
sed -i 's/\r$//' /workspace/rag-pipeline-workflow/scripts/runpod/c2_verify_pod.sh 2>/dev/null || true
bash /workspace/rag-pipeline-workflow/scripts/runpod/c2_verify_pod.sh
```

Hoặc thủ công — **phải dùng đúng tên model Qwen**, không `gpt-4o-mini`:

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-14B-Instruct-AWQ","messages":[{"role":"user","content":"안녕"}],"max_tokens":32}'
```

**Lỗi `gpt-4o-mini does not exist` trên vLLM:** client (PC) gửi sai `model` — `.env` có `OPENAI_MODEL=gpt-4o-mini` trong khi `OPENAI_BASE_URL` trỏ RunPod. **`.env.c2` phải ghi đè** (`OPENAI_MODEL=Qwen/...`). Đã sửa loader trong repo.

**Checklist:**

- [x] `/v1/models` trả danh sách model — `Qwen/Qwen2.5-14B-Instruct-AWQ`
- [ ] `POST /v1/chat/completions` — câu thử tiếng Hàn (tùy chọn)
- [x] vLLM 0.7.3 + venv `/workspace/venv` + transformers 4.x

**Log:**

| Thời gian | Việc | Kết quả |
|---|---|---|
| 2026-06-03 | vLLM Tab1 complete + curl models | OK — model id `Qwen/Qwen2.5-14B-Instruct-AWQ`, max_model_len 8192 |

---

## Phase 4 — Máy dev / VPS wiring

1. Copy `.env.c2.example` → `.env.c2` (không commit).
2. Điền `OPENAI_BASE_URL` = URL proxy RunPod vLLM (`.../v1`).
3. Giữ `OPENAI_API_KEY` cho embed.

```powershell
python scripts/c2_gpu_preflight.py
# Sau khi vLLM sẵn sàng:
$env:C2_PREFLIGHT_STRICT = "true"
python scripts/c2_gpu_preflight.py
```

**Checklist:**

- [x] `openai_embed` OK
- [x] `vllm_llm` OK (proxy `...-8000.proxy.runpod.net/v1`, Qwen AWQ)
- [x] `index_cache` OK
- [x] `rerank_cuda` — **CPU fallback** trên máy dev (benchmark vẫn chạy CrossEncoder CPU)

**Log:**

| Thời gian | Việc | Kết quả |
|---|---|---|
| 2026-06-03 | Preflight local (chưa có pod) | embed **OK** · index **OK** · vLLM **FAIL** (chưa `OPENAI_BASE_URL` pod) · rerank **FAIL** (máy dev không CUDA) |
| 2026-06-03 | Sửa URL `.env.c2` (`//v1` → `/v1`) + UA preflight | vLLM **OK** · embed **OK** |
| 2026-06-03 | curl + LangChain smoke Qwen | HTTP 200 · trả lời OK qua proxy 8000 |

---

## Phase 5 — Test reranker (cô lập)

```powershell
$env:RAG_RERANK_ENABLED = "true"
$env:RAG_RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
$env:RAG_RERANK_STRICT = "true"
# 1 cau thu qua retrieval_v3 / smoke script
```

**Checklist:**

- [x] Rerank không fallback overlap (strict) — CrossEncoder CPU trên máy dev
- [x] Latency ghi nhận: query avg **2.88 s** (tổng E2E 105 s / 15 câu)

**Log:**

| Thời gian | Việc | Kết quả |
|---|---|---|
| 2026-06-03 | E2E implicit (benchmark C2) | `reranker_effective=true`, không fallback overlap |

---

## Phase 6 — E2E benchmark C2

**Chạy đúng spec C2 (LLM GPU pod + rerank GPU pod):** trên **pod**, không phải PC Windows.

```bash
# Chuẩn bị một lần: clone/rsync repo + dataset + artifacts/benchmark_cache vào /workspace/rag-pipeline-workflow
# pip install deps benchmark trong venv (sentence-transformers, qdrant-client, ...)
export OPENAI_API_KEY=sk-...   # embed OpenAI
bash /workspace/rag-pipeline-workflow/scripts/runpod/run_c2_benchmark_on_pod.sh
```

Chạy từ PC (rerank CPU) **không đạt yêu cầu C2** — chỉ dùng smoke wiring; kết quả `2026-06-03` trên PC **không chốt gate**.

```powershell
.\scripts\run_c2_gpu_e2e.ps1 -StrictPreflight
```

**Output mong đợi:**

- `reports/benchmark_exportjson_c2_gpu_e2e_results.csv`
- `reports/benchmark_exportjson_c2_gpu_e2e_summary.md`
- `reports/benchmark_exportjson_c2_gpu_e2e_failure_audit.md`

**Gate (tối thiểu vs baseline OpenAI):**

| Metric | Ngưỡng |
|---|---:|
| retrieval_hit_rate | ≥ 0.85 |
| answer_correctness | ≥ 0.70 |
| composite_score | ≥ 0.72 |

**Log:**

| Thời gian | config_id | hit | cit | answer | composite | Ghi chú |
|---|---|---:|---:|---:|---:|---|
| 2026-06-04 | `c2_gpu_hybrid_qdrant_generative` | 0.8667 | 0.8667 | 0.7333 | **0.7667** | Pod GPU rerun OK — **gate PASS** |
| 2026-06-04 | `c2_gpu_hybrid_qdrant_generative` | 0.8667 | 0.8667 | 0.0 | 0.63 | Invalid — proxy .env.c2 ghi đè URL |

---

## Phase 7 — Kết luận & production

- [x] Bảng so sánh OpenAI vs C2 trong journal
- [ ] Cập nhật `decisions.md` nếu đổi `production_openai_hybrid_qdrant_generative.yaml` (gate PASS — chờ xác nhận triển khai)
- [x] Báo cáo tóm tắt (VN): `reports/c2-gpu-benchmark-summary.md`

**So sánh nhanh (OpenAI vs C2):**

| | OpenAI mini | C2 Qwen+bge |
|---|---:|---:|
| composite | 0.7533 | **0.7667** |
| latency (s) | 183.6 | **105.3** |
| groundedness | 0.60 | **0.7333** |

---

## Lệnh nhanh

| Mục đích | Lệnh |
|---|---|
| Preflight | `python scripts/c2_gpu_preflight.py` |
| Reindex (nếu cần) | `python scripts/p0_1_reindex_full_lane.py` |
| Benchmark C2 | `.\scripts\run_c2_gpu_e2e.ps1 -StrictPreflight` |
| Bootstrap pod | `bash scripts/runpod/c2_bootstrap_pod.sh` |

---

*Cập nhật file này sau mỗi phiên setup/test.*
