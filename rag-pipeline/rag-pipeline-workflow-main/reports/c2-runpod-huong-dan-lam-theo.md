# Hướng dẫn làm theo — Benchmark C2 trên RunPod (4090 + Qwen + bge-reranker)

Tài liệu cho **người mới** triển khai lại từ đầu.

**Kiến trúc tóm tắt:**

```text
[PC]  dataset + eval + index cache (OpenAI embed)  ──upload──►  [Pod volume /workspace]
[Pod Tab 1]  vLLM Qwen :8000  (process chạy nền, giữ mở)
[Pod Tab 2]  benchmark Python (rerank GPU + gọi LLM local + embed OpenAI API)
```

---

## Hai chế độ URL — đọc trước khi làm (tránh nhầm proxy)

| Chạy ở đâu | LLM (Qwen) gọi qua | Rerank | Embed |
|---|---|---|---|
| **Benchmark trên pod (Tab 2)** — **chuẩn gate C2** | `http://127.0.0.1:8000/v1` | GPU trên pod | OpenAI API (`OPENAI_API_KEY`) |
| **Test / preflight từ PC** | Proxy RunPod trong `.env.c2` | Không có GPU (cảnh báo) | OpenAI API |

**Vì sao bước 8 không dùng proxy `.env.c2`?**

- Benchmark + rerank chạy **cùng một máy** (pod). Gọi `127.0.0.1` = nói chuyện thẳng với vLLM Tab 1, nhanh và ổn định.
- Proxy (`https://<pod-id>-8000.proxy.runpod.net`) là đường **từ internet vào pod** — dùng khi máy chạy benchmark là **PC**, không phải pod.
- Nếu trên pod mà để URL proxy cũ trong `.env.c2` → request 404 → `answer_correctness = 0` (đã gặp thực tế).

**File `.env.c2` tạo khi nào?** → **Bước 0 trên PC** (xem bảng dưới).

---

## Bước 0 — Chuẩn bị trên PC (trước RunPod)

### 0.1 Repo, data, index

**Ưu tiên Git (khuyến nghị):** push code từ PC → trên pod `git clone` / `git pull` → `bash scripts/runpod/c2_after_git_clone.sh`. Chi tiết: `docs/RUNPOD_GIT.md`, checklist push: `docs/CHUAN_BI_PUSH_GIT.md`.

| Việc | Chi tiết |
|---|---|
| Repo trên pod | `git clone` → `/workspace/rag-pipeline-workflow` (hoặc zip bước 4 nếu không dùng Git) |
| OpenAI API key | Embed `text-embedding-3-small` trong benchmark |
| Dataset | `data/rag_dataset/05_company_export_json/<package>/` — **không** trên Git; upload/rsync riêng |
| Eval | `.rag/rag-pipeline-practice/eval_set_company_export_json_dev_ko.md` (trên Git) |
| Index cache | PC: `python scripts/p0_1_reindex_full_lane.py` → upload `artifacts/benchmark_cache/` (không trên Git) |

### 0.2 Tạo `.env.c2` trên PC (một lần)

```powershell
copy .env.c2.example .env.c2
# Sửa file .env.c2 — KHÔNG commit
```

| Biến | PC (test từ ngoài) | Đưa lên pod trong zip |
|---|---|---|
| `OPENAI_API_KEY` | Điền key thật | **Có** — benchmark embed trên pod cần key |
| `OPENAI_BASE_URL` / `C2_LLM_BASE_URL` | Proxy **mới** sau mỗi lần Start pod: `https://<pod-id>-8000.proxy.runpod.net/v1` | **Có thể có** nhưng trên pod sẽ **comment** trước benchmark (bước 8) |
| `OPENAI_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` | Giống PC |

**Khi nào đóng gói `.env.c2` vào zip?** → **Bước 4** (`build_c2_pod_bundle.ps1` tự copy `.env.c2` nếu file tồn tại).

---

## Bước 1 — Chốt stack

| Thành phần | Chọn |
|---|---|
| GPU | RTX **4090 24GB** |
| LLM | **Qwen2.5-14B-Instruct-AWQ** (vLLM) |
| Reranker | **BAAI/bge-reranker-v2-m3** (GPU, cùng pod) |
| Embed | **openai:text-embedding-3-small** (API) |
| Config benchmark | `configs/benchmark_exportjson_c2_gpu_e2e.yaml` |

Tham chiếu: `configs/c2_runpod_stack.yaml`, báo cáo 12.

---

## Bước 2 — Network Volume (RunPod UI)

1. **Storage** → **Network Volumes** → **Create**
2. Tên: `rag-models-ko` (gợi ý)
3. Dung lượng: **40–50 GB**
4. **Region** cố định (vd. **US-IL-1**) — pod sau này **phải cùng region**
5. Mount path khi gắn pod: **`/workspace`**

---

## Bước 3 — Tạo và Start Pod (RunPod UI)

1. Deploy → GPU **RTX 4090 24GB**, **cùng region** volume
2. Gắn volume → `/workspace`
3. Container disk **≥ 40 GB**
4. **Expose HTTP ports:** `8000` (vLLM); tùy chọn `8888` (upload file)
5. **Start** → trạng thái **Running**
6. Migrate nếu GPU bận; cuối cùng chỉ **một** pod + volume

**Ghi vào sổ tay (PC):** Pod ID + **HTTP Service URL port 8000** (cho `.env.c2` trên PC).

---

## Bước 3b — Mở hai Web Terminal (ngay sau pod Running)

Trên trang pod RunPod → **Connect** → mở **hai** cửa sổ terminal:

| | Tab 1 | Tab 2 |
|---|---|---|
| **Mục đích** | Chỉ chạy **vLLM** | Mọi lệnh setup / benchmark |
| **Quy tắc** | Để chạy nền, **không** Ctrl+C khi đang benchmark | Làm việc bình thường |
| **Thứ tự lần đầu** | Bước 6 (sau khi có model) | Bước 4 → 5 → 7 → 8 |

Từ đây mọi lệnh ghi **Tab 1** hoặc **Tab 2** — không nhảy cóc giữa các bước.

---

## Bước 4 — Đưa mã nguồn + data + cache lên pod (Tab 2)

**Mục tiêu:** có thư mục `/workspace/rag-pipeline-workflow` trước khi chạy script trong repo.

### Cách 1 — Zip từ PC (đã dùng trong dự án này)

**PC:**

```powershell
cd E:\Documents\rag-pipeline-workflow
.\scripts\build_c2_pod_bundle.ps1      # gồm src, configs, scripts, dataset, .rag/eval, .env.c2
.\scripts\build_c2_index_cache_zip.ps1 # nếu cần zip riêng cache
```

**Upload** file zip vào `/workspace` (RunPod file browser / Jupyter 8888).

**Tab 2:**

```bash
cd /workspace
apt-get update -qq && apt-get install -y -qq unzip
unzip -o c2_pod_bundle.zip
unzip -o c2_index_cache_only.zip    # chỉ khi cache chưa nằm trong bundle
chown -R root:root /workspace/rag-pipeline-workflow
chmod -R u+rwX,go+rX /workspace/rag-pipeline-workflow
ls /workspace/rag-pipeline-workflow
ls /workspace/rag-pipeline-workflow/artifacts/benchmark_cache/index_cache
```

### Cách 2 — Git clone trên pod (phổ biến khác, không cần zip script)

**Tab 2:**

```bash
cd /workspace
git clone https://github.com/thenhat/rag-pipeline-workflow.git
# Upload riêng dataset + index_cache + .env.c2 (scp/rsync) vì gitignore
```

→ Xem **Phụ lục D** so sánh cách triển khai.

---

## Bước 5 — Tải model HuggingFace lên volume (Tab 2)

**Điều kiện:** đã có `cd /workspace/rag-pipeline-workflow` (bước 4).

```bash
cd /workspace/rag-pipeline-workflow
sed -i 's/\r$//' scripts/runpod/*.sh
bash scripts/runpod/c2_bootstrap_pod.sh
```

| Việc script | Tác dụng |
|---|---|
| `snapshot_download` Qwen AWQ | ~9GB vào `/workspace/models/hf` |
| `snapshot_download` bge-reranker | ~2.3GB |
| Tạo `/workspace/start_c2_vllm.sh` | Lệnh start vLLM nhanh (nhớ chỉnh `0.68` khi dùng) |

Lỗi disk/CUDA → `bash scripts/runpod/c2_disk_and_venv_setup.sh`

```bash
ls /workspace/models/hf
nvidia-smi
```

---

## Bước 6 — Chạy vLLM (Tab 1)

**Tab 1** (mở mới từ bước 3b):

```bash
source /workspace/venv/bin/activate
export HF_HOME=/workspace/models/hf
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-14B-Instruct-AWQ \
  --host 0.0.0.0 --port 8000 --dtype auto \
  --quantization awq_marlin --max-model-len 8192 \
  --gpu-memory-utilization 0.68 \
  --served-model-name Qwen/Qwen2.5-14B-Instruct-AWQ
```

Đợi log **Application startup complete**. **Giữ Tab 1 mở.**

**Tab 2 — kiểm tra:**

```bash
curl -s http://127.0.0.1:8000/v1/models | head -c 200
```

**PC (tùy chọn):** cập nhật proxy mới trong `.env.c2` → `python scripts/c2_gpu_preflight.py` (gọi qua internet, không thay bước 8).

---

## Bước 7 — Cài deps benchmark + verify (Tab 2)

```bash
cd /workspace/rag-pipeline-workflow
source /workspace/venv/bin/activate
bash scripts/runpod/c2_install_benchmark_deps.sh
bash scripts/runpod/c2_verify_pod.sh
```

Kỳ vọng: bước 5 verify → **`rerank_device cuda`**, không OOM.

---

## Bước 8 — Benchmark E2E (Tab 2) — gate C2

**Profile môi trường trên pod:**

```bash
cd /workspace/rag-pipeline-workflow
source /workspace/venv/bin/activate

# Chỉ giữ API key từ .env.c2; tắt URL proxy để không ghi đè 127.0.0.1
sed -i 's/^OPENAI_BASE_URL=/#OPENAI_BASE_URL=/' .env.c2
sed -i 's/^C2_LLM_BASE_URL=/#C2_LLM_BASE_URL=/' .env.c2

export C2_POD_LOCAL_VLLM=1
export OPENAI_BASE_URL=http://127.0.0.1:8000/v1
export OPENAI_MODEL=Qwen/Qwen2.5-14B-Instruct-AWQ
export RAG_BENCHMARK_LANGUAGE=ko
export RAG_BENCHMARK_LLM_PROVIDER=openai_api
export RAG_RERANK_ENABLED=true
export RAG_RERANK_STRICT=true

python src/run_model_candidate_benchmark.py \
  --config configs/benchmark_exportjson_c2_gpu_e2e.yaml \
  --enable-ragas false \
  --timeout-sec 3600

tail -2 reports/benchmark_exportjson_c2_gpu_e2e_results.csv
```

| Gate | Ngưỡng |
|---|---:|
| hit | ≥ 0.85 |
| answer | ≥ 0.70 |
| composite | ≥ 0.72 |

Tham chiếu PASS: `mc_20260604-024822` — composite **0.7667**.

---

## Bước 9 — Kết thúc

- Copy CSV về PC
- **Stop** pod (tiết kiệm phí)
- Volume giữ model/cache cho lần sau

---

## Phụ lục D — Cách đưa code lên RunPod: cái nào phổ biến?

| Cách | Mô tả | Phổ biến khi | Dự án C2 |
|---|---|---|---|
| **A. Zip upload** | PC build bundle → UI upload → unzip | Demo, không có SSH, Windows | **Đang dùng** |
| **B. Git trên pod** | `git clone` + upload data/cache riêng | Team có repo public/private | **Khuyến nghị** (`docs/RUNPOD_GIT.md`) |
| **C. SSH / rsync / scp** | PC `scp -r` hoặc `rsync` thẳng | Dev có SSH RunPod | Script `push_c2_bundle_to_pod.ps1` |
| **D. Docker image** | Image chứa code+deps, pod pull image | Production, CI/CD | Chưa setup |
| **E. Benchmark từ PC qua proxy** | PC `OPENAI_BASE_URL` = proxy RunPod | Chỉ test LLM từ xa | **Không đủ gate C2** (rerank CPU/ thiếu GPU) |
| **F. RunPod API / SDK** | Tạo pod, chạy lệnh từ CI | Tự động hóa fleet | Có thể mở rộng sau |

### “Coi RunPod như API, chạy lệnh trên local” — được không?

**Một phần:**

| Thành phần | Chạy từ PC qua proxy/API | Ghi chú |
|---|---|---|
| **LLM (Qwen)** | **Có** — `OPENAI_BASE_URL` = proxy port 8000 trong `.env.c2` | Giống gọi OpenAI remote |
| **Embed** | **Có** — OpenAI API từ PC | Như hiện tại |
| **Rerank GPU** | **Không** trên PC thường | PC không có 4090 → rerank CPU → **không** đạt spec C2 |
| **Index / Qdrant** | **Có** nếu cache trên PC | Không cần upload cache lên pod |

→ Pattern **hybrid phổ biến trong production:**

- **Pod (hoặc cluster GPU):** vLLM + reranker API
- **PC / LangGraph / backend:** embed + retrieve + gọi HTTP tới pod

**Benchmark gate C2 trong repo này** được định nghĩa chạy **trên pod** (LLM local + rerank CUDA). Chạy full benchmark từ PC chỉ hợp lệ cho smoke LLM, không thay run gate.

**Hướng “chuẩn sản phẩm” sau này:**

1. Pod expose vLLM (proxy) + có thể thêm endpoint rerank.
2. App local/production chỉ cần URL + API key trong config (giống `.env.c2`).
3. Không bắt buộc zip cả repo lên pod mỗi lần — chỉ deploy **image** hoặc **git pull** trên pod.

---

## Phụ lục E — Dataset mới (3 công ty)

1. PC: eval mới + reindex → cache mới  
2. PC: `build_c2_pod_bundle.ps1` (+ cache zip)  
3. Pod: bước 4 upload (hoặc rsync phần thay đổi)  
4. Tab 1: vLLM (model trên volume giữ nguyên)  
5. Tab 2: bước 7–8 (config `company_filter` / eval path mới)

---

## Phụ lục F — Lỗi thường gặp

| Triệu chứng | Xử lý |
|---|---|
| OOM rerank | vLLM `gpu-memory-utilization 0.68` |
| answer=0, ~17s | Trên pod dùng proxy `.env.c2` thay vì `127.0.0.1` |
| Permission denied sau unzip | `chown` / `chmod` |
| Pod migrate | Migrate một lần; giữ một pod |

---

*Cập nhật: sửa thứ tự bước, làm rõ Tab 1/2, `.env.c2`, và chế độ URL.*
