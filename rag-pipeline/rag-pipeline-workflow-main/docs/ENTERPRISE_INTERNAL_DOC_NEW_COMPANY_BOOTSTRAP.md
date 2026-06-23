# Enterprise internal-doc — New Company Bootstrap Kit

Hướng dẫn khởi tạo skeleton cho **công ty doanh nghiệp thật đầu tiên** (hoặc công ty tiếp theo) mà không phải thiết kế lại flow.

---

## Bootstrap nhanh

```bash
python scripts/bootstrap_enterprise_company.py \
  --company-id acme_corp \
  --company-label "ACME Corp"
```

Tuỳ chọn refresh capability cases sau khi đăng ký PROBE_PATHS:

```bash
python scripts/bootstrap_enterprise_company.py \
  --company-id acme_corp \
  --company-label "ACME Corp" \
  --refresh-cases
```

---

## File được tạo

| Path | Mục đích |
|---|---|
| `data/enterprise_docs/holdout_probes_{company_id}.jsonl` | Probes mẫu (3 quant) |
| `data/enterprise_docs/{company_id}/onboarding_notes.md` | Checklist nội bộ |
| `data/enterprise_docs/{company_id}/onboarding_review_{company_id}.md` | Review sau gate |
| `data/enterprise_docs/{company_id}/company_registry_stub.json` | Stub copy vào registry |
| `data/enterprise_docs/{company_id}/bootstrap_manifest.json` | Manifest + manual steps |

---

## Template có sẵn

| Template | Dùng khi |
|---|---|
| `templates/holdout_probes_template.jsonl` | Author probes mới |
| `templates/natural_capability_cases_template.jsonl` | Tham chiếu shape natural case |
| `templates/onboarding_review_template.md` | Review sau gate |

Placeholder: `{company_id}`, `{company_label}`, `{review_date}`.

---

## Bước thủ công bắt buộc (sau bootstrap)

### 1. Registry

Copy/adapt `company_registry_stub.json` → `company_doc_registry.json`:

- `corpus_artifact` trỏ corpus thật sau ingest
- `logical_documents` khớp cấu trúc tài liệu công ty

### 2. PROBE_PATHS

Thêm vào `src/enterprise_docs/crossdoc_case_builder.py`:

```python
PROBE_PATHS = {
    ...
    "acme_corp": ROOT / "data/enterprise_docs/holdout_probes_acme_corp.jsonl",
}
```

### 3. Ingest

Đặt raw files → chạy ingest path hiện có → `corpus_units.jsonl`.

### 4. Probes

Chỉnh sửa probes: câu hỏi, item, expected_signal theo tài liệu thật.

Pilot families được gate đo capability:

- `employee_headcount`
- `environment_ghg`
- `governance`

### 5. Gate

```bash
python scripts/run_enterprise_docs_natural_onboarding_gate.py
```

### 6. Review

Điền `onboarding_review_{company_id}.md` theo failure_mode.

---

## File cần có trước khi chạy gate

1. `corpus_units.jsonl` (hoặc reingested/filtered artifact)
2. `company_doc_registry.json` — block company
3. `holdout_probes_{company_id}.jsonl`
4. `PROBE_PATHS` registered
5. `crossdoc_capability_cases.jsonl` refreshed (constructed + natural)

---

## Phân loại kết quả

### corpus_limited

- **Dấu hiệu:** `corpus_limited_rate` cao; failure_mode `corpus_limited_*`
- **Ý nghĩa:** Corpus chưa đủ overlap hoặc chưa retrieve được candidate
- **Hành động:** Thêm tài liệu / map logical doc — **không** harden pipeline lõi

### system_gap

- **Dấu hiệu:** `system_gap_rate` > 0; có candidate nhưng extraction/fusion fail
- **Ý nghĩa:** Gap capability thật trên family
- **Hành động:** Mở `metric_equivalence_registry` / cross_role patterns đúng family

---

## Trạng thái lane sau bootstrap kit

| Thành phần | Trạng thái |
|---|---|
| Constructed regression gate | PASS 100% — CI chuẩn |
| Natural onboarding path | `ready_for_natural_plug_in` |
| Bootstrap kit | Đủ SOP + template + script |
| Chờ | Dữ liệu doanh nghiệp thật |

---

## Nếu dữ liệu thật chưa tới

- Giữ constructed gate làm CI
- Dry-run SOP trên `hanssem` / `musinsa`
- **Không** mở LangGraph, synthesis, hoặc harden lõi thêm
- **Không** chase natural demo score trên holdout hiện tại

---

## Liên kết

- Runbook đầy đủ: `docs/ENTERPRISE_INTERNAL_DOC_OPERATIONAL_RUNBOOK.md`
- Onboarding gate: `docs/ENTERPRISE_INTERNAL_DOC_NATURAL_CASE_ONBOARDING.md`
- Schema: `data/enterprise_docs/natural_capability_case_schema.json`
