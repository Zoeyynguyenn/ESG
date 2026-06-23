# Natural-case onboarding flow

Artifact: `reports/enterprise_docs_natural_onboarding_gate_20260619-103432`

## Mục tiêu

Biến capability benchmark thành onboarding gate plug-in-ready: constructed suite giữ regression CI; natural cases đo dữ liệu thật qua cùng harness.

## Flow ngắn nhất (5 bước)

1. **ingest_documents** — Ingest enterprise PDF/HTML/XML/Excel via existing enterprise_docs ingest path
   - Output: `Corpus units + logical_doc mapping for company_id`
2. **define_probes** — Author holdout probes JSONL (question, item, pattern_family, expected_signal)
   - Output: `data/enterprise_docs/holdout_probes_{company_id}.jsonl`
3. **build_natural_cases** — Run natural_case_from_probe / build_natural_cases_for_company or write_onboarding_cases_jsonl
   - Output: `Natural rows in crossdoc_capability_cases.jsonl with case_origin=natural`
4. **run_capability_gate** — scripts/run_enterprise_docs_natural_onboarding_gate.py
   - Output: `Gate report: constructed regression must pass; natural diagnostics by failure_mode`
5. **review_by_layer** — Inspect report_by_capability_layer — corpus_limited vs system_gap
   - Output: `Decision: expand corpus overlap vs extend registry/equivalence`

## Lệnh chạy gate

```bash
python scripts/run_enterprise_docs_natural_onboarding_gate.py
```

## Phân biệt case_origin

| Loại | Mục đích | Sửa pipeline lõi? |
|---|---|---|
| `constructed` | Regression capability (extraction→promotion) | Không — thêm case trong JSONL |
| `natural` | Diagnostic trên corpus thật | Không — thêm probe + natural row |

## Sau gate

Onboard công ty thật đầu tiên: ingest → probes → natural cases → gate; phân tích corpus_limited vs system_gap; mở registry/equivalence chỉ khi system_gap; giữ constructed regression làm CI gate.
