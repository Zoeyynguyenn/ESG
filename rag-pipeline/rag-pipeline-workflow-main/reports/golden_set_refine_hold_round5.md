# Golden Set — Refine Hold Round 5

Generated: 2026-06-12T14:34:18

## Mục tiêu

Refine 17 hold rows thành lane mở rộng có kiểm soát cho **gold_core_v1_1**, không đụng **gold_core_v1** đã freeze.

## Vì sao refine hold sau khi freeze v1

- `gold_core_v1` (26 row) đã đủ làm artifact chính thức đầu tiên.
- Hold backlog là lane giá trị cao nhất để mở rộng core.
- Không benchmark — tập vẫn đang mở rộng.

## Chia lane hold như thế nào

- **lane_1_known_cluster_cleanup:** cluster đã rõ; trim news chrome / meta / prohibited.
- **lane_2_fc_unknown_resolution:** FC_UNKNOWN — resolve cluster + rewrite nhẹ Q/disclosure.

## Kết quả tổng quan

- **input_hold_count:** 17
- **promote_candidate:** 3
- **keep_hold:** 9
- **drop_after_refine:** 5

### Breakdown theo lane

- `lane_1_known_cluster_cleanup`: {'drop_after_refine': 2, 'promote_candidate': 2, 'keep_hold': 1}
- `lane_2_fc_unknown_resolution`: {'promote_candidate': 1, 'drop_after_refine': 3, 'keep_hold': 8}

### Breakdown theo công ty

- **무신사**: 2
- **한샘**: 15

### Breakdown theo refined cluster

- `FC_ESG_GOVERNANCE`: 3
- `FC_REPORT_FRAMEWORK`: 5
- `FC_UNKNOWN`: 3
- `FC_HUMAN_RIGHTS`: 2
- `FC_MATERIAL_8`: 1
- `FC_CLIMATE_GHG`: 1
- `FC_QUAL_POLICY`: 1
- `FC_KGCS_A`: 1

### FC_UNKNOWN

- **resolved:** 9
- **unresolved:** 3

## Ví dụ

- **Known cluster cleanup thành công:** `MS-V4-Q09`
- **FC_UNKNOWN resolve thành công:** `HS-V4-T03`
- **Drop sau refine:** `MS-V4-Q08`

## Kết luận

- Có thể mở **gold_core_v1_1** với **3** row promote_candidate (chưa promote trong task).
- Còn **9** row giữ hold cho round sau.
- **RX:** source-acquisition dependent — excluded from refine round 5
