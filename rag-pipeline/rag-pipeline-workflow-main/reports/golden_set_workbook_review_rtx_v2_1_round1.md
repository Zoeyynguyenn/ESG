# Golden Set — Workbook Review RTX V2.1 Round 1

Generated: 2026-06-12T16:16:16

## Mục tiêu

Mở lại Review Round 1 trên workbook **v2.1 fact-quality** (42 candidates).
Không dùng v1 / manual_round2 legacy.

## Vì sao v2.1 mới đủ mở review round 1

- 0 exact duplicate question; mỗi row có `fact_target`
- Post-audit quality errors = 0 trên input
- Question layer đã fact-specific và aligned

## Rule triage round 1

| Decision | Điều kiện |
|----------|-----------|
| `keep` | Question tự nhiên, fact rõ, disclosure usable |
| `rewrite` | Fact đúng; chỉnh wording/disclosure nhẹ (table/trend awkward) |
| `reject` | Mismatch, residue, disclosure quá yếu |
| `collapse_into_cluster` | Trùng fact cluster; year không thêm giá trị |

## Kết quả tổng quan

- Input total: **42**
- keep: **22**
- rewrite: **7**
- reject: **0**
- collapse_into_cluster: **13**
- Reviewable (keep + rewrite): **29**

### Breakdown theo question_type (reviewable)

- `trend`: 5
- `quantitative`: 19
- `qualitative`: 5

### Breakdown theo document_kind (reviewable)

- `appendix`: 4
- `questionnaire`: 4
- `data_table`: 7
- `10k`: 6
- `proxy_statement`: 6
- `policy_page`: 2

### Breakdown theo review_reason

- `v21_clean_grounded`: 22
- `duplicate_fact_cluster`: 13
- `disclosure_too_long`: 6
- `trend_should_be_quantitative;disclosure_too_long`: 1

## Ví dụ

### Keep tốt
- `RTX-V21-T01`: What Scope 3 GHG emissions does RTX report for 2023? — v21_clean_grounded
- `RTX-V21-Q02`: What Scope 1 and Scope 2 GHG emissions does RTX report for 2019? — v21_clean_grounded
- `RTX-V21-Q04`: What TCFD-aligned climate disclosures does RTX provide for 2024? — v21_clean_grounded

### Rewrite hợp lý
- `RTX-V21-Q03`: What Scope 1 and Scope 2 GHG emissions does RTX report in its CDP questionnaire? — disclosure_too_long
- `RTX-V21-T04`: What compliance resolution related to government contracts has RTX disclosed for 2024? — trend_should_be_quantitative;disclosure_too_long
- `RTX-V21-T07`: What ESG oversight role does RTX's Audit Committee have for 2025? — disclosure_too_long

### Collapse đúng
- `RTX-V21-Q01`: What Scope 1 and Scope 2 GHG emissions does RTX report for 2024 (disclosed figure includes — duplicate_fact_cluster
- `RTX-V21-T02`: How did RTX's Scope 1 and Scope 2 GHG emissions change from 2023 to 2024? — duplicate_fact_cluster
- `RTX-V21-Q06`: What Scope 1 and Scope 2 GHG emissions does RTX report for 2024? — duplicate_fact_cluster

### Reject

## Kết luận

- Reviewable rows: **29**
- Đủ mở manual review prep: **Có — đủ để mở manual review prep (lane split + polish)**
- `manual_review_ready_flag` = **True**
