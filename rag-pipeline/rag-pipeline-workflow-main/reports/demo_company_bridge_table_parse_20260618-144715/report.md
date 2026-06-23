# Demo Company — Bridge + Table-First + Narrative Parse

Generated: 20260618-144715

## Delta vs `143749`

- `single_extraction_success_rate_on_ready`: 0.8 → **0.8** (Δ 0.0)
- `wrong_row_risk_count`: 0 → **0** (Δ 0.0)
- `quant_aggregation_success_rate`: 0.2 → **0.2** (Δ 0.0)
- `aggregation_conflict_rate`: 0.0 → **0.0** (Δ 0.0)
- `table_unit_hit_rate`: None → **0.7** (Δ None)
- `semantic_bridge_usage_count`: None → **4** (Δ None)
- `narrative_metric_parse_success_count`: None → **0** (Δ None)
- `missing_role_rate`: None → **0.0** (Δ None)

## Focus cases

### QUANT-0044
- docs_sufficient: True
- table_unit_preferred: True
- extraction: False — units_retrieved_but_no_parseable_numeric_row
- aggregation: failed — no_numeric_candidates_from_units
- fail_stage: extraction_gap

### QUANT-0208
- docs_sufficient: True
- table_unit_preferred: True
- extraction: True — matched_row:Capital expenditures
- aggregation: partial — missing_roles:doc_01_business,doc_evidence_csv
- fail_stage: aggregation_gap

### QUANT-0210
- docs_sufficient: True
- table_unit_preferred: True
- extraction: True — matched_row:Defined contribution plan contributions, partial benefits proxy
- aggregation: partial — missing_roles:doc_01_business,doc_evidence_csv
- fail_stage: aggregation_gap

### QUANT-0209
- docs_sufficient: True
- table_unit_preferred: True
- extraction: True — matched_row:Interest expense, net
- aggregation: partial — missing_roles:doc_01_business,doc_evidence_csv
- fail_stage: aggregation_gap

### QUANT-0213
- docs_sufficient: True
- table_unit_preferred: True
- extraction: True — matched_row:Income tax expense
- aggregation: partial — missing_roles:doc_01_business,doc_evidence_csv
- fail_stage: aggregation_gap

### QUANT-0046
- docs_sufficient: True
- table_unit_preferred: False
- extraction: False — source_not_disclosed_for_metric
- aggregation: failed — no_numeric_candidates_from_units
- fail_stage: extraction_gap


## Kết luận

Bridge/table/narrative round: quant_success=0.2, wrong_row=0, rescued=[], still_fail=['QUANT-0044', 'QUANT-0208', 'QUANT-0210', 'QUANT-0209', 'QUANT-0213', 'QUANT-0046']. Chua mo synthesis; khoa tiep demo_company.

