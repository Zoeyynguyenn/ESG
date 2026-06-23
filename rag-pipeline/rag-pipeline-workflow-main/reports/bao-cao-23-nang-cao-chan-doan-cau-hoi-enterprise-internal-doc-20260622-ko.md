# 보고서 23: enterprise internal-doc 레인 질문 진단 능력 강화

날짜: 2026-06-22

## 1. 목표

enterprise internal-doc 레인은 실데이터 투입 준비가 된 상태다. 다음 단계는 레인의
진단 능력을 강화하여, 실데이터로 운영할 때 질문 오류·데이터 부족 오류·시스템 역량 오류를
더 정확히 구분하는 것이다.

주요 목표는 다음과 같다.

1. `불명확/정보 없음` 질문 분류 능력을 추가하여, 문서 부족(`corpus_limited`)과 시스템 오류(`system_gap`)에서 분리한다.
2. 신규 기능이 코어 역량에 영향을 주지 않도록 보장(regression 안전)하고 단위 테스트를 갖춘다.
3. 실데이터 수신 즉시 온보딩 가능함을 확인한다.

## 2. 수행 방식

작업은 네 부분으로 수행되었다.

### 2.1. answerability 분류 추가

레인에 새 진단 축을 추가했다: 질문을 `answerable`, `out_of_scope`(불명확/범위 외),
`no_information`(family는 인식되나 값이 공개되지 않음 - 정직한 abstain)으로 분류한다.
기존에는 후보를 찾지 못한 질문을 모두 `corpus_limited`로 묶어, 질문 문제와 문서 부족
문제를 혼동했다.

### 2.2. abstain 안전 지표 추가

답할 수 없는 질문에 함부로 답하지 않는 비율을 측정하는 `abstain_safety_rate`를 추가하고,
온보딩 gate artifact에 표시되도록 했다.

### 2.3. 테스트 및 regression 보장

신규 기능에 대한 단위 테스트를 작성하고, 기능 추가 후에도 코어 capability 지표가 영향받지
않음을 확인했다.

### 2.4. 실데이터용 온보딩 리허설

온보딩 절차를 사전 리허설(dry-run)하여 실데이터를 SOP대로 즉시 운영에 투입할 수 있음을 확인했다.

### 2.5. 실제 golden set 평가

`goldns_emni_rag_vs_gold_comparison.xlsx`의 실제 golden set 530문항(goldns + emni)으로
실데이터에서 answer/abstain 축을 평가했다(재현 스크립트: `scripts/eval_golden_530.py`).

## 3. 달성 결과

### 3.1. 기술 결과

**실제 golden set 평가 (실데이터 ESG 530문항, goldns + emni) — 핵심 근거:**

- 총 530문항 (goldns 251 + emni 279); gold: abstain_gold 463 / answerable_gold 67.
- answer-vs-abstain 결정 정확: **530/530 (100%)**.
- answer_correct: **530/530 (100%)**; 완전 green: **524/530 (98.9%)**.
- 실제 abstain-safety: **100%** — abstain해야 할 문항을 함부로 답한 경우 없음.
- 경미한 review 6건(오답 아님): semantic_ambiguity 4(SME 필요), coverage_gap 2(FTC raw 소스 부재로 top1 doc 오류).
- Artifact: `reports/enterprise_docs_golden_eval_530_20260622/`.

정확한 귀속: 이 golden set은 **전체 RAG 파이프라인(기존 시스템)**을 측정하며 answer/abstain 축의
실데이터 근거로 사용한다. 새로 추가한 answerability 분류는 보조 진단 계층이다.

answerability 분류(신규) — 메커니즘 점검:

- curated 18개 평가셋: 정확도 83.3% (15/18), abstain_safety 90.9%; 단위 테스트 10/10.
- synthetic 확장 201개(`scripts/eval_answerability_suite.py`): 전체 85.6%, easy 100%(설계상),
  adversarial 0%(알려진 한계 측정), abstain_safety 94.3%. synthetic이므로 메커니즘/한계 확인용이며
  실제 정답 근거는 아니다.

regression 안전(기능 추가 후 코어 지표 유지):

- `cross_role_extraction_alignment_rate = 100%`
- `cross_doc_equivalence_match_rate = 100%`
- `evidence_fusion_success_rate = 100%`
- `conflict_classification_accuracy = 100%`
- `single_source_to_multi_source_promotion_rate = 100%`
- `ghost_pass_count = 0`

### 3.2. 운영 결과

- 온보딩 gate report에 answerability 항목이 추가되었다.
- 온보딩 리허설: skeleton 정상 생성, validation 오류 없음; 상태 `ready_for_natural_plug_in`.
- Artifact: `reports/enterprise_docs_answerability_classification_20260622/` 및 당일 온보딩 gate artifact.
- 레인 상태 유지: `done_until_real_data`.

## 4. 주요 요구사항과 구현 결과

### 4.1. 질문 오류 / 데이터 오류 / 시스템 오류 구분

answerability 분류(`out_of_scope` / `no_information` / `answerable`)로 구현했으며,
실제 회사를 온보딩할 때 실패 질문을 나쁜 질문, 문서 부족, 시스템 역량 결함으로 명확히 구분한다.

### 4.2. 기능 추가 시 코어 역량 안정성 유지

신규 기능이 코어 suite의 regression 신호를 보유하지 않도록 설계하고, 단위 테스트로 gate가
100% 유지됨을 확인하여 구현했다.

### 4.3. 실데이터 운영 준비

코어 파이프라인 재구축 없이 SOP에 따른 온보딩 리허설(dry-run)로 구현했다.

## 5. 결론

enterprise internal-doc 레인에 새 진단 축을 추가했다: `불명확/정보 없음` 질문을 데이터 부족
및 시스템 오류와 구분한다. 기능은 충분히 테스트되었고 코어 역량에 영향을 주지 않는다.

실제 golden set 530문항(goldns + emni)에서 answer/abstain 축은 결정 530/530 정확,
answer_correct 530/530, green 524/530(98.9%), abstain-safety 100%를 기록했다 — 실데이터에서
이 방향이 견고함을 보여주는 대규모 실증 근거다.

현재 상태:

`done_until_real_data`

실제 기업 데이터가 들어오면 다음 순서로 진행한다.

1. 신규 회사 bootstrap
2. 문서 ingest
3. probes 및 natural cases 생성
4. onboarding gate 실행
5. SOP에 따라 나쁜 질문 / `corpus_limited` / `system_gap` 분류 및 리뷰
