# Thư mục `reports/`

## Giữ trên Git (chốt / gate / vận hành)

| Nhóm | File ví dụ |
|---|---|
| **C2** | `c2-gpu-benchmark-summary.md`, `c2-runpod-huong-dan-lam-theo.md`, `c2-tham-khao-*.md`, `benchmark_exportjson_c2_gpu_e2e_*` |
| **OpenAI baseline** | `openai_e2e_answerable_ko_rerun_report.md`, `benchmark_exportjson_openai_e2e_*` |
| **Chốt pipeline** | `bao-cao-11-*`, `bao-cao-12-*` |
| **Preflight** | `openai_connectivity_preflight.json`, `openai_connectivity_preflight.md` (bản canonical) |

## Tùy chọn commit

- `benchmark_exportjson_openai_phase3_summary.md` (production gate)
- `benchmark_exportjson_phase1_summary.md`, `phase3_summary.md` (tóm tắt, không cần CSV)
- `openai_benchmark_bias_audit.md`, `benchmark_best_practice_adoption.md`

## Đã chuyển `_archive/` (local, không push)

CSV/audit cũ phase 1–3, `model_candidate_*`, reranker diagnostic, recovery audit, v.v.  
Xem `reports/_archive/` — thư mục trong `.gitignore`.

## Không commit (`.gitignore`)

- `*.html`, `*.pdf`, `*.log`
- `reports/_archive/`, `reports/_tmp_*`

## Dataset mới — so OpenAI vs C2

Tạo báo cáo mới cạnh file cũ; không ghi đè gate PASS cũ trừ khi có chủ đích.  
Quy trình: `docs/DATASET_MOI_OPENAI_VA_C2.md`.
