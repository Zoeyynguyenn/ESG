# Demo Company Extractor + Aggregator Pilot Report

Generated: 20260618-142543

## Single-doc extraction pilot

- Subset size: **20**
- Ready for extraction: **10**
- `single_extraction_success_rate_on_ready`: **1.0**
- `single_extraction_success_rate_all`: **0.5**

### Fail breakdown

- `ready`: 10
- `retrieval_gap`: 10

## Cross-doc aggregation pilot

- `count`: **15**
- `quantitative_cross_count`: **10**
- `aggregation_success_rate`: **0.3333**
- `aggregation_partial_rate`: **0.1333**
- `aggregation_conflict_rate`: **0.2**
- `aggregation_missing_role_rate`: **0.4667**
- `quant_aggregation_success_rate`: **0.5**

### Fail breakdown

- `synthesis_gap`: 5
- `aggregation_gap`: 5
- `ready`: 5

## Ví dụ single

- **QUANT-0001** value=`6,200,000` doc=`doc_04_hr_safety` reason=`matched_row:구성원 총 교육 시간`
- **QUANT-0006** value=`약 180,000` doc=`doc_04_hr_safety` reason=`matched_row:총 임직원`
- **QUANT-0013** FAIL stage=`retrieval_gap` reason=`not_single_doc_ready_or_empty_units`
- **QUANT-0019** FAIL stage=`retrieval_gap` reason=`not_single_doc_ready_or_empty_units`

## Ví dụ cross

- **QUANT-0133** status=`success` value=`1,409,597` flags=[]
- **QUANT-0208** status=`success` value=`88,603` flags=[]
- **QUAL-0001** status=`failed` reason=`qualitative_aggregation_deferred_to_synthesis_phase` missing_roles=['doc_06_governance', 'doc_01_business', 'doc_07_certification', 'doc_evidence_csv']
- **QUAL-0002** status=`failed` reason=`qualitative_aggregation_deferred_to_synthesis_phase` missing_roles=['doc_06_governance']

## Kết luận

structured_extractor giải quyết đúng bottleneck unit-level cho nhóm ready; có thể mở rộng extractor pilot. aggregator tạo được mergeable evidence một phần — vẫn chưa đủ cho qualitative synthesis.

## Bước tiếp theo

Mở rộng extractor + conflict resolution trong aggregator; thêm role-aware subquery retrieval.
