# Enterprise internal-doc — Holdout handoff enablement

Artifact: `reports\enterprise_docs_holdout_handoff_enablement_20260618-171016`

## Routing alignment

[
  {
    "category": "path_hint_vs_corpus_document_id",
    "description": "Holdout logical path_hint did not match corpus IDs (Company_Evidence_*)",
    "status": "fixed",
    "fix": "corpus_match_tokens in company_doc_registry v1.3.0"
  },
  {
    "category": "multi_primary_cross_doc_on_holdout",
    "description": "Multi-domain routing triggered cross_document_answer on narrative SR corpus",
    "status": "fixed",
    "fix": "holdout_routing.force_single_doc_quant + max_primary_docs=1"
  },
  {
    "category": "supporting_doc_unmapped_coverage_gap",
    "description": "Unmapped supporting logical docs forced coverage_gap",
    "status": "fixed",
    "fix": "diagnostics require_primary_logical_map_only for holdout"
  },
  {
    "category": "build_index_company_id_not_passed_to_logical_map",
    "description": "build_index_from_units used demo_company for logical_to_corpus_map on all holdout runs",
    "status": "fixed",
    "fix": "cross_doc_retriever.build_logical_to_corpus_map(..., company_id=company_id)"
  }
]

- alignment_gap_rate: **0.1481** (heuristic proxy)

## Confidence policy

[
  {
    "id": "narrative_max_row_and_narrative_conf",
    "applies_when": "narrative_metric_parse_used",
    "resolution": "max(extraction_confidence, narrative_confidence), then narrative_floor_min"
  },
  {
    "id": "holdout_sustainability_narrative_floor",
    "applies_when": "holdout_company AND narrative AND source_type in sustainability/governance/dart",
    "resolution": "floor >= 0.3"
  },
  {
    "id": "table_strong",
    "applies_when": "NOT narrative AND extraction_confidence >= 0.85",
    "resolution": "table_extraction_strong"
  }
]

## Results by company

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
    "promoted_count": 6,
    "handoff_candidate_count": 6,
    "readiness_before": {
      "not_ready_for_synthesis": 8,
      "extraction_ready": 6,
      "retrieval_ready": 2
    },
    "readiness_after": {
      "not_ready_for_synthesis": 8,
      "single_source_sufficient": 6,
      "retrieval_ready": 2
    },
    "promotion_rate": 0.375
  },
  "musinsa": {
    "case_count": 11,
    "promoted_count": 4,
    "handoff_candidate_count": 4,
    "readiness_before": {
      "not_ready_for_synthesis": 5,
      "extraction_ready": 4,
      "retrieval_ready": 2
    },
    "readiness_after": {
      "not_ready_for_synthesis": 5,
      "single_source_sufficient": 4,
      "retrieval_ready": 2
    },
    "promotion_rate": 0.3636
  }
}

## Pilot families

{
  "employee_headcount": {
    "case_count": 4,
    "quantitative_count": 4,
    "promoted_count": 2,
    "single_source_count": 2,
    "multi_source_count": 0,
    "handoff_candidate_count": 2,
    "still_extraction_ready": 0,
    "not_handoff_ready": 2,
    "promotion_rate": 0.5,
    "blocker_breakdown": {
      "missing_predicted_value": 2,
      "evidence_bundle_insufficient": 2,
      "confidence_below_min": 2
    },
    "companies": [
      "demo_company",
      "hanssem",
      "musinsa"
    ]
  },
  "environment_ghg": {
    "case_count": 14,
    "quantitative_count": 12,
    "promoted_count": 7,
    "single_source_count": 9,
    "multi_source_count": 0,
    "handoff_candidate_count": 9,
    "still_extraction_ready": 0,
    "not_handoff_ready": 5,
    "promotion_rate": 0.5,
    "blocker_breakdown": {
      "qualitative_kind": 2,
      "handoff_blocked_state:not_ready_for_synthesis": 2,
      "missing_predicted_value": 5,
      "evidence_bundle_insufficient": 5,
      "confidence_below_min": 5
    },
    "companies": [
      "demo_company",
      "hanssem",
      "musinsa"
    ]
  },
  "governance": {
    "case_count": 18,
    "quantitative_count": 14,
    "promoted_count": 5,
    "single_source_count": 9,
    "multi_source_count": 0,
    "handoff_candidate_count": 9,
    "still_extraction_ready": 0,
    "not_handoff_ready": 9,
    "promotion_rate": 0.2778,
    "blocker_breakdown": {
      "qualitative_kind": 4,
      "handoff_blocked_state:not_ready_for_synthesis": 4,
      "missing_predicted_value": 9,
      "evidence_bundle_insufficient": 9,
      "confidence_below_min": 9
    },
    "companies": [
      "demo_company",
      "hanssem",
      "musinsa"
    ]
  }
}

## System decision

{
  "phase": "holdout_handoff_enablement",
  "ready_for_limited_langgraph_handoff": false,
  "ready_for_limited_langgraph_handoff_preparation": true,
  "not_ready_for_synthesis": true,
  "not_ready_for_langgraph_trial": true,
  "holdout_promoted_families": [
    "employee_headcount",
    "environment_ghg",
    "governance"
  ],
  "holdout_promoted_by_family": {
    "environment_ghg": 3,
    "governance": 4,
    "employee_headcount": 1
  },
  "holdout_promotion_rate": 0.3704,
  "holdout_promotion_delta_vs_prior": 0.3704,
  "holdout_promoted_family_count": 3,
  "demo_promoted_count": 6,
  "gaps_before_trial": [
    "confidence_policy_calibration",
    "review_owner_rule_enforcement"
  ]
}

## Promotion delta vs prior

{
  "demo_promoted_delta": 0,
  "hanssem_promoted_delta": 6,
  "musinsa_promoted_delta": 4,
  "holdout_readiness_after_before": {
    "hanssem": {
      "before": {
        "coverage_gap": 16
      },
      "after": {
        "not_ready_for_synthesis": 8,
        "single_source_sufficient": 6,
        "retrieval_ready": 2
      }
    },
    "musinsa": {
      "before": {
        "coverage_gap": 11
      },
      "after": {
        "not_ready_for_synthesis": 5,
        "single_source_sufficient": 4,
        "retrieval_ready": 2
      }
    }
  }
}
