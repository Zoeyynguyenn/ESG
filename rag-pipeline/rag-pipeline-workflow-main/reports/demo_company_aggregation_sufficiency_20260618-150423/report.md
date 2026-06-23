# Demo Company — Aggregation Sufficiency Taxonomy

Generated: 20260618-150423

## Delta vs `144715`

- `quant_aggregation_success_rate`: 0.2 → **0.7** (Δ 0.5)
- `resolved_single_source_sufficient_rate`: None → **0.6** (Δ None)
- `aggregation_partial_rate`: 0.2667 → **0.0** (Δ -0.2667)
- `aggregation_conflict_rate`: 0.0 → **0.0** (Δ 0.0)
- `metric_absent_in_role_rate`: None → **1.0** (Δ None)
- `missing_numeric_role_rate`: None → **0.0** (Δ None)
- `narrative_metric_parse_success_count`: 0 → **1** (Δ 1.0)

## Focus case audit

- **QUANT-0044**: metric_absent — sufficiency=`failed` value=`None`
- **QUANT-0133**: resolved_single_source_sufficient — sufficiency=`resolved_single_source_sufficient` value=`20.8`
- **QUANT-0208**: resolved_single_source_sufficient — sufficiency=`resolved_single_source_sufficient` value=`2,625`
- **QUANT-0210**: resolved_single_source_sufficient — sufficiency=`resolved_single_source_sufficient` value=`1.4`
- **QUANT-0209**: resolved_single_source_sufficient — sufficiency=`resolved_single_source_sufficient` value=`1,862`
- **QUANT-0213**: resolved_single_source_sufficient — sufficiency=`resolved_single_source_sufficient` value=`1,181`
- **QUANT-0046**: not_disclosed_honest_fail — sufficiency=`failed` value=`None`

## Benchmark honesty

quant_aggregation_success chi tang khi co rationale single_source_sufficient; partial giam khi role phu la metric_absent_in_role, khong inflate success vo co.

## Kết luận

partial→single_source_sufficient: 6 cases; quant_success=0.7; chua mo synthesis; khoa demo_company.
