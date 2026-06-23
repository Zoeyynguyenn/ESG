# Thư mục `data/`

## Đang dùng cho OpenAI E2E + C2 (export JSON)

| Đường dẫn | Vai trò |
|---|---|
| `rag_dataset/05_company_export_json/<package>/` | Corpus company (jsonl lanes/records/splits) — **sync pod/PC**, không bắt buộc trên Git |

**Packages hiện tại (2026-06-08, 3 cty):**

| Công ty | Package |
|---|---|
| 레이시온 | `레이시온_dataset_package_20260608T055801` |
| 한샘 | `한샘_dataset_package_20260608T042739` |
| 무신사 | `무신사_dataset_package_20260608T092823` |

Registry + benchmark batch: `configs/companies_3cty_registry.yaml`, `configs/benchmark_exportjson_3cty_c2_e2e.yaml`.
| `rag_dataset/dataset_readme.md`, `sources.md`, `esg_*.md/json` | Metadata / schema tham chiếu |

**Lane benchmark:** `company_export_json_full` — config `company_filter` trỏ tới tên thư mục package.

## Legacy (học V1–V3, không cần cho C2 hiện tại)

| Đường dẫn | ~Dung lượng | Ghi chú |
|---|---:|---|
| `rag_dataset/02_esg_public_core/` | ~2.6 MB | HTML ESG public — đã bỏ khỏi Git |
| `rag_dataset/03_esg_public_complex/` | ~6.8 MB | HTML/PDF phức tạp — đã bỏ khỏi Git |
| `rag_dataset/01_synthetic_controlled/` | nhỏ | Baseline V1 — có thể giữ trên Git |
| `sample_docs/` | nhỏ | Mini RAG V1 |

Có thể **xóa local** thư mục 02/03 nếu không còn chạy benchmark matrix cũ.

## Dataset mới

1. Team Dataset đặt package mới: `05_company_export_json/<company>_dataset_package_YYYYMMDD>/`
2. Cập nhật `company_filter` + `corpus_version` trong config (xem `docs/DATASET_MOI_OPENAI_VA_C2.md`)
3. Reindex → upload cache lên pod nếu chạy C2
