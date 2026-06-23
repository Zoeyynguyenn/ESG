# Enterprise internal-doc — Cross-doc core capability benchmark

Artifact: `reports\enterprise_docs_crossdoc_core_capability_20260619-100639`

## Câu trả lời bắt buộc

{
  "1_core_capability_strength_by_area": {
    "alias_normalization_success_rate": 0.5,
    "cross_doc_equivalence_match_rate": 0.3333,
    "cross_role_extraction_alignment_rate": 0.0,
    "evidence_fusion_success_rate": 0.5,
    "conflict_classification_accuracy": 0.3333,
    "conflict_resolution_readiness_rate": 0.1667,
    "single_source_to_multi_source_promotion_rate": 1.0
  },
  "2_corpus_vs_system_failure_split": {
    "natural_corpus_limited_rate": 1.0,
    "natural_system_gap_rate": 0.0,
    "constructed_shows_system_capability": 0.5,
    "interpretation": "Natural fail chủ yếu do corpus_limited; constructed cases đo capability riêng"
  },
  "3_constructed_multi_source_fusion": {
    "evidence_fusion_success_rate": 0.5,
    "cross_role_extraction_alignment_rate": 0.0,
    "promotion_rate": 1.0
  },
  "4_conflict_handling_strength": {
    "strongest": "classification",
    "classification_accuracy": 0.3333,
    "resolution_readiness_rate": 0.1667,
    "promotion_rate": 1.0
  },
  "5_best_family_for_real_docs": "environment_ghg",
  "6_next_step_for_real_enterprise_docs": "Plug-in readiness: giữ capability benchmark làm regression gate; khi có tài liệu mới chỉ cần thêm natural cases — không rebuild pipeline; tiếp tục harden equivalence/fusion/conflict trên constructed suite"
}

## Capability metrics (constructed — proxy/heuristic)

{
  "alias_normalization_success_rate": 0.5,
  "cross_doc_equivalence_match_rate": 0.3333,
  "cross_role_extraction_alignment_rate": 0.0,
  "evidence_fusion_success_rate": 0.5,
  "conflict_classification_accuracy": 0.3333,
  "conflict_resolution_readiness_rate": 0.1667,
  "single_source_to_multi_source_promotion_rate": 1.0,
  "counts": {
    "alias": {
      "ok": 1,
      "total": 2
    },
    "equivalence": {
      "ok": 1,
      "total": 3
    },
    "extraction": {
      "ok": 0,
      "total": 6
    },
    "fusion": {
      "ok": 3,
      "total": 6
    },
    "classification": {
      "ok": 2,
      "total": 6
    },
    "resolution": {
      "ok": 1,
      "total": 6
    },
    "promotion": {
      "ok": 6,
      "total": 6
    }
  },
  "metric_notes": {
    "alias_normalization_success_rate": "constructed value_pair cases",
    "cross_doc_equivalence_match_rate": "constructed canonical/equiv cases",
    "cross_role_extraction_alignment_rate": "constructed multi-source extract per logical doc",
    "evidence_fusion_success_rate": "constructed multi_source_confirmed expectation",
    "conflict_classification_accuracy": "constructed expected_conflict_status match",
    "conflict_resolution_readiness_rate": "proxy: aggregation resolution_status resolved*",
    "single_source_to_multi_source_promotion_rate": "constructed promotion_ok heuristic"
  }
}
