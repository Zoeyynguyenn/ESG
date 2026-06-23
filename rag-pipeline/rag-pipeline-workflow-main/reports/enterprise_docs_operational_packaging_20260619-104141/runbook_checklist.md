# Runbook checklist — Enterprise internal-doc onboarding

Lane status: **`done_until_real_data`**

## Flow vận hành (7 bước)

1. **ingest** — `ingest + corpus_units.jsonl`
2. **map_logical_docs** — `company_doc_registry.json`
3. **create_probes** — `holdout_probes_{company_id}.jsonl`
4. **build_natural_cases** — `natural_case_from_probe / crossdoc_capability_cases.jsonl`
5. **run_onboarding_gate** — `python scripts/run_enterprise_docs_natural_onboarding_gate.py`
6. **classify_failure** — `corpus_limited vs system_gap in summary.json`
7. **decide_next_action** — `onboarding_review template + DECISION_RULES`

## Checklists

### Checklist tiếp nhận dữ liệu doanh nghiệp

- [ ] Xác nhận company_id (slug ASCII, ví dụ `acme_corp`)
- [ ] Thu thập SR/ESG report, DART/XML, bảng Excel/CSV hỗ trợ
- [ ] Liệt kê logical documents (SR narrative, evidence table, governance, HR, …)
- [ ] Ghi nhận format file (.pdf/.html/.xml/.json/.csv) và năm báo cáo
- [ ] Không bắt đầu tune pipeline trước khi ingest xong

### Checklist ingest

- [ ] Tạo thư mục `data/enterprise_docs/{company_id}/`
- [ ] Chạy ingest theo profile trong `company_doc_registry.json`
- [ ] Sinh `corpus_units.jsonl` (hoặc reingested/filtered artifact theo policy)
- [ ] Kiểm tra parser: mỗi unit có `evidence_text` hoặc `text` không rỗng
- [ ] Ghi `reingest_summary.json` nếu dùng structured ESG re-ingest path

### Checklist logical-doc mapping

- [ ] Thêm company block vào `company_doc_registry.json`
- [ ] Khai báo `logical_documents` với path_hint, domains, role_labels
- [ ] Gán `corpus_artifact` trỏ tới corpus JSONL đã ingest
- [ ] Xác nhận ít nhất 2 logical docs có metric overlap cho cross-doc (nếu cần fusion)
- [ ] Review routing: holdout_routing / primary_document_ids cho quant probes

### Checklist tạo probes

- [ ] Copy template → `holdout_probes_{company_id}.jsonl`
- [ ] Ưu tiên `kind=quantitative` trong 3 pilot families
- [ ] Mỗi probe: probe_id, pattern_family, item, question, expected_signal
- [ ] Đăng ký path trong `PROBE_PATHS` (`crossdoc_case_builder.py`) hoặc dùng bootstrap manifest
- [ ] Không dùng constructed cases để đo corpus thật

### Checklist chạy gate

- [ ] Refresh natural cases: `write_capability_cases_jsonl` hoặc bootstrap merge
- [ ] Chạy `python scripts/run_enterprise_docs_natural_onboarding_gate.py`
- [ ] Constructed regression **phải PASS** (5 layers, ghost_pass=0)
- [ ] Natural metrics là diagnostic — không fail CI vì corpus_limited cao
- [ ] Lưu artifact timestamp vào onboarding review

### Checklist review corpus_limited vs system_gap

- [ ] Đọc `natural_metrics.by_failure_mode` trong summary.json
- [ ] corpus_limited_* → thiếu overlap tài liệu → bổ sung source, không harden lõi
- [ ] system_gap → registry/extraction/equivalence theo family_id
- [ ] parser empty text → parser lane, không nhầm với system_gap
- [ ] Điền `onboarding_review_{company_id}.md` từ template

## Quy tắc quyết định

### `corpus_limited`
- **Nghĩa:** Corpus thiếu metric ở >=2 logical docs hoặc không tìm thấy candidate
- **Hành động:** Bổ sung tài liệu / logical-doc map; **không** mở workstream hardening pipeline lõi
- **Không làm:** rebuild parser, rebuild retrieval, tune constructed cases

### `system_gap`
- **Nghĩa:** Corpus đủ nhưng extraction/equivalence/fusion fail trên natural case
- **Hành động:** Mở rộng `metric_equivalence_registry` / cross_role patterns đúng family_id
- **Không làm:** chase demo score, inflate multi_source metric

### `parser_fail`
- **Nghĩa:** Unit rỗng, format không parse được, evidence_text trống
- **Hành động:** Quay lại parser lane (html/xml/pdf) cho format cụ thể
- **Không làm:** đổi fusion contract, mở LangGraph

### `natural_pass`
- **Nghĩa:** Natural probes pass capability layers; fusion/promotion integrity OK
- **Hành động:** Chuyển structured ESG output sang bước báo cáo / handoff prep (không mở synthesis trial)
- **Không làm:** rebuild core pipeline

## Lệnh bootstrap công ty mới

```bash
python scripts/bootstrap_enterprise_company.py --company-id acme_corp --company-label "ACME Corp"
python scripts/run_enterprise_docs_natural_onboarding_gate.py
```