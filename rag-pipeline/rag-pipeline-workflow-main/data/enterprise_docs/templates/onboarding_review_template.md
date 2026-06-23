# Onboarding review — {company_id}

Ngày review: {review_date}
Reviewer: {reviewer}
Artifact gate: `reports/enterprise_docs_natural_onboarding_gate_{gate_timestamp}/`

## 1. Tóm tắt gate

| Gate | Kết quả |
|---|---|
| Constructed regression | PASS / FAIL |
| Natural case count | |
| candidate_found_rate | |
| corpus_limited_rate | |
| system_gap_rate | |

## 2. Phân loại theo failure_mode

| failure_mode | Số case | Case IDs |
|---|---:|---|
| corpus_limited_no_candidate | | |
| corpus_limited_single_logical_doc | | |
| system_gap | | |
| passed | | |

## 3. Quyết định vận hành

- [ ] **corpus_limited** — bổ sung tài liệu / logical-doc overlap; **không** mở hardening pipeline lõi
- [ ] **system_gap** — mở rộng registry/equivalence/extraction đúng `family_id`
- [ ] **parser fail** — quay lại parser lane (format-specific)
- [ ] **natural pass tốt** — sẵn sàng chuyển structured output sang báo cáo tiếp theo

## 4. Ghi chú

{notes}

## 5. Bước tiếp theo

{next_actions}
