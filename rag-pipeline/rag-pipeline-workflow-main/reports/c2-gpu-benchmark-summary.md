# Báo cáo benchmark C2 GPU — RunPod Qwen14B + bge-reranker



**Eval:** 15 câu answerable-only KO — `.rag/rag-pipeline-practice/eval_set_company_export_json_dev_ko.md`  

**Config:** `configs/benchmark_exportjson_c2_gpu_e2e.yaml`  

**Gate:** `configs/c2_runpod_stack.yaml` — hit ≥ 0.85 · answer ≥ 0.70 · composite ≥ 0.72  

**Production (frozen 2026-06-04):** `configs/production_c2_runpod_hybrid_qdrant_generative.yaml`



---



## Run chính thức — Pod GPU ✅ (2026-06-04)



**Run ID:** `mc_20260604-024822_001`  

**Môi trường:** RunPod 4090 · vLLM Qwen AWQ `127.0.0.1:8000` · rerank **CUDA** · embed OpenAI · index cache reuse



| Metric | C2 pod | Gate | Đạt |

|---|---:|---:|:---:|

| retrieval_hit_rate | **0.8667** | ≥ 0.85 | ✅ |

| citation_correctness | **0.8667** | — | ✅ |

| answer_correctness | **0.7333** | ≥ 0.70 | ✅ |

| groundedness | **0.7333** | — | ✅ |

| composite_score | **0.7667** | ≥ 0.72 | ✅ |

| latency (s) | 23.3 | — | — |

| query_time_avg (s) | 0.569 | — | — |



---



## Xác nhận Git-first trên pod ✅ (2026-06-04)



**Run ID:** `mc_20260604-085911_001`  

**Môi trường:** `git clone` + copy cache/data từ `.bak` · cùng stack C2 · pod Stop sau benchmark



| Metric | Run 085911 | Run 024822 | Ghi chú |

|---|---:|---:|---|

| hit / citation | 0.8667 | 0.8667 | Khớp |

| answer | 0.7333 | 0.7333 | Khớp |

| composite | 0.7667 | 0.7667 | Khớp |

| latency (s) | 24.7 | 23.3 | ~tương đương |

| ingest | reused_index_cache | reused_index_cache | OK |



**Kết luận:** Luồng **Git push → pod clone → volume cũ** ổn định; không cần zip full repo mỗi lần đổi code.



**Audit:** CE-J04, CE-J05 vẫn `retrieval_miss` (như OpenAI baseline) — không regression từ Git deploy.



---



## So sánh OpenAI baseline (cùng eval 15 câu)



| Metric | OpenAI `gpt-4o-mini` (rerank none) | C2 pod |

|---|---:|---:|

| hit / citation | 0.8667 | 0.8667 |

| answer | 0.7333 | 0.7333 |

| groundedness | 0.60 | **0.7333** |

| composite | 0.7533 | **0.7667** |

| latency (s) | 183.6 | **~24** |



Baseline: `reports/openai_e2e_answerable_ko_rerun_report.md`  

Baseline production (superseded): `configs/production_openai_hybrid_qdrant_generative.yaml`



---



## Run invalid (bỏ qua)



| Run ID | answer | composite | Lý do |

|---|---:|---:|---|

| `mc_20260604-023749_001` | 0.0 | 0.63 | `.env.c2` ghi đè `OPENAI_BASE_URL` proxy cũ → LLM fail |



---



## Vận hành



1. Tab 2 benchmark: `127.0.0.1:8000` + `C2_POD_LOCAL_VLLM=1` (không proxy `.env.c2` trên pod).

2. Tab 1: vLLM `--gpu-memory-utilization 0.68` (tránh OOM rerank).

3. Deploy code: `git pull` trên pod; dataset/cache upload riêng — `docs/RUNPOD_GIT.md`.

4. **Production YAML:** `production_c2_runpod_hybrid_qdrant_generative.yaml` — frozen **2026-06-04**.



---



## Artifact



- `reports/benchmark_exportjson_c2_gpu_e2e_results.csv` (run `mc_20260604-085911`)

- `reports/benchmark_exportjson_c2_gpu_e2e_summary.md`

- `reports/benchmark_exportjson_c2_gpu_e2e_failure_audit.md`

- `reports/c2-gpu-setup-test-journal.md`

