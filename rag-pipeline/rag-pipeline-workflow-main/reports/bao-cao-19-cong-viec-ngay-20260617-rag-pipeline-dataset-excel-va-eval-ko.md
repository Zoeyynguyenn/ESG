# 2026-06-17 RAG Pipeline 작업 보고

## 1. 이번 워크스트림의 목표

이번 workstream에서 `RAG pipeline` 팀의 목표는 Dataset 팀이 전달한 데이터를 실제로 평가 가능한 파이프라인으로 전환하는 것이다. 입력은 ESG Excel workbook만이 아니라, provenance 보강과 원문 파싱을 위해 Dataset 팀이 함께 전달한 JSON/DART 파일도 포함한다.

최종적으로 RAG 팀이 보고해야 하는 결과는 단순한 응답 여부가 아니라 다음 지표를 포함한 평가 결과다.

- `retrieval_hit_rate`
- `answer_accuracy`
- `abstain_accuracy`
- `source_match_rate`
- `overall_score`

현재 단계에서는 RAG 실행 이전의 데이터 계층과 source intake를 정리하는 작업을 마무리하고 있으며, 이후 실제 RAG 실행 시 신뢰 가능한 점수를 산출할 수 있도록 기반을 갖추는 것이 목적이다.

## 2. RAG pipeline의 전체 흐름

### 1단계. Dataset 팀으로부터 데이터 수령

현재 입력은 두 층으로 구성된다.

1. ESG Excel workbook
   - 질문 목록
   - Dataset 팀이 찾은 정답
   - `Not disclosed` 상태
   - `Source URL`, `File URL`, `Source document/page`
2. 추가 JSON/DART 패키지
   - `DART_주요정보`
   - `DART_재무`
   - provenance 보강 및 parser 전용 lane 처리를 위한 local source

### 2단계. 입력을 구조화된 artifact로 변환

Workbook은 다음 3개 artifact로 분리된다.

- `questions`
- `gold_answers`
- `sources`

이 단계의 목적은 수작업 입력을 반복 가능한 benchmark 입력으로 바꾸는 것이다.

### 3단계. RAG 실행 전 eval 세트 정제

Workbook의 모든 row가 즉시 benchmark 가능한 것은 아니다. 따라서 RAG 팀은 데이터를 다음과 같이 구분한다.

- `answerable_gold`
- `abstain_gold`
- `needs_review`

이를 통해:

- 정답과 source가 모두 있는 질문
- 시스템이 abstain 해야 하는 질문
- provenance 또는 의미 해석 재검토가 필요한 질문

을 분리한다.

### 4단계. Source intake

`sources`가 준비되면 source를 두 개의 lane으로 나눈다.

- `crawl_web`
- `resolve_local_file_first`

이 단계는 웹 filing page와 실제로 parse/chunk 해야 하는 local JSON 원문을 혼동하지 않기 위해 중요하다.

### 5단계. Parse, chunk, corpus 구성

각 source는 적절한 lane에 들어간 뒤 다음 순서로 처리된다.

1. raw content parse
2. metadata 정규화
3. chunk 분할
4. retrieval용 corpus/index 적재

### 6단계. RAG 실행

Corpus가 준비되면 실제 RAG를 수행한다.

1. retrieval
2. evidence selection
3. answer generation 또는 abstain
4. source/provenance 연결

### 7단계. Gold 비교 및 metrics/score 보고

RAG 결과는 `question_id` 기준으로 `answerable_gold`, `abstain_gold`와 비교한다.

최종 보고는 두 층으로 구성된다.

1. Coverage
   - 전체 질문 수
   - answerable 질문 수
   - abstain 질문 수
   - 실행 완료 수
   - skip/block 수
2. Metrics / score
   - `retrieval_hit_rate`
   - `answer_accuracy`
   - `abstain_accuracy`
   - `source_match_rate`
   - `overall_score`

### 8단계. 개선 및 재실행

점수가 목표에 미달하면 다음 층을 개선한다.

- source mapping
- parser/chunking
- retrieval
- reranking
- generation guardrails

이후 eval을 재실행하고 metrics/score를 갱신한다.

## 3. 현재 진행 상태

현재까지 RAG 팀은 다음을 완료했다.

- ESG workbook ingest
- local JSON/DART package를 source lane에 연결
- `eval-ready` 세트 생성
- web source와 local source를 parse/chunk 전 단계까지 준비

아직 최종 RAG benchmark 단계에 들어가지는 않았기 때문에 최종 score는 아직 보고하지 않는다. 다만 실제 RAG 실행으로 넘어가기 위한 데이터 계층은 준비가 완료된 상태다.

## 4. 현재 결과

### 4.1. 재처리한 입력

현재 사용 중인 두 workbook은 다음과 같다.

- `C:\Users\nguye\Downloads\data-company\dataset-excel\골드앤에스_Final_ESG_Data.xlsx`
- `C:\Users\nguye\Downloads\data-company\dataset-excel\이엠앤아이_Final_ESG_Data.xlsx`

또한 Dataset 팀이 추가 제공한 local JSON은 다음 경로에 존재한다.

- `C:\Users\nguye\Downloads\data-company\dataset-excel\output_restart_emni_20260617\output_restart_emni_20260617\이엠앤아이_일반자료_20260617\02_재무_신용`
- `C:\Users\nguye\Downloads\data-company\dataset-excel\output_restart_goldns_20260616\output_restart_goldns_20260616\골드앤에스_일반자료_20260616\02_재무_신용`

### 4.2. Eval-ready 결과

새 `emni` workbook으로 전체 체인을 다시 실행한 뒤 현재 결과는 다음과 같다.

- `goldns`
  - `24 answerable`
  - `227 abstain`
  - `0 needs_review`
- `emni`
  - `43 answerable`
  - `236 abstain`
  - `0 needs_review`

즉, 두 회사 모두 benchmark에 사용할 수 있는 eval-ready 세트가 준비되었다.

### 4.3. Source intake 상태

현재 source prep 결과는 다음과 같다.

- 총 unique source: `18`
- `crawl_web`: `4`
- `resolve_local_file_first`: `14`
- `needs_review`: `0`

회사별 분포:

- `emni`: `13` source
  - `1` web
  - `12` local JSON
- `goldns`: `5` source
  - `3` web
  - `2` local JSON

### 4.4. Local JSON collect 상태

최신 manifest 기준 local source collector 결과는 다음과 같다.

- 총 local source: `14`
- collect 성공: `14/14`
- fail: `0`

Schema 분포:

- `dart_financial_statement`: `3`
- `dart_employee_status`: `5`
- `dart_executive_status`: `3`
- `dart_board_director_change`: `3`

생성 artifact 경로:

- `data/source_raw/20260617_goldns_emni_local/`

각 source에는 다음 파일이 생성된다.

- `source_manifest.json`
- `extracted.txt`
- `records.jsonl`
- `raw.json`

### 4.5. Web source 상태

Web lane에서는 이전 단계에서 raw source를 이미 수집했다.

- 총 web source: `9`
- 다운로드 성공: `8`
- FTC 사이트 redirect loop로 인해 `1` source 미해결

이 backlog는 local JSON lane을 막지는 않지만, 전체 web corpus 완성을 위해 후속 처리 필요가 있다.

## 5. 주요 업무 메모

`emni`의 2024 회계 lane에서는:

- `2024_재무_CFS.json`은 없고
- `2024_재무_OFS.json`은 존재한다

RAG 팀은 이 provenance를 기준으로 관련 질문을 `answerable_gold`에 연결했다.

다만 다음 항목은 SME semantic audit이 필요하다.

- `emni-0237`
  - `2024_재무_OFS.json`의 값 `1487`
  - 현재 `당기순이익(손실)` account와 매칭됨
  - workbook label인 `세금 및 공과 + 법인세`와의 의미 일치 여부는 추가 확인 필요

즉, provenance는 확보되었지만 semantic mapping은 별도 점검이 필요하다.

## 6. 결론 및 다음 단계

오늘 기준으로 RAG 팀은 두 회사에 대해 데이터 및 source intake 계층을 완료했다. 이는 실제 RAG benchmark와 metrics/score 산출 전에 반드시 필요한 준비 단계다.

다음 단계는 다음과 같다.

1. local JSON과 web raw source를 통합하여 chunk/index 구성
2. eval runner를 `question_id` 기준으로 연결
3. `answerable_gold`, `abstain_gold` 기준으로 RAG 실행
4. `retrieval_hit_rate`, `answer_accuracy`, `abstain_accuracy`, `source_match_rate`, `overall_score` 보고
5. 결과가 미흡하면 pipeline 개선 후 재실행
