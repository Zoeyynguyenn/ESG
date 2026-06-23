# Golden Set — Distillation Pilot Hansem Round 2.3

Generated: 2026-06-11T09:42:52

## Mục tiêu pilot R2.3

Chạy Distillation R2.1 (prompt/guardrails không đổi) trên pilot Hansem sau selector R2.3; xác nhận gate **≥8 keep usable** trước Silver QC pilot.

## Input pilot

- File: `data\golden_set\v2\step1_corpus_units\pilot_hanssem_15_eligible_r2_3.jsonl`
- Số unit: **15**
- Proven anchors (selector): **4**
- Corpus fill (selector): **11**

| # | record_id | pilot_source | grounding_risk | selector_rank |
|---|-----------|--------------|----------------|--------------:|
| 1 | `rec_3adad134db5cb9c2` | `proven_usable_r2_2` | `low` | 375.0 |
| 2 | `rec_66100907c00656ec` | `proven_usable_r2_2` | `low` | 305.0 |
| 3 | `rec_41a160ead0ae1be6` | `proven_usable_r2_2` | `medium` | 287.0 |
| 4 | `rec_5edea297fe4ab1d8` | `proven_usable_r2_2` | `low` | 275.0 |
| 5 | `rec_b54d398775fdb14b` | `corpus_fill_r2_3` | `low` | 136.0 |
| 6 | `rec_abdc38fe1d1a8be1` | `corpus_fill_r2_3` | `medium` | 111.0 |
| 7 | `rec_fd59eb6b40389294` | `corpus_fill_r2_3` | `medium` | 93.0 |
| 8 | `rec_cece4f8f062194a3` | `corpus_fill_r2_3` | `medium` | 63.0 |
| 9 | `rec_2d0cf95b00a0fefc` | `corpus_fill_r2_3` | `medium` | 59.0 |
| 10 | `rec_6012503bc8a4e28d` | `corpus_fill_r2_3` | `medium` | 57.0 |
| 11 | `rec_ba9d092227fde816` | `corpus_fill_r2_3` | `medium` | 39.0 |
| 12 | `rec_86c98b945fc03e6d` | `corpus_fill_r2_3` | `medium` | 23.0 |
| 13 | `rec_ce1fb6e4651850d3` | `corpus_fill_r2_3` | `medium` | 23.0 |
| 14 | `rec_f01cb7ee8b222ec9` | `corpus_fill_r2_3` | `medium` | 9.0 |
| 15 | `rec_147089a328626757` | `corpus_fill_r2_3` | `medium` | 9.0 |

## Prompt / setup đã dùng

- Distillation version: `2.1.0` (prompt R2.1, không nới lỏng)
- Model: `gpt-4o-mini`
- Temperature: `0.1`
- Prompt: `reports/golden_set_distillation_prompt_round2_1.md`
- Module: `src/golden_set/step2_distill_r2_1.py`
- Output: `data\golden_set\v2\step2_silver\pilot_hanssem_15_distilled_r2_3.jsonl`

## Kết quả tổng quan

| Chỉ số | Giá trị |
|--------|--------:|
| Input units | 15 |
| Output rows | 15 |
| decision=keep | 6 |
| decision=drop | 9 |
| usable (sau audit) | 6 |

### Breakdown question_type (keep)

| question_type | count |
|---------------|------:|
| `qualitative_narrative` | 2 |
| `qualitative_strategy` | 3 |
| `quantitative_fact` | 1 |

### Breakdown difficulty (keep)

| difficulty | count |
|------------|------:|
| `easy` | 4 |
| `medium` | 2 |

### Drop reasons

| drop_reason | count |
|-------------|------:|
| `ambiguous_grounding` | 1 |
| `duplicate_same_fact` | 3 |
| `insufficient_substance / unanswerable_from_unit` | 4 |
| `nav_or_menu_noise` | 1 |

## So sánh với R2.2

| Metric | R2.2 | R2.3 | Delta |
|--------|-----:|-----:|------:|
| keep | 6 | 6 | +0 |
| drop | 9 | 9 | +0 |
| usable | 6 | 6 | +0 |
| duplicate_same_fact drops | 2 | 3 |
| ambiguous_grounding drops | n/a | 1 |

### Pattern đã giảm

- keep usable: R2.2=6 → R2.3=6 (Δ+0)
- duplicate_same_fact: R2.2=2 → R2.3=3
- ambiguous_grounding: R2.2=3 → R2.3=1
- insufficient_substance: R2.2=2 → R2.3=4

### Pattern còn tồn tại

- duplicate_same_fact: 3
- ambiguous_grounding: 1

## Phân tích chất lượng output

- Thiếu `ground_truth_answer` (keep): **0**
- Thiếu `evidence_span` (keep): **0**
- Thiếu `why_grounded` (keep): **0**
- Keep weak/generic: **0**
- Keep grounding tốt: **6**
- Drop duplicate same fact: **3**
- Drop ambiguous grounding: **1**
- Silver QC ready: **6**


### Mẫu keep

- **SV2-P23-0001** (`rec_3adad134db5cb9c2`): 한샘은 ESG 경영을 위해 어떤 기준을 도입했나요?…
- **SV2-P23-0003** (`rec_41a160ead0ae1be6`): 한샘은 2050년까지 어떤 목표를 달성할 계획인가요?…
- **SV2-P23-0004** (`rec_5edea297fe4ab1d8`): 한샘은 올해 지속가능경영보고서에 어떤 보고서를 수록했나요?…
- **SV2-P23-0009** (`rec_2d0cf95b00a0fefc`): 한샘은 어떤 중대 이슈를 선정했나요?…
- **SV2-P23-0011** (`rec_ba9d092227fde816`): 한샘은 2022년 ESG 경영 평가에서 어떤 등급을 획득했나요?…
- **SV2-P23-0015** (`rec_147089a328626757`): 한샘은 2022년 지속가능경영보고서에서 어떤 ESG 경영 성과를 발표했나요?…

### Mẫu drop

- **SV2-P23-0002** `ambiguous_grounding` record=`rec_66100907c00656ec` note=evidence_span_not_in_unit
- **SV2-P23-0005** `insufficient_substance / unanswerable_from_unit` record=`rec_b54d398775fdb14b` note=None
- **SV2-P23-0006** `duplicate_same_fact` record=`rec_abdc38fe1d1a8be1` note=duplicate_evidence_span_in_batch
- **SV2-P23-0007** `insufficient_substance / unanswerable_from_unit` record=`rec_fd59eb6b40389294` note=None
- **SV2-P23-0008** `insufficient_substance / unanswerable_from_unit` record=`rec_cece4f8f062194a3` note=None
- **SV2-P23-0010** `nav_or_menu_noise` record=`rec_6012503bc8a4e28d` note=None
- **SV2-P23-0012** `duplicate_same_fact` record=`rec_86c98b945fc03e6d` note=duplicate_evidence_span_in_batch
- **SV2-P23-0013** `insufficient_substance / unanswerable_from_unit` record=`rec_ce1fb6e4651850d3` note=None
- **SV2-P23-0014** `duplicate_same_fact` record=`rec_f01cb7ee8b222ec9` note=duplicate_evidence_span_in_batch

## Các lỗi còn lại

- rec_66100907c00656ec: evidence_span_not_in_unit
- rec_abdc38fe1d1a8be1: duplicate_evidence_span_in_batch
- rec_86c98b945fc03e6d: duplicate_evidence_span_in_batch
- rec_f01cb7ee8b222ec9: duplicate_evidence_span_in_batch

## Kết luận

- **Đạt ngưỡng ≥8 keep usable?** **Chưa** (6/8)
- **Đủ mở Silver QC pilot?** **Chưa**
- **Root cause:** selector — tail corpus-fill units vẫn noisy; có thể thu pilot xuống ~10 anchor+unique
