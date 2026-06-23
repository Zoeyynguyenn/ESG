# Enterprise internal-doc — Structured ESG output evaluation

Artifact: `reports\enterprise_docs_structured_esg_20260618-174141`

> **Trọng tâm**: `document → structured ESG data` — không LangGraph handoff/trial.

## Format transformation audit

### Priority

{
  "strengthen_next": [
    "html",
    "xml",
    "pdf"
  ],
  "maintain": [
    "markdown",
    "csv",
    "json",
    "jsonl"
  ],
  "planned_not_in_corpus": [
    "word",
    "ppt",
    "image_ocr"
  ]
}

### By format (readiness)

- **markdown**: docs=32, tier=strong, score=0.85, extraction=strong
- **csv**: docs=1, tier=adequate, score=0.63, extraction=adequate
- **json**: docs=24, tier=adequate, score=0.58, extraction=adequate
- **jsonl**: docs=2, tier=adequate, score=0.5, extraction=weak
- **html**: docs=140, tier=weak, score=0.4, extraction=weak
- **xml**: docs=98, tier=weak, score=0.37, extraction=weak
- **pdf**: docs=26, tier=weak, score=0.32, extraction=weak
- **image_ocr**: docs=0, tier=weak, score=0.0, extraction=not_implemented
- **ppt**: docs=0, tier=weak, score=0.0, extraction=not_implemented
- **word**: docs=0, tier=weak, score=0.0, extraction=not_implemented

## ESG schema

Chi tiết: `esg_schema.json` / `data/enterprise_docs/esg_target_schema.json`

## Metrics by company

{
  "demo_company": {
    "case_count": 18,
    "structured_record_coverage": 0.6667,
    "esg_field_mapping_rate": 1.0,
    "single_source_sufficient_rate": 0.6667,
    "multi_source_confirmed_rate": 0.0,
    "conflict_rate": 0.0,
    "not_disclosed_detection_rate": 0.0,
    "review_required_rate": 0.7222,
    "metric_absent_rate": 0.3333,
    "conflict_status_distribution": {
      "single_source_sufficient": 12,
      "metric_absent": 6
    },
    "readiness_distribution": {
      "extraction_ready": 3,
      "retrieval_ready": 9,
      "single_source_sufficient": 6
    },
    "family_distribution": {
      "employee_headcount": 1,
      "environment_ghg": 8,
      "governance": 9
    }
  },
  "hanssem": {
    "case_count": 11,
    "structured_record_coverage": 0.5455,
    "esg_field_mapping_rate": 1.0,
    "single_source_sufficient_rate": 0.5455,
    "multi_source_confirmed_rate": 0.0,
    "conflict_rate": 0.0,
    "not_disclosed_detection_rate": 0.0,
    "review_required_rate": 0.1818,
    "metric_absent_rate": 0.4545,
    "conflict_status_distribution": {
      "metric_absent": 5,
      "single_source_sufficient": 6
    },
    "readiness_distribution": {
      "not_ready_for_synthesis": 3,
      "multi_source_sufficient": 6,
      "retrieval_ready": 2
    },
    "family_distribution": {
      "governance": 6,
      "environment_ghg": 4,
      "employee_headcount": 1
    }
  },
  "musinsa": {
    "case_count": 7,
    "structured_record_coverage": 0.2857,
    "esg_field_mapping_rate": 1.0,
    "single_source_sufficient_rate": 0.2857,
    "multi_source_confirmed_rate": 0.0,
    "conflict_rate": 0.0,
    "not_disclosed_detection_rate": 0.0,
    "review_required_rate": 0.2857,
    "metric_absent_rate": 0.7143,
    "conflict_status_distribution": {
      "metric_absent": 5,
      "single_source_sufficient": 2
    },
    "readiness_distribution": {
      "not_ready_for_synthesis": 3,
      "retrieval_ready": 2,
      "multi_source_sufficient": 2
    },
    "family_distribution": {
      "governance": 3,
      "environment_ghg": 2,
      "employee_headcount": 2
    }
  }
}

## Metrics by family

{
  "employee_headcount": {
    "case_count": 4,
    "structured_record_coverage": 0.5,
    "esg_field_mapping_rate": 1.0,
    "single_source_sufficient_rate": 0.5,
    "multi_source_confirmed_rate": 0.0,
    "conflict_rate": 0.0,
    "not_disclosed_detection_rate": 0.0,
    "review_required_rate": 0.75,
    "metric_absent_rate": 0.5,
    "conflict_status_distribution": {
      "metric_absent": 2,
      "single_source_sufficient": 2
    },
    "readiness_distribution": {
      "retrieval_ready": 2,
      "multi_source_sufficient": 1,
      "extraction_ready": 1
    },
    "family_distribution": {
      "employee_headcount": 4
    }
  },
  "environment_ghg": {
    "case_count": 14,
    "structured_record_coverage": 0.7143,
    "esg_field_mapping_rate": 1.0,
    "single_source_sufficient_rate": 0.7143,
    "multi_source_confirmed_rate": 0.0,
    "conflict_rate": 0.0,
    "not_disclosed_detection_rate": 0.0,
    "review_required_rate": 0.5,
    "metric_absent_rate": 0.2857,
    "conflict_status_distribution": {
      "single_source_sufficient": 10,
      "metric_absent": 4
    },
    "readiness_distribution": {
      "multi_source_sufficient": 4,
      "not_ready_for_synthesis": 2,
      "retrieval_ready": 4,
      "extraction_ready": 2,
      "single_source_sufficient": 2
    },
    "family_distribution": {
      "environment_ghg": 14
    }
  },
  "governance": {
    "case_count": 18,
    "structured_record_coverage": 0.4444,
    "esg_field_mapping_rate": 1.0,
    "single_source_sufficient_rate": 0.4444,
    "multi_source_confirmed_rate": 0.0,
    "conflict_rate": 0.0,
    "not_disclosed_detection_rate": 0.0,
    "review_required_rate": 0.3889,
    "metric_absent_rate": 0.5556,
    "conflict_status_distribution": {
      "metric_absent": 10,
      "single_source_sufficient": 8
    },
    "readiness_distribution": {
      "not_ready_for_synthesis": 4,
      "retrieval_ready": 7,
      "multi_source_sufficient": 3,
      "single_source_sufficient": 4
    },
    "family_distribution": {
      "governance": 18
    }
  }
}

## Cross-doc conflict matrix

Cases: **7** — chi tiết `cross_doc_conflict_matrix.json`

## System focus

{
  "phase": "structured_esg_output",
  "langgraph_handoff_priority": false,
  "primary_goals": [
    "multi_format_transformation",
    "esg_schema_mapping",
    "cross_document_conflict_handling"
  ]
}
