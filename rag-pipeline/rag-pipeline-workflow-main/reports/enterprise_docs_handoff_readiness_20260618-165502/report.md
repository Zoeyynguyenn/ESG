# Enterprise internal-doc — Handoff readiness round

Artifact: `reports\enterprise_docs_handoff_readiness_20260618-165502`

## Mục tiêu
Formal hóa schema handoff theo family và kiểm tra promotion `extraction_ready` → `single_source_sufficient`.
Không synthesis, không LangGraph trial.

## Family pilot summary

### `employee_headcount` (pilot #1)
- question_type: `quantitative_headcount`
- required_readiness_state: `single_source_sufficient`
- required_evidence_count: 1
- primary_doc_rule: doc_hr_safety_or_sustainability_report
- handoff_blockers: qualitative_kind, coverage_gap, wrong_row_risk, missing_predicted_value
- notes: Pilot family — table on demo_company; narrative headcount on holdout SR corpus

### `environment_ghg` (pilot #2)
- question_type: `quantitative_climate_metric`
- required_readiness_state: `single_source_sufficient`
- required_evidence_count: 1
- primary_doc_rule: sustainability_report_or_ghg_doc
- handoff_blockers: qualitative_kind, coverage_gap, unresolved_conflict
- notes: Climate/year/scope narrative metrics; qualitative CDP probes remain blocked

### `governance` (pilot #3)
- question_type: `quantitative_governance_narrative`
- required_readiness_state: `single_source_sufficient`
- required_evidence_count: 1
- primary_doc_rule: governance_or_sustainability_report
- handoff_blockers: qualitative_kind, coverage_gap, wrong_row_risk
- notes: Board meetings, ESG grades, materiality counts — narrative-first on holdout

## Kết quả promotion

- promoted / not_promoted: `{'not_promoted': 45}`

### Theo company

{
  "demo_company": {
    "case_count": 18,
    "promoted_count": 0,
    "handoff_candidate_count": 5,
    "readiness_before": {
      "extraction_ready": 3,
      "retrieval_ready": 9,
      "single_source_sufficient": 6
    },
    "readiness_after": {
      "extraction_ready": 3,
      "retrieval_ready": 9,
      "single_source_sufficient": 6
    },
    "promotion_rate": 0.0
  },
  "hanssem": {
    "case_count": 16,
    "promoted_count": 0,
    "handoff_candidate_count": 0,
    "readiness_before": {
      "coverage_gap": 16
    },
    "readiness_after": {
      "coverage_gap": 16
    },
    "promotion_rate": 0.0
  },
  "musinsa": {
    "case_count": 11,
    "promoted_count": 0,
    "handoff_candidate_count": 0,
    "readiness_before": {
      "coverage_gap": 11
    },
    "readiness_after": {
      "coverage_gap": 11
    },
    "promotion_rate": 0.0
  }
}

### Theo family (pilot)

{
  "employee_headcount": {
    "case_count": 4,
    "quantitative_count": 4,
    "promoted_count": 0,
    "single_source_count": 0,
    "multi_source_count": 0,
    "handoff_candidate_count": 0,
    "still_extraction_ready": 1,
    "not_handoff_ready": 4,
    "promotion_rate": 0.0,
    "companies": [
      "demo_company",
      "hanssem",
      "musinsa"
    ]
  },
  "environment_ghg": {
    "case_count": 14,
    "quantitative_count": 12,
    "promoted_count": 0,
    "single_source_count": 2,
    "multi_source_count": 0,
    "handoff_candidate_count": 1,
    "still_extraction_ready": 2,
    "not_handoff_ready": 13,
    "promotion_rate": 0.0,
    "companies": [
      "demo_company",
      "hanssem",
      "musinsa"
    ]
  },
  "governance": {
    "case_count": 18,
    "quantitative_count": 14,
    "promoted_count": 0,
    "single_source_count": 4,
    "multi_source_count": 0,
    "handoff_candidate_count": 4,
    "still_extraction_ready": 0,
    "not_handoff_ready": 14,
    "promotion_rate": 0.0,
    "companies": [
      "demo_company",
      "hanssem",
      "musinsa"
    ]
  }
}

## System decision

{
  "phase": "handoff_preparation",
  "ready_for_limited_langgraph_handoff": false,
  "ready_for_limited_langgraph_handoff_preparation": false,
  "not_ready_for_synthesis": true,
  "not_ready_for_langgraph_trial": true,
  "single_source_sufficient_families": [
    "environment_ghg",
    "governance"
  ],
  "extraction_ready_only_families": [
    "employee_headcount",
    "environment_ghg"
  ],
  "handoff_prep_candidate_families": [],
  "not_handoff_ready_families": [
    "employee_headcount"
  ],
  "holdout_promotion_rate": 0.0,
  "holdout_promoted_by_family": {},
  "prior_holdout_extraction_avg": 0.5995,
  "gaps_before_trial": [
    "evidence_packaging_on_holdout",
    "confidence_policy_calibration",
    "review_owner_rule_enforcement",
    "formal_single_source_sufficient_on_holdout"
  ]
}
