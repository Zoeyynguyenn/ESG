# Golden Set — RTX Duplicate Question Audit

Generated: 2026-06-12T15:58:38

## Mục tiêu

Xác định mức độ lỗi **duplicate / over-generic question** trên lane RTX
trước khi rebuild question layer fact-specific (v2).

## Triệu chứng lỗi

- Nhiều row dùng cùng `question_draft` nhưng khác `question_type`, `document_kind`, `disclosure`
- Reviewer không thể phân biệt fact target đúng/sai
- Workbook không đạt chuẩn Golden Set ở tầng question synthesis

## Top exact duplicate question templates (v1)

- Total rows v1: **3170**
- Unique questions v1: **11**
- Exact duplicate templates: **11**
- Rows affected: **3170** (100.0%)
- Banned generic template hits: **3008**

- `1376`× `What ESG-related policies or performance does RTX disclose?`
- `1016`× `What quantitative ESG metrics does RTX disclose?`
- `230`× `How is ESG governance structured at RTX?`
- `211`× `How have RTX's key ESG metrics changed over time?`
- `175`× `What ethics and compliance practices does RTX disclose?`
- `78`× `How does RTX address data security and privacy?`
- `41`× `What greenhouse gas emissions does RTX disclose?`
- `21`× `What compliance resolutions has RTX disclosed related to government contracts?`
- `10`× `How does RTX engage stakeholders on sustainability topics?`
- `8`× `What diversity and inclusion commitments does RTX report?`

## Top near-duplicate templates (v1)

- Near-duplicate prefix groups: **0**
- Rows in near-duplicate groups: **0**

## Manual round 2 (sau polish) — vẫn còn generic

- Reviewable rows: **221**
- Unique questions: **27**
- Exact duplicate templates: **17**
- Rows affected: **211**
- Fallback generic hits: **165**

### Breakdown affected rows by document_kind (v1)

- `10k`: 1523
- `proxy_statement`: 815
- `appendix`: 352
- `data_table`: 243
- `questionnaire`: 168
- `policy_page`: 59
- `press_release`: 10

## Ảnh hưởng

- **Review**: reviewer không biết row nào test fact nào
- **Gold set**: không thể promote câu hỏi không gắn fact target
- **Benchmark**: metric retrieval/answer sẽ meaningless nếu question không specific

## Kết luận

Lane RTX phải **rebuild question layer (v2 fact-specific)** trước khi mở lại review round 1.
Tạm dừng manual review round 2 execution, canonical, gold decision, benchmark.
