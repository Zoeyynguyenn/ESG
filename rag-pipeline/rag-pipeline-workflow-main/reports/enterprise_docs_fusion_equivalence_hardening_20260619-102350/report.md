# Enterprise internal-doc — Fusion equivalence hardening

Artifact: `reports\enterprise_docs_fusion_equivalence_hardening_20260619-102350`

## Câu trả lời bắt buộc

{
  "1_cross_doc_equivalence_increased": {
    "before": 0.6667,
    "after": 1.0,
    "delta": 0.3333,
    "increased": true
  },
  "2_evidence_fusion_increased_and_remaining_failures": {
    "before": 0.8333,
    "after": 1.0,
    "delta": 0.1667,
    "remaining_failure_stages": {}
  },
  "3_narrative_table_fusion_status": {
    "narrative_vs_table_cases": [
      {
        "case_id": "CONSTRUCT-FUSION-NARRATIVE-TABLE-SCALED",
        "family_id": "environment_ghg",
        "item": "총 온실가스",
        "extract_alignment_ok": true,
        "equivalence_collapse_ok": true,
        "fusion_ok": true,
        "multi_source_confirmed": true,
        "confirming_logical_docs": [
          "doc_evidence_csv",
          "doc_sr_narrative"
        ],
        "resolved_value": "12500",
        "failure_stage": "none"
      },
      {
        "case_id": "CONSTRUCT-NARRATIVE-VS-TABLE",
        "family_id": "environment_ghg",
        "item": "총 온실가스",
        "extract_alignment_ok": true,
        "equivalence_collapse_ok": true,
        "fusion_ok": true,
        "multi_source_confirmed": true,
        "confirming_logical_docs": [
          "doc_evidence_csv",
          "doc_sr_narrative"
        ],
        "resolved_value": "12,500",
        "failure_stage": "none"
      }
    ]
  },
  "4_hardest_numeric_equivalence_type": "comma_decimal_format",
  "5_promotion_integrity": {
    "promotion_rate": 1.0,
    "fusion_rate": 1.0,
    "ghost_pass_count": 0,
    "bams_fusion": true
  },
  "6_next_step_for_real_docs": "Giữ constructed regression gate; plug-in tài liệu thật bằng natural cases; tiếp tục mở rộng scaled/unit equivalence khi gặp pattern mới"
}

## Capability metrics delta

{
  "alias_normalization_success_rate": {
    "before": 1.0,
    "after": 1.0,
    "delta": 0.0
  },
  "cross_doc_equivalence_match_rate": {
    "before": 0.6667,
    "after": 1.0,
    "delta": 0.3333
  },
  "cross_role_extraction_alignment_rate": {
    "before": 1.0,
    "after": 1.0,
    "delta": 0.0
  },
  "evidence_fusion_success_rate": {
    "before": 0.8333,
    "after": 1.0,
    "delta": 0.1667
  },
  "conflict_classification_accuracy": {
    "before": 0.8333,
    "after": 1.0,
    "delta": 0.1667
  },
  "conflict_resolution_readiness_rate": {
    "before": 1.0,
    "after": 1.0,
    "delta": 0.0
  },
  "single_source_to_multi_source_promotion_rate": {
    "before": 0.8333,
    "after": 1.0,
    "delta": 0.1667
  }
}
