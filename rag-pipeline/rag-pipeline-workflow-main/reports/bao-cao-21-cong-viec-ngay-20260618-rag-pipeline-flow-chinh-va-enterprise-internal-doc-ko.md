# 2026-06-18 업무 보고 21

## 1. RAG 팀의 메인 플로우 진행 결과

- 팀은 `Dataset -> Source -> RAG -> metrics/score -> Excel review` 흐름을 계속 운영했습니다.
- `goldns`와 `emni` 2개 회사에 대해서는 이 흐름이 end-to-end로 완료되었고 현재 안정 상태에 있습니다.
- 현재 benchmark 결과는 다음과 같습니다.
  - `answer_accuracy = 1.0`
  - `abstain_accuracy = 1.0`
  - `overall_score = 0.9702`
- 또한 RAG 결과와 원본 gold 파일을 직접 비교할 수 있도록 Excel 비교 파일을 생성했습니다.
  - `reports/goldns_emni_rag_vs_gold_comparison.xlsx`
- 이 review 파일에는 완전 일치 행, SME 검토 필요 행, source/coverage 부족 행, retrieval 확인 필요 행을 별도로 볼 수 있는 sheet가 포함되어 있습니다.

## 2. 메인 플로우의 의미

- 팀은 이제 `metrics`와 `score`로 RAG 품질을 안정적으로 측정할 수 있는 흐름을 확보했습니다.
- 기술 리포트만 보는 방식이 아니라 Excel 기반으로 빠르게 결과를 검토할 수 있는 체계도 마련했습니다.
- 동시에 이후 다른 회사에도 재사용할 수 있도록 공통 `rule`과 `pattern`을 축적하기 시작했습니다.

## 3. 신규 보완 lane: enterprise internal-doc

- 메인 플로우와 별도로 오늘 `enterprise internal-doc` lane을 추가로 확장했습니다.
- 이 lane은 기업 제공 자료 및 내부 문서를 대상으로 하며, `PDF`, `Excel`, `HTML`, `JSON`, `Word`, `PPT` 등 다양한 형식을 처리하는 것을 목표로 합니다.
- 목적은 문서를 구조화된 `evidence`로 변환하고, 데이터의 준비 상태를 판단한 뒤, 이후 조건이 충족되면 LangGraph 팀으로 handoff하는 것입니다.

## 4. enterprise internal-doc lane의 현재 상태

- 이 lane은 pilot 수준을 넘어, 보다 명확한 contract를 가진 framework 단계로 올라왔습니다.
- 현재 다음 요소들이 구성되어 있습니다.
  - pattern 및 문서 관리용 registry
  - readiness model
  - holdout harness
  - LangGraph handoff contract
- 현재까지의 결과는 방향이 맞다는 것을 보여주지만, 아직 synthesis/generative 단계는 열지 않았습니다.
- 현 단계에서는 개별 오류 수정보다 abstraction, holdout robustness, synthesis gate 정리에 우선순위를 두고 있습니다.

## 5. 결론 및 다음 단계

- 메인 플로우 `Dataset -> RAG -> metrics/score -> Excel review`는 이미 명확한 결과를 내고 있으며 시스템 품질 평가에 바로 활용할 수 있습니다.
- `enterprise internal-doc` lane은 향후 실제 기업 문서 처리 과제를 대비하기 위한 필수 보완 방향으로 추가되었습니다.
- 다음 단계에서는 시스템의 재사용성을 계속 강화하고, holdout 범위를 통제된 방식으로 확장하되, quality gate가 충족되기 전까지는 새 lane에서 synthesis를 열지 않을 예정입니다.
