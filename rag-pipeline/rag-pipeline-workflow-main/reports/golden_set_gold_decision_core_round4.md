# Golden Set — Gold Decision Core Round 4

Generated: 2026-06-12T14:14:24

## Mục tiêu

Gold decision round cho core **한샘 + 무신사**: approve / revise_hold / reject — không promote hàng loạt.

## Vì sao mở gold decision round lúc này

- Core canonical 45 row (HS 36, MS 9) đủ chặt sau merge.
- Cần tách row gold-ready vs hold vs reject trước promote.
- `FC_UNKNOWN=15` yêu cầu siết riêng — không auto-approve.

## Rule approve / hold / reject

| Decision | Điều kiện |
|----------|-----------|
| `gold_approve` | Cluster rõ (hoặc unknown đã resolve), Q/disclosure sạch |
| `gold_revise_hold` | Fact đúng nhưng wording/cluster/prohibited cần sửa |
| `gold_reject` | Listing/meta, truncated, unknown quá mơ hồ |

## Rule riêng cho `FC_UNKNOWN`

- Không auto-approve.
- Approve chỉ khi `final_question + final_disclosure` xác định fact rõ (clarity≥6, không listing).
- Còn lại: hold hoặc reject.

## Kết quả tổng quan

- Input: **45**
- approve: **26**
- revise_hold: **17**
- reject: **2**
- **Core gold ready (approve):** **26**

### Breakdown theo công ty

- **무신사**: approve=5, hold=2, reject=2
- **한샘**: approve=21, hold=15, reject=0

### Breakdown theo cluster

- `FC_ESG_GOVERNANCE`: 13
- `FC_UNKNOWN`: 1
- `FC_MATERIAL_8`: 5
- `FC_HUMAN_RIGHTS`: 3
- `FC_TCFD`: 2
- `FC_KGCS_A`: 2

### FC_UNKNOWN breakdown

- approve: **1**
- hold: **12**
- reject: **2**
- **Chưa chốt (hold+reject):** **14**

## Ví dụ

### Approve mạnh
- `MS-V4-Q06` (무신사, FC_ESG_GOVERNANCE): `known_cluster_clean_anchor`
- `MS-V4-T03` (무신사, FC_UNKNOWN): `unknown_resolved_clear_fact`
- `MS-V4-Q16` (무신사, FC_ESG_GOVERNANCE): `known_cluster_usable`

### Hold wording/cluster
- `MS-V4-Q08` (무신사, FC_ESG_GOVERNANCE): `known_cluster_news_chrome`
- `MS-V4-Q09` (무신사, FC_ESG_GOVERNANCE): `known_cluster_news_chrome`
- `HS-V4-T03` (한샘, FC_UNKNOWN): `unknown_cluster_needs_review`

### Reject
- `MS-V4-T04` (무신사, FC_UNKNOWN): `unknown_cluster_too_vague`
- `MS-V4-T05` (무신사, FC_UNKNOWN): `unknown_cluster_too_vague`

## Kết luận

- Core gold ready: **26** (HS 21, MS 5)
- RX status: **source-acquisition dependent — 1 survivor + 22 lane C + reject rows; không trong gold core**
