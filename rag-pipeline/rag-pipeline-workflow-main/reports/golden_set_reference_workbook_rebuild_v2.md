# Golden Set — Reference Workbook Rebuild V2

Generated: 2026-06-11T10:39:26

## Mục tiêu

Khôi phục hướng **workbook-first 3 công ty**: giữ 4 Hansem canonical frozen, rebuild seed pool cho **무신사** và **레이시온** từ source sạch hơn.

## Vì sao R2 chưa đủ

- R2 chỉ còn **4 seed Hansem-only** — không phải workbook 3 công ty.
- 무신사 biến mất vì source corpus chủ yếu là **portal/nav** và **news/financial**.
- 레이시온 corpus gần như **항만 portal + 정보공개**, chỉ vài câu ESG disclosure salvageable.

## Audit source — 무신사

- Tổng unit corpus: **38**
- Pool keep/conditional: **19**
- Drop chính: portal/nav, news/financial, listing — xem `source_pool_musinsa_r2.jsonl`

## Audit source — 레이시온

- Tổng unit corpus: **40**
- Pool keep/conditional: **6**
- Drop chính: portal/nav, 민원/정보공개, cross-company contamination

## Quy tắc chọn source sạch

- **keep**: ESG narrative/fact có company name, substance ≥ 2 signals
- **conditional**: press release mixed nhưng trích được câu fact company
- **drop**: portal, listing, financial/analyst, cross-company, DART metadata

## Kết quả rebuild

| Thành phần | Số seed |
|-----------|--------:|
| Hansem frozen anchors | 4 |
| Musinsa new seeds | 5 |
| Raysolution new seeds | 1 |
| **Tổng workbook v2** | **10** |

## Coverage theo công ty

- **한샘**: 4 seed
- **무신사**: 5 seed
- **레이시온**: 1 seed

## Coverage theo fact cluster

- `FC_MATERIAL_8`: 1
- `FC_NET_ZERO_2050`: 1
- `FC_KGCS_A`: 1
- `FC_ESG_GOVERNANCE`: 2
- `FC_IMPACT_REPORT`: 1
- `FC_CLIMATE_GHG`: 1
- `FC_EXTERNAL_DIRECTOR`: 1
- `FC_COMMUNITY_DONATION`: 1
- `FC_STAKEHOLDER_DISCLOSURE`: 1

## Những chỗ vẫn thiếu source sạch

- 무신사: thiếu report body narrative sạch — phụ thuộc press release / headline salvage
- 레이시온: thiếu metric/governance narrative — chỉ có stakeholder disclosure sentence
- Cả hai: cần ingest PDF sustainability report thật (Impact Report / 2024 SR) để mở rộng cluster

## Kết luận

- **Workbook v2 gần 3-company review-ready?** **Chưa đủ** — có mặt 3 công ty nhưng Musinsa/Raysolution còn mỏng (press/headline salvage; RX chỉ 1 cluster)
- **Thiếu ở đâu:** 무신사 (narrative report body), 레이시온 (ESG metric/governance body)

### Ba câu trả lời

1. Musinsa rebuild: **5** seed mới
2. Raysolution rebuild: **1** seed mới
3. Tổng coverage: **10** seed / **9** fact cluster — partial 3-company workbook — đủ làm format anchor + pilot review, chưa đủ golden workbook đầy đủ
