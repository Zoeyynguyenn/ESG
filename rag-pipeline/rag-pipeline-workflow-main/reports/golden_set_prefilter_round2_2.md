# Golden Set — Pre-filter Round 2.2 + Pilot Selection

Generated: 2026-06-10T18:42:04

## Mục tiêu R2.2

Siết prefilter sau pilot Distillation R2.1 (yield 3/15): loại news chrome, portal/archive, report-mention-only; chọn pilot Hansem 15 unit sạch hơn với mục tiêu Distillation **8–10 keep**.

## Vì sao pilot R2.1 fail

- R8 R2.1 `keep` nhầm khi chỉ có keyword `지속가능경영보고서` trên article rewrite / portal.
- 10/15 pilot unit có news UI, byline, portal nav, hoặc archive listing.
- LLM Distillation drop đúng 8 case `insufficient_substance` — input noisy, không phải prompt.

### Phân loại 15 unit pilot R2.1

| record_id | Distill | Vấn đề input | R2.2 pilot |
|-----------|---------|--------------|------------|
| `rec_2ac36b6aa8233480` | keep | news-mixed, trùng body với unit khác | **Loại** (text dup) |
| `rec_2d0cf95b00a0fefc` | drop | news UI chrome | **Loại** |
| `rec_6d11be8f9ba7006c` | drop | news UI + ESRS body | **Giữ** (conditional) |
| `rec_80928c7327855bfa` | drop | portal nav | **Loại** |
| `rec_80472635b427982e` | drop | URL chrome only | **Loại** |
| `rec_86c98b945fc03e6d` | drop | news duplicate chrome | **Loại** |
| `rec_adf521a49feec751` | drop | report intro / nav | **Giữ** (keep) |
| `rec_abdc38fe1d1a8be1` | keep | news + Net Zero (trùng cluster) | **Loại** |
| `rec_0f7c7247e048a21e` | drop | JSON metadata + news lead | **Giữ** (keep, noise thấp) |
| `rec_770c772d010352ff` | drop | IR portal listing | **Loại** |
| `rec_ce1fb6e4651850d3` | drop | news title repeat | **Loại** |
| `rec_39fe9a810a0d6923` | keep | excerpt 8 material issues — **strong** | **Giữ** (conditional) |
| `rec_cece4f8f062194a3` | drop | news chrome | **Loại** |
| `rec_030916ba7f52fe4d` | drop | report archive listing | **Loại** |
| `rec_41a160ead0ae1be6` | drop | duplicate Net Zero | **Giữ** (conditional, 1 slot) |

**Strong candidates R2.1:** `rec_39fe9a810a0d6923`, `rec_2ac36b6aa8233480` (body), `rec_adf521a49feec751` (intro).

## Rule siết thêm (R2.2)

| Rule | Thay đổi |
|------|----------|
| **R6** | Drop portal category menu + noise cao (`noise>=9` hoặc byline+`noise>=6`); url/json chrome |
| **R2** | Drop portal nav + archive list (`다운로드`, `국문 영문`, `보고서&자료실`) |
| **R8** | Keep chỉ khi `substance_score >= 4` và `noise_ratio < 0.75`; drop `report_mention_only` |
| **R10** | Conditional news mixed + `substance>=16`, `noise<=8` — pilot được nếu đủ substance |

## Hansem eligible trước và sau R2.2

| Metric | R2.1 | R2.2 |
|--------|-----:|-----:|
| Hansem keep | 23 | 10 |
| Pilot candidate pool | — | 25 |
| Pilot selected | 15 (R2.1) | 15 |

## Pilot selection strategy mới

- Score: `selection_priority = substance*10 - noise*5` (+20 keep, +5 conditional).
- `pilot_candidate=yes` khi keep sạch hoặc conditional có `substance >= 16`, `noise <= 8`.
- Dedupe theo text fingerprint (không loại hết unit cùng fact family).
- Bucket: ~9 primary, ~3 metric, ~2 governance.
- Supplement từ rejected (borderline): **0** unit — `substance>=14`, `noise<=7`, không portal/archive.

## So sánh pilot cũ vs mới

- Overlap record_id: **5** `['rec_0f7c7247e048a21e', 'rec_39fe9a810a0d6923', 'rec_41a160ead0ae1be6', 'rec_6d11be8f9ba7006c', 'rec_adf521a49feec751']`

### Pilot R2.1 (cũ)

- `rec_2ac36b6aa8233480`
- `rec_2d0cf95b00a0fefc`
- `rec_6d11be8f9ba7006c`
- `rec_80928c7327855bfa`
- `rec_80472635b427982e`
- `rec_86c98b945fc03e6d`
- `rec_adf521a49feec751`
- `rec_abdc38fe1d1a8be1`
- `rec_0f7c7247e048a21e`
- `rec_770c772d010352ff`
- `rec_ce1fb6e4651850d3`
- `rec_39fe9a810a0d6923`
- `rec_cece4f8f062194a3`
- `rec_030916ba7f52fe4d`
- `rec_41a160ead0ae1be6`

### Pilot R2.2 (mới)

- `rec_3adad134db5cb9c2` — keep, sub=23, noise=0, prio=250.0, cluster=`fact_8_material_issues|fact_board_esg_2021|fact_net_zero_2050`
- `rec_6d11be8f9ba7006c` — conditional, sub=23, noise=8, prio=195.0, cluster=`fact_8_material_issues|fact_board_esg_2021|fact_net_zero_2050`
- `rec_41a160ead0ae1be6` — conditional, sub=22, noise=6, prio=195.0, cluster=`fact_board_esg_2021|fact_consecutive_publish_years|fact_net_zero_2050`
- `rec_fcab1197e3c245b6` — keep, sub=16, noise=0, prio=180.0, cluster=`fact_report_edition`
- `rec_66100907c00656ec` — keep, sub=16, noise=0, prio=180.0, cluster=`fact_board_esg_2021|fact_consecutive_publish_years`
- `rec_acac077bde904698` — keep, sub=16, noise=0, prio=180.0, cluster=`fact_board_esg_2021|fact_consecutive_publish_years`
- `rec_0f7c7247e048a21e` — keep, sub=16, noise=4, prio=160.0, cluster=`fact_board_esg_2021|fact_consecutive_publish_years`
- `rec_b1e5d2fd63103966` — conditional, sub=18, noise=5, prio=160.0, cluster=`fact_8_material_issues|fact_net_zero_2050`
- `rec_39fe9a810a0d6923` — conditional, sub=16, noise=2, prio=155.0, cluster=`fact_8_material_issues|fact_net_zero_2050`
- `rec_5edea297fe4ab1d8` — keep, sub=13, noise=0, prio=150.0, cluster=`fact_board_esg_2021`
- `rec_adf521a49feec751` — keep, sub=12, noise=0, prio=140.0, cluster=`cccfcd495071`
- `rec_102f3d47a149ed3d` — keep, sub=13, noise=2, prio=140.0, cluster=`fact_board_esg_2021|fact_consecutive_publish_years`
- `rec_65c50bede5bb66da` — keep, sub=11, noise=0, prio=130.0, cluster=`fact_net_zero_2050`
- `rec_89c6e8dd36c4db22` — conditional, sub=16, noise=7, prio=130.0, cluster=`fact_board_esg_2021|fact_consecutive_publish_years`
- `rec_ea632bae09735059` — keep, sub=10, noise=0, prio=120.0, cluster=`fact_report_edition`

## Rủi ro còn lại

- Một số unit conditional (TOC mixed) vẫn có thể vào pilot — cần Distillation strict.
- Hansem pool nhỏ hơn R2.1 — có thể thiếu metric diversity.
- Chưa chạy Distillation validation trên pilot mới trong task này.

## Điều kiện sang Distillation pilot lần 2

1. Review `pilot_hanssem_15_eligible_r2_2.jsonl` — ưu tiên unit `keep` + conditional có substance cao.
2. Chạy `run_distill_pilot_hanssem_r2_1.py` (hoặc step 2 `--distill-r2-1`) với input pilot R2.2.
3. Ngưỡng pass: **>= 8 keep usable** trước khi mở Silver QC.
