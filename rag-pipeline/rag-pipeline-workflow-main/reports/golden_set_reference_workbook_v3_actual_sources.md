# Golden Set — Reference Workbook V3 (Actual Sources)

Generated: 2026-06-11T11:19:58

## Mục tiêu

Rebuild workbook từ **actual report body** hoặc **company-primary narrative**, không hardcode salvage record id.

## Vì sao v2 chưa đủ

- V2 salvage từ Yonhap/headline/portal với record id cố định.
- Không có ingest từ PDF/report body thật.

## Source thật đã ingest được

- Musinsa company newsroom (not full PDF): https://newsroom.musinsa.com/newsroom-menu/2024-0719
- Musinsa company newsroom (not full PDF): https://newsroom.musinsa.com/newsroom-menu/2025-0724

## Kết quả seed

- Musinsa actual report body: **0**
- Musinsa company-primary narrative: **4**
- Raysolution actual report body: **0**
- Seeds salvage (portal/press): **1**
- Hansem frozen: **4**
- **Tổng workbook v3:** **9**

## Coverage theo công ty

- **한샘**: 4
- **무신사**: 4
- **레이시온**: 1

## Coverage theo fact cluster

- `FC_MATERIAL_8`: 1
- `FC_NET_ZERO_2050`: 1
- `FC_KGCS_A`: 1
- `FC_ESG_GOVERNANCE`: 1
- `FC_CLIMATE_GHG`: 1
- `FC_IMPACT_REPORT`: 1
- `FC_UNKNOWN`: 1
- `FC_GRI_FRAMEWORK`: 1
- `FC_STAKEHOLDER_DISCLOSURE`: 1

## Đánh giá

- Bớt phụ thuộc press/headline so với v2? **Có — Musinsa dùng newsroom.musinsa.com thay Yonhap/headline v2**
- Gần 3-company review-ready hơn v2? **Gần hơn v2 về provenance, nhưng chưa đủ review-ready**

## Kết luận

V3 cải thiện provenance (company newsroom) nhưng chưa có full report PDF cho cả hai công ty.

**Bước tiếp:** Source acquisition: Musinsa Impact Report PDF + 레이시온 2024 SR PDF vào package _sources/
