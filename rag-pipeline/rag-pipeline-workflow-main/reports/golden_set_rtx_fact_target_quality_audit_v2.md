# Golden Set — RTX Fact-Target Quality Audit (V2)

Generated: 2026-06-12T16:08:36

## Mục tiêu

Đánh giá chất lượng `fact_target → question → disclosure` trên RTX v2
trước khi quyết định mở review round 1.

## Vì sao v2 chưa đủ mở review

- v2 sửa duplicate (0 exact dup) nhưng question vẫn có thể là phrase extraction thô
- Có row **fact mismatch** (question hỏi fact A, disclosure là fact B)
- Có residue parse (`s Workforce`, `GHGemissions`, `What Reductions from...`)

## Breakdown theo loại lỗi

- `fact_mismatch`: **23** rows
- `unnatural_question_wording`: **261** rows
- `residue_led_question`: **164** rows
- `overlong_fact_phrase`: **137** rows
- Usable without rebuild: **10** / **327**

## Ví dụ cụ thể

### fact_mismatch
- `RTX-V2-Q04`: What high and elevated ergonomic risks in 2025 does RTX report?…

### unnatural_question_wording
- `RTX-V2-Q01`: What energy intensity (GJ per $M revenue) in 2022 does RTX report?…
- `RTX-V2-Q02`: What Reductions from the 2019 baseline with a new metric/goal in 2022 does RTX report?…
- `RTX-V2-Q03`: What high and elevated ergonomic risks in 2020 does RTX report?…

### residue_led_question
- `RTX-V2-Q01`: What energy intensity (GJ per $M revenue) in 2022 does RTX report?…
- `RTX-V2-Q02`: What Reductions from the 2019 baseline with a new metric/goal in 2022 does RTX report?…
- `RTX-V2-Q03`: What high and elevated ergonomic risks in 2020 does RTX report?…

### overlong_fact_phrase
- `RTX-V2-Q02`: What Reductions from the 2019 baseline with a new metric/goal in 2022 does RTX report?…
- `RTX-V2-Q06`: What s Workforce 2030 Energy and GHGemissions reduction in 2030 does RTX report?…
- `RTX-V2-Q10`: What energy consumption reduction since 2019 baseline in 2022 does RTX report?…

## Kết luận

- Usable: **10**
- Needs rebuild: **317**
- Bước tiếp: **RTX v2.1 fact-quality rebuild** — không mở review trên v2.
