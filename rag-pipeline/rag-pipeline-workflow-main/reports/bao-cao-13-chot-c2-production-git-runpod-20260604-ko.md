# 보고서 13: C2 프로덕션 확정 및 RunPod Git 배포

**일자:** 2026-06-04 · **이전 보고서:** [보고서 12](bao-cao-12-chot-embed-openai-va-de-xuat-gpu-llm-ko.md)  
**데이터셋 / 평가:** `넥스트아이_dataset_package_20260528T091409` · answerable-only 15문항 (한국어)

---

## 1. 요약

| 항목 | 결과 |
|---|---|
| **프로덕션 스택** | **C2** — Qwen2.5-14B AWQ + bge-reranker GPU + OpenAI embed + Qdrant hybrid |
| **벤치마크 게이트** | **PASS** (hit 0.8667 · answer 0.7333 · composite **0.7667**) |
| **RunPod 배포** | Git clone + 기존 volume (cache/data/model) — **검증 완료** |
| **프로덕션 YAML** | `production_c2_runpod_hybrid_qdrant_generative.yaml` — **동결(frozen)** |
| **OpenAI 베이스라인** | `production_openai_hybrid_qdrant_generative.yaml` — superseded (비교용 유지) |

---

## 2. 수행 작업

1. **Pod GPU에서 C2 벤치마크** — 로컬 vLLM + rerank CUDA; OpenAI 베이스라인 대비 게이트 통과.
2. **Git-first 저장소 정비** — `data/` / `reports/` 정리, `.gitignore`, RunPod 문서; code + `scripts/runpod/` push.
3. **Pod:** `git clone` → volume의 `.bak`에서 cache/dataset 연결 → 벤치마크 재실행 (**run `mc_20260604-085911`**).
4. **아티팩트** — pod 결과 → Git push → PC pull.
5. **프로덕션 확정** — default production을 C2로 전환; 게이트 보고서 및 `decisions.md` 갱신.

---

## 3. 벤치마크 결과 (eval 15문항 KO)

| 지표 | OpenAI 베이스라인 | C2 pod | 게이트 |
|---:|---:|---:|:---:|
| hit / citation | 0.8667 | 0.8667 | ≥ 0.85 ✅ |
| answer | 0.7333 | 0.7333 | ≥ 0.70 ✅ |
| composite | 0.7533 | **0.7667** | ≥ 0.72 ✅ |
| latency | ~184 s | **~24 s** | — |

**참조 run:** `mc_20260604-024822` (공식 pod) · `mc_20260604-085911` (Git-first 검증).  
**고정 miss:** CE-J04, CE-J05 (retrieval) — 베이스라인 대비 regression 없음.

상세: `reports/c2-gpu-benchmark-summary.md`

---

## 4. 설치

### 4.1 RunPod 인프라 (최초 1회)

| 항목 | 구성 |
|---|---|
| GPU | RTX **4090 24GB**, region 고정 (예: US-IL-1) |
| Network volume | **40–50 GB**, mount `/workspace` (model + venv + repo) |
| Expose port | **8000** (vLLM); 선택 8888 (파일 업로드) |
| Container disk | ≥ 40 GB |

최초: `c2_disk_and_venv_setup.sh` (venv `/workspace/venv`) → `c2_bootstrap_pod.sh` (Qwen AWQ + bge-reranker volume 다운로드).  
**이후** (volume 유지): bootstrap **불필요** — pod Start만.

### 4.2 Pod의 code 및 데이터

| 구성요소 | Pod 반영 방법 |
|---|---|
| **Code** | `git clone` / `git pull` → `bash scripts/runpod/c2_after_git_clone.sh` |
| **Dataset jsonl** | Git **미포함** — `.bak`, zip, UI 업로드 |
| **Index cache** | PC reindex → `c2_index_cache_only.zip` 또는 `artifacts/benchmark_cache/` 복사 |
| **`.env.c2`** | backup 복사 또는 `cp .env.c2.example .env.c2` + `OPENAI_API_KEY` |

GitHub private: 사용자별 **PAT** (Contents Read/Write); pod 공유 시 PAT **공유 금지**.

### 4.3 환경 변수 (`.env.c2`)

| 변수 | 값 / 비고 |
|---|---|
| `OPENAI_API_KEY` | OpenAI embed 키 (pod 필수) |
| `OPENAI_MODEL` | `Qwen/Qwen2.5-14B-Instruct-AWQ` |
| `OPENAI_BASE_URL` / `C2_LLM_BASE_URL` | **PC 테스트:** RunPod proxy `https://<pod-id>-8000.proxy.runpod.net/v1` |
| `RAG_RERANK_ENABLED` | `true` · model `BAAI/bge-reranker-v2-m3` |

**Pod 벤치마크(Tab 2):** `.env.c2`의 proxy 줄 comment, `OPENAI_BASE_URL=http://127.0.0.1:8000/v1`, `C2_POD_LOCAL_VLLM=1` — 구 proxy URL로 `answer=0` 방지.

---

## 5. 운영

### 5.1 C2 게이트 벤치마크 흐름 (실행 시)

```text
Tab 1: c2_restart_vllm_tab1.sh  (vLLM, gpu-memory-utilization 0.68)
Tab 2: c2_tab2_run_all.sh       (verify → deps → 15문항 benchmark)
```

- **Embed:** pod에서 OpenAI API (`.env.c2` 키).
- **Rerank + LLM:** 동일 pod GPU; PC에서 full benchmark는 게이트 **무효** (rerank GPU 없음).

### 5.2 Code만 갱신 (dataset/cache 동일)

```bash
cd /workspace/rag-pipeline-workflow
git pull
bash scripts/runpod/c2_after_git_clone.sh
# 필요 시 Tab 1 vLLM 재시작 → Tab 2 benchmark
```

### 5.3 결과를 PC / 팀에 공유

Pod SSH 없음: pod에서 `git add reports/benchmark_*` → `git push` → PC `git pull`.  
또는 RunPod File browser로 다운로드.

### 5.4 Pod Stop / Start 및 비용

- 벤치마크 후 **Stop** — GPU 비용 절감; **volume 유지** (model, cache, repo).
- **Start** 후: Tab 1 vLLM 가동; proxy URL은 pod마다 변경 → PC 외부 테스트 시 `.env.c2` 갱신.
- **LangGraph / 타 팀:** pod Running 시 **LLM proxy port 8000** 호출 — RunPod 계정 없이 RAG가 URL 제공 가능.

### 5.5 프로덕션 런타임 (frozen)

- Config: `configs/production_c2_runpod_hybrid_qdrant_generative.yaml`
- Runtime: `src/production_config.py` (bge rerank + Qwen via `C2_LLM_BASE_URL`)
- 상세 가이드: `reports/c2-runpod-huong-dan-lam-theo.md`, `docs/RUNPOD_GIT.md`

---

*보고서 13 — C2 프로덕션 확정 및 RunPod Git 배포 검증.*
