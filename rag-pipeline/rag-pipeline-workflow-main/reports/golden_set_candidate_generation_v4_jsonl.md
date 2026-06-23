# Golden Set — Candidate Generation V4 (JSONL)

Generated: 2026-06-11T11:58:15

## Mục tiêu

Rebuild candidate generation từ `corpus_units.jsonl` theo hướng **workbook-first**:
một passage tốt → nhiều seed candidate; không ép 1 unit = 1 QA.

## Vì sao workflow cũ sai

- Prefilter/distillation/QC ép `1 unit → 1 QA` và hard-drop duplicate sớm.
- Yield sụp trước khi có workbook reviewable.
- Gate precision sớm không phản ánh khả năng khai thác ESG fact từ jsonl.

## Nguyên tắc builder v4 từ jsonl

- Nguồn chính: `corpus_units.jsonl` (118 units).
- Không yêu cầu PDF thật; không hardcode salvage record id.
- Provenance flag: `jsonl_primary_candidate` / `jsonl_mixed_candidate` / `jsonl_noisy_but_salvageable`.

## Passage-level filtering

Chỉ loại noise mạnh: nav/listing/contact, pure financial/analyst, cross-company contamination, passage quá ngắn/không ESG.

- Passages accepted: **98**
- Passages rejected: **20**

Top rejection reasons:
- `cross_company_contamination`: 14
- `no_esg_substance`: 3
- `portal_navigation_noise`: 2
- `pure_financial_or_analyst_noise`: 1

## Candidate-level generation

Từ mỗi passage: tách câu ESG substance → sinh candidate theo `quantitative` / `trend` / `qualitative` và `candidate_kind`.

- Raw candidates generated: **899**
- Rejected at candidate-level (implicit in generation): filtered during `candidate_level_filter`

## Workbook-level dedupe

Collapse duplicate thực sự (cùng company + question + disclosure prefix); giữ diversity theo record/question.

- After workbook dedupe + balanced select: **175**

## Kết quả

- Tổng passage dùng: **98**
- Raw candidates: **899**
- Sau lọc/dedupe: **175**

### Coverage theo công ty
- **한샘**: 97
- **레이시온**: 31
- **무신사**: 47

### Coverage theo question_type

- `trend`: 12
- `quantitative`: 88
- `qualitative`: 75

## So sánh định tính với nhánh cũ

- Yield cao hơn v1/v2/v3? **Có — v4 có 175 rows vs v1 ~17**
- Diversity tốt hơn? **Có — multi-seed per passage + 3 company mix**
- Noise còn lại: **~0 noisy-salvageable; reviewer should triage portal/press rows**

## Kết luận

- Gần tinh thần `golden_set_3companies_v4`? **Có — workbook-first, candidate-rich, chưa canonical**
- Đủ mở review workbook round tiếp? **Có — đủ để mở review workbook round tiếp (draft candidates, không gold-ready)**
