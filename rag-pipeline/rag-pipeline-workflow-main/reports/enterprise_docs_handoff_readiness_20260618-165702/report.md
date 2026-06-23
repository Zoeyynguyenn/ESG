# Enterprise internal-doc — Handoff readiness round

Artifact: `reports\enterprise_docs_handoff_readiness_20260618-165702`

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

- promoted / not_promoted: `{'not_promoted': 39, 'promoted': 6}`

### Theo company

{
  "demo_company": {
    "case_count": 18,
    "promoted_count": 6,
    "handoff_candidate_count": 12,
    "readiness_before": {
      "extraction_ready": 3,
      "retrieval_ready": 9,
      "single_source_sufficient": 6
    },
    "readiness_after": {
      "single_source_sufficient": 12,
      "retrieval_ready": 6
    },
    "promotion_rate": 0.3333
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
    "promoted_count": 1,
    "single_source_count": 1,
    "multi_source_count": 0,
    "handoff_candidate_count": 1,
    "still_extraction_ready": 0,
    "not_handoff_ready": 3,
    "promotion_rate": 0.25,
    "companies": [
      "demo_company",
      "hanssem",
      "musinsa"
    ]
  },
  "environment_ghg": {
    "case_count": 14,
    "quantitative_count": 12,
    "promoted_count": 4,
    "single_source_count": 6,
    "multi_source_count": 0,
    "handoff_candidate_count": 6,
    "still_extraction_ready": 0,
    "not_handoff_ready": 8,
    "promotion_rate": 0.2857,
    "companies": [
      "demo_company",
      "hanssem",
      "musinsa"
    ]
  },
  "governance": {
    "case_count": 18,
    "quantitative_count": 14,
    "promoted_count": 1,
    "single_source_count": 5,
    "multi_source_count": 0,
    "handoff_candidate_count": 5,
    "still_extraction_ready": 0,
    "not_handoff_ready": 13,
    "promotion_rate": 0.0556,
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
    "employee_headcount",
    "environment_ghg",
    "governance"
  ],
  "extraction_ready_only_families": [],
  "handoff_prep_candidate_families": [],
  "not_handoff_ready_families": [],
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
