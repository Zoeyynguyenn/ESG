# Enterprise internal-doc — Limited LangGraph handoff preparation

Artifact: `reports\enterprise_docs_langgraph_handoff_prep_20260618-172138`

> **Preparation gate only** — không runtime trial, không synthesis, không integration thật.

## Family handoff contract (3 pilot families)

### `employee_headcount`

- question_type: `quantitative_headcount`
- min_confidence_table: **0.85**
- min_confidence_narrative: **0.25**
- blockers: ['qualitative_kind', 'coverage_gap', 'wrong_row_risk', 'missing_predicted_value']

### `environment_ghg`

- question_type: `quantitative_climate_metric`
- min_confidence_table: **0.85**
- min_confidence_narrative: **0.25**
- blockers: ['qualitative_kind', 'coverage_gap', 'unresolved_conflict']

### `governance`

- question_type: `quantitative_governance_narrative`
- min_confidence_table: **0.85**
- min_confidence_narrative: **0.25**
- blockers: ['qualitative_kind', 'coverage_gap', 'wrong_row_risk']

## Payload schema

Nhóm field: `identity`, `readiness`, `answer`, `evidence`, `review_control`.
Chi tiết: `handoff_payload_schema.json`.

## Review owner rules

[
  {
    "id": "qualitative_blocked",
    "condition": "kind == qualitative",
    "owner": null,
    "prep_status": "handoff_blocked",
    "reason": "qualitative_requires_synthesis_not_extractive_handoff"
  },
  {
    "id": "not_ready_for_synthesis",
    "condition": "readiness_state == not_ready_for_synthesis",
    "owner": null,
    "prep_status": "handoff_blocked",
    "reason": "synthesis_blocker"
  },
  {
    "id": "coverage_gap",
    "condition": "readiness_state == coverage_gap OR blocker coverage",
    "owner": "Dataset",
    "prep_status": "needs_manual_review_before_handoff",
    "reason": "corpus_or_logical_doc_gap"
  },
  {
    "id": "needs_sme_review",
    "condition": "readiness_state == needs_sme_review OR wrong_row_risk",
    "owner": "SME",
    "prep_status": "needs_manual_review_before_handoff",
    "reason": "sme_validation_required"
  },
  {
    "id": "confidence_below_family_min",
    "condition": "promoted AND confidence < family_min AND NOT wrong_row_risk",
    "owner": "RAG",
    "prep_status": "needs_manual_review_before_handoff",
    "reason": "confidence_policy_calibration"
  },
  {
    "id": "retrieval_or_extraction_not_promoted",
    "condition": "readiness_state in (retrieval_ready, extraction_ready) AND NOT promoted",
    "owner": "RAG",
    "prep_status": "handoff_blocked",
    "reason": "extraction_or_retrieval_incomplete"
  },
  {
    "id": "promoted_adequate_confidence",
    "condition": "promoted AND single_source_sufficient AND confidence >= family_min",
    "owner": "None",
    "prep_status": "handoff_allowed_for_preparation",
    "reason": "family_contract_met"
  },
  {
    "id": "promoted_multi_source",
    "condition": "promoted AND multi_source_sufficient",
    "owner": "None",
    "prep_status": "handoff_allowed_for_preparation",
    "reason": "multi_source_contract_met"
  },
  {
    "id": "default_blocked",
    "condition": "fallback",
    "owner": "RAG",
    "prep_status": "handoff_blocked",
    "reason": "prep_conditions_not_met"
  }
]

## Results by company

{
  "demo_company": {
    "total_cases": 18,
    "promoted_count": 6,
    "handoff_allowed_for_preparation": 6,
    "blocked_count": 12,
    "review_required_count": 0,
    "prep_status_distribution": {
      "handoff_allowed_for_preparation": 6,
      "handoff_blocked": 12
    },
    "review_owner_distribution": {
      "None": 6,
      "RAG": 12
    }
  },
  "hanssem": {
    "total_cases": 16,
    "promoted_count": 6,
    "handoff_allowed_for_preparation": 6,
    "blocked_count": 10,
    "review_required_count": 0,
    "prep_status_distribution": {
      "handoff_blocked": 10,
      "handoff_allowed_for_preparation": 6
    },
    "review_owner_distribution": {
      "unset": 8,
      "None": 6,
      "RAG": 2
    }
  },
  "musinsa": {
    "total_cases": 11,
    "promoted_count": 4,
    "handoff_allowed_for_preparation": 4,
    "blocked_count": 7,
    "review_required_count": 0,
    "prep_status_distribution": {
      "handoff_blocked": 7,
      "handoff_allowed_for_preparation": 4
    },
    "review_owner_distribution": {
      "unset": 5,
      "None": 4,
      "RAG": 2
    }
  }
}

## Results by family

{
  "employee_headcount": {
    "preparation_ready_count": 2,
    "blocked_count": 2,
    "review_required_count": 0,
    "promoted_count": 2,
    "dominant_blocker": "missing_predicted_value",
    "dominant_review_owner": "RAG",
    "blocker_breakdown": {
      "missing_predicted_value": 2,
      "evidence_bundle_insufficient": 2,
      "confidence_below_min": 2
    },
    "review_owner_breakdown": {
      "RAG": 2,
      "None": 2
    }
  },
  "environment_ghg": {
    "preparation_ready_count": 7,
    "blocked_count": 7,
    "review_required_count": 0,
    "promoted_count": 7,
    "dominant_blocker": "missing_predicted_value",
    "dominant_review_owner": "None",
    "blocker_breakdown": {
      "qualitative_kind": 2,
      "handoff_blocked_state:not_ready_for_synthesis": 2,
      "missing_predicted_value": 5,
      "evidence_bundle_insufficient": 5,
      "confidence_below_min": 5
    },
    "review_owner_breakdown": {
      "None": 7,
      "unset": 2,
      "RAG": 5
    }
  },
  "governance": {
    "preparation_ready_count": 5,
    "blocked_count": 13,
    "review_required_count": 0,
    "promoted_count": 5,
    "dominant_blocker": "missing_predicted_value",
    "dominant_review_owner": "RAG",
    "blocker_breakdown": {
      "qualitative_kind": 4,
      "handoff_blocked_state:not_ready_for_synthesis": 4,
      "missing_predicted_value": 9,
      "evidence_bundle_insufficient": 9,
      "confidence_below_min": 9
    },
    "review_owner_breakdown": {
      "unset": 4,
      "None": 5,
      "RAG": 9
    }
  }
}

## Blocker categories

{
  "synthesis_blocker": 26,
  "package_blocker": 46,
  "confidence_blocker": 23
}

## System decision

{
  "phase": "langgraph_handoff_preparation",
  "gate_type": "preparation_gate_not_integration_gate_not_runtime_trial",
  "ready_for_limited_langgraph_handoff_preparation": true,
  "ready_for_limited_langgraph_handoff_trial": false,
  "not_ready_for_synthesis": true,
  "holdout_prep_allowed_count": 10,
  "holdout_prep_allowed_families": [
    "employee",
    "employee_headcount",
    "environment_ghg",
    "financial",
    "governance"
  ],
  "total_prep_allowed": 16,
  "total_blocked": 29,
  "total_review_required": 0,
  "dominant_blocker_category": "package_blocker",
  "recommend_trial": false,
  "trial_blockers": [
    "preparation_contract_signoff_pending",
    "confidence_policy_calibration",
    "holdout_review_owner_clearance",
    "no_runtime_integration_yet"
  ],
  "trial_readiness_note": "Prep payload contract sufficient for limited trial design review; runtime trial still blocked until explicit sign-off"
}

## Prior enablement reference

{
  "holdout_promotion_rate": 0.3704,
  "ready_for_limited_langgraph_handoff_preparation": true
}
