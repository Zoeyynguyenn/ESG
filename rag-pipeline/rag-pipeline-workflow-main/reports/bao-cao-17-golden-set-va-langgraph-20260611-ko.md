# 보고서 17: Golden Set 6단계 워크플로우 및 LangGraph staging retrieval 정리

**일자:** 2026-06-11  
**범위:** 당일 핵심 작업 2건 — `Golden Set` 구축 방식 정리, `LangGraph staging retrieval` 원인 및 수정 방향 정리

---

## 1. Golden Set ESG 작업

현재 목표는 ESG용 `Golden Set`을 `Silver -> Gold` 방식으로 구축하는 것이다.  
이 단계에서는 최종 점수나 최종 accuracy를 확정하지 않고, 실제 운영 가능한 **6단계 워크플로우**를 기준으로 정리한다.

### 1.1 전체 흐름

```text
1. Corpus Units 준비
   ↓
2. Distillation으로 Silver Dataset 생성
   ↓
3. Evol-Instruct로 질문 난이도 확장
   ↓
4. 자동 QC + LLM-as-a-judge
   ↓
5. SME 검증 또는 AI judge 대체 검증
   ↓
6. Gold Set으로 승격(Promote)
```

### 1.2 6단계 설명

#### 1) Corpus Units 준비

입력은 `company_export_json` 패키지의 `jsonl` 데이터다.

주요 작업:
- `jsonl`에서 ESG 관련 문단/record를 읽는다.
- `company`, `record_id`, `source`, `section` 같은 metadata를 붙인다.
- 이후 질문 생성에 쓸 수 있는 단위(`corpus units`)로 정리한다.

의미:
- 질문과 답변이 나중에 반드시 원문 source로 되돌아갈 수 있게 만든다.
- 뒤 단계의 품질관리 기준점을 준비한다.

#### 2) Distillation으로 Silver Dataset 생성

LLM이 `corpus units`를 읽고 `question-answer` 쌍을 자동으로 만든다.

주요 작업:
- context 기반 질문 생성
- context 안에서만 답변 생성
- 대량의 Silver Q&A를 빠르게 확보

의미:
- 사람이 처음부터 전부 수작업하지 않아도 된다.
- 넓은 후보군을 확보한 뒤 다음 단계에서 정제할 수 있다.

#### 3) Evol-Instruct로 질문 난이도 확장

Silver의 단순 질문만으로는 실제 RAG 평가가 약해지기 때문에 일부 질문을 더 어렵게 확장한다.

주요 작업:
- 단순 fact 질문을 reasoning 질문으로 변형
- 여러 문맥을 함께 읽어야 하는 multi-context 질문 생성
- 질문 다양성 확대

의미:
- 너무 쉬운 문제만 있는 평가셋을 피한다.
- 실제 RAG 성능 차이를 더 잘 드러낼 수 있다.

#### 4) 자동 QC + LLM-as-a-judge

Silver 단계의 샘플을 자동으로 1차 필터링한다.

주요 작업:
- `answerability` 확인: context만으로 답 가능한가
- `difficulty` 확인: 너무 쉬운가, 단순 복사인가
- `groundedness` 확인: 답변이 context 밖으로 벗어나지 않는가
- `LLM-as-a-judge`로 1차 판정

의미:
- 사람 검토 전에 품질이 너무 낮은 샘플을 줄인다.
- SME 검토 비용을 낮춘다.

#### 5) SME 검증 또는 AI judge 대체 검증

이 단계에서 샘플을 실제 검증 가능한 수준으로 끌어올린다.

주요 작업:
- 질문, 답변, context를 다시 확인
- approve / revise / reject 판단
- SME가 충분하지 않으면 AI judge를 보조 또는 대체 수단으로 사용

의미:
- 단순히 “LLM이 만든 샘플”에서
- “검증을 통과한 샘플”로 상태가 바뀐다.

#### 6) Gold Set으로 승격

QC와 검증을 통과한 샘플만 최종 `Gold Set`으로 올린다.

주요 작업:
- 승인된 샘플만 선택
- Gold 파일로 저장
- 이후 evaluation / regression의 기준 데이터로 사용

의미:
- 이 단계부터 `source of truth` 역할을 할 수 있다.
- benchmark나 regression test에 쓸 수 있는 안정된 기준셋이 된다.

### 1.3 요약

Golden Set 작업의 핵심은:
- 처음부터 Gold를 만들려고 하지 않고
- `Silver -> QC -> 검증 -> Gold` 순서로 단계적으로 신뢰도를 높이는 것이다.

---

## 2. LangGraph staging retrieval 수정

이 작업은 `LangGraph staging retrieval`이 ESG 데이터에서 더 정확한 evidence를 찾도록 만드는 데 목적이 있다.

### 2.1 현재 문제가 생기는 이유

원인은 크게 3가지다.

#### 1) Noise가 많음

현재 retrieval 대상 passage 안에는 다음이 섞여 있다.
- `news chrome`
- `listing`
- `meta`
- `cross-company contamination`

이 때문에 검색 결과가 ESG 본문보다 주변 잡음으로 끌릴 수 있다.

#### 2) 한국어 처리가 충분히 반영되지 않음

질문과 corpus는 대부분 한국어인데,
- BM25 / lexical retrieval에서 한국어 tokenization이 약하면
- keyword 기반 검색이 제대로 동작하지 않는다.

즉, 영어 중심 토큰 처리로는 한국어 ESG 질문에 약해진다.

#### 3) rerank가 runtime에서 제대로 작동하지 않음

설정 파일에서 retrieval mode나 rerank를 켜더라도,
- staging service가 올바른 runtime path를 타지 않으면
- 실제 검색 결과에는 rerank 효과가 반영되지 않는다.

즉, 문제는 단순 config가 아니라 **service wiring**에도 있다.

### 2.2 수정 방향

수정 방향은 아래 3가지다.

#### 1) Noise 영향을 줄이기

- retrieval 대상에서 `listing`, `meta`, `news chrome`의 영향을 줄인다.
- ESG 본문 evidence가 상위에 오도록 정리한다.

#### 2) 한국어 retrieval 보강

- Korean BM25 / tokenization을 우선 보강한다.
- 한국어 질문에서도 lexical retrieval이 실제 역할을 하도록 만든다.

#### 3) staging이 올바른 retrieval + rerank path를 타게 만들기

- service가 `retrieval_mode`를 제대로 읽어야 한다.
- runtime이 실제 `retrieve/rerank` 경로를 타야 한다.
- 그래야 config에서 켠 rerank가 실제로 효력을 가진다.

### 2.3 요약

LangGraph staging retrieval의 문제는 단순히 “설정 변경”이 아니라,
- 데이터에 noise가 많고
- 한국어 retrieval 보강이 필요하며
- rerank가 runtime path에서 제대로 연결되어야 한다는 점이다.

따라서 현재 수정 방향은:
- noise 완화
- 한국어 retrieval 개선
- rerank path 정상화

---

## 3. 최종 요약

오늘 핵심 작업은 2가지다.

1. `Golden Set`을 6단계 `Silver -> Gold` 워크플로우로 정리했다.
2. `LangGraph staging retrieval`의 문제를 `noise`, `한국어`, `rerank path` 기준으로 정리하고 수정 방향을 명확히 했다.

현재 단계에서는 결과 수치보다 **방법과 방향을 정확히 잡는 것**이 더 중요하다.
