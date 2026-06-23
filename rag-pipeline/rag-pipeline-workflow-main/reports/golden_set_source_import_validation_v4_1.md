# Golden Set — Source Import Validation V4.1

Generated: 2026-06-11T11:35:43

## Mục tiêu

Import 2 PDF ESG từ Downloads vào package workspace và validate khả năng đọc / độ phù hợp.

## File nào được import

- `한샘_esg_export_20260608_043142.pdf` (한샘) — 20915 bytes
- `레이시온_esg_export_20260608_055704.pdf` (레이시온) — 21253 bytes

## Import vào đâu

- **한샘:** `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/_sources/한샘_esg_export_20260608_043142.pdf`
- **레이시온:** `data/rag_dataset/05_company_export_json/레이시온_dataset_package_20260608T055801/_sources/레이시온_esg_export_20260608_055704.pdf`

## Kết quả validation từng file

### 한샘 — `한샘_esg_export_20260608_043142.pdf`

- **exists_after_import:** True
- **readability:** readable (5 pages, 9520 chars extracted)
- **ESG signal score:** 8
- **Company signal score:** 6
- **verdict:** `accept_with_warnings`
- **document type note:** ESG coverage export (not full SR body)
- **reason:** readable_esg_coverage_export_not_full_sustainability_report_body
- **preview:** Page 1 한샘 | 2026-06-08T04:31:42Z ESG Requirement Coverage 한샘 | generated 2026-06-08T04:31:42Z This compact report shows how many rows from each ESG workbook family were matched by public evidence. Only matched rows are listed in the detailed tables. Total guide rows 278 Matched rows 142 Coverage rat…

### 레이시온 — `레이시온_esg_export_20260608_055704.pdf`

- **exists_after_import:** True
- **readability:** readable (5 pages, 9793 chars extracted)
- **ESG signal score:** 8
- **Company signal score:** 6
- **verdict:** `accept_with_warnings`
- **document type note:** ESG coverage export (not full SR body)
- **reason:** readable_esg_coverage_export_not_full_sustainability_report_body
- **preview:** Page 1 레이시온 | 2026-06-08T05:57:04Z ESG Requirement Coverage 레이시온 | generated 2026-06-08T05:57:04Z This compact report shows how many rows from each ESG workbook family were matched by public evidence. Only matched rows are listed in the detailed tables. Total guide rows 278 Matched rows 142 Coverage…

## Đánh giá

- **한샘 PDF usable cho ingest?** Có (coverage export — cần SR body riêng cho seed report-body) — `accept_with_warnings`
- **레이시온 PDF usable cho ingest?** Có (coverage export — cần SR body riêng cho seed report-body) — `accept_with_warnings`

## Kết luận

**Sẵn sàng re-ingest:**
- 한샘: `한샘_esg_export_20260608_043142.pdf` (accept_with_warnings)
- 레이시온: `레이시온_esg_export_20260608_055704.pdf` (accept_with_warnings)

**Bước kế tiếp (chưa chạy trong task này):** rerun `ingest_actual_esg_sources_v3.py` hoặc wrapper v4.2 re-ingest sau khi cập nhật discovery cho package `_sources/` mới.
