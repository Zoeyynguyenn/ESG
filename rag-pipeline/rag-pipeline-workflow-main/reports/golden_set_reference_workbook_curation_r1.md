# Golden Set — Reference Workbook Curation R1

Generated: 2026-06-11T10:20:02

## Mục tiêu

Làm sạch `reference_seed_workbook_v1` theo hướng **workbook-first**: phân loại contamination đúng lớp, giữ seed ESG thật, loại portal/news/financial noise — **không** quay lại gate `single-unit hard drop`.

## Vì sao workflow cũ sai hướng

1. Nhánh R2.1–R2.4 ép `1 unit → 1 QA → drop` → yield ~0 dù hệ thống vẫn tìm được ESG fact.
2. Gate `>=8 usable` trên pilot Hansem 5–15 row không phản ánh khả năng sinh seed workbook.
3. Workbook tham chiếu (`golden_set_3companies_v4.xlsx`) cho phép **multi-seed per passage** và review disclosure — không phải mini-pilot precision.

## Quy tắc curation R1

| Decision | Điều kiện |
|----------|-----------|
| `keep_strong` | ESG body sạch, metric/governance/materiality rõ, không chrome |
| `keep_but_needs_rewrite` | Fact ESG thật, Q generic hoặc passage còn noise nhẹ |
| `drop_news_chrome` | News page chrome nặng, fact không đủ salvage |
| `drop_listing_archive` | TOC/archive/report index |
| `drop_contact_or_navigation` | Portal/nav/contact/FAQ |
| `drop_financial_non_esg` | Analyst/financial dominant |
| `drop_cross_company_contamination` | Cross-company marker |
| `drop_too_generic` | Site text/generic Q không đủ specificity |
| `drop_not_esg_enough` | Thiếu tín hiệu ESG substance |

## Kết quả tổng quan

| Chỉ số | Giá trị |
|--------|--------:|
| Tổng seed input | 17 |
| keep_strong | 3 |
| keep_but_needs_rewrite | 11 |
| curated total (keep) | 14 |
| rejected total | 3 |
| usable thực sự (strong) | 3 |
| salvageable (rewrite) | 11 |

### Rejected theo nhóm

- `drop_contact_or_navigation`: **1**
- `drop_listing_archive`: **2**

## Ví dụ theo nhóm

### `drop_contact_or_navigation`
- **MS-E-L01** (무신사): Passage là portal/nav/contact/FAQ listing, không phải ESG disclosure body.

### `keep_but_needs_rewrite`
- **HS-G-T01** (한샘): Fact ESG có thật nhưng cần rewrite question/disclosure.
- **HS-G-Q01** (한샘): Fact ESG có thật nhưng cần rewrite question/disclosure.

### `drop_listing_archive`
- **HS-G-Q05** (한샘): Passage là TOC/archive/listing hoặc report chrome không có fact ESG cụ thể.
- **HS-G-L05** (한샘): Passage là TOC/archive/listing hoặc report chrome không có fact ESG cụ thể.

### `keep_strong`
- **HS-G-T04** (한샘): ESG narrative/metric grounded, contamination thấp.
- **HS-G-Q06** (한샘): ESG narrative/metric grounded, contamination thấp.

## Đánh giá

- **Seed usable thực sự (keep_strong):** 3
- **Seed cần rewrite:** 11
- **Công ty thiếu narrative sạch:** ['무신사']

## Kết luận

- **Workbook curated R1 đủ cho review round tiếp theo?** **Có** — 14 seed keep (strong + rewrite).
- **Bước kế tiếp:** `review + rewrite round 2` trên workbook curated — **không** benchmark, **không** mini-pilot distillation.
- **Cần build seed workbook v2 từ source sạch hơn?** Chưa bắt buộc — curated R1 đủ review round 2; v2 khi mở rộng corpus Hansem/무신사 narrative sạch.
