# 2026-06-12 업무 보고

## 1. LangGraph 팀과 협업하여 Rayxion 기업 보고서 패키지 준비

이번 작업은 단순히 "기업 보고서를 작성"하는 것이 아니라, `Dataset 팀`과 `RAG 팀`이 함께 구조화된 보고서 패키지를 만드는 흐름을 정리하는 데 목적이 있다.

### 두 팀의 역할 분담

- `Dataset 팀`은 해당 기업의 원천 자료를 수집하고 정리한다.
- 수집된 자료는 `RAG 팀`에 전달된다.
- `RAG 팀`은 이 자료를 chunking, retrieval, evidence 추출에 사용한 뒤, 여러 개의 보고서 파일로 구조화한다.

### 목표 출력 형식

목표 출력은 다음과 같은 패키지 형식을 따른다.

- `C:\Users\nguye\Downloads\data-company\demo_company\rtx_7step_dataset\rtx_7step_dataset`

이 샘플 패키지는 주제별 Markdown 파일로 구성되어 있다.

1. `01_사업보고서_발췌.md`
   - 회사 개요, 사업 부문, 인력, 매출, 운영 규모
2. `02_온실가스_에너지_명세.md`
   - Scope 1, Scope 2, 에너지, 물, 폐기물, 환경 위반
3. `03_재생에너지_계약.md`
   - 재생에너지 계약 및 사용 방식
4. `04_인사_안전_통계.md`
   - 인사, 산업안전, EEO-1, workforce 통계
5. `05_사회공헌_인권.md`
   - 인권, 사회공헌, 지역사회 활동
6. `06_지배구조_운영.md`
   - 이사회, 컴플라이언스, 윤리, 지배구조 운영
7. `07_인증_현황.md`
   - 인증, 표준, 검증 체계

추가로 다음 Excel 파일도 포함된다.

- `RTX_quantitative_questions.xlsx`

이 파일은 결과물이 단순한 서술형 보고서가 아니라, 정량 질의와 retrieval/extraction 검증에도 재사용될 수 있음을 보여준다.

## 2. LangGraph 팀용 API 수정 및 낮은 신뢰도 플래그 추가

두 번째 작업은 `LangGraph` 팀이 사용하는 API 응답 형식을 더 안전하게 바꾸는 것이다.

### 수정이 필요한 이유

API가 단순히 `items`만 반환하면, `LangGraph` 쪽에서는 다음과 같은 문제가 생길 수 있다.

- 약한 evidence를 정상 evidence로 오인
- retrieval이 충분하지 않은데도 generation을 계속 진행
- 겉보기에는 자연스럽지만 근거가 약한 보고서를 생성

### API 수정 방향

응답에 다음과 같은 reliability 신호를 추가했다.

- `retrieval_confidence`
- `abstain_recommended`
- `no_relevant_evidence`
- `answerable_candidate`

이 신호를 통해 `LangGraph` 팀은 다음을 구분할 수 있다.

- evidence가 충분한 경우
- evidence는 있으나 아직 약한 경우
- 현재 단계에서는 답변 또는 보고서 생성을 멈춰야 하는 경우

### Handoff 문서

아래 문서를 별도로 작성했다.

- `docs/LANGGRAPH_SWAGGER_RETRIEVE_HANDBOOK_20260612.md`

문서에는 다음 내용이 포함된다.

- `/retrieve` 호출 방식
- reliability 플래그 해석 방법
- `generation_guard`를 켜야 하는 경우
- 근거가 약할 때 generation을 바로 이어가면 안 되는 이유

## 3. 새로운 데이터로 Silver -> Golden Set 흐름 진행

세 번째 작업은 `Silver -> Golden Set` 흐름을 더 나은 새 데이터에 적용하여, Golden Set 생성 시스템 자체를 다시 검증하는 것이다.

### 현재 목적

핵심 목적은 이전의 부족한 데이터셋을 계속 보정하는 것이 아니라, 더 나은 데이터에서 시스템이 올바르게 작동하는지 확인하는 것이다.

### 새 입력 lane

새로운 RTX lane:

- `data/rag_dataset/06_rtx_references_raw`

현재 입력 구성:

- `_sources` 내 PDF `4`개
- `web_sources` 내 raw HTML `5`개
- DOJ fallback snapshot `.md` `1`개

총합:

- 원천 파일 `10`개

### 초기 처리 결과

이 lane은 다음과 같이 chunking 되었다.

- `2762` chunks
- `2761` corpus units

normalize 이후:

- source units `2761`
- normalized units `2724`

### workbook-first 진행 결과

첫 번째 candidate generation 결과:

- raw candidates `4116`
- filtered candidates `3170`

이후 큰 문제가 확인되었다.

- `3170`개 row가 있었지만 실제 question template은 `11`개뿐이었다.
- 즉, `100%` row가 exact duplicate question backbone의 영향을 받았다.

그래서 다음 순서로 방향을 재설정했다.

1. duplicate question audit
2. `v2 fact-specific` rebuild
3. `fact-target quality` audit
4. `v2.1 fact-quality` rebuild

### 현재 상태

현재 유효한 결과는 다음과 같다.

- usable candidates `42`
- unique questions `42`
- exact duplicate `0`

현재 기준 artifact:

- `data/golden_set/v2/reference_style/reference_seed_workbook_rtx_v2_1_fact_quality.xlsx`

이 상태의 의미:

- 시스템이 대량의 일반 질문을 반복 생성하는 문제는 해소되었다.
- 새로운 lane은 `review round 1`을 다시 열 수 있을 정도로 정리되었다.
- 아직 benchmark, canonical, gold decision 단계로는 넘어가지 않았다.

## 4. 오늘 작업의 전체 연결 구조

오늘의 세 가지 작업은 서로 연결된 하나의 흐름으로 볼 수 있다.

1. `Dataset 팀`이 `Rayxion` 관련 원천 자료를 수집 및 전달
2. `RAG 팀`이 이 자료를 사용해 `7-step dataset` 형태의 보고서 파일 패키지 생성 준비
3. `LangGraph 팀`은 reliability 플래그가 포함된 retrieval/API 결과를 받아 더 안전하게 보고서를 생성
4. 동시에 `Silver -> Golden Set` 시스템은 새로운 데이터에서 다시 검증됨

오늘 보고서에서 강조해야 할 핵심은 다음과 같다.

- `Rayxion` 작업은 단순 보고서 요청이 아니라 `dataset -> report package` 흐름이다.
- `LangGraph API` 수정은 downstream이 언제 경고해야 하고 언제 generation을 멈춰야 하는지 판단하기 위한 것이다.
- `Golden Set` 작업은 더 좋은 데이터로 시스템을 다시 검증하는 단계까지 넘어갔다.
