# Golden Set — Workbook Review RTX Round 1

Generated: 2026-06-12T15:40:54

## Mục tiêu

Triage `reference_seed_candidates_rtx_v1.jsonl` (3170 rows) thành workbook reviewable hơn
trước manual review — giảm candidate inflation, không benchmark/canonical.

## Vì sao không review thẳng 3170 row

- Chỉ **11** unique `question_draft` — generic template inflation
- Nhiều row cùng cluster, khác một dòng table hoặc số liệu liền kề
- 10-K/proxy governance sections inflate yield rất nhanh

## Rule triage round 1

| Decision | Điều kiện |
|----------|-----------|
| `keep` | Fact rõ, specificity đủ, không generic yếu, anchor trong cluster |
| `rewrite` | Fact có thật; question generic hoặc table excerpt cần gọt |
| `reject` | Table residue, framework meta, governance boilerplate, generic+weak |
| `collapse_into_cluster` | Trùng fact cluster với anchor mạnh hơn |

## Kết quả tổng quan

- Total input: **3170**
- keep: **5**
- rewrite: **216**
- reject: **736**
- collapse_into_cluster: **2213**
- **Reviewable sau round 1 (keep + rewrite):** **221**

### Breakdown theo question_type (reviewable)

- `trend`: 65
- `quantitative`: 109
- `qualitative`: 47

### Breakdown theo document_kind (reviewable)

- `appendix`: 43
- `questionnaire`: 4
- `10k`: 141
- `proxy_statement`: 19
- `data_table`: 13
- `policy_page`: 1

### Breakdown theo rejection reason

- `insufficient_esg_substance`: 351
- `generic_question_weak_grounding`: 309
- `table_residue_only`: 68
- `governance_boilerplate`: 4
- `weak_grounding`: 2
- `framework_meta_only`: 2

### Breakdown theo cluster action

- `anchor`: 221
- `collapsed_variant`: 2213
- `rejected`: 736

## Ví dụ

### Table duplicate bị collapse
- `RTX-V1-Q05` cluster `RTX::FC_CLIMATE_GHG::scope_ghg::rtx_2023_esg_esgappendix_0170` — Trùng cụm với anchor RTX-V1-T05
- `RTX-V1-T09` cluster `RTX::FC_TREND_MULTIYEAR::energy_intensity::rtx_2025_cdp_rtx_corporation_questionnaire_0037` — Cap tổng 35 row cho question template
- `RTX-V1-L05` cluster `RTX::FC_CLIMATE_GHG::scope_ghg::rtx_2023_esg_esgappendix_0170` — Trùng cụm với anchor RTX-V1-T05

### Generic row được rewrite
- `RTX-V1-T01`: `How have RTX's key ESG metrics changed over time?` → `What is RTX's disclosed energy intensity (GJ per revenue)?`
- `RTX-V1-T02`: `How have RTX's key ESG metrics changed over time?` → `How has RTX's reductions|baseline|metric|starting changed across reported years?`
- `RTX-V1-T03`: `How have RTX's key ESG metrics changed over time?` → `How has RTX's decrease|elevated|ergonomic|risks changed across reported years?`

### Weak row bị reject
- `RTX-V1-T13` (`table_residue_only`): For more information, see: • 2021 ESG Report | | 3-2 | List of material topics | See ESG Report sect…
- `RTX-V1-Q121` (`table_residue_only`): | | %of executives that are women | 30.1% | 32.7% | 33.4% | | | # of executives that are women | 398…
- `RTX-V1-Q122` (`table_residue_only`): | 398 | 412 | 403 | | | %of executives that are men | 69.9% | 67.3% | 66.6% | | | # of executives th…

### Strong row được keep
- `RTX-V1-T238`: `How does RTX engage stakeholders on sustainability topics?` — In 2023, 2024 and 2025, the Company sought to engage constructively with the proponent in order to b…
- `RTX-V1-Q960`: `How does RTX engage stakeholders on sustainability topics?` — Calio: ● Presides at all meetings of the full Board ● Presides at meetings of shareowners ● Calls sp…
- `RTX-V1-L1495`: `How does RTX engage stakeholders on sustainability topics?` — ● Presides over all private sessions of the independent directors, whether regularly scheduled or ca…

## Kết luận

- Reviewable rows (keep + rewrite): **221**
- Manual review round 2 ready? **Có — đủ sạch để mở manual review round 2 (keep+rewrite workbook)**
- Flag: `manual_review_ready_flag` = **True**
