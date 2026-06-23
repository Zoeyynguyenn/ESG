# Golden Set — Manual Review Round 2 Execution

Generated: 2026-06-11T13:49:48

## Mục tiêu

Thực thi manual review trên **Lane A + Lane B** (confirm/revise/drop);
Lane C giữ backlog. Chuẩn bị workbook cho canonical round kế tiếp.

## Vì sao chỉ xử lý Lane A + B

- Lane A/B = phần tạo giá trị chính (confirm nhanh + rewrite nhẹ).
- Lane C = passage bẩn — chỉ xử lý nếu còn bandwidth.
- Không review phẳng 107 row.

## Kết quả tổng quan

- Input Lane A+B: **80**
- confirm: **31**
- revise: **30**
- drop: **19**

### Breakdown theo công ty

- **레이시온**: confirm=1, revise=0, drop=12, canonical_candidates=1
- **무신사**: confirm=6, revise=5, drop=6, canonical_candidates=11
- **한샘**: confirm=24, revise=25, drop=1, canonical_candidates=49

### Breakdown theo question_type

- `quantitative`: 39
- `trend`: 5
- `qualitative`: 17

## Ví dụ

### Row confirm tốt
- `HS-V4-Q02` (한샘): 한샘는 몇 개의 중대 이슈를 선정했는가? — `lane_a_clean_grounded`
- `HS-V4-Q05` (한샘): 한샘의 ESG 거버넌스 체계는 어떻게 운영되는가? — `lane_a_clean_grounded`
- `HS-V4-Q06` (한샘): 한샘의 ESG 거버넌스 체계는 어떻게 운영되는가? — `lane_a_clean_grounded`

### Row revise tốt
- `MS-V4-T03` (무신사): 무신사의 주요 ESG 지표 또는 목표는 어떻게 변화했는가? — `generic_question_to_specific`
- `HS-V4-T03` (한샘): 한샘의 주요 ESG 지표 또는 목표는 어떻게 변화했는가? — `generic_question_to_specific`
- `MS-V4-Q03` (무신사): 무신사가 공시한 주요 ESG 수치는 무엇인가? — `generic_question_to_specific`

### Row drop (Lane B)
- `HS-V4-T02` (한샘): 한샘는 2050년까지 어떤 기후 목표를 추진하는가? — `company_not_in_disclosure`
- `RX-V4-Q09` (레이시온): 레이시온의 주요 ESG 수치는 무엇인가? — `portal_nav_noise`
- `RX-V4-L07` (레이시온): 레이시온의 안전보건 운영 내용은 무엇인가? — `portal_nav_noise`

## Đánh giá

- Canonical candidate estimate: **61**
- 레이시온 survivors (confirm+revise): **1**
- Lane C backlog: **22**

## Kết luận

- Mở canonical round kế tiếp? **Có — đủ anchor để mở canonical round (Lane A/B); Lane C giữ backlog**
- Lane C tiếp tục? **Giữ backlog — chỉ mở Lane C nếu cần mở rộng coverage RX/MS sau canonical core**
