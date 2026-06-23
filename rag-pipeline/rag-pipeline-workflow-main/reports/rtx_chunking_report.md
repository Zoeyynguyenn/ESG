# RTX Reference Lane — Chunking Report

Generated: 2026-06-12T15:21:28

## Mục tiêu

Chunk lane `06_rtx_references_raw` thành corpus riêng cho RAG và Golden Set workbook-first.

## Input đã chunk

- PDF: **4** (`_sources/`)
- HTML: **5** (`web_sources/`)
- Fallback MD: **1** (DOJ snapshot)

## Chiến lược chunking

- Text extraction: `rag_common.load_file_text` (PDF/HTML); MD snapshot parser riêng.
- SEC HTML (`10k`, `proxy_statement`): tách theo `<h1-h3>` rồi sliding window.
- Chunk size/overlap: **900** / **150** (cùng lexical default).
- Output tách lane — không trộn `05_company_export_json`.

## Kết quả

- **Tổng chunks:** 2762
- **Tổng corpus units:** 2761

### Breakdown theo source_type

- `pdf`: 508
- `html`: 2252
- `md_fallback`: 2

### Breakdown theo document_kind

- `appendix`: 240
- `questionnaire`: 63
- `data_table`: 205
- `10k`: 1684
- `policy_page`: 24
- `proxy_statement`: 544
- `press_release`: 2

## Lưu ý

- **DOJ:** dùng **fallback snapshot `.md`** (`md_fallback`) — không có raw HTML.
- Không có file rỗng hoặc unreadable.

## Kết luận

- Sẵn sàng cho RAG: **Có**
- Sẵn sàng cho Golden Set workbook-first: **Có**
