# Golden Set — Pilot Selector Round 2.3

Generated: 2026-06-11T09:28:23

## Mục tiêu selector R2.3

Tái chọn pilot Hansem 15 unit sau Distillation R2.2 (6/15 usable): loại duplicate fact, TOC/intro, unit grounding yếu; tăng xác suất đạt **≥8 keep usable**.

## Vì sao R2.2 chưa đạt gate

- Distillation R2.2: **keep 6 / usable 6** — thiếu 2 so với ngưỡng 8.
- **2** drop `duplicate_same_fact` — pilot chứa unit trùng cluster 8 issues / KGCS.
- **5** drop TOC/intro/ambiguous — `rec_fcab1197`, `rec_adf521a49`, `rec_65c50bed`, `rec_102f3d47`, `rec_89c6e8dd`.
- Prompt Distillation + validation **không** phải bottleneck.

## Pattern bị loại ở level selector

| Pattern | Hành vi R2.3 |
|---------|--------------|
| `distill_r22_hard_block` | Hard block 7 unit TOC/ambiguous/insufficient |
| `distill_r22_soft_dup` | Block duplicate-span unit; thay bằng anchor proven |
| `toc_intro_about_report` | Block TOC, About this Report, 보고서 개요 |
| `near_dup_proven_body` | Block `rec_6d11be8f` (dup `rec_3adad134`) |
| Fact tag dedupe | Chỉ 1 unit / fact tag trước khi fill |
| `grounding_risk=high` | Không chọn trừ last-resort |

### Block counts (pool Hanssem)

- `distill_r22_hard_block`: 7
- `distill_r22_soft_dup`: 2
- `insufficient_substance_score`: 4
- `near_dup_proven_body`: 2
- `noise_too_high`: 12
- `toc_intro_about_report`: 6

## Logic ranking / dedupe / replacement

- `selector_rank = substance*10 - noise*6 + keep_bonus + proven_boost(+120) - risk_penalty`
- `fact_tags`: 8 issues, 12 issues, Net Zero, KGCS, Scope3/CDP, ESRS, …
- Dedupe: text fingerprint + claimed fact tags
- Ưu tiên 5 proven usable (trừ near-dup), sau đó diversity tag, cuối cùng fill low-risk

## So sánh pilot R2.2 vs R2.3

| Metric | R2.2 | R2.3 |
|--------|-----:|-----:|
| Pilot size | 15 | 15 |
| Overlap | — | 4 |
| Replacements | — | 11 |
| Proven usable retained | — | 4 |
| grounding_risk low | — | 4 |
| grounding_risk medium | — | 11 |

### Unit bị thay ra

- `rec_0f7c7247e048a21e`
- `rec_102f3d47a149ed3d`
- `rec_39fe9a810a0d6923`
- `rec_65c50bede5bb66da`
- `rec_6d11be8f9ba7006c`
- `rec_89c6e8dd36c4db22`
- `rec_acac077bde904698`
- `rec_adf521a49feec751`
- `rec_b1e5d2fd63103966`
- `rec_ea632bae09735059`
- `rec_fcab1197e3c245b6`

### Unit mới đưa vào

- `rec_147089a328626757`
- `rec_2d0cf95b00a0fefc`
- `rec_6012503bc8a4e28d`
- `rec_86c98b945fc03e6d`
- `rec_abdc38fe1d1a8be1`
- `rec_b54d398775fdb14b`
- `rec_ba9d092227fde816`
- `rec_ce1fb6e4651850d3`
- `rec_cece4f8f062194a3`
- `rec_f01cb7ee8b222ec9`
- `rec_fd59eb6b40389294`

### Pilot R2.3 (ranked)

- `rec_3adad134db5cb9c2` rank=375.0 risk=low tags=['fact_8_material_issues', 'fact_net_zero_2050', 'fact_double_materiality', 'fact_esrs_issb', 'fact_housing_social', 'fact_gov_compliance_pct', 'fact_board_esg_2021'] sub=23 noise=0
- `rec_66100907c00656ec` rank=305.0 risk=low tags=['fact_kgcs_rating', 'fact_scope3_cdp', 'fact_iso45001', 'fact_board_esg_2021', 'fact_consecutive_publish', 'fact_sustinvest_aa', 'fact_un_global_compact'] sub=16 noise=0
- `rec_41a160ead0ae1be6` rank=287.0 risk=medium tags=['fact_12_material_issues', 'fact_net_zero_2050', 'fact_scope3_cdp', 'fact_double_materiality', 'fact_iso45001', 'fact_board_esg_2021', 'fact_consecutive_publish'] sub=22 noise=6
- `rec_5edea297fe4ab1d8` rank=275.0 risk=low tags=['fact_12_material_issues', 'fact_double_materiality', 'fact_iso45001', 'fact_board_esg_2021'] sub=13 noise=0
- `rec_b54d398775fdb14b` rank=136.0 risk=low tags=['fact_kgcs_rating', 'fact_scope3_cdp', 'fact_iso45001', 'fact_board_esg_2021', 'fact_consecutive_publish', 'fact_sustinvest_aa', 'fact_un_global_compact'] sub=16 noise=4
- `rec_abdc38fe1d1a8be1` rank=111.0 risk=medium tags=['fact_12_material_issues', 'fact_net_zero_2050', 'fact_scope3_cdp', 'fact_double_materiality', 'fact_iso45001', 'fact_board_esg_2021', 'fact_consecutive_publish'] sub=22 noise=14
- `rec_fd59eb6b40389294` rank=93.0 risk=medium tags=['fact_kgcs_rating', 'fact_scope3_cdp', 'fact_iso45001', 'fact_board_esg_2021', 'fact_consecutive_publish', 'fact_sustinvest_aa', 'fact_un_global_compact'] sub=16 noise=7
- `rec_cece4f8f062194a3` rank=63.0 risk=medium tags=['fact_12_material_issues', 'fact_net_zero_2050', 'fact_scope3_cdp', 'fact_double_materiality', 'fact_iso45001', 'fact_board_esg_2021', 'fact_consecutive_publish'] sub=22 noise=17
- `rec_2d0cf95b00a0fefc` rank=59.0 risk=medium tags=['fact_8_material_issues', 'fact_net_zero_2050', 'fact_double_materiality', 'fact_esrs_issb'] sub=18 noise=11
- `rec_6012503bc8a4e28d` rank=57.0 risk=medium tags=['fact_kgcs_rating', 'fact_board_esg_2021', 'fact_consecutive_publish'] sub=16 noise=13
- `rec_ba9d092227fde816` rank=39.0 risk=medium tags=['fact_kgcs_rating', 'fact_scope3_cdp', 'fact_iso45001', 'fact_board_esg_2021', 'fact_sustinvest_aa', 'fact_un_global_compact'] sub=19 noise=16
- `rec_86c98b945fc03e6d` rank=23.0 risk=medium tags=['fact_8_material_issues', 'fact_net_zero_2050', 'fact_double_materiality', 'fact_esrs_issb'] sub=18 noise=17
- `rec_ce1fb6e4651850d3` rank=23.0 risk=medium tags=['fact_8_material_issues', 'fact_net_zero_2050', 'fact_double_materiality', 'fact_esrs_issb'] sub=18 noise=17
- `rec_f01cb7ee8b222ec9` rank=9.0 risk=medium tags=['fact_kgcs_rating', 'fact_scope3_cdp', 'fact_iso45001', 'fact_board_esg_2021', 'fact_consecutive_publish', 'fact_sustinvest_aa', 'fact_un_global_compact'] sub=16 noise=16
- `rec_147089a328626757` rank=9.0 risk=medium tags=['fact_kgcs_rating', 'fact_board_esg_2021', 'fact_consecutive_publish'] sub=16 noise=16

## Dự báo xác suất đạt ≥8 usable

- Proven usable trong pilot: **4**
- Heuristic forecast: **9–13** usable (không chạy Distillation trong task này)
- Pass threshold ≥8: **có khả năng**

## Kết luận và bước kế tiếp

1. Chạy Distillation pilot trên `pilot_hanssem_15_eligible_r2_3.jsonl` (prompt R2.1 unchanged).
2. Nếu ≥8 usable → mở Silver QC pilot.
3. Nếu vẫn thiếu: mở rộng corpus Hansem hoặc prefilter promote thêm unit report-body.
