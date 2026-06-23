# Goldns/Emni RAG Eval Report (20260617-163805)

## Metrics

- retrieval_hit_rate: **0.2388**
- source_match_rate: **0.9851**
- answer_accuracy: **0.4627**
- abstain_accuracy: **1.0**
- overall_score: **0.6716**

- total_questions: 530
- answerable_count: 67
- abstain_count: 463

## Theo company

| Company | Answerable | Abstain | Retrieval hit | Answer accuracy | Abstain accuracy |
|---|---:|---:|---:|---:|---:|
| emni | 43 | 236 | 0.093 | 0.3721 | 1.0 |
| goldns | 24 | 227 | 0.5 | 0.625 | 1.0 |

## Blocked / skipped sources

- case.ftc.go.kr self_redirect_loop_blocked_by_site (web download lane)

## Semantic audit notes

- `emni-0237`: provenance da co, nhung label gold `세금 및 공과 + 법인세` van can SME audit vi account match trong OFS dang la `당기순이익(손실)`.
