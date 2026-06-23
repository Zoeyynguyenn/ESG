# Goldns/Emni RAG Eval Report (20260618-091904)

## Metrics (v2)

- retrieval_hit_top1: **0.8507**
- retrieval_hit_topk: **0.9851**
- source_match_top1: **0.8507**
- source_match_topk: **0.9851**
- answer_accuracy: **0.806**
- abstain_accuracy: **1.0**
- overall_score: **0.8769**

## Metric definitions

- `retrieval_hit_top1`: answerable only; expected source/doc match o top-1 evidence
- `retrieval_hit_topk`: answerable only; expected source/doc match trong top-k evidence
- `source_match_top1`: alias cua retrieval_hit_top1 trong v2
- `source_match_topk`: alias cua retrieval_hit_topk trong v2
- `answer_accuracy`: answerable only; predicted answer match gold
- `abstain_accuracy`: abstain only; model abstain khi gold khong co provenance
- `overall_score`: trung binh 4 metric: retrieval_hit_top1, source_match_top1, answer_accuracy, abstain_accuracy

## Fail by question family

- board_director: 6
- financial_tax: 5
- minimum_wage: 2
- executive_diversity: 1
- financial_revenue: 1
- financial_generic: 1

## Wrong top-1 docs

- 제재이력.json: 7
- 2025 최저임금 고시: 3

## emni fail examples (up to 10)

- `emni-0224` family=minimum_wage gold=2096270 pred=2156880 top1=2025 최저임금 고시 reason=minimum_wage_value
- `emni-0236` family=financial_tax gold=-4838 pred=-11 top1=2025 최저임금 고시 reason=financial_account_match
- `emni-0237` family=financial_tax gold=1487 pred=13 top1=2025 최저임금 고시 reason=financial_account_match
- `emni-0238` family=financial_tax gold=-387 pred=24 top1=2025 최저임금 고시 reason=financial_account_match
- `emni-0265` family=board_director gold=5 pred=Not disclosed top1=2023_exctvSttus.json reason=unsupported_answer_family
- `emni-0266` family=board_director gold=3 pred=Not disclosed top1=2025_exctvSttus.json reason=unsupported_answer_family
- `emni-0267` family=board_director gold=3 pred=Not disclosed top1=2024_exctvSttus.json reason=unsupported_answer_family
- `emni-0268` family=board_director gold=3 pred=Not disclosed top1=2023_exctvSttus.json reason=unsupported_answer_family

## Semantic audit notes

- `emni-0237`: van can SME audit semantic.
