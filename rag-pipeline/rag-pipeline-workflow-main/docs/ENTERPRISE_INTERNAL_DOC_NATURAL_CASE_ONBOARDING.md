# Enterprise internal-doc — Natural-case onboarding

Lane `enterprise internal-doc`, ưu tiên `document → structured ESG data`.

## Trạng thái

Sau vòng **fusion equivalence hardening**, constructed suite đạt 100% trên các lớp capability core. Vòng **natural-case onboarding gate** đóng gói regression harness thành path plug-in-ready cho tài liệu doanh nghiệp thật.

## Mục tiêu

- **Không rebuild** pipeline lõi (extraction → equivalence → fusion → conflict → promotion).
- **Không mở** LangGraph runtime / synthesis.
- Khi có tài liệu thật: ingest → probes → natural cases → chạy gate → đọc báo cáo theo lớp.

## Artifact chính

Chạy:

```bash
python scripts/run_enterprise_docs_natural_onboarding_gate.py
```

Output: `reports/enterprise_docs_natural_onboarding_gate_<timestamp>/`

| File | Nội dung |
|---|---|
| `summary.json` | Metrics + gate pass/fail |
| `gate_definition.json` | Draft acceptance thresholds |
| `case_schema.json` | Schema natural vs constructed |
| `onboarding_flow.md` | Flow 5 bước cho team |
| `report.md` | 6 câu trả lời bắt buộc + layer breakdown |

## Schema natural case

Canonical schema: `data/enterprise_docs/natural_capability_case_schema.json`

Trường tối thiểu cho natural case:

- `case_id`, `case_origin=natural`, `company_id`, `family_id`
- `test_type=natural_holdout_probe`
- `probe` (embedded holdout probe: `probe_id`, `question`, `item`, `pattern_family`, `expected_signal`)

Trường tùy chọn (không đụng pipeline lõi):

- `logical_docs`, `expected_outcome_class`, `expected_canonical_value`
- `expected_conflict_status`, `readiness_expectation`

## Code modules

| Module | Vai trò |
|---|---|
| `src/enterprise_docs/capability_gate_runner.py` | Chạy benchmark + evaluate gate theo layer |
| `src/enterprise_docs/natural_case_onboarding.py` | Build/validate natural cases, onboarding orchestration |
| `src/enterprise_docs/crossdoc_capability_benchmark.py` | Harness đánh giá case (reuse, không fork) |

## Flow onboarding (ngắn nhất)

1. **Ingest** — corpus + logical_doc map qua ingest hiện có.
2. **Probes** — `data/enterprise_docs/holdout_probes_{company_id}.jsonl`.
3. **Natural cases** — `natural_case_from_probe()` hoặc refresh `crossdoc_capability_cases.jsonl`.
4. **Gate** — `run_enterprise_docs_natural_onboarding_gate.py`.
5. **Review** — `corpus_limited` vs `system_gap` trong natural diagnostics.

## Hai loại gate

### Constructed regression (bắt buộc pass)

| Layer | Metric | Minimum |
|---|---|---|
| extraction | `cross_role_extraction_alignment_rate` | 1.0 |
| equivalence | `cross_doc_equivalence_match_rate` | 1.0 |
| fusion | `evidence_fusion_success_rate` | 1.0 |
| conflict | `conflict_classification_accuracy` | 1.0 |
| promotion | `single_source_to_multi_source_promotion_rate` | 1.0, `ghost_pass_count=0` |

### Natural onboarding (draft, informational)

- `candidate_found_rate` ≥ 0.3 (draft)
- `system_gap_rate` ≤ 0.2 (draft)
- `corpus_limited_rate` — chấp nhận cao khi corpus chưa overlap; không dùng làm fail CI

## Phụ thuộc demo còn lại

- Holdout corpus `hanssem` / `musinsa` cho natural probes hiện tại.
- Constructed `source_units` synthetic — chỉ phục vụ regression, không thay corpus thật.
- `PROBE_PATHS` hardcoded — mở rộng bằng thêm file JSONL + company_id.

## Bước tiếp theo

Onboard công ty thật đầu tiên qua flow trên; chỉ mở registry/equivalence khi natural báo `system_gap`, không khi chỉ `corpus_limited`.
