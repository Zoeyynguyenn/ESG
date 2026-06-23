# 보고서 09: 2026-05-28 벤치마크 및 ESG 데이터셋 요약

## 1. 오늘의 목표

2026-05-28의 핵심 작업은 RAG 벤치마크를 넓고 불안정한 실험 상태에서, 표준화된 ESG 데이터셋 기반의 통제된 실행 흐름으로 전환하는 것이었다.

주요 목표는 다음과 같다.

1. 야간 벤치마크 결과를 검토하고 아직 모델을 확정할 수 없는 이유를 정리한다.
2. ingestion/retrieval 안정화를 위한 기술 옵션을 추가한다.
3. 실행 시간을 줄이기 위해 벤치마크 범위를 단일 기업으로 축소한다.
4. Dataset 팀과 함께 ESG response readiness 목적에 맞게 패키지를 표준화한다.
5. 새 데이터셋 패키지를 받은 뒤 3단계 테스트 로드맵을 다시 설계한다.

## 2. 야간 벤치마크 결과

야간 model candidate benchmark는 실행되었지만, 최종 결론으로 사용하기에는 신뢰도가 충분하지 않았다.

| 문제 | 영향 |
|---|---|
| 일부 case timeout 또는 kill 발생 | 전체 matrix에 대한 metric이 완전하지 않음 |
| 일부 case가 `invalid_case_output` 반환 | runner가 유효한 결과를 기록하지 못함 |
| BGE/e5 ingest 및 index 시간이 김 | full matrix 재실행 시 timeout 가능성이 큼 |
| Qdrant runtime이 초기에 막혀 있었음 | vectorDB 비교를 공정하게 수행할 수 없음 |

결론:

- overnight 결과로 model winner를 확정하지 않는다.
- 해당 결과는 timeout, cache, prebuild index, failure taxonomy 같은 병목을 파악하는 용도로만 사용한다.
- 이후 실행은 더 작은 batch와 명확한 checkpoint를 기준으로 다시 수행해야 한다.

## 3. Pipeline 기술 보강

벤치마크 안정화를 위해 다음 옵션을 추가했다.

| 영역 | 변경 사항 | 상태 |
|---|---|---|
| Parser | 복잡한 문서 처리를 위한 `docling` optional 추가 | 옵션, 기본값 아님 |
| 기본 parser | 안정적인 benchmark를 위해 `pypdf` 유지 | 빠른 benchmark에 사용 |
| Metadata | chunk/document metadata 추가 | 통합 완료 |
| Retrieval | metadata-aware retrieval 추가 | 필요 lane에서 선택적으로 사용 |
| Fallback | metadata filter no-hit 시 non-filter fallback | 빈 결과 방지 |
| VectorDB | local `qdrant` 실행 경로 추가 | Pha 3에서만 제한적으로 사용 |
| Cache | embedding/vector store별 prebuild index 지원 | 반복 ingest 감소 목적 |

결론:

- `docling`과 metadata-aware retrieval은 품질 결론이 아니라 지원 옵션이다.
- 최종 benchmark는 통제된 matrix로 측정해야 하며, option 추가 자체를 성능 개선으로 간주하면 안 된다.

## 4. 단일 기업 기준 benchmark 축소

여러 기업과 많은 PDF를 대상으로 benchmark를 실행하면 시간이 너무 오래 걸리므로, 우선 단일 기업 기준으로 범위를 줄였다.

수행한 작업:

1. 단일 기업 lane을 위한 eval/config를 추가했다.
2. runner/prebuild에 `company_filter`를 추가했다.
3. 잘못된 index reuse를 막기 위해 company 기준 cache key를 분리했다.
4. dense vs hybrid, embedding comparison, rerank, Qdrant 순서의 작은 phase를 설계했다.

결론:

- 단일 기업 기준 실행은 속도와 pipeline 동작을 점검하기에 적절하다.
- Dataset 팀의 새 ESG package가 전달된 이후에는 Hyundai-only lane보다 `05_company_export_json` package가 더 중요한 benchmark 대상이 되었다.

## 5. Dataset: fix request 반영 완료

초기 package `넥스트아이_dataset_package_20260528T082146`는 contract v1.1 형식은 충족했지만, `dataset_team_fix_request_nexteye_20260528.md`에 정리된 몇 가지 수정이 필요했다.

fix request의 핵심 요구사항과 새 package 반영 상태는 다음과 같다.

| 요구사항 | 새 package 상태 |
|---|---|
| `company_evidence`, `requirement_taxonomy`, `ai_extracted_response` 분리 | `lanes/`에 반영됨 |
| summary/AI response를 원천 evidence와 섞지 않기 | lane 분리 완료 |
| taxonomy/requirement 역할 명확화 | `requirement_taxonomy` lane 제공 |
| AI extracted response 역할 명확화 | `ai_extracted_response` lane 제공 |
| full split은 raw company evidence여야 함 | `full=170`, `company_evidence=170`으로 정렬됨 |
| split/lane checksum 제공 | `checksums`, `lane_checksums` 제공 |

현재 우선 사용 package:

`data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T091409`

Manifest 기준 주요 정보:

| 항목 | 값 |
|---|---:|
| `dataset_version` | `1.1.1` |
| `schema_version` | `1.1` |
| `record_count` | `270` |
| `document_count` | `262` |
| `company_count` | `1` |
| `source_count` | `92` |
| `dev` | `77` |
| `validation` | `93` |
| `full` | `170` |
| `company_evidence` | `170` |
| `requirement_taxonomy` | `50` |
| `ai_extracted_response` | `50` |

결론:

- fix request의 핵심 항목은 새 dataset package에 반영되었다.
- 새 dataset은 기술 smoke benchmark를 실행할 수 있는 상태다.
- `source_url=null`은 현재 결정에 따라 임시로 허용한다. smoke 단계에서는 `metadata.source_path`, `source_system`, lane role로 traceability를 보완할 수 있다.

## 6. 새 dataset 기준 테스트 로드맵

새 benchmark는 3단계로 재설계했다.

| 단계 | 목표 | 고정 조건 | 비교 변수 |
|---|---|---|---|
| Pha 1 | retrieval config 빠른 선별 | `vectorDB=chroma`, `reranker=none` | `chunking`, `embedding`, `retrieval_mode` |
| Pha 2 | reranker 효과 측정 | Pha 1 top retrieval configs | `reranker` |
| Pha 3 | production candidate 확정 | Top 2-3 configs | `vectorDB=chroma` vs `qdrant` |

너무 큰 matrix를 한 번에 실행하는 문제를 피하기 위해 다음 smoke test부터 시작하는 것이 적절하다.

| Smoke 항목 | 설정 |
|---|---|
| Dataset | `넥스트아이_dataset_package_20260528T091409/splits/dev.jsonl` |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` |
| VectorDB | `chroma` |
| Reranker | `none` |
| Retrieval mode | `semantic_dense`, `hybrid_dense_bm25` |
| 목적 | matrix 확장 전 ingest/index/query 시간 측정 |

## 7. 실제 실행 상태

Smoke 실행 준비는 시작되었다.

1. `src/rag_common.py`에 `.jsonl` record 읽기를 추가했다.
2. `src/run_benchmark_case.py`에서 `넥스트아이_dataset_package_20260528T091409` package를 필터링하도록 준비했다.
3. `configs/benchmark_model_candidates_exportjson_smoke.yaml`를 생성했다.
4. MiniLM 2 case smoke를 실행했지만, 보고서 작성 요청으로 중간에 중단했다.

현재 상태:

- smoke 최종 runtime metric은 아직 없다.
- Pha 1은 아직 확정되지 않았다.
- model/method winner도 아직 확정되지 않았다.

## 8. 남은 작업

| 작업 | 이유 |
|---|---|
| smoke 재실행 | 새 dataset의 실제 실행 속도 확인 |
| loader가 새 split/lane만 읽는지 확인 | 이전 package 또는 구 export file 혼입 방지 |
| Pha 1을 작은 batch로 실행 | BGE/e5 추가 시 timeout 방지 |
| Pha 1 이후 reranker 활성화 | reranker가 citation 개선에 실제 도움이 되는지 확인 |
| Top config에 대해서만 Qdrant 테스트 | 전체 matrix에 Qdrant를 적용하면 시간 낭비가 큼 |

## 9. 권장 실행 순서

1. 18개 case를 한 번에 다시 실행하지 않는다.
2. MiniLM smoke를 먼저 실행해 실제 시간을 측정한다.
3. smoke가 acceptable하면 Pha 1을 chunking, retrieval mode, heavy embedding 순서로 나누어 실행한다.
4. BGE/e5는 prebuild index 또는 단일 case 단위로 실행한다.
5. Qdrant는 Pha 3에서 top 2-3 config에 대해서만 실행한다.

## 10. 결론

2026-05-28의 가장 중요한 진전은 dataset 정리다. `dataset_team_fix_request_nexteye_20260528.md`의 요구사항은 새 package `넥스트아이_dataset_package_20260528T091409`에 반영되었고, evidence/taxonomy/AI response lane이 명확히 분리되었다.

다만 benchmark는 아직 최종 결론 단계가 아니다. 실행 과정에서 timeout/kill이 있었고, 새 dataset smoke도 완료되지 않았다. 다음 단계는 새 package 기준 smoke를 다시 실행한 뒤, 작은 batch로 Pha 1을 여는 것이다.
