# Enterprise Internal-Doc — Abstraction + Holdout Robustness

Generated: 20260618-155302

## 1. Registry migration audit

- Already registry-driven: **8**
- Partially registry-driven: **5**
- Still code-driven: **1**

### Pilot hotspots

- `doc_mapping.py`
- `doc_router.py`
- `structured_extractor.py`
- `evidence_aggregator.py`
- `cross_doc_retriever.py`
- `parsers.py / ingest.py`

## 2. Holdout robustness round

| company | probes | parser | retrieval | extraction | aggregation |
|---|---:|---:|---:|---:|---:|
| `hanssem` | 12 | 1.0 | 0.9167 | 0.25 | 0.25 |
| `musinsa` | 8 | 1.0 | 1.0 | 0.375 | 0.375 |

## 3. Family generalization

- **employee**: retrieval=1.0, extraction=0.3333, reusability=retrieval_only, dominant_readiness=`not_ready_for_synthesis`
- **employee_headcount**: retrieval=1.0, extraction=1.0, reusability=reusable_holdout, dominant_readiness=`extraction_ready`
- **environment_ghg**: retrieval=1.0, extraction=0.6667, reusability=reusable_holdout, dominant_readiness=`extraction_ready`
- **financial**: retrieval=1.0, extraction=1.0, reusability=pilot_only, dominant_readiness=`extraction_ready`
- **governance**: retrieval=0.8333, extraction=0.1667, reusability=retrieval_only, dominant_readiness=`not_ready_for_synthesis`
- **other**: retrieval=1.0, extraction=0.0, reusability=retrieval_only, dominant_readiness=`not_ready_for_synthesis`

Strongest: **employee_headcount** | Weakest: **governance**

## 4. System decision gate

- `ready_for_holdout_expansion`: **[{'company_id': 'hanssem', 'probe_id': 'HOLDOUT-001', 'document_type': 'sustainability_report', 'family_guess': 'governance_narrative', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': False, 'aggregation_feasible': False, 'readiness_state': 'not_ready_for_synthesis', 'fail_stage': 'synthesis_gap', 'kind': 'qualitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'hanssem', 'probe_id': 'HOLDOUT-002', 'document_type': 'sustainability_report', 'family_guess': 'climate_narrative', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': True, 'aggregation_feasible': True, 'readiness_state': 'extraction_ready', 'fail_stage': 'ready', 'kind': 'quantitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'hanssem', 'probe_id': 'HOLDOUT-003', 'document_type': 'sustainability_report', 'family_guess': 'governance_numeric_narrative', 'parser_ok': True, 'retrieval_feasible': False, 'extraction_feasible': False, 'aggregation_feasible': False, 'readiness_state': 'coverage_gap', 'fail_stage': 'retrieval_gap', 'kind': 'quantitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'hanssem', 'probe_id': 'HOLDOUT-004', 'document_type': 'sustainability_report', 'family_guess': 'esg_rating_narrative', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': True, 'aggregation_feasible': True, 'readiness_state': 'extraction_ready', 'fail_stage': 'ready', 'kind': 'quantitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'hanssem', 'probe_id': 'HOLDOUT-005', 'document_type': 'sustainability_report', 'family_guess': 'employee_safety', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': False, 'aggregation_feasible': False, 'readiness_state': 'not_ready_for_synthesis', 'fail_stage': 'synthesis_gap', 'kind': 'qualitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'hanssem', 'probe_id': 'HOLDOUT-006', 'document_type': 'sustainability_report', 'family_guess': 'supply_chain', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': False, 'aggregation_feasible': False, 'readiness_state': 'not_ready_for_synthesis', 'fail_stage': 'synthesis_gap', 'kind': 'qualitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'hanssem', 'probe_id': 'HOLDOUT-007', 'document_type': 'sustainability_report', 'family_guess': 'scope_expansion', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': True, 'aggregation_feasible': True, 'readiness_state': 'extraction_ready', 'fail_stage': 'ready', 'kind': 'quantitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'hanssem', 'probe_id': 'HOLDOUT-008', 'document_type': 'sustainability_report', 'family_guess': 'report_meta', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': False, 'aggregation_feasible': False, 'readiness_state': 'not_ready_for_synthesis', 'fail_stage': 'synthesis_gap', 'kind': 'qualitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'hanssem', 'probe_id': 'HOLDOUT-009', 'document_type': 'sustainability_report', 'family_guess': 'environment_cdp', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': False, 'aggregation_feasible': False, 'readiness_state': 'not_ready_for_synthesis', 'fail_stage': 'synthesis_gap', 'kind': 'qualitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'hanssem', 'probe_id': 'HOLDOUT-010', 'document_type': 'sustainability_report', 'family_guess': 'governance_materiality', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': False, 'aggregation_feasible': False, 'readiness_state': 'not_ready_for_synthesis', 'fail_stage': 'synthesis_gap', 'kind': 'qualitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'hanssem', 'probe_id': 'HOLDOUT-011', 'document_type': 'sustainability_report', 'family_guess': 'employee_hr', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': False, 'aggregation_feasible': False, 'readiness_state': 'not_ready_for_synthesis', 'fail_stage': 'synthesis_gap', 'kind': 'qualitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'hanssem', 'probe_id': 'HOLDOUT-012', 'document_type': 'sustainability_report', 'family_guess': 'narrative_esg', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': False, 'aggregation_feasible': False, 'readiness_state': 'not_ready_for_synthesis', 'fail_stage': 'synthesis_gap', 'kind': 'qualitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'musinsa', 'probe_id': 'HOLDOUT-M001', 'document_type': 'other', 'family_guess': 'impact_report_meta', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': False, 'aggregation_feasible': False, 'readiness_state': 'not_ready_for_synthesis', 'fail_stage': 'synthesis_gap', 'kind': 'qualitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'musinsa', 'probe_id': 'HOLDOUT-M002', 'document_type': 'other', 'family_guess': 'governance_dart', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': False, 'aggregation_feasible': False, 'readiness_state': 'not_ready_for_synthesis', 'fail_stage': 'synthesis_gap', 'kind': 'qualitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'musinsa', 'probe_id': 'HOLDOUT-M003', 'document_type': 'other', 'family_guess': 'business_narrative', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': True, 'aggregation_feasible': True, 'readiness_state': 'extraction_ready', 'fail_stage': 'ready', 'kind': 'quantitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'musinsa', 'probe_id': 'HOLDOUT-M004', 'document_type': 'other', 'family_guess': 'platform_metric', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': True, 'aggregation_feasible': True, 'readiness_state': 'extraction_ready', 'fail_stage': 'ready', 'kind': 'quantitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'musinsa', 'probe_id': 'HOLDOUT-M005', 'document_type': 'other', 'family_guess': 'esg_report_listing', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': False, 'aggregation_feasible': False, 'readiness_state': 'not_ready_for_synthesis', 'fail_stage': 'synthesis_gap', 'kind': 'qualitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'musinsa', 'probe_id': 'HOLDOUT-M006', 'document_type': 'other', 'family_guess': 'environment_narrative', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': False, 'aggregation_feasible': False, 'readiness_state': 'not_ready_for_synthesis', 'fail_stage': 'synthesis_gap', 'kind': 'qualitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'musinsa', 'probe_id': 'HOLDOUT-M007', 'document_type': 'other', 'family_guess': 'employee_headcount', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': True, 'aggregation_feasible': True, 'readiness_state': 'extraction_ready', 'fail_stage': 'ready', 'kind': 'quantitative', 'note': 'feasibility_only_no_gold_answer'}, {'company_id': 'musinsa', 'probe_id': 'HOLDOUT-M008', 'document_type': 'other', 'family_guess': 'governance_board', 'parser_ok': True, 'retrieval_feasible': True, 'extraction_feasible': False, 'aggregation_feasible': False, 'readiness_state': 'not_ready_for_synthesis', 'fail_stage': 'synthesis_gap', 'kind': 'qualitative', 'note': 'feasibility_only_no_gold_answer'}]**
- `ready_for_limited_langgraph_handoff`: **False**
- `not_ready_for_synthesis`: **True**
- `requires_more_registry_abstraction`: **True**
- Handoff candidate families: none
- Priority next: **registry_abstraction_completion**

Holdout expanded; retrieval hanssem 0.9167, musinsa 1.0; strongest family employee_headcount; synthesis still blocked.
