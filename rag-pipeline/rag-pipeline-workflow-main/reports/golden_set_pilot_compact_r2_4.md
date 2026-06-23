# Golden Set — Pilot Compact Hansem Round 2.4

Generated: 2026-06-11T09:49:53

## Mục tiêu pilot compact

Thiết kế pilot Hansem **ít nhưng sạch** (8–10 unit mục tiêu) để kiểm tra: tỷ lệ usable có đủ cao để mở **Silver QC pilot hạn chế** hay cần mở rộng corpus trước.

## Vì sao pilot 15 unit thất bại

- Distillation R2.2 và R2.3 đều cho **keep 6 / drop 9 / usable 6** trên pilot 15.
- Hansem eligible+conditional chỉ **16 unit**, **~15 fingerprint unique**; full corpus **40 unit**, **~37 fingerprint**.
- Pilot 15 bị **ép lấp** bằng 9–11 unit corpus tail (noise 4–17, substance thấp) → 3 duplicate, 4 insufficient, 1 ambiguous, 1 nav.
- Prompt Distillation R2.1 + validation **không** phải bottleneck.

### Phân tích pool

- `hanssem_pool_size`: 40
- `unique_body_fingerprints`: 37
- `proven_anchor_count`: 6
- `tail_corpus_only_estimate`: 21
- `duplicate_clusters`: 5
- `saturated_cluster_ids`: ['fact_report_edition', 'fact_board_esg_2021|fact_consecutive_publish_years', 'fact_8_material_issues|fact_board_esg_2021|fact_net_zero_2050', 'fact_board_esg_2021|fact_consecutive_publish_years|fact_net_zero_2050', 'fact_8_material_issues|fact_net_zero_2050']

## Logic chọn compact pilot

1. **Phase 1 — Anchor:** 6 unit proven usable từ Distillation R2.3 (không tail filler).
2. **Phase 2 — Expansion:** chỉ từ eligible/conditional; unique fingerprint + unique `duplicate_cluster_id`; substance≥14, noise≤6; **không** corpus tail fill.
3. **Hard exclude:** TOC/intro, distill-hard-block, near-dup, soft-dup, saturated fact cluster.
4. **Không** lấy 2 unit cùng cluster trừ khi proven anchor.

- Target: **8–10** unit
- Đạt được: **6** unit (anchor 6 + expansion 0)
- Fact categories covered: ['governance', 'materiality', 'metric', 'rating_recognition', 'report_publication', 'strategy']

## Danh sách unit đã chọn và vì sao

| # | record_id | pilot_source | select_reason | substance | noise | fact_categories |
|--:|-----------|--------------|---------------|----------:|------:|-----------------|
| 1 | `rec_3adad134db5cb9c2` | `proven_usable_r2_3` | `distill_r23_validated_keep` | 23 | 0 | ['materiality', 'strategy', 'governance'] |
| 2 | `rec_41a160ead0ae1be6` | `proven_usable_r2_3` | `distill_r23_validated_keep` | 22 | 6 | ['materiality', 'strategy', 'metric', 'governance', 'report_publication'] |
| 3 | `rec_5edea297fe4ab1d8` | `proven_usable_r2_3` | `distill_r23_validated_keep` | 13 | 0 | ['materiality', 'governance'] |
| 4 | `rec_2d0cf95b00a0fefc` | `proven_usable_r2_3` | `distill_r23_validated_keep` | 18 | 11 | ['materiality', 'strategy'] |
| 5 | `rec_ba9d092227fde816` | `proven_usable_r2_3` | `distill_r23_validated_keep` | 19 | 16 | ['rating_recognition', 'metric', 'governance'] |
| 6 | `rec_147089a328626757` | `proven_usable_r2_3` | `distill_r23_validated_keep` | 16 | 16 | ['rating_recognition', 'governance', 'report_publication'] |

## Kết quả distillation compact

| Chỉ số | Giá trị |
|--------|--------:|
| Input units | 6 |
| decision=keep | 5 |
| decision=drop | 1 |
| usable | 5 |
| usable / input | **83.3%** |
| usable / keep | **100.0%** |

### Drop reasons

- `ambiguous_grounding`: 1

## So sánh R2.3 15-unit vs R2.4 compact

| Metric | R2.3 (15) | R2.4 compact | Delta |
|--------|----------:|-------------:|------:|
| input | 15 | 6 | -9 |
| keep | 6 | 5 | -1 |
| usable | 6 | 5 | -1 |
| usable/input | 40.0% | 83.3% | +43.3% |
| tail filler in pilot | 11 | 0 | -11 |

- Unit bỏ khỏi R2.3: 9 tail/noisy slots

## Đánh giá

- Tỷ lệ usable/input **83.3%** và usable/keep **100.0%** — **cao hơn đáng kể** so với R2.3 (40.0%).
- **Đề xuất:** mở **Silver QC pilot hạn chế** trên 5 row (không đủ gate chính ≥8 từ pilot 15, nhưng compact đủ sạch để QC có ý nghĩa).
- Phase 2 expansion **không tìm được** unit eligible mới — pool Hansem đã bão hòa sau 6 anchor.

### Mẫu keep

- **SV2-P24-0001** (`rec_3adad134db5cb9c2`): 한샘은 ESG 경영을 위해 어떤 중대 이슈를 선정했나요?…
- **SV2-P24-0002** (`rec_41a160ead0ae1be6`): 한샘은 2050년까지 어떤 목표를 달성할 계획인가요?…
- **SV2-P24-0003** (`rec_5edea297fe4ab1d8`): 한샘은 올해 지속가능경영보고서에 어떤 보고서를 수록했나요?…
- **SV2-P24-0004** (`rec_2d0cf95b00a0fefc`): 한샘은 2025 지속가능경영보고서에서 몇 개의 중대 이슈를 선정했나요?…
- **SV2-P24-0005** (`rec_ba9d092227fde816`): 한샘은 2022년 ESG 경영 평가에서 어떤 등급을 획득했나요?…

### Mẫu drop

- **SV2-P24-0006** `ambiguous_grounding` record=`rec_147089a328626757`

## Kết luận và bước kế tiếp

**Hướng A — Mở Silver QC pilot hạn chế** trên 5 row compact (`SV2-P24-*`).

Bước kế tiếp:
1. Silver QC pilot hạn chế (không full QC, không Evol/Judge).
2. Song song lên kế hoạch mở rộng corpus Hansem để đạt gate ≥8 cho full pilot.
3. Giữ nguyên prompt Distillation R2.1.
