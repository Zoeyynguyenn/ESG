# Golden Set — Actual Source Audit V3

## Mục tiêu

Xác định có **actual ESG report body** trong repo hay không, trước khi rebuild workbook v3.

## Đã tìm ở đâu

- `data/rag_dataset/05_company_export_json/*/_sources/*.pdf`
- `records/company_evidence.jsonl` metadata (`source_url`, `source_path`)
- `splits/full.jsonl` (scan cùng package)

## Musinsa

- **Có report PDF usable?** False
- **PDF paths:** _sources/519596ec18257c3d2b14d707.pdf, _sources/89eff9bbf6c2110fb722fbb3.pdf, _sources/adcbee6c60651179073c3494.pdf
- **Company newsroom primary:** True
- **Newsroom URLs:** https://newsroom.musinsa.com/newsroom-menu/2024-0719, https://newsroom.musinsa.com/newsroom-menu/2025-0724
- **Usable for ingest:** True

## Raysolution

- **Có report PDF usable?** False
- **PDF paths:** — (không có _sources/)
- **Portal salvage only:** True
- **Usable for ingest:** True

## Kết luận

- **Musinsa:** Không có PDF report body usable; có company newsroom summary (newsroom.musinsa.com)
- **Raysolution:** Không có report body; chỉ portal salvage hoặc thiếu hoàn toàn

### Source acquisition gap

- Musinsa: thiếu Impact Report PDF usable trong package _sources/
- 레이시온: không có _sources/ PDF; corpus = YGPA portal + cross-company noise
