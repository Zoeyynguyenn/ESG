# Goldns/Emni RAG Eval Report (20260618-091942)

## Metrics (v2)

- retrieval_hit_top1: **0.7612**
- retrieval_hit_topk: **0.8507**
- source_match_top1: **0.7612**
- source_match_topk: **0.8507**
- answer_accuracy: **0.8657**
- abstain_accuracy: **1.0**
- overall_score: **0.847**

## Metric definitions

- `retrieval_hit_top1`: answerable only; doc_title/file_url khop o top-1 evidence (khong dung source_url chung)
- `retrieval_hit_topk`: answerable only; doc_title/file_url khop trong top-k evidence
- `source_match_top1`: alias cua retrieval_hit_top1 trong v2
- `source_match_topk`: alias cua retrieval_hit_topk trong v2
- `answer_accuracy`: answerable only; predicted answer match gold
- `abstain_accuracy`: abstain only; model abstain khi gold khong co provenance
- `overall_score`: trung binh 4 metric: retrieval_hit_top1, source_match_top1, answer_accuracy, abstain_accuracy

## Fail by question family

- board_director: 7
- financial_tax: 5
- executive_diversity: 1
- minimum_wage: 1
- financial_revenue: 1
- financial_generic: 1

## Wrong top-1 docs

- 제재이력.json: 7
- 2025 최저임금 고시: 3
- 2024_exctvSttus.json: 2
- 2023_exctvSttus.json: 2
- 2025_exctvSttus.json: 1
- 2025_empSttus.json: 1

## emni fail examples (up to 10)

- `emni-0236` family=financial_tax gold=-4838 pred=-11 top1=2025 최저임금 고시 reason=financial_account_match
- `emni-0237` family=financial_tax gold=1487 pred=13 top1=2025 최저임금 고시 reason=financial_account_match
- `emni-0238` family=financial_tax gold=-387 pred=24 top1=2025 최저임금 고시 reason=financial_account_match
- `emni-0264` family=board_director gold=4 pred=4 top1=2024_exctvSttus.json reason=numeric_fallback
- `emni-0265` family=board_director gold=5 pred=Not disclosed top1=2023_exctvSttus.json reason=unsupported_answer_family
- `emni-0266` family=board_director gold=3 pred=3 top1=2025_exctvSttus.json reason=numeric_fallback
- `emni-0267` family=board_director gold=3 pred=3 top1=2024_exctvSttus.json reason=numeric_fallback
- `emni-0268` family=board_director gold=3 pred=3 top1=2023_exctvSttus.json reason=numeric_fallback

## Semantic audit notes

- `emni-0237`: van can SME audit semantic.
