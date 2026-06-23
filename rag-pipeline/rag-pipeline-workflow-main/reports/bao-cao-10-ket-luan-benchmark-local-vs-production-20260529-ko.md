# 보고서 10: 로컬 벤치마크 결론, 결과 편차 및 ESG production 방향

**날짜:** 2026-05-29  
**범위:** lane `company_export_json`, Nexteye 패키지 `091409` 3단계 벤치마크  
**목적:** 완료된 벤치마크 결과의 의미, CPU-only 로컬 환경에서 metric이 왜 왜곡되는지, production 스택 선택 프레임 정리.

---

## 1. 경영 요약

3단계 벤치마크 **완료**. 공식 결과 파일:

| 단계 | 결과 파일 |
|---|---|
| 1단계 | `reports/benchmark_exportjson_phase1_results.csv` |
| 2단계 | `reports/benchmark_exportjson_phase2_results.csv` |
| 3단계 | `reports/benchmark_exportjson_phase3_results.csv` |

**총평:** 벤치마크는 **파이프라인 아키텍처**(chunking, hybrid retrieval, 부적합 reranker 제외) 확정에 **유용**하나, CPU-only 로컬만으로 production winner를 확정하기에는 **불충분** — 특히 2·3단계 validation/full에서 `retrieval_hit_rate = 0` (해당 metric 신뢰 전 eval 점검 필요).

로컬 결과를 production에 **직접 적용하기 어려운** 3가지 이유:

1. **실제 GPT / generation 없음** — 모든 run이 `retrieval_only`, RAGAS `skipped`; end-to-end 답변 품질 미측정.
2. **다국어 corpus에 영어 reranker** — `cross-encoder/ms-marco-MiniLM-L-6-v2`는 한국어/ESG에 부적합; **모델 선택 오류**이지 reranker 자체가 무용함을 증명하지 않음.
3. **CPU 병목(대형 embedding)** — BGE-M3 index ~287–356s/case vs MiniLM ~17–20s; composite 순위가 latency에 크게 영향.

**Vector store:** 동일 MiniLM+dense config에서 3단계 full lane Chroma composite가 Qdrant보다 소폭 높음 (~0.26 vs ~0.16–0.22). 대규모 production은 여전히 **Qdrant**(hybrid native, metadata filter, 수평 확장) 권장.

**GPU 없이 다음 단계:** OpenAI API key 보유 — `text-embedding-3-small`, GPT-4o-mini, RAGAS로 짧은 벤치마크 가능(GPU 요청 전).

---

## 2. 3단계 결과 개요

### 2.1. 1단계 — chunking × embedding × retrieval (dev lane)

**Lane:** `company_export_json_dev`  
**Matrix:** 3 chunking × 3 embedding × 2 retrieval (dense/hybrid), Chroma, reranker = none  
**상태:** **18/18 success**

| 그룹 | case 수 | retrieval_hit_rate | composite_score (범위) | index_build_time (범위) |
|---|---|---|---|---|
| MiniLM (6) | 6 | 1.0 | **0.764 – 0.765** | ~17–20s |
| BGE-M3 (6) | 6 | 1.0 | 0.673 – 0.692 | ~287–356s |
| multilingual-e5-base (6) | 6 | 1.0 | 0.734 – 0.743 | ~78–89s |

**1단계 요점:**

- dev에서 dense와 hybrid **동일 hit_rate 1.0**; composite 유사 — 작은 dev lane에서는 hybrid 우위 불명확.
- **MiniLM** composite 최고는 주로 **latency_normalized** 유리(index/query 빠름) 때문이며, production 다국어 embedding 최선을 의미하지 않음.
- **BGE-M3**, **e5**는 Chroma dimension 충돌 해결(embedding별 collection 분리) 후 성공.

### 2.2. 2단계 — reranker (validation lane)

**Lane:** `company_export_json_validation`  
**내용:** 1단계 top 3 config × none vs rerank (`semantic_dense` / `semantic_dense_rerank`, pool = 64)  
**상태:** **6/6 success**

| config (요약) | reranker | hit_rate | citation | composite | query_time_avg |
|---|---|---|---|---|---|
| rec800 dense none | none | 0.0 | 0.0 | 0.2449 | ~0.16s |
| rec800 dense rerank | ms-marco | 0.0 | 0.0 | 0.1843 | ~2.67s |
| rec512 dense none | none | 0.0 | 0.0 | 0.2468 | ~0.15s |
| rec512 dense rerank | ms-marco | 0.0 | 0.0 | 0.1725 | ~3.03s |
| section dense none | none | 0.0 | 0.0 | **0.2500** | ~0.14s |
| section dense rerank | ms-marco | 0.0 | 0.0 | 0.1833 | ~2.70s |

**2단계 해석:**

- none vs rerank가 **동일 retrieval mode(dense)**, **동일 pool = 64** — 이전 run보다 공정.
- Reranker는 **composite 낮음**, query **~15–20× 느림** — MS MARCO가 corpus 언어에 맞지 않다는 가설과 일치.
- **전체 hit_rate/citation = 0** — validation lane eval 문제(ground truth alias, record vs split); **eval 수정 전 2단계로 production hit_rate 확정 금지**.

### 2.3. 3단계 — Chroma vs Qdrant (full lane)

**Lane:** `company_export_json_full`  
**상태:** **6/6 success** (Qdrant `enabled`)

| config | vector_store | hit_rate | citation | composite | query_time_avg |
|---|---|---|---|---|---|
| section_based + MiniLM | chroma | 0.0 | 0.0 | **0.2575** | ~0.14s |
| section_based + MiniLM | qdrant | 0.0 | 0.0 | 0.1575 | ~0.18s |
| recursive_512 + MiniLM | chroma | 0.0 | 0.0 | 0.2035 | ~0.16s |
| recursive_512 + MiniLM | qdrant | 0.0 | 0.0 | 0.2213 | ~0.16s |
| recursive_800 + MiniLM | chroma | 0.0 | 0.0 | 0.2256 | ~0.16s |
| recursive_800 + MiniLM | qdrant | 0.0 | 0.0 | 0.2254 | ~0.16s |

**3단계 해석:** Chroma·Qdrant 모두 안정 실행; hit/citation=0이면 composite·latency로만 구분 — **1단계 dev를 아키텍처 결론의 우선 근거**로 사용.

---

## 3. 허용 / 비허용 결론

### 3.1. **허용**되는 결론

| 결론 | 근거 |
|---|---|
| ingest → index → retrieve 3단계 안정 | CSV 30/30 success |
| dev에서 hybrid ≈ dense (hit 1.0) | 1단계 18 case |
| MiniLM은 **CPU 빠른 벤치마크**에 적합 | index ~17–20s |
| BGE-M3/e5 **실행 가능**(Chroma fix 후) | 1단계 12 case |
| `ms-marco-MiniLM` reranker **부적합**(현 corpus) | 2단계 composite·latency |
| Chroma·Qdrant **로컬 feasible** | 3단계 6/6 |
| production generation 품질 **미측정** | retrieval_only + RAGAS skipped |

### 3.2. **아직 불가**한 결론

| 미확정 | 이유 |
|---|---|
| production embedding winner | BGE/e5 CPU latency penalty; OpenAI embedding run 없음 |
| reranker “무용” 일반화 | 영어 모델만 테스트 |
| validation/full 최적 config | hit_rate = 0 |
| production latency | 로컬 수치 ≠ GPU/API |
| 대규모 Chroma vs Qdrant | 단일 기업 corpus + hit metric 문제 |

---

## 4. 결과 편차 원인

### 4.1. GPT / 실제 generation 없음

| 현황 | 결과 |
|---|---|
| `benchmark_kind = retrieval_only` | retrieval + heuristic citation만 |
| `ragas_status = skipped` | judge faithfulness/relevancy 없음 |
| `answer_correctness` 낮음 (~0.05–0.15) | extractive placeholder, GPT-4o-mini 미반영 |

벤치마크가 답하는 질문: *“retrieval이 맞는 chunk/lane을 찾는가?”* — 아직: *“ESG 답변이 고객/파트너용으로 신뢰 가능한가?”*

### 4.2. 언어 불일치 reranker (코드 오류 아님)

| 항목 | 2단계 사실 |
|---|---|
| Model | `cross-encoder/ms-marco-MiniLM-L-6-v2` (영어 MS MARCO) |
| Corpus | 한국어 ESG export JSON |
| 비교 | 동일 dense, pool 64 |

Query **~2.7–3.0s vs ~0.15s**, composite none보다 낮음. production 전 **다국어 reranker**(예: `BAAI/bge-reranker-v2-m3`) 시험 필요.

### 4.3. CPU local vs GPU production — embedding

| Model | Index (1단계 CPU) | production 참고 |
|---|---|---|
| MiniLM | ~17–20s | 빠름; ESG 다국어 품질 상한 낮음 |
| BGE-M3 | ~287–356s | GPU에서는 초/batch 수준 |
| e5-base | ~78–89s | 중간; API embedding과 추가 비교 필요 |

**참고:** 초기 1단계는 Chroma 384-dim collection에 1024-dim embed 충돌로 실패; cache key별 collection 분리로 해결. 현 CSV는 fix 이후.

### 4.4. validation/full hit_rate = 0 (2·3단계)

dev hit 1.0 vs validation/full 0.0 — **동일 pipeline이라면 비정상**. 가능성:

- eval ground truth가 `splits/*.jsonl`만 가리킴;
- full/validation은 **record-level** scoring 필요.

**조치:** eval alias 수정 후 2·3단계로 winner 확정; 당분간 **1단계 아키텍처 결론 우선**.

---

## 5. Chroma vs Qdrant

### 5.1. 3단계 (full lane, MiniLM)

둘 다 성공. composite 최고: `section_based` + Chroma (0.2575). Qdrant runtime 안정 (`qdrant_status = enabled`).

### 5.2. production 방향 (오픈소스 관행)

| 기준 | Chroma | Qdrant |
|---|---|---|
| 용도 | Dev, prototype, laptop 벤치마크 | Production, multi-tenant, 대용량 |
| Hybrid | BM25 파일 + dense 분리 | Dense + sparse native, RRF |
| Metadata | dev 충분 | company, lane, source_type 필터 강함 |
| Scale | Single-node | Replication, 수평 확장 |

**결론:** dev/benchmark는 **Chroma**; 다기업 ESG production 로드맵은 **Qdrant**. 3단계 로컬 결과는 Qdrant 방향을 **반박하지 않음**.

---

## 6. AI 평가 및 오픈소스 관행 대조

| 단계 | Industry / OSS | 로컬 벤치마크 확인 | Production 목표 |
|---|---|---|---|
| Parse | pypdf / structured | export JSON lane 안정 | pypdf + 선택적 고급 parser |
| Chunking | Structure-based | `section_based` dev 우수 | section_based + parent |
| Embedding | BGE/E5 또는 API | MiniLM이 composite 1위(**CPU**) | BGE-M3(GPU) 또는 OpenAI API |
| Retrieval | Hybrid + metadata | dev hybrid ≈ dense | Hybrid RRF + filter |
| Reranker | Multilingual CE | ms-marco **부적합** | bge-reranker-v2-m3 |
| Generation | LLM tiering | 미실행 | GPT-4o-mini / 4o |

baseline retrieval 확정 후: query rewrite, low-evidence 검사, parent chunk 확장, tenant metadata filter — ESG response readiness에 적합.

---

## 7. 파이프라인 권장 (요약)

### 7.1. Laptop dev/benchmark (CPU, OpenAI key)

- Chunking: `section_based` 또는 `recursive_800_120`
- Embedding: `text-embedding-3-small`(API) 또는 MiniLM(offline)
- Retrieval: `hybrid_dense_bm25`
- Vector store: Chroma(빠름) 또는 Qdrant(production 근접)
- Reranker: **none**; ms-marco 한국어 사용 금지
- Generation + eval: GPT-4o-mini + RAGAS

### 7.2. GPU production

- Embedding: `BAAI/bge-m3`
- Vector store: Qdrant
- Retrieval: Qdrant hybrid RRF
- Reranker: `BAAI/bge-reranker-v2-m3`
- Generation: GPT-4o-mini / GPT-4o

### 7.3. 후보 pipeline A/B

| ID | Chunking | Embedding | Retrieval | 비고 |
|---|---|---|---|---|
| **A** | section_based | OpenAI `text-embedding-3-small` | hybrid | 1단계 dev + production 방향 |
| **B** | recursive_800_120 | OpenAI 또는 MiniLM | hybrid | 구조화 약한 문서 |

---

## 8. 스택 선택: Local CPU | GPU | OpenAI API

| 구성요소 | Local CPU만 | GPU production | OpenAI API (GPU 불필요) |
|---|---|---|---|
| Parse | `pypdf` | `pypdf` + OCR 등 | export JSON structured |
| Chunking | section_based / recursive_800_120 | section_based + parent | CPU와 동일 |
| Embedding | MiniLM (빠름, 품질 상한) | **BGE-M3** | **text-embedding-3-small** |
| Vector DB | **Chroma** | **Qdrant** | Chroma 또는 Qdrant |
| Retrieval | hybrid_dense_bm25 | Qdrant hybrid RRF | hybrid_dense_bm25 |
| Reranker | ms-marco 금지; **none** | **bge-reranker-v2-m3** | API rerank 또는 none |
| Generation | rule/extractive | GPT API | **GPT-4o-mini** |
| Evaluation | internal hit/cit (1단계 dev) | RAGAS + spot check | **RAGAS** |
| Query latency | 25–90s | ~2–5s | ~2–4s |
| 비용 | $0 model, CPU 시간 | GPU CapEx | API OpEx |
| 적합 | 아키텍처 debug, 소규모 | 다기업, SLA | GPU 전 품질 확정 |

---

## 9. 로컬 환경 FAQ

| 질문 | 답 |
|---|---|
| CPU 결과가 **틀렸나**? | **아니오** — 측정 범위(아키텍처, reranker 종류) 내에서는 맞음. |
| CPU만으로 **production model 확정** 가능? | **아직 아니오** — GPT/RAGAS 없음; 2·3단계 hit=0; 대형 embed penalty. |
| GPU 즉시 필요? | OpenAI key 있으면 **필수 아님**; 대규모·장기 API 비용 절감 시 GPU. |

---

## 10. 다음 단계

1. `.env`에 `OPENAI_API_KEY` (commit 금지).
2. validation/full eval scoring 수정(record-level, alias).
3. 짧은 벤치마크: pipeline A/B × OpenAI embedding × full_pipeline + RAGAS.
4. `experiment_log.md`, `decisions.md` 기록.
5. OpenAI run 수치·N개 기업 비용 추정 후 GPU proposal.

---

## 11. Repo 참조

| 문서 | 경로 |
|---|---|
| 1단계 결과 | `reports/benchmark_exportjson_phase1_results.csv` |
| 2단계 결과 | `reports/benchmark_exportjson_phase2_results.csv` |
| 3단계 결과 | `reports/benchmark_exportjson_phase3_results.csv` |
| 데이터 contract | `data_contract_dataset_team_v1_1.md` |
| 보고서 09 | `reports/bao-cao-09-tong-hop-benchmark-va-dataset-esg-20260528-ko.md` |
| Workflow | `.rag/rag-pipeline-practice/progress.md`, `decisions.md` |

---

*3단계 벤치마크 완료 요약 (2026-05-28/29). 수치는 공식 CSV 기준; 개별 run experiment log를 대체하지 않음.*
