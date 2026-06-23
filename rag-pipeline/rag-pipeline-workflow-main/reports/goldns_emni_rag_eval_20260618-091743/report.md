# Goldns/Emni RAG Eval Report (20260618-091743)

## Metrics (v2)

- retrieval_hit_top1: **0.8507**
- retrieval_hit_topk: **0.9851**
- source_match_top1: **0.8507**
- source_match_topk: **0.9851**
- answer_accuracy: **0.7164**
- abstain_accuracy: **1.0**
- overall_score: **0.8545**

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
- financial_revenue: 4
- financial_interest: 3
- minimum_wage: 2
- executive_diversity: 1
- financial_generic: 1

## Wrong top-1 docs

- 제재이력.json: 7
- 2025 최저임금 고시: 3

## emni fail examples (up to 10)

- `emni-0224` family=minimum_wage gold=2096270 pred=Not disclosed top1=2025 최저임금 고시 reason=unsupported_answer_family
- `emni-0225` family=financial_revenue gold=18380 pred=2.4e-05 top1=2025_재무_CFS.json reason=financial_account_match
- `emni-0226` family=financial_revenue gold=29699 pred=3.4e-05 top1=2024_재무_OFS.json reason=financial_account_match
- `emni-0227` family=financial_revenue gold=26312 pred=2.4e-05 top1=2023_재무_CFS.json reason=financial_account_match
- `emni-0229` family=financial_interest gold=891 pred=0.000104 top1=2025_재무_CFS.json reason=financial_account_match
- `emni-0230` family=financial_interest gold=749 pred=0.000401 top1=2024_재무_OFS.json reason=financial_account_match
- `emni-0231` family=financial_interest gold=114 pred=0.000882 top1=2023_재무_CFS.json reason=financial_account_match
- `emni-0236` family=financial_tax gold=-4838 pred=2.3e-05 top1=2025 최저임금 고시 reason=financial_account_match
- `emni-0237` family=financial_tax gold=1487 pred=-10.97299 top1=2025 최저임금 고시 reason=financial_account_match
- `emni-0238` family=financial_tax gold=-387 pred=-10.97299 top1=2025 최저임금 고시 reason=financial_account_match

## Semantic audit notes

- `emni-0237`: van can SME audit semantic.
