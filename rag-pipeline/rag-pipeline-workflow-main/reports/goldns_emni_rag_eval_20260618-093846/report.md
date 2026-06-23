# Goldns/Emni RAG Eval Report (20260618-093846)

## Metrics (v4)

- retrieval_hit_top1: **0.9403**
- retrieval_hit_topk: **0.9403**
- source_match_top1: **0.9403**
- source_match_topk: **0.9403**
- answer_accuracy: **0.9254**
- abstain_accuracy: **1.0**
- overall_score: **0.9515**

## Delta vs v3

- `retrieval_hit_top1`: +0.0896 (v3=0.8507)
- `retrieval_hit_topk`: +0.0896 (v3=0.8507)
- `source_match_top1`: +0.0896 (v3=0.8507)
- `source_match_topk`: +0.0896 (v3=0.8507)
- `answer_accuracy`: +0.0299 (v3=0.8955)
- `abstain_accuracy`: +0.0000 (v3=1.0)
- `overall_score`: +0.0523 (v3=0.8992)

## Delta vs v2

- `retrieval_hit_top1`: +0.1791 (v2=0.7612)
- `retrieval_hit_topk`: +0.0896 (v2=0.8507)
- `source_match_top1`: +0.1791 (v2=0.7612)
- `source_match_topk`: +0.0896 (v2=0.8507)
- `answer_accuracy`: +0.0597 (v2=0.8657)
- `abstain_accuracy`: +0.0000 (v2=1.0)
- `overall_score`: +0.1045 (v2=0.847)

## Metric definitions

- `retrieval_hit_top1`: answerable only; doc_title/file_url/lane khop o top-1 evidence
- `retrieval_hit_topk`: answerable only; doc_title/file_url/lane khop trong top-k evidence
- `source_match_top1`: alias cua retrieval_hit_top1
- `source_match_topk`: alias cua retrieval_hit_topk
- `answer_accuracy`: answerable only; predicted answer match gold
- `abstain_accuracy`: abstain only; model abstain khi gold khong co provenance
- `overall_score`: trung binh 4 metric: retrieval_hit_top1, source_match_top1, answer_accuracy, abstain_accuracy

## Fail type breakdown

- `semantic_ambiguity`: 4
- `answer_fail`: 5
- `answer_correct_but_wrong_top1`: 2
- `retrieval_top1_miss`: 4

### answer_fail examples

- `goldns-0104` (goldns) family=sanction_safetykorea gold=0 pred=1 top1=제재이력_safetykorea.json
- `goldns-0106` (goldns) family=sanction_safetykorea gold=0 pred=1 top1=제재이력_safetykorea.json
- `goldns-0107` (goldns) family=sanction_safetykorea gold=0 pred=1 top1=제재이력_safetykorea.json
- `goldns-0208` (goldns) family=financial_generic gold=963 pred=3957 top1=2025_재무_OFS.json
- `goldns-0213` (goldns) family=financial_tax gold=2 pred=-2 top1=2025_재무_OFS.json

### retrieval_top1_miss examples

- `emni-0237` (emni) family=financial_tax gold=1487 pred=1487 top1=2024_exctvSttus.json
- `emni-0238` (emni) family=financial_tax gold=-387 pred=-387 top1=2023_exctvSttus.json
- `goldns-0237` (goldns) family=fair_trade_sanction gold=0 pred=0 top1=제재이력_pipc.json
- `goldns-0238` (goldns) family=fair_trade_sanction gold=0 pred=0 top1=제재이력_pipc.json

### answer_correct_but_wrong_top1 examples

- `goldns-0237` (goldns) family=fair_trade_sanction gold=0 pred=0 top1=제재이력_pipc.json
- `goldns-0238` (goldns) family=fair_trade_sanction gold=0 pred=0 top1=제재이력_pipc.json

### semantic_ambiguity examples

- `emni-0236` (emni) family=financial_tax gold=-4838 pred=-4838 top1=2025_재무_CFS.json
- `emni-0237` (emni) family=financial_tax gold=1487 pred=1487 top1=2024_exctvSttus.json
- `emni-0238` (emni) family=financial_tax gold=-387 pred=-387 top1=2023_exctvSttus.json
- `goldns-0214` (goldns) family=financial_tax gold=-1474 pred=-1474 top1=2025_재무_OFS.json

## Fail by question family (answer/retrieval issues)

- sanction_safetykorea: 3
- fair_trade_sanction: 2
- financial_generic: 1
- financial_tax: 1

## Wrong top-1 docs

- 제재이력_pipc.json: 2
- 2024_exctvSttus.json: 1
- 2023_exctvSttus.json: 1

## emni fail examples (up to 10)

- `emni-0237` family=financial_tax gold=1487 pred=1487 top1=2024_exctvSttus.json reason=retained_value_profit_proxy
- `emni-0238` family=financial_tax gold=-387 pred=-387 top1=2023_exctvSttus.json reason=retained_value_profit_proxy

## Semantic audit / ambiguity

- `emni-0236` (financial_tax): workbook label tax nhung gold map sang 당기순이익
- `emni-0237` (financial_tax): SME follow-up: workbook label may not match account in OFS
- `emni-0238` (financial_tax): workbook label tax nhung gold map sang 당기순이익
- `goldns-0214` (financial_tax): workbook label tax nhung gold map sang 당기순이익
