# 보고서 14: LangGraph API 스테이징 및 H200 / AI Nexus 조사

**일자:** 2026-06-05 · **이전 보고서:** [보고서 13](bao-cao-13-chot-c2-production-git-runpod-20260604-ko.md)  
**범위:** 당일 업무 — LangGraph 팀 연동(Retrieval API) 및 H200 준비

---

## 1. 요약

| 항목 | 결과 |
|---|---|
| **LangGraph API** | FastAPI 스테이징 구축, 스펙 §8 합의, `nexteye` 사전 인덱싱, 스모크 **PASS** |
| **트랙 분리** | 스테이징 API(CPU, rerank off)와 C2 / H200 벤치마크 **독립** |
| **H200 / AI Nexus** | 운영 문서 **5건** 조사 중; 사내 **Qwen 3.5 122B** 도입 진행 |
| **프로덕션 C2** | 변경 없음 — RunPod 동결 유지; H200은 실험·이전 트랙 |

---

## 2. 수행 작업

### 2.1 H200 / kt cloud AI Nexus (문서 5건 조사)

회사 GPU 환경(kt cloud AI Nexus, NIPA 워크플로, VM 전환, 운영 QnA 등) 관련 **안내·VoC 문서 5건**을 검토 중이다. RunPod C2 벤치마크를 H200으로 옮기기 전에 **세션, NAS, 쿼터, 포트, idle 정책** 등 운영 개념을 파악하는 단계이다.

**조사 중인 요지 (개요):**

- AI Nexus는 GPU 플랫폼(Backend.AI)이며 **기본 LLM이 포함되지 않음** — 자체 배포 또는 사내 엔드포인트 필요.
- 저장: 코드·데이터·모델은 **vFolder NAS**; 로컬 scratch는 용량 제한.
- 세션: 보통 단일 세션 + **tmux**; 서빙 포트 사전 개방(예: vLLM **8000**).
- RunPod와의 차이: DinD 이중 탭 없음; 계정·NAS·쿼터는 **관리자 확인** 필요.

**산출물:** 텍스트 추출 `reports/_h200_extract/` · 내부 메모 `docs/H200_AI_NEXUS_C2.md` (초안).

**사내 소식:** H200에 **Qwen 3.5 122B** 설치 진행 — 이후 vLLM 계획 및 신규 모델로 C2 게이트 벤치마크 예정(당일 게이트 미실행).

### 2.2 LangGraph 팀용 Evidence Retrieval API

1. **기술 합의** (LangGraph §8 회신): `company_id` slug(`nexteye`), `year` **하드 필터**, `evidence_type` enum, rule-based confidence, RAG **사전 인덱싱**, 스테이징은 사내망/VPN, 미인덱스 회사 **404** / 증거 없음 **200 + 빈 배열**.
2. **스테이징 API 구현** — `src/evidence_api/`, 설정 `configs/langgraph_staging.yaml` (`production_c2_*`와 **분리**).
3. **사전 인덱싱** — Dataset `nexteye` (~630 chunks, hybrid + Qdrant, OpenAI embed, **rerank off**, GPU 미사용).
4. **스모크 테스트** — `/health`, `/retrieve`, unknown company 404; Swagger `/docs` + API key Authorize.
5. **핸드오프** — `docs/LANGGRAPH_EVIDENCE_API_THONG_NHAT.md` (rev.4), `docs/LANGGRAPH_API_HANDOFF.md`.
6. **운영 스크립트** — 인덱스 빌드·서버 기동·중지·방화벽·(선택) Cloudflare tunnel.

**LangGraph 연동 흐름:** `POST /retrieve` → `items[].text` 컨텍스트 결합 → **로컬 Ollama**로 답변 생성; RAG는 **LLM 미제공**.

---

## 3. LangGraph API 스테이징 결과

| 항목 | 상태 |
|---|---|
| 스택 | OpenAI `text-embedding-3-small` + hybrid BM25/Qdrant, rerank **off**, CPU |
| 인덱스 회사 | `nexteye` |
| 엔드포인트 | `GET /health`, `POST /retrieve`, `POST /ingest` (관리자·비동기) |
| 인증 | `X-API-Key` (스테이징) |
| 내부 테스트 | 스모크 PASS; 서버 `0.0.0.0:8787` |

**팀 전달 시 유의:**

- 코퍼스는 **한국어 중심**; vi/en 쿼리는 스테이징 허용하나 품질은 제한적.
- `year` 필터는 패키지에 `year` 메타데이터가 없어 **당분간 실효 없음**.
- 원격 팀은 **동일 LAN/VPN** 또는 tunnel URL 필요.

---

## 4. 주요 문서·파일

| 파일 | 용도 |
|---|---|
| `docs/LANGGRAPH_EVIDENCE_API_THONG_NHAT.md` | LangGraph와 합의된 스펙 |
| `docs/LANGGRAPH_API_HANDOFF.md` | URL, API key, 테스트 예시 |
| `configs/langgraph_staging.yaml` | 스테이징 스택 (C2 미사용) |
| `src/evidence_api/` | FastAPI 앱 |
| `docs/H200_AI_NEXUS_C2.md` | H200 내부 메모 |

---

## 5. 향후 작업

| 트랙 | 작업 |
|---|---|
| **LangGraph** | LAN/tunnel로 통합 테스트; integration log(Ollama 모델, KO 코퍼스 한계) |
| **H200** | AI Nexus 계정·NAS 확보; **Qwen 3.5 122B** vLLM 계획; C2 체크리스트 → H200 세션 매핑 |
| **Dataset** | 필요 시 record `year` 메타데이터 보강 |

---

*보고서 14 — 2026-06-05: LangGraph API 스테이징 및 H200 조사 단계.*
