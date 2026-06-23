# Golden Set — Distillation Pilot Hansem Round 2.2

Generated: 2026-06-11T09:14:01

## Mục tiêu pilot R2.2

Chạy Distillation R2.1 (prompt/guardrails không đổi) trên pilot Hansem đã pre-filter R2.2; ngưỡng pass: **≥8 keep usable** trước Silver QC.

## Input pilot

- File: `data\golden_set\v2\step1_corpus_units\pilot_hanssem_15_eligible_r2_2.jsonl`
- Số unit: **15** (`10` keep + `5` conditional)

| # | record_id | prefilter | pilot_source | substance | noise |
|---|-----------|-----------|--------------|----------:|------:|
| 1 | `rec_3adad134db5cb9c2` | `keep` | `eligible_keep_r2_2` | 23 | 0 |
| 2 | `rec_6d11be8f9ba7006c` | `conditional` | `conditional_r2_2` | 23 | 8 |
| 3 | `rec_41a160ead0ae1be6` | `conditional` | `conditional_r2_2` | 22 | 6 |
| 4 | `rec_fcab1197e3c245b6` | `keep` | `eligible_keep_r2_2` | 16 | 0 |
| 5 | `rec_66100907c00656ec` | `keep` | `eligible_keep_r2_2` | 16 | 0 |
| 6 | `rec_acac077bde904698` | `keep` | `eligible_keep_r2_2` | 16 | 0 |
| 7 | `rec_0f7c7247e048a21e` | `keep` | `eligible_keep_r2_2` | 16 | 4 |
| 8 | `rec_b1e5d2fd63103966` | `conditional` | `conditional_r2_2` | 18 | 5 |
| 9 | `rec_39fe9a810a0d6923` | `conditional` | `conditional_r2_2` | 16 | 2 |
| 10 | `rec_5edea297fe4ab1d8` | `keep` | `eligible_keep_r2_2` | 13 | 0 |
| 11 | `rec_adf521a49feec751` | `keep` | `eligible_keep_r2_2` | 12 | 0 |
| 12 | `rec_102f3d47a149ed3d` | `keep` | `eligible_keep_r2_2` | 13 | 2 |
| 13 | `rec_65c50bede5bb66da` | `keep` | `eligible_keep_r2_2` | 11 | 0 |
| 14 | `rec_89c6e8dd36c4db22` | `conditional` | `conditional_r2_2` | 16 | 7 |
| 15 | `rec_ea632bae09735059` | `keep` | `eligible_keep_r2_2` | 10 | 0 |

## Prompt / setup đã dùng

- Distillation version: `2.1.0` (prompt R2.1, không nới lỏng)
- Model: `gpt-4o-mini`
- Temperature: `0.1`
- Prompt: `reports/golden_set_distillation_prompt_round2_1.md`
- Module: `src/golden_set/step2_distill_r2_1.py`
- Output: `data\golden_set\v2\step2_silver\pilot_hanssem_15_distilled_r2_2.jsonl`

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
| `ambiguous_grounding` | 3 |
| `duplicate_same_fact` | 2 |
| `insufficient_substance / unanswerable_from_unit` | 2 |
| `nav_or_menu_noise` | 2 |

## So sánh R2.1 vs R2.2

| Metric | Pilot R2.1 | Pilot R2.2 | Delta |
|--------|----------:|----------:|------:|
| keep | 3 | 6 | +3 |
| drop | 12 | 9 | -3 |
| usable | 3 | 6 | +3 |

### Pattern đã giảm (R2.2)

- insufficient_substance drops: R2.1=8 → R2.2=2
- nav_or_menu_noise drops: R2.1=2 → R2.2=2
- keep usable: R2.1=3 → R2.2=6

### Pattern còn tồn tại

- conditional units trong keep: 2 — cần QC thủ công
- duplicate_same_fact drops: 2

## Phân tích chất lượng output

- Thiếu `ground_truth_answer` (keep): **0**
- Thiếu `evidence_span` (keep): **0**
- Thiếu `why_grounded` (keep): **0**
- Keep yếu/generic: **0**
- Keep grounding tốt: **6**
- Drop duplicate same fact: **2**
- Strong enough cho Silver QC: **6**

### Silver QC candidates (usable)

- **SV2-P22-0001** — unit `한샘_dataset_package_20260608T042739::rec_3adad134db5cb9c2` · `qualitative_strategy` · evidence_span grounded; type=qualitative_strategy; prefilter=keep
- **SV2-P22-0002** — unit `한샘_dataset_package_20260608T042739::rec_6d11be8f9ba7006c` · `quantitative_fact` · evidence_span grounded; type=quantitative_fact; prefilter=conditional
- **SV2-P22-0003** — unit `한샘_dataset_package_20260608T042739::rec_41a160ead0ae1be6` · `qualitative_strategy` · evidence_span grounded; type=qualitative_strategy; prefilter=conditional
- **SV2-P22-0005** — unit `한샘_dataset_package_20260608T042739::rec_66100907c00656ec` · `qualitative_narrative` · evidence_span grounded; type=qualitative_narrative; prefilter=keep
- **SV2-P22-0006** — unit `한샘_dataset_package_20260608T042739::rec_acac077bde904698` · `qualitative_narrative` · evidence_span grounded; type=qualitative_narrative; prefilter=keep
- **SV2-P22-0010** — unit `한샘_dataset_package_20260608T042739::rec_5edea297fe4ab1d8` · `qualitative_strategy` · evidence_span grounded; type=qualitative_strategy; prefilter=keep

### Mẫu keep

- **SV2-P22-0001** (`rec_3adad134db5cb9c2`): 한샘은 ESG 경영을 위해 어떤 중대 이슈를 선정했나요?…
- **SV2-P22-0002** (`rec_6d11be8f9ba7006c`): 한샘은 2025 지속가능경영보고서에서 몇 개의 중대 이슈를 선정했나요?…
- **SV2-P22-0003** (`rec_41a160ead0ae1be6`): 한샘은 2050년까지 어떤 목표를 달성할 계획인가요?…
- **SV2-P22-0005** (`rec_66100907c00656ec`): 한샘은 2022년 지속가능경영보고서에서 어떤 ESG 경영 성과를 보고했나요?…
- **SV2-P22-0006** (`rec_acac077bde904698`): 한샘은 2022년 ESG 경영 성과 평가에서 어떤 등급을 받았나요?…
- **SV2-P22-0010** (`rec_5edea297fe4ab1d8`): 한샘은 올해 어떤 ESG 경영 체계화를 위한 평가를 도입했나요?…

### Mẫu drop

- **SV2-P22-0004** `ambiguous_grounding` record=`rec_fcab1197e3c245b6` llm=keep note=evidence_span_not_in_unit
- **SV2-P22-0007** `duplicate_same_fact` record=`rec_0f7c7247e048a21e` llm=keep note=duplicate_evidence_span_in_batch
- **SV2-P22-0008** `insufficient_substance / unanswerable_from_unit` record=`rec_b1e5d2fd63103966` llm=drop note=None
- **SV2-P22-0009** `duplicate_same_fact` record=`rec_39fe9a810a0d6923` llm=keep note=duplicate_evidence_span_in_batch
- **SV2-P22-0011** `nav_or_menu_noise` record=`rec_adf521a49feec751` llm=drop note=None
- **SV2-P22-0012** `ambiguous_grounding` record=`rec_102f3d47a149ed3d` llm=keep note=evidence_span_not_in_unit
- **SV2-P22-0013** `nav_or_menu_noise` record=`rec_65c50bede5bb66da` llm=drop note=None
- **SV2-P22-0014** `ambiguous_grounding` record=`rec_89c6e8dd36c4db22` llm=keep note=evidence_span_not_in_unit

## Các lỗi còn lại

- rec_fcab1197e3c245b6: evidence_span_not_in_unit
- rec_0f7c7247e048a21e: duplicate_evidence_span_in_batch
- rec_39fe9a810a0d6923: duplicate_evidence_span_in_batch
- rec_102f3d47a149ed3d: evidence_span_not_in_unit
- rec_89c6e8dd36c4db22: evidence_span_not_in_unit

## Kết luận

- **Đạt ngưỡng ≥8 keep usable?** **Chưa** (6/8)
- **Đủ mở Silver QC?** **Chưa** — thiếu 2 usable so với ngưỡng pass
- **Root cause:** chủ yếu **pilot selector**, không phải prompt Distillation
  - **2 drop** `duplicate_same_fact` — pilot chứa nhiều unit cùng cluster `8 material issues` / KGCS grade (`rec_39fe9a810`, `rec_0f7c7247` trùng với `rec_3adad134`/`rec_6d11be8f`)
  - **3 drop** `ambiguous_grounding` — unit TOC/intro/news (`rec_fcab1197`, `rec_102f3d47`, `rec_89c6e8dd`) prefilter R2.2 vẫn `keep`/`conditional`
  - **2 drop** `nav_or_menu_noise` — LLM drop đúng intro/TOC (`rec_adf521a49`, `rec_65c50bed`)
  - Prompt R2.1 + post-validation: **6/6 keep đều usable**, 0 weak/generic

### Khuyến nghị trước Silver QC

1. **Pilot selector R2.3:** dedupe theo `duplicate_cluster_id` (fact family), loại TOC/About-this-report khỏi pilot.
2. Thay 4–5 unit drop bằng unit keep sạch từ pool còn lại → kỳ vọng đạt ≥8 usable mà không sửa prompt.
3. Có thể mở **Silver QC hạn chế** trên 6 candidate hiện tại song song với selector fix (không khuyến nghị làm gate chính).
