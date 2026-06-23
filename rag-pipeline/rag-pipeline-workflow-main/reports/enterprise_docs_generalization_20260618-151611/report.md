# Enterprise Internal-Doc — Generalization Hardening

Generated: 20260618-151611

## Rule inventory

- Total rules: **27**
- Reusable generic: **13**
- Pilot-only: **7**
- `reusable_system_coverage`: **0.4815**

## Demo readiness (development set)

- Cases: **35**
- Quant synthesis-gate allowed rate: **0.2333**

### Readiness counts

- `extraction_ready`: 8
- `honest_abstain`: 1
- `multi_source_sufficient`: 1
- `not_ready_for_synthesis`: 5
- `retrieval_ready`: 14
- `single_source_sufficient`: 6

## Holdout sanity (한샘)

- Probes: **8**
- Parser OK rate: **1.0**
- Retrieval feasible: **0.0**
- Extraction feasible: **0.0**

## Architecture decision

- Expand holdout: **False**
- Open synthesis: **False**
- Weakest layer: **retrieval**
- Priority next: **abstraction_rule_registry**

Lane co 13 reusable rules / 27 total; demo quant synthesis-gate 0.2333; holdout retrieval 0.0; chua mo synthesis; can abstraction truoc full holdout.
