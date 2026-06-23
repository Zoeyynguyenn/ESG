# Goldns/Emni RAG Eval Report (20260618-092758)

## Metrics (v3)

- retrieval_hit_top1: **0.8507**
- retrieval_hit_topk: **0.8507**
- source_match_top1: **0.8507**
- source_match_topk: **0.8507**
- answer_accuracy: **0.8955**
- abstain_accuracy: **1.0**
- overall_score: **0.8992**

## Delta vs v2

- `retrieval_hit_top1`: +0.0895 (v2=0.7612)
- `retrieval_hit_topk`: +0.0000 (v2=0.8507)
- `source_match_top1`: +0.0895 (v2=0.7612)
- `source_match_topk`: +0.0000 (v2=0.8507)
- `answer_accuracy`: +0.0298 (v2=0.8657)
- `abstain_accuracy`: +0.0000 (v2=1.0)
- `overall_score`: +0.0522 (v2=0.847)

## Metric definitions

- `retrieval_hit_top1`: answerable only; doc_title/file_url khop o top-1 evidence (khong dung source_url chung)
- `retrieval_hit_topk`: answerable only; doc_title/file_url khop trong top-k evidence
- `source_match_top1`: alias cua retrieval_hit_top1 trong v2
- `source_match_topk`: alias cua retrieval_hit_topk trong v2
- `answer_accuracy`: answerable only; predicted answer match gold
- `abstain_accuracy`: abstain only; model abstain khi gold khong co provenance
- `overall_score`: trung binh 4 metric: retrieval_hit_top1, source_match_top1, answer_accuracy, abstain_accuracy

## Fail by question family

- financial_tax: 4
- generic: 2
- board_director: 2
- executive_diversity: 1
- minimum_wage: 1
- financial_revenue: 1
- financial_generic: 1

## Wrong top-1 docs

- 2025_empSttus.json: 7
- 2024_exctvSttus.json: 1
- 2023_exctvSttus.json: 1
- 제재이력.json: 1

## emni fail examples (up to 10)

- `emni-0237` family=financial_tax gold=1487 pred=1487 top1=2024_exctvSttus.json reason=retained_value_profit_proxy
- `emni-0238` family=financial_tax gold=-387 pred=-387 top1=2023_exctvSttus.json reason=retained_value_profit_proxy

## Semantic audit / ambiguity

- `emni-0236` (financial_tax): workbook label tax nhung gold map sang 당기순이익
- `emni-0237` (financial_tax): SME follow-up: workbook label may not match account in OFS
- `emni-0238` (financial_tax): workbook label tax nhung gold map sang 당기순이익
