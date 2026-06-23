# Enterprise internal-doc — Operational packaging

Artifact: `reports/enterprise_docs_operational_packaging_20260619-104141`

**Lane status:** `done_until_real_data`
**Kit complete:** `True`

## Câu trả lời bắt buộc

{
  "1_bootstrap_kit_contents": {
    "answer": "Runbook SOP, bootstrap guide, 3 templates (probes/natural cases/review), bootstrap script, onboarding gate script, schema, company registry reference, 6 checklist sections, 4 decision rules.",
    "files": [
      "docs/ENTERPRISE_INTERNAL_DOC_OPERATIONAL_RUNBOOK.md",
      "docs/ENTERPRISE_INTERNAL_DOC_NEW_COMPANY_BOOTSTRAP.md",
      "docs/ENTERPRISE_INTERNAL_DOC_NATURAL_CASE_ONBOARDING.md",
      "data/enterprise_docs/natural_capability_case_schema.json",
      "data/enterprise_docs/templates/holdout_probes_template.jsonl",
      "data/enterprise_docs/templates/natural_capability_cases_template.jsonl",
      "data/enterprise_docs/templates/onboarding_review_template.md",
      "scripts/bootstrap_enterprise_company.py",
      "scripts/run_enterprise_docs_natural_onboarding_gate.py",
      "data/enterprise_docs/company_doc_registry.json",
      "data/enterprise_docs/crossdoc_capability_cases.jsonl"
    ],
    "checklist_section_ids": [
      "data_intake",
      "ingest",
      "logical_doc_mapping",
      "probes",
      "gate",
      "review"
    ]
  },
  "2_shortest_onboarding_flow": {
    "answer": "ingest → map logical docs → create probes → build natural cases → run gate → classify → decide",
    "steps": [
      {
        "step": 1,
        "name": "ingest",
        "command_hint": "ingest + corpus_units.jsonl"
      },
      {
        "step": 2,
        "name": "map_logical_docs",
        "command_hint": "company_doc_registry.json"
      },
      {
        "step": 3,
        "name": "create_probes",
        "command_hint": "holdout_probes_{company_id}.jsonl"
      },
      {
        "step": 4,
        "name": "build_natural_cases",
        "command_hint": "natural_case_from_probe / crossdoc_capability_cases.jsonl"
      },
      {
        "step": 5,
        "name": "run_onboarding_gate",
        "command_hint": "python scripts/run_enterprise_docs_natural_onboarding_gate.py"
      },
      {
        "step": 6,
        "name": "classify_failure",
        "command_hint": "corpus_limited vs system_gap in summary.json"
      },
      {
        "step": 7,
        "name": "decide_next_action",
        "command_hint": "onboarding_review template + DECISION_RULES"
      }
    ]
  },
  "3_files_before_gate": {
    "answer": "corpus_units.jsonl + company_doc_registry entry; holdout_probes_{company_id}.jsonl; PROBE_PATHS registration; refreshed crossdoc_capability_cases.jsonl with natural rows.",
    "required_artifacts": [
      "data/enterprise_docs/{company_id}/corpus_units*.jsonl",
      "data/enterprise_docs/company_doc_registry.json (company block)",
      "data/enterprise_docs/holdout_probes_{company_id}.jsonl",
      "data/enterprise_docs/crossdoc_capability_cases.jsonl"
    ]
  },
  "4_corpus_limited_vs_system_gap": {
    "corpus_limited": {
      "signal": "corpus_limited",
      "meaning": "Corpus thiếu metric ở >=2 logical docs hoặc không tìm thấy candidate",
      "action": "Bổ sung tài liệu / logical-doc map; **không** mở workstream hardening pipeline lõi",
      "do_not": [
        "rebuild parser",
        "rebuild retrieval",
        "tune constructed cases"
      ]
    },
    "system_gap": {
      "signal": "system_gap",
      "meaning": "Corpus đủ nhưng extraction/equivalence/fusion fail trên natural case",
      "action": "Mở rộng `metric_equivalence_registry` / cross_role patterns đúng family_id",
      "do_not": [
        "chase demo score",
        "inflate multi_source metric"
      ]
    },
    "how_to_read": "Xem natural_metrics.by_failure_mode trong gate summary: corpus_limited_* = thiếu corpus/overlap; system_gap = capability fail dù có candidate."
  },
  "5_done_until_real_data": {
    "answer": "Có — constructed gate là regression chuẩn; natural onboarding path sẵn sàng; bootstrap kit đủ để team onboard mà không suy nghĩ lại flow.",
    "lane_status": "done_until_real_data",
    "all_kit_files_present": true
  },
  "6_next_step_if_no_real_data_yet": {
    "answer": "Giữ constructed regression làm CI; không mở LangGraph/synthesis; chờ dữ liệu doanh nghiệp thật rồi chạy bootstrap_enterprise_company.py + gate; hoặc dry-run trên hanssem/musinsa để team làm quen SOP.",
    "do_not": [
      "harden core pipeline",
      "chase natural demo score",
      "source acquisition as main workstream"
    ]
  }
}

## Bootstrap kit files

[
  {
    "key": "runbook",
    "path": "docs/ENTERPRISE_INTERNAL_DOC_OPERATIONAL_RUNBOOK.md",
    "exists": true,
    "size_bytes": 5050
  },
  {
    "key": "bootstrap_guide",
    "path": "docs/ENTERPRISE_INTERNAL_DOC_NEW_COMPANY_BOOTSTRAP.md",
    "exists": true,
    "size_bytes": 4165
  },
  {
    "key": "onboarding_doc",
    "path": "docs/ENTERPRISE_INTERNAL_DOC_NATURAL_CASE_ONBOARDING.md",
    "exists": true,
    "size_bytes": 3691
  },
  {
    "key": "schema",
    "path": "data/enterprise_docs/natural_capability_case_schema.json",
    "exists": true,
    "size_bytes": 4746
  },
  {
    "key": "probe_template",
    "path": "data/enterprise_docs/templates/holdout_probes_template.jsonl",
    "exists": true,
    "size_bytes": 993
  },
  {
    "key": "natural_case_template",
    "path": "data/enterprise_docs/templates/natural_capability_cases_template.jsonl",
    "exists": true,
    "size_bytes": 1041
  },
  {
    "key": "review_template",
    "path": "data/enterprise_docs/templates/onboarding_review_template.md",
    "exists": true,
    "size_bytes": 1085
  },
  {
    "key": "bootstrap_script",
    "path": "scripts/bootstrap_enterprise_company.py",
    "exists": true,
    "size_bytes": 6901
  },
  {
    "key": "onboarding_gate_script",
    "path": "scripts/run_enterprise_docs_natural_onboarding_gate.py",
    "exists": true,
    "size_bytes": 6261
  },
  {
    "key": "company_registry",
    "path": "data/enterprise_docs/company_doc_registry.json",
    "exists": true,
    "size_bytes": 9177
  },
  {
    "key": "capability_cases",
    "path": "data/enterprise_docs/crossdoc_capability_cases.jsonl",
    "exists": true,
    "size_bytes": 19102
  }
]

## Constraints

{
  "no_langgraph_runtime": true,
  "no_synthesis": true,
  "no_core_pipeline_rebuild": true,
  "no_demo_score_tuning": true
}
