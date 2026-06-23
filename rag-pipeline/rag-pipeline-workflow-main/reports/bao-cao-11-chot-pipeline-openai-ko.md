# 보고서 11: OpenAI 파이프라인 확정

**이어짐:** [보고서 10](bao-cao-10-ket-luan-benchmark-local-vs-production-20260529-ko.md)  
**데이터셋:** Nexteye export JSON package (lane `company_export_json_*`)  
**Production ID:** `e2e_openai_hybrid_qdrant_generative`  
**Config freeze:** `configs/production_openai_hybrid_qdrant_generative.yaml`

---

## 1. 결론

| | Local (BC10) | OpenAI (확정) |
|---|---|---|
| 역할 | CPU에서 chunking·embedding·hybrid·vector DB 비교 | 운영 스택 + end-to-end eval |
| Benchmark | 3단계 · 30/30 case · `retrieval_only` | Validation · Phase 3 · E2E 20문항 · smoke 5문항 |
| LLM | Extractive / rule (GPT 없음) | **gpt-4o-mini** generative |
| Smoke CI | — | **PASS** (hit/cit 5/5) |

**Production 흐름:**

`jsonl package` → **section_based 800/120** → **text-embedding-3-small** → **Qdrant** → **hybrid_dense_bm25** (pool **64**, top_k **4**, reranker **none**) → **gpt-4o-mini**.

- **Embedding:** `text-embedding-3-small` — OpenRouter 추가 벤치마크 없음.  
- **RAGAS:** E2E 1회 실행(참고용); **release gate로 사용하지 않음**.

---

## 2. 테스트 요약

**Local (BC10)** — 동일 Nexteye 패키지, CPU:

| 단계 | 내용 | 요약 결과 |
|---|---|---|
| 1 | 3 chunking × 3 embedding (MiniLM, BGE-M3, e5) × dense/hybrid | 18/18 OK; dev hit 1.0; hybrid ≈ dense |
| 2 | Reranker `none` vs `ms-marco-MiniLM` | EN reranker ~15× 느림, composite 낮음 → **미사용** |
| 3 | Chroma vs Qdrant (MiniLM) | 6/6 OK; 두 아키텍처 모두 실행 가능 |

**OpenAI** — eval matcher 수정 후 (`package_split_match`):

| 단계 | Lane / eval | 비고 |
|---|---|---|
| Validation | 20문항, 4 config | hit/cit **1.0** |
| Phase 3 | `section_hybrid` × Chroma/Qdrant, pool 64 | Winner **Qdrant**, composite **0.7575** |
| E2E | `company_export_json_full`, 20문항 | Generative vs extractive |
| P0.1 | field boost + manifest inject 후 generative | **12/20** answer_correct |
| Smoke CI | CE-J02, J03, J06, J07, J16 | Production gate PASS |

**수행하지 않음:** Downloads raw data; OpenRouter embedding 비교; RAGAS를 주요 기준으로 사용.

---

## 3. Local CPU vs OpenAI 확정표

| 구성요소 | Local CPU (측정) | OpenAI (확정) |
|---|---|---|
| Chunking | `section_based`, `recursive_800_120` | **`section_based` 800/120** |
| Embedding | MiniLM; BGE-M3; e5-base | **`openai:text-embedding-3-small`** |
| Vector DB | Chroma + Qdrant | **Qdrant** |
| Retrieval | `hybrid_dense_bm25`, pool 64 | 동일 |
| Reranker | `none` (ms-marco 제외) | **`none`** |
| LLM | Rule / extractive | **gpt-4o-mini** |
| Hit / citation | 1.0 (1단계 dev) | **1.0** validation, full, smoke |
| Answer (rule) | 낮음 (generative 없음) | **12/20** full; smoke 4/4 scored (J06 waive) |
| Query / 문항 | ~0.15s retrieval only | **~2.05s** full 20q gen.; **~4.2s** smoke 5q |
| Index build | MiniLM **~17–20s**; BGE **~287–356s** | OpenAI **~58–64s** (batch 32) |
| GPU (향후) | 제안: bge-m3, bge-reranker-v2-m3 | 당분간 API embed/LLM 유지 |

---

## 4. OpenAI 수치 결과

**Phase 3 — validation, config `p3_openai_section_hybrid_qdrant`:**

| Metric | 값 |
|---|---:|
| retrieval_hit_rate | 1.0 |
| citation_correctness | 1.0 |
| composite_score | 0.7575 |
| query_time_avg | 0.998 s |
| index_build_time | 13.2 s |

동일 hybrid에서 Qdrant가 Chroma보다 composite +0.059 (gate 임계 ≥ 0.02).

**E2E full lane — 20문항 (`company_export_json_full`):**

| Metric | Extractive | Generative (production) |
|---|---:|---:|
| hit / citation | 1.0 / 1.0 | 1.0 / 1.0 |
| answer_correctness | 0.0 | **0.35** |
| insufficient_handling | 0.75 | **1.0** |
| composite | 0.65 | **0.7875** |
| query_time_avg (s) | 0.94 | **2.05** |

**Smoke CI (5문항):** hit/cit **1.0**; J16 insufficient OK; answer 임계 ≥ 0.6 (J06 waived).

**RAGAS (E2E 10문항, gate 아님):** faithfulness 0.89 extractive / 0.40 generative — paraphrase vs rule metric 정의 차이; 스택 결정 변경 없음.

---

## 5. 스택 파라미터 설명

| 용어 | 요약 |
|---|---|
| **section_based 800/120** | JSON section/record 단위 분할; chunk 최대 **800**자; 인접 chunk **120**자 overlap. |
| **hybrid_dense_bm25** | 벡터(dense/Qdrant) + 키워드(BM25) **결합** retrieval: 의미 + 코드/티커에 유리. |
| **pool 64** | 질문당 hybrid에서 **64**개 후보 chunk, 이후 **top_k = 4**를 LLM context로 전달. |
| **~2s full** | generative eval **20문항** 평균 **~2.05 s/문항** (retrieval + GPT, index 제외). |
| **~4s smoke 5q** | smoke **5문항** 평균 **~4.2 s/문항** — 동일 스택, 샘플 적음 / metadata 무거울 수 있음. |
| **MiniLM ~20s** | CPU `all-MiniLM-L6-v2` index — laptop 벤치마크용. |
| **BGE ~300s+** | CPU `BAAI/bge-m3` index — 동일 corpus **~5–6분**; GPU production 속도와 무관. |

---

## 6. 상세 참조

- 보고서 10 (local): `reports/bao-cao-10-ket-luan-benchmark-local-vs-production-20260529-ko.md`  
- Phase 3 gate: `reports/benchmark_exportjson_openai_phase3_production_gate.md`  
- E2E: `reports/openai_e2e_full_lane_report.md`  
- Generative 12/20: `reports/openai_generative_results_summary.md`

---

*OpenAI production 스택 확정 요약.*
