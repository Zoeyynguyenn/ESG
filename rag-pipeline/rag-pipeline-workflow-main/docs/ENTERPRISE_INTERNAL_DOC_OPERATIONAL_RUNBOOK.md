# Enterprise internal-doc - Operational Runbook (SOP)

Lane `enterprise internal-doc`, uu tien bai toan `document -> structured ESG data`.

**Trang thai lane:** `done_until_real_data`

## Muc tieu

- Onboard tai lieu doanh nghiep that vao pipeline ma khong can rebuild loi he thong
- Phan loai ro `corpus_limited` va `system_gap`
- Duy tri constructed regression gate on dinh truoc khi mo rong natural cases

## Flow van hanh 7 buoc

| # | Buoc | Output |
|---|---|---|
| 1 | Ingest | `data/enterprise_docs/{company_id}/corpus_units.jsonl` |
| 2 | Map logical docs | Block trong `company_doc_registry.json` |
| 3 | Tao probes | `holdout_probes_{company_id}.jsonl` |
| 4 | Build natural cases | Rows trong `crossdoc_capability_cases.jsonl` |
| 5 | Chay onboarding gate | `reports/enterprise_docs_natural_onboarding_gate_<ts>/` |
| 6 | Classify failure | `corpus_limited` vs `system_gap` |
| 7 | Decide next action | `onboarding_review_{company_id}.md` |

## Generated corpus note

Nhung file sau la generated artifacts lon, khong phai source-of-truth va khong can commit vao git:

- `corpus_units_reingested.jsonl`
- `corpus_units_filtered.jsonl`
- `corpus_units_family_scoped.jsonl`
- `corpus_units_overlap_ready.jsonl`

Neu thieu cac file nay sau khi pull repo, can rebuild truoc khi chay holdout lane:

```bash
python scripts/build_holdout_reingested_corpus.py
python scripts/build_holdout_filtered_corpus.py
```

Khong xem viec thieu cac file tren la loi code.

## Checklist 1 - Tiep nhan du lieu

- [ ] Chot `company_id` (slug ASCII)
- [ ] Thu SR/ESG report, bang so lieu, DART/XML neu co
- [ ] Liet ke logical documents du kien
- [ ] Ghi format file va nam bao cao
- [ ] Khong tune pipeline truoc khi co corpus

## Checklist 2 - Ingest

- [ ] Tao `data/enterprise_docs/{company_id}/`
- [ ] Ingest theo `ingest_profile` trong registry
- [ ] Corpus JSONL co `text` / `evidence_text` khong rong
- [ ] Re-ingest structured ESG neu can parser v1.1

## Checklist 3 - Logical-doc mapping

- [ ] Them company vao `company_doc_registry.json`
- [ ] Khai bao `logical_documents`, `path_hint`, `domains`, `role_labels`
- [ ] `corpus_artifact` tro dung file corpus
- [ ] Xac nhan overlap tiem nang giua >=2 logical docs cho cross-doc quant

## Checklist 4 - Probes

- [ ] Copy tu `templates/holdout_probes_template.jsonl`
- [ ] Uu tien `kind=quantitative`, pilot families: `employee_headcount`, `environment_ghg`, `governance`
- [ ] Moi probe co `probe_id`, `pattern_family`, `item`, `question`, `expected_signal`
- [ ] Dang ky probe path theo huong dan bootstrap

## Checklist 5 - Chay gate

```bash
python scripts/run_enterprise_docs_natural_onboarding_gate.py
```

- [ ] Constructed regression PASS
- [ ] Natural metrics chi dung cho diagnostic
- [ ] Luu artifact path vao review template

## Checklist 6 - Review ket qua

Doc `summary.json` va tach ro:

| failure_mode | Ket luan | Hanh dong |
|---|---|---|
| `corpus_limited_no_candidate` | Thieu corpus / retrieve khong ra | Bo sung tai lieu, khong harden loi |
| `corpus_limited_single_logical_doc` | Metric chi nam o 1 logical doc | Bo sung overlap corpus |
| `system_gap` | Co candidate nhung extraction/fusion fail | Mo registry/equivalence dung family |
| parser fail | Format parse chua tot | Xu ly parser lane |

## Quy tac quyet dinh

- `corpus_limited` -> khong mo hardening pipeline loi
- `system_gap` -> mo rong registry/equivalence/extraction theo `family_id`
- parser fail -> xu ly parser lane
- natural pass tot -> dua vao bao cao / structured ESG lane tiep theo

## Regression CI

Constructed suite la regression gate chuan:

- cross-role extraction
- equivalence
- fusion
- conflict
- promotion

Yeu cau: `ghost_pass_count = 0`

## Lenh tham chieu

```bash
python scripts/bootstrap_enterprise_company.py --company-id acme_corp --company-label "ACME Corp"
python scripts/run_enterprise_docs_natural_onboarding_gate.py
python scripts/run_enterprise_docs_operational_packaging.py
```

## Artifact tham chieu

| Artifact | Muc dich |
|---|---|
| `reports/enterprise_docs_natural_onboarding_gate_20260619-103432/` | Onboarding gate baseline |
| `reports/enterprise_docs_operational_packaging_20260619-104141/` | Bootstrap kit manifest |
| `docs/ENTERPRISE_INTERNAL_DOC_NEW_COMPANY_BOOTSTRAP.md` | Huong dan bootstrap chi tiet |
