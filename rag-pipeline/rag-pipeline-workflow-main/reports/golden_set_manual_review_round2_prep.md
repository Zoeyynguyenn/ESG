# Golden Set — Manual Review Round 2 Prep

Generated: 2026-06-11T13:41:15

## Mục tiêu

Chuẩn bị workbook manual review round 2 với **lane split** để giảm review cost:
reviewer không xử lý phẳng 107 row như nhau.

## Vì sao cần lane split

Round 1 `rewrite` trộn hai loại:
- **rewrite_light**: fact sạch, chỉ cần chỉnh wording/specificity
- **rewrite_heavy**: passage còn bẩn (ads, JSON, meta, truncated headline)

Nếu review phẳng, reviewer tốn công vào row gần reject.

## Rule chia lane

| Lane | Điều kiện |
|------|-----------|
| `lane_a_ready_keep` | Round1 keep + disclosure sạch, confirm/drop nhanh |
| `lane_b_rewrite_light` | Fact thật; chỉnh Q/disclosure gọn |
| `lane_c_rewrite_heavy` | Fact salvageable nhưng passage bẩn |
| `reject_recommended` | Fact yếu + noise cao; không đáng cứu |

## Kết quả

- Lane A: **14**
- Lane B: **66**
- Lane C: **22**
- Reject recommended: **5**

### Breakdown theo công ty

- **레이시온**: A=0, B=13, C=0, reject=1
- **무신사**: A=3, B=14, C=5, reject=0
- **한샘**: A=11, B=39, C=17, reject=4

### Breakdown theo question_type

- `trend`: 8
- `quantitative`: 59
- `qualitative`: 35

## Ví dụ mỗi lane

### Lane A
- `HS-V4-Q02` (한샘): 한샘는 몇 개의 중대 이슈를 선정했는가? — round1_keep_clean_grounded
- `HS-V4-Q05` (한샘): 한샘의 ESG 거버넌스 체계는 어떻게 운영되는가? — round1_keep_clean_grounded
- `HS-V4-Q06` (한샘): 한샘의 ESG 거버넌스 체계는 어떻게 운영되는가? — round1_keep_clean_grounded

### Lane B
- `HS-V4-T02` (한샘): 한샘는 2050년까지 어떤 기후 목표를 추진하는가? — keep_with_minor_cleanup
- `MS-V4-T03` (무신사): 무신사의 주요 ESG 지표 추이는 어떻게 변화했는가? — generic_question_clean_disclosure
- `HS-V4-T03` (한샘): 한샘의 주요 ESG 지표 추이는 어떻게 변화했는가? — generic_question_clean_disclosure

### Lane C
- `HS-V4-T01` (한샘): 한샘는 2050년까지 어떤 기후 목표를 추진하는가? — dirty_passage_salvage; truncated_excerpt
- `HS-V4-Q03` (한샘): 한샘는 2050년까지 어떤 기후 목표를 추진하는가? — dirty_passage_salvage; truncated_excerpt,very_short_excerpt
- `HS-V4-Q17` (한샘): 한샘의 주요 ESG 수치는 무엇인가? — dirty_passage_salvage; json_blob

### Reject recommended
- `HS-V4-Q01` (한샘): 한샘는 ESG 평가에서 어떤 등급을 획득했는가? — low_fact_high_noise; contam=10; fact=10; heavy_chrome,news_chrome_flag
- `HS-V4-Q04` (한샘): 한샘의 기후변화 대응 공시는 무엇을 기반으로 하는가? — low_fact_high_noise; contam=11; fact=6; truncated_excerpt,very_short_excerpt,framework_definition_only
- `HS-V4-Q08` (한샘): 한샘는 ESG 평가에서 어떤 등급을 획득했는가? — low_fact_high_noise; contam=16; fact=9; heavy_chrome,news_chrome_flag

## Kết luận

- Reviewer bắt đầu từ: **Lane_A_ReadyKeep → Lane_B_RewriteLight → Lane_C_RewriteHeavy; bỏ qua Reject_Recommended trừ audit**
- Ước lượng row sống tới canonical round tiếp: **~72**
  (A ~90% + B ~75% + C ~45% của row không reject)
