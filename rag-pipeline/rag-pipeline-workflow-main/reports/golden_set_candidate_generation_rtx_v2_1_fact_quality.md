# Golden Set — Candidate Generation RTX V2.1 (Fact Quality)

Generated: 2026-06-12T16:11:13

## Mục tiêu

Rebuild question layer với canonical facts + quality gates; ưu tiên usability + alignment.

## Audit lỗi v2 cho thấy gì

- v2 input: **327**; needs rebuild: **317**
- Lỗi chính: fact mismatch, unnatural wording, residue-led questions, overlong phrases

## Rule rebuild v2.1

- Chỉ dùng **canonical fact catalog** với câu hỏi tự nhiên định sẵn
- `passes_quality_gates` trước khi giữ row
- Drop nếu question/disclosure không align

## Kết quả

- Raw candidates: **165**
- Filtered candidates: **42**
- Usable count: **42**
- Dropped fact mismatch (est.): **23**
- Dropped wording/residue (est.): **562**

### Breakdown theo question_type

- `quantitative`: 30
- `trend`: 7
- `qualitative`: 5

### Breakdown theo document_kind

- `questionnaire`: 7
- `appendix`: 6
- `data_table`: 8
- `10k`: 10
- `proxy_statement`: 9
- `policy_page`: 2

## Ví dụ v2 lỗi → v2.1 sửa


## Kết luận

- v2.1 đủ mở review round 1: **Có — question layer v2.1 đủ tốt để mở lại RTX review round 1**
- `review_ready_flag` = **True**
