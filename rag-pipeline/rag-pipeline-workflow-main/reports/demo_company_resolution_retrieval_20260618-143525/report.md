# Demo Company — Row Disambiguation + Conflict Resolution + Role-Aware Retrieval

Generated: 20260618-143525

## Delta vs vòng `142543`

- `single_doc_ready_count`: 10 → **10** (Δ 0.0)
- `single_extraction_success_rate_on_ready`: 1.0 → **0.7** (Δ -0.3)
- `single_extraction_success_rate_all`: 0.5 → **0.35** (Δ -0.15)
- `wrong_row_risk_count`: None → **0** (Δ None)
- `quant_aggregation_success_rate`: 0.5 → **0.0** (Δ -0.5)
- `aggregation_success_rate`: 0.3333 → **0.0** (Δ -0.3333)
- `aggregation_conflict_rate`: 0.2 → **0.0** (Δ -0.2)
- `aggregation_partial_rate`: 0.1333 → **0.0667** (Δ -0.0666)
- `aggregation_missing_role_rate`: 0.4667 → **1.0** (Δ 0.5333)
- `role_coverage_rate`: None → **1.0** (Δ None)
- `csv_role_hit_rate`: None → **1.0** (Δ None)
- `missing_role_rate`: None → **0.0** (Δ None)

## Single-doc (row disambiguation)

- `count`: **20**
- `single_doc_ready_count`: **10**
- `single_extraction_success_rate_on_ready`: **0.7**
- `single_extraction_success_rate_all`: **0.35**
- `wrong_row_risk_count`: **0**
- `wrong_row_risk_rate_on_ready`: **0.0**
- `single_fail_breakdown`: **{'ready': 7, 'retrieval_gap': 10, 'extraction_gap': 3}**

## Cross-doc (conflict resolution)

- `count`: **15**
- `quantitative_cross_count`: **10**
- `aggregation_success_rate`: **0.0**
- `aggregation_partial_rate`: **0.0667**
- `aggregation_conflict_rate`: **0.0**
- `aggregation_missing_role_rate`: **1.0**
- `quant_aggregation_success_rate`: **0.0**
- `quant_resolution_rate`: **0.1**

## Retrieval-aware

- `role_coverage_rate`: **1.0**
- `csv_role_hit_rate`: **1.0**
- `missing_role_rate`: **0.0**

## 3 case cải thiện

- **QUANT-0001**: wrong-row fixed: matched_row:구성원 총 교육 시간 → 총 임직원

## 3 case vẫn fail

- **QUANT-0042**: status=failed reason=no_numeric_candidates_from_units
- **QUANT-0044**: status=failed reason=no_numeric_candidates_from_units
- **QUANT-0133**: status=failed reason=no_numeric_candidates_from_units

## Kết luận

row disambiguation giảm wrong-row risk so với vòng 142543. conflict resolution chưa tăng quant success đáng kể. role-aware retrieval giảm missing role một phần. Chưa mở qualitative synthesis — bottleneck extraction/aggregation vẫn còn.

**open_synthesis**: False

## Bước tiếp theo

Tiếp tục siết row scoring cho HR/GHG tables; mở rộng metric-key normalization; tăng CSV unit floor cho cross-doc partial cases.
