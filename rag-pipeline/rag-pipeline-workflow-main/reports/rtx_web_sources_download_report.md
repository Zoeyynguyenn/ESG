# RTX Web Sources — Raw HTML Download Report

Generated: 2026-06-12

## Mục tiêu

Tải **6 URL web tham chiếu RTX** thành raw HTML local thật trong `data/rag_dataset/06_rtx_references_raw/web_sources/`, thay thế snapshot `.md` tạm.

## 6 URL đã tải

| # | URL | File local |
|---|---|---|
| 1 | SEC DEF 14A 2025 | `rtx_proxy_2025.html` |
| 2 | SEC 10-K FY2025 | `rtx_10k_2025.html` |
| 3 | SEC 10-K FY2024 | `rtx_10k_2024.html` |
| 4 | RTX Data Security & Privacy | `rtx_data_security_privacy.html` |
| 5 | RTX Ethics & Compliance | `rtx_ethics_compliance.html` |
| 6 | DOJ Raytheon resolution PR | `doj_rtx_resolution_press_release.html` |

## Kết quả từng file

| Filename | Size | Title / headline | Status |
|---|---|---|---|
| `rtx_proxy_2025.html` | 2,223,634 B | RTX Corporation - DEF 14A | **ok** |
| `rtx_10k_2025.html` | 3,685,659 B | rtx-20251231 (body: Form 10-K) | **ok** |
| `rtx_10k_2024.html` | 3,861,241 B | rtx-20241231 (body: Form 10-K) | **ok** |
| `rtx_data_security_privacy.html` | 58,399 B | Data security and privacy \| RTX | **ok** |
| `rtx_ethics_compliance.html` | 83,230 B | Ethics and Compliance \| RTX | **ok** |
| `doj_rtx_resolution_press_release.html` | — | — | **fail** (HTTP 403 Access Denied) |

**Tổng: 5/6 ok, 1 fail**

### Chi tiết fail

- DOJ `justice.gov` trả **HTTP 403** (Akamai Access Denied) từ môi trường agent, kể cả với browser User-Agent và `curl.exe`.
- File HTML 403 tạm (527 B) đã bị xóa — không lưu error page làm artifact.
- Snapshot `doj_rtx_resolution_press_release.md` **giữ lại** làm fallback.

## Snapshot `.md` đã được thay thế

| Snapshot | Thay bằng HTML | Đã xóa |
|---|---|---|
| `rtx_proxy_2025.md` | `rtx_proxy_2025.html` | Có |
| `rtx_10k_2025.md` | `rtx_10k_2025.html` | Có |
| `rtx_10k_2024.md` | `rtx_10k_2024.html` | Có |
| `rtx_data_security_privacy.md` | `rtx_data_security_privacy.html` | Có |
| `rtx_ethics_compliance.md` | `rtx_ethics_compliance.html` | Có |
| `doj_rtx_resolution_press_release.md` | — | **Không** (download fail) |

## Kết luận

- Lane RTX hiện có: **4 PDF + 5 raw HTML** (+ 1 snapshot DOJ fallback).
- **Chưa đủ hoàn chỉnh 6/6 HTML** cho chunking đồng nhất — thiếu DOJ press release HTML.
- Có thể bắt đầu chunking cho **5 nguồn HTML + 4 PDF**; DOJ cần tải thủ công hoặc qua môi trường không bị 403.
- Script tái sử dụng: `scripts/download_rtx_web_sources.py`
