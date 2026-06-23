# 보고서 16: LangGraph API — 신규 3개사, OpenAI 검증, 엔드포인트 확장

**일자:** 2026-06-08 · **이전 보고서:** [보고서 14](bao-cao-14-langgraph-api-va-h200-20260605-ko.md)  
**범위:** LangGraph 스테이징 API 확장; OpenAI 사전 인덱싱 및 검증 (rerank none)

---

## 1. 요약

| 항목 | 결과 |
|---|---|
| **스테이징 데이터셋** | **신규 3개사** 추가 — 주 테스트 대상 전환; **`nexteye` 캐시 유지**(legacy) |
| **레지스트리** | `musinsa`, `rayshion`, `hanssem` + `nexteye` (`legacy_cache_only`) |
| **신규 API** | `GET /companies` — 회사 목록 + 인덱스 상태 |
| **사전 인덱싱** | OpenAI embed + hybrid Qdrant, **rerank off** — `--force` 재빌드 **PASS** |
| **검증** | `verify_langgraph_openai_flow.py` + 스모크 **PASS** — 4/4 indexed |
| **H200** | 백엔드 **대기**(LLM + rerank GPU); LangGraph 스테이징과 **독립** |

---

## 2. 수행 작업

### 2.1 레지스트리 및 캐시 확장

| `company_id` | Dataset 패키지 | 비고 |
|---|---|---|
| `musinsa` | `무신사_dataset_package_20260608T092823` | **주 테스트** |
| `rayshion` | `레이시온_dataset_package_20260608T055801` | **주 테스트** |
| `hanssem` | `한샘_dataset_package_20260608T042739` | **주 테스트** |
| `nexteye` | `넥스트아이_dataset_package_20260528T091409` | **Legacy** — 기존 캐시만 사용, 재빌드 없음 |

- 설정: `configs/langgraph_staging.yaml` (`api_id: langgraph_staging_v2`)
- `nexteye`: 기존 `corpus_version` 유지 → v1 인덱스 캐시 호환
- 신규 3개사: `corpus_version: langgraph_staging_20260608`

### 2.2 LangGraph API — 엔드포인트

| 엔드포인트 | 용도 | LangGraph MVP |
|---|---|---|
| `GET /companies` | `company_id` + `indexed` + `legacy_cache_only` | **사용** — 목록 조회 |
| `GET /health` | 서버·인덱스 상태 | 사용 |
| `POST /retrieve` | Evidence 검색 | **핵심** |
| `POST /ingest` | 인덱스 비동기 재빌드 (관리자) | **미사용** — RAG가 스크립트로 사전 인덱싱 |

`POST /ingest` = Qdrant/BM25 인덱스 재구축(스크립트와 동일). PDF 업로드·답변 생성 **없음**.

### 2.3 사전 인덱싱 및 OpenAI 검증 (rerank none)

**재빌드 명령:**

```powershell
python scripts/prebuild_langgraph_staging_index.py --company musinsa --force
python scripts/prebuild_langgraph_staging_index.py --company rayshion --force
python scripts/prebuild_langgraph_staging_index.py --company hanssem --force
```

**인덱스 결과:**

| 회사 | Chunks | Retrieve 점검 |
|---|---:|---|
| musinsa | 739 | 5 items, `record_id` 있음 — **양호** |
| rayshion | 739 | 2 items, `manifest.json` 메타데이터 편향 |
| hanssem | 759 | 2 items, rayshion과 유사 |
| nexteye (legacy) | 기존 캐시 | 인덱스 OK; 쿼리 시 `items: []` 가능 |

**검증 스크립트:** `scripts/verify_langgraph_openai_flow.py`  
**스모크:** `scripts/smoke_langgraph_evidence_api.py` — PASS (4/4 indexed, `unknown_co` → 404)

### 2.4 LangGraph 팀 운영

- 서버: `python scripts/run_langgraph_evidence_api.py --host 0.0.0.0 --port 8787`
- Swagger: `/docs` · 회사 목록: `/companies`
- 핸드오프: `docs/LANGGRAPH_API_HANDOFF.md`, `docs/LANGGRAPH_EVIDENCE_API_THONG_NHAT.md`
- 네트워크: LAN / 방화벽 / Cloudflare tunnel (원격 팀)

---

## 3. 트랙 분리 (확정)

```text
LangGraph 스테이징 (완료):
  OpenAI embed + hybrid Qdrant + rerank OFF + CPU
  → POST /retrieve → LangGraph Ollama generate

H200 (추후):
  사내 백엔드 → LLM API (Qwen 3.5 122B) + rerank GPU 테스트
  → C2 게이트 벤치마크 — langgraph_staging과 config/index 분리
```

---

## 4. 기술 검증 결과

| 항목 | 결과 |
|---|---|
| OpenAI API key | OK |
| `rerank_enabled` | `false` |
| `gpu` | `false` |
| `GET /companies` | 4개사, `indexed_count: 4` |
| `POST /retrieve` musinsa | HTTP 200, `record_id` 포함 evidence |
| 미등록 company | HTTP 404 `company_not_indexed` |

---

## 5. 이슈 및 제한사항

1. **rayshion / hanssem** — 검색 시 `manifest.json` 메타데이터가 evidence 본문보다 우선되는 경우 있음 → ingest(lane `company_evidence`) 개선 검토.
2. **nexteye legacy** — 디스크에 패키지 없을 수 있음; 캐시만 신뢰. LangGraph는 **신규 3개사** 우선 테스트.
3. **`year` 필터** — 패키지에 `year` 메타데이터 없음 → empty 반환 (스펙 준수).
4. **H200** — LLM/rerank API 미검증; 사내 인프라 대기.

---

## 6. 향후 작업

| 트랙 | 작업 |
|---|---|
| **LangGraph** | 3개사 통합 테스트; `/companies` → `/retrieve` → Ollama; integration log |
| **RAG 스테이징** | (선택) rayshion/hanssem ingest 개선 |
| **H200** | AI Nexus 계정·NAS; vLLM Qwen 3.5 122B; rerank GPU 테스트 |
| **Dataset** | `year` 메타데이터 보강 |

---

## 7. 참고 파일

| 파일 | 내용 |
|---|---|
| `configs/langgraph_staging.yaml` | 4개사 레지스트리 |
| `scripts/prebuild_langgraph_staging_index.py` | 사전 인덱싱 |
| `scripts/verify_langgraph_openai_flow.py` | OpenAI + retrieve 검증 |
| `scripts/smoke_langgraph_evidence_api.py` | 스모크 테스트 |
| `docs/LANGGRAPH_API_HANDOFF.md` | LangGraph 핸드오프 |

---

*보고서 16 — 2026-06-08: LangGraph 스테이징 3개사 확장 및 OpenAI 검증(rerank none).*
