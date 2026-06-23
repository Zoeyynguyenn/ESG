# Demo Company Cross-Document Diagnostic Report

Generated: 20260618-141731

## Tổng quan subset

- Single-doc: **20** câu
- Cross-doc: **15** câu
- Corpus units: **47**

> Heuristic evidence plan là bootstrap — metric đo retrieval/aggregation readiness, không phải answer accuracy.

## Metric single-doc

- `count`: **20**
- `doc_hit_at_1`: **0.85**
- `doc_hit_at_k`: **0.9**
- `unit_hit_at_k`: **0.55**
- `parser_fail_rate`: **0.0**
- `single_doc_ready_rate`: **0.5**

### Fail stages (single)

- ready: 18
- retrieval_gap: 2

## Metric cross-doc

- `count`: **15**
- `multi_doc_recall`: **0.8611**
- `evidence_plan_coverage`: **0.8611**
- `required_doc_hit_rate`: **1.0**
- `aggregation_readiness`: **1.0**
- `missing_role_rate`: **0.0722**
- `conflict_detected_rate`: **1.0**
- `parser_fail_rate`: **0.0**
- `cross_doc_ready_rate`: **0.8667**

### Fail stages (cross)

- synthesis_gap: 4
- ready: 9
- retrieval_gap: 2

## Top fail patterns

- `ready`: 27
- `retrieval_gap`: 4
- `synthesis_gap`: 4

## Sẵn sàng cho bước answer (approximation)

- Single ready (10): QUANT-0001, QUANT-0006, QUANT-0028, QUANT-0146, QUANT-0151, QUANT-0200, QUANT-0083, QUANT-0126, QUANT-0017, QUANT-0031
- Single NOT ready (10): QUANT-0013, QUANT-0019, QUANT-0147, QUANT-0215, QUANT-0219, QUANT-0224, QUANT-0207, QUANT-0086, QUANT-0144, QUANT-0220
- Cross ready (13): QUAL-0001, QUAL-0002, QUAL-0005, QUAL-0008, QUAL-0020, QUANT-0042, QUANT-0044, QUANT-0133, QUANT-0208, QUANT-0210, QUANT-0209, QUANT-0155, QUANT-0046
- Cross NOT ready (2): QUANT-0134, QUANT-0213

## Bottleneck chính

- **mixed — retrieval mostly OK on single**

single_doc_ready_rate≈0.5, cross_doc_ready_rate≈0.8667

## Khuyến nghị bước tiếp

Pilot answer extractor trên single subset; parallel improve aggregator cho cross.
