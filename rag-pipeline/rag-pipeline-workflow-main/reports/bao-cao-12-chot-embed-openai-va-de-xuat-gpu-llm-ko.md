# 보고서 12: OpenAI Embedding 확정 및 GPU+LLM 3종 제안

**이어짐:** [보고서 11](bao-cao-11-chot-pipeline-openai-ko.md)  
**데이터셋:** `넥스트아이_dataset_package_20260528T091409` · eval 한국어

---

## 1. 요약

| 항목 | 결정 |
|---|---|
| **Embed** | **`openai:text-embedding-3-small`** — 유지 |
| **bge-m3 embed** | privacy / retrieval 명확한 개선 / embed API 비용이 GPU를 초과할 때만 |
| **Retrieve (BC11)** | `section_based` 800/120 · Qdrant · hybrid pool 64 |
| **GPU pod** | Rerank + LLM만 — embed는 **GPU에서 수행하지 않음** |
| **우선 조합** | **C2 — RTX 4090 + Qwen2.5-14B-Instruct (Q4 quant)** (+ bge-reranker-v2-m3) |

Production YAML (`configs/production_openai_hybrid_qdrant_generative.yaml`)은 GPU 배포가 안정적으로 확인될 때까지 **변경하지 않음**.

> **용어:** **Qwen2.5-14B-Instruct** = 모델명( instruction-tuned ). **Q4** = 4-bit **quantization**(양자화)으로 VRAM을 줄여 4090 24GB에서 reranker와 함께 구동하는 방식.

---

## 2. 파이프라인 앞단 — 확정

**흐름:**

`package` → `section_based 800/120` → OpenAI embed → Qdrant hybrid (pool 64) → **[GPU]** bge-reranker-v2-m3 → Qwen generative

| 구성요소 | 값 | GPU pod? |
|---|---|:---:|
| Chunking | section_based **800/120** | 아니오 |
| Embedding | **text-embedding-3-small** | 아니오 |
| Vector + retrieve | Qdrant · **hybrid_dense_bm25** · pool **64** | 아니오 |
| Rerank + LLM | bge-reranker-v2-m3 · Qwen2.5-Instruct | **예** |

**BC11 측정값:** hit/citation **1.0** · generative composite **0.7875** · 1개사 index **~58–64 s** (OpenAI embed).

---

## 3. bge-m3 (embed)를 언제 쓰는가?

**기본: 사용하지 않음.** OpenAI embed 유지.

| bge-m3로 전환하는 경우 | 전환하지 않는 경우 |
|---|---|
| 데이터를 **외부 API로 보낼 수 없음** | **LLM** 비용만 줄이려는 경우 → GPU + Qwen 사용 |
| A/B로 retrieval composite **+2–3%** 입증 | rerank만 부족 → **bge-reranker** 추가, OpenAI embed 유지 |
| embed token 월 비용 **>** GPU re-index 비용 | 10–100개사 규모 (~$0.1–1.2/월 embed) — 여전히 GPU embed보다 저렴 |

---

## 4. Embed 비용: OpenAI vs bge-m3 GPU

OpenAI 가격: **$0.02 / 1M token** · 추정 ~200K 신규 token/일 (10개사).

| 규모 | OpenAI/월 | bge-m3 GPU/월* |
|---:|---:|---:|
| 10개사 | **~$0.12** | ~$0.5–2 |
| 100개사 | **~$1.20** | ~$1–4 |

\* re-index 2–4h × $0.27–0.69/hr GPU. **결론: 현재 규모에서는 OpenAI embed가 더 저렴.**

---

## 5. GPU + LLM 3종 조합

**공통:** embed OpenAI · rerank **bge-reranker-v2-m3** · volume **~50GB** model cache · 미사용 시 pod Stop.

### 5.1. 개요

| ID | GPU | LLM | 역할 | 우선순위 |
|---|---|---|---|---|
| C1 | A5000 24GB | Qwen2.5-**7B** Q4 | 저렴 · POC | 예비 |
| **C2** | **4090 24GB** | Qwen2.5-**14B-Instruct** Q4 | **24GB 균형** | **★ 1순위** |
| C3 | L40S 48GB | Qwen2.5-**14B** 8-bit | headroom · scale | C2 OOM 시 |

### 5.2. RunPod 가격 (참고)

| GPU | VRAM | ~$/시간 | vs A5000 |
|---|---:|---:|---|
| A5000 | 24 GB | **$0.27** | 1× |
| **4090** | 24 GB | **$0.69** | ~2.5× |
| L40S | 48 GB | **$0.67–0.79** | ~2.5–3× |
| Volume 50GB | — | **$3.5/월** | 고정 |

### 5.3. 3종 비교 (한 표)

| 기준 | C1 A5000+7B | **C2 4090+14B** ★ | C3 L40S+14B |
|---|:---:|:---:|:---:|
| ~$/시간 GPU | **최저** | 높음 | 중간 |
| ~$/4h 실행 | **~$1.1** | ~$2.8 | ~$2.7–3.2 |
| LLM 속도 (추정) | 100% | **130–160%** | 120–150% |
| query E2E (추정) | 1.5–2.5 s | **1.2–2.0 s** | 1.2–2.0 s |
| VRAM (rerank+LLM) | ~7–8 GB | **~10–12 GB** | ~16–18 GB |
| answer 품질 | ★★★ | **★★★★** | ★★★★☆ |
| 24GB 안정성 | VRAM 여유 | **적당** | — |

**상대 비교 (개념도)** — C1=기준 · `█`=상대 수준 · `░`=여백

```text
LLM 속도 (상대):      C1 ████████░░   C2 ██████████████   C3 █████████████░
GPU 시간당 비용:      C1 ██░░░░░░░░   C2 ██████░░░░░░   C3 ██████░░░░░░
answer 품질 (추정):   C1 ███░░░░░░░   C2 ████████░░░░   C3 █████████░░░
```

### 5.4. **C2**를 우선하는 이유

| 이유 | 설명 |
|---|---|
| **4090 시간당 비용 대비 7B보다 큰 모델** | 14B Q4 + rerank가 24GB에 맞음 — 4090+7B보다 GPU 활용도 높음 |
| **품질** | 14B가 ESG 한국어 / governance에 7B보다 적합; BC11 answer 12/20 |
| **속도** | A5000+7B보다 빠름; OpenAI ~2.05 s/문항에 근접 |
| **비용 대비** | C1보다 ~2.5×/시간이지만 production 24GB 한 세트로 충분 — OOM 전까지 L40S 불필요 |

**C1:** budget이 매우 낮거나 region에 4090이 없을 때만.  
**C3:** C2 OOM 또는 동시 사용자 많을 때.  
**4090+7B:** 비우선 — C2와 비슷한 가격이지만 모델이 더 작음.

### 5.5. **Qwen2.5-Instruct**를 선택하는 이유 (다른 LLM 대비)

과제: **한국어 ESG RAG QA** — 짧은 context 읽기, 근거 있는 답변, metadata (ticker, corp code, insufficient).

| LLM / 방향 | 한국어 | QA + instruction | 4090 self-host (7–14B) | ESG RAG 적합 | 비고 |
|---|---|:---:|:---:|:---:|---|
| **Qwen2.5-Instruct** ★ | **우수** (다국어·CJK) | **우수** | **7B / 14B Q4** | **높음** | vLLM/Ollama 보편; Instruct 버전 제공 |
| Llama 3.1 Instruct | 보통 | 우수 (EN) | 8B / 70B | 보통 | 한국어 약점; 70B는 4090에 부적합 |
| Mistral / Mixtral Instruct | 약–보통 | 우수 (EN/EU) | 7B ok | 보통 | KO corpus + 한국어 용어 최적화 부족 |
| Nemotron / diffusion 8B | 보통 | 목적 상이 | 8B | **낮음** | reasoning/diffusion — 표준 Instruct QA 아님 |
| Gemma 2 Instruct | 보통 | 우수 | 9B / 27B | 보통 | 27B는 24GB 빠듯; 다국어에서 Qwen 대비 열세 |
| **gpt-4o-mini (API)** | 우수 | 우수 | self-host 불가 | 높음 (BC11) | **누적 token 비용** — GPU 전환 동기 |

**Qwen 선택 이유:**

1. **언어:** Nexteye export JSON + eval KO — **한국어 + 숫자/metadata** 이해 필요; 동급 Llama/Mistral 대비 다국어 task에서 유리한 경우가 많음.  
2. **모델 형태:** **Instruct** — “context 읽기 → 답변 / insufficient 표현”에 바로 사용, repo generative layer와 일치.  
3. **VRAM:** **7B·14B quant(Q4)** 는 4090에서 **reranker와 동시 구동** 가능 — 24GB에서 32B+ 불필요.  
4. **생태계:** Hugging Face weights, AWQ/GPTQ, **vLLM** — RunPod volume cache, OpenAI 호환 API 용이.  
5. **운영 비용:** **gpt-4o-mini token 과금** → **GPU 시간 과금**; C2에서 Qwen 14B가 품질/비용 균형점.

**기본으로 선택하지 않음:** Llama/Mistral (동급 한국어 열세) · Nemotron diffusion (use case 불일치) · 4090에서 >32B (OOM 또는 quant 과부하).

---

## 6. RunPod — 요약

| # | 항목 |
|---|---|
| 1 | Volume은 pod와 **동일 region** (예: `rag-models-ko` 50GB) |
| 2 | **Running** = GPU 과금 · **Stop** = GPU 과금 중단 |
| 3 | Model은 volume에 cache — 매번 재다운로드 불필요 |
| 4 | Embed는 여전히 로컬/VPS에서 OpenAI 호출 |

---

## 7. 결론

1. **앞단 확정:** OpenAI embed + Qdrant hybrid (BC11).  
2. **bge-m3 embed:** 아직 미사용 — §3 참고.  
3. **GPU + LLM:** **C2 (4090 + Qwen2.5-14B-Instruct Q4 + bge-reranker-v2-m3)** 우선 — 한국어/ESG 및 24GB self-host에 적합 (§5.5).  
4. **Production YAML:** 아직 미갱신.

---

*기술 제안 보고서 — 보고서 11 freeze를 아직 대체하지 않음.*
