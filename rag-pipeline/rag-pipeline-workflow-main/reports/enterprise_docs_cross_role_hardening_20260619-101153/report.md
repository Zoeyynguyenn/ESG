# Enterprise internal-doc — Cross-role extraction hardening

Artifact: `reports\enterprise_docs_cross_role_hardening_20260619-101153`

## Câu trả lời bắt buộc

{
  "1_cross_role_extraction_alignment_increased": {
    "before": 0.0,
    "after": 1.0,
    "delta": 1.0,
    "increased": true
  },
  "2_hardest_mismatch_type": "none",
  "3_fusion_fail_primary_cause": "extraction",
  "4_best_hardened_family": "governance",
  "5_promotion_ghost_remaining": {
    "promotion_rate": 0.8333,
    "fusion_rate": 0.8333,
    "still_ghost": false,
    "note": "promotion now requires fusion_ok for expected multi-source cases"
  },
  "6_next_step_for_real_docs": "Giữ constructed suite làm regression gate; tiếp tục harden mismatch còn lại; plug-in tài liệu thật bằng cách thêm natural cases — không rebuild pipeline"
}

## Capability metrics delta vs prior benchmark

{
  "alias_normalization_success_rate": {
    "before": 0.5,
    "after": 1.0,
    "delta": 0.5
  },
  "cross_doc_equivalence_match_rate": {
    "before": 0.3333,
    "after": 0.6667,
    "delta": 0.3334
  },
  "cross_role_extraction_alignment_rate": {
    "before": 0.0,
    "after": 1.0,
    "delta": 1.0
  },
  "evidence_fusion_success_rate": {
    "before": 0.5,
    "after": 0.8333,
    "delta": 0.3333
  },
  "conflict_classification_accuracy": {
    "before": 0.3333,
    "after": 0.8333,
    "delta": 0.5
  },
  "conflict_resolution_readiness_rate": {
    "before": 0.1667,
    "after": 1.0,
    "delta": 0.8333
  },
  "single_source_to_multi_source_promotion_rate": {
    "before": 1.0,
    "after": 0.8333,
    "delta": -0.1667
  }
}

## Current capability metrics

{
  "alias_normalization_success_rate": 1.0,
  "cross_doc_equivalence_match_rate": 0.6667,
  "cross_role_extraction_alignment_rate": 1.0,
  "evidence_fusion_success_rate": 0.8333,
  "conflict_classification_accuracy": 0.8333,
  "conflict_resolution_readiness_rate": 1.0,
  "single_source_to_multi_source_promotion_rate": 0.8333,
  "counts": {
    "alias": {
      "ok": 2,
      "total": 2
    },
    "equivalence": {
      "ok": 2,
      "total": 3
    },
    "extraction": {
      "ok": 6,
      "total": 6
    },
    "fusion": {
      "ok": 5,
      "total": 6
    },
    "classification": {
      "ok": 5,
      "total": 6
    },
    "resolution": {
      "ok": 6,
      "total": 6
    },
    "promotion": {
      "ok": 5,
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
