# Golden Set — Freeze Gold Core V1

Generated: 2026-06-12T14:20:28

## Mục tiêu

Freeze **gold_core_v1** từ 26 row `gold_approve` — artifact gold chính thức nhỏ nhưng usable cho 한샘 + 무신사.

## Vì sao freeze 26 approved ngay lúc này

- Core round 4 đã tách rõ approve/hold/reject.
- 26 approved đủ làm baseline gold core; 17 hold là lane mở rộng sau.
- Không chặn freeze vì hold chưa refine.

## Input approved set

**26** rows từ `golden_set_core_round4_approved.jsonl`.

## Schema final của gold core

Fields: `gold_id`, `company`, `question_type`, `question`, `ground_truth_context`,
`ground_truth_answer`, `facts_tuple`, `prohibited_claims`, `source_record_id`,
`source_file`, `fact_cluster_id`, `gold_version`, `gold_status`, `notes`.

## Kết quả

- **gold_core_v1_count:** 26

### Breakdown theo công ty

- **무신사**: 5
- **한샘**: 21

### Breakdown theo question_type

- `qualitative`: 7
- `quantitative`: 18
- `trend`: 1

### Breakdown theo fact cluster

- `FC_ESG_GOVERNANCE`: 13
- `FC_OFFLINE_RETAIL`: 1
- `FC_MATERIAL_8`: 5
- `FC_TCFD`: 2
- `FC_HUMAN_RIGHTS`: 3
- `FC_KGCS_A`: 2

## Đánh giá

- **Core gold nhỏ nhưng usable:** 26 row frozen, không inflate từ hold.
- **Hold backlog:** 17 row — refine round 5.
- **RX:** ngoài core — source-acquisition dependent.

## Kết luận

- gold_core_v1 sẵn sàng artifact chính thức? **Có — gold_core_v1 frozen, usable làm artifact chính thức core**
- Bước tiếp theo: **Refine hold round 5 (17 rows) song song eval mapping từ eval_gold_core_v1_ko.md — không benchmark trong round freeze**
