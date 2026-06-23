# Enterprise internal-doc — Holdout handoff enablement

Artifact: `reports\enterprise_docs_holdout_handoff_enablement_20260618-170917`

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
    "category": "narrative_confidence_zero",
    "description": "Narrative extract had value but confidence=0 blocked promotion",
    "status": "fixed",
    "fix": "confidence_policy.resolve_extraction_confidence"
  }
]

- alignment_gap_rate: **0.5926** (heuristic proxy)

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

## Pilot families

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
    "blocker_breakdown": {
      "handoff_blocked_state:coverage_gap": 3,
      "missing_predicted_value": 3,
      "evidence_bundle_insufficient": 3,
      "primary_doc_missing": 3,
      "confidence_below_min": 3
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
    "promoted_count": 4,
    "single_source_count": 6,
    "multi_source_count": 0,
    "handoff_candidate_count": 6,
    "still_extraction_ready": 0,
    "not_handoff_ready": 8,
    "promotion_rate": 0.2857,
    "blocker_breakdown": {
      "handoff_blocked_state:coverage_gap": 6,
      "missing_predicted_value": 8,
      "evidence_bundle_insufficient": 8,
      "primary_doc_missing": 6,
      "confidence_below_min": 8,
      "qualitative_kind": 2
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
    "promoted_count": 1,
    "single_source_count": 5,
    "multi_source_count": 0,
    "handoff_candidate_count": 5,
    "still_extraction_ready": 0,
    "not_handoff_ready": 13,
    "promotion_rate": 0.0556,
    "blocker_breakdown": {
      "qualitative_kind": 4,
      "handoff_blocked_state:coverage_gap": 9,
      "missing_predicted_value": 13,
      "evidence_bundle_insufficient": 13,
      "primary_doc_missing": 9,
      "confidence_below_min": 13
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
  "ready_for_limited_langgraph_handoff_preparation": false,
  "not_ready_for_synthesis": true,
  "not_ready_for_langgraph_trial": true,
  "holdout_promoted_families": [],
  "holdout_promoted_by_family": {},
  "holdout_promotion_rate": 0.0,
  "holdout_promotion_delta_vs_prior": 0.0,
  "holdout_promoted_family_count": 0,
  "demo_promoted_count": 6,
  "gaps_before_trial": [
    "holdout_promotion_zero",
    "musinsa_environment_corpus_gap",
    "confidence_policy_calibration",
    "review_owner_rule_enforcement"
  ]
}

## Promotion delta vs prior

{
  "demo_promoted_delta": 0,
  "hanssem_promoted_delta": 0,
  "musinsa_promoted_delta": 0,
  "holdout_readiness_after_before": {
    "hanssem": {
      "before": {
        "coverage_gap": 16
      },
      "after": {
        "coverage_gap": 16
      }
    },
    "musinsa": {
      "before": {
        "coverage_gap": 11
      },
      "after": {
        "coverage_gap": 11
      }
    }
  }
}
