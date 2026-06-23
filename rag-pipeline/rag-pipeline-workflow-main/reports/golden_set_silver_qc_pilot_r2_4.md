# Golden Set — Silver QC Pilot R2.4 (Hạn chế)

Generated: 2026-06-11T09:53:53

## Mục tiêu QC pilot hạn chế

Kiểm tra 5 silver row usable từ compact pilot R2.4 trước khi cân nhắc **gold pilot mini-set**.
Đây **không** phải gate production / full Silver QC.

## Input gồm 5 row

| silver_id | record_id | question_type | pilot_source |
|-----------|-----------|---------------|--------------|
| `SV2-P24-0001` | `rec_3adad134db5cb9c2` | `qualitative_strategy` | `proven_usable_r2_3` |
| `SV2-P24-0002` | `rec_41a160ead0ae1be6` | `qualitative_strategy` | `proven_usable_r2_3` |
| `SV2-P24-0003` | `rec_5edea297fe4ab1d8` | `qualitative_narrative` | `proven_usable_r2_3` |
| `SV2-P24-0004` | `rec_2d0cf95b00a0fefc` | `quantitative_fact` | `proven_usable_r2_3` |
| `SV2-P24-0005` | `rec_ba9d092227fde816` | `quantitative_fact` | `proven_usable_r2_3` |

File input: `data/golden_set/v2/step4_silver_qc/pilot_hanssem_5_usable_for_qc_r2_4.jsonl`

## Rubric QC đã áp

Theo `reports/golden_set_method_round2.md` (3 trục pass/partial/fail), rule-based pilot:

| Trục | Tiêu chí chính |
|------|----------------|
| **Faithfulness** | `evidence_span` ∈ unit text; answer grounded trong span |
| **Answer Relevancy** | Câu hỏi đặc hiệu, có company, không generic/weak |
| **Groundedness** | Record ESG primary; không nav/listing; news chrome → partial |
| **Duplicate** | Cùng `evidence_span` fingerprint hoặc fact cluster `8개 중대 이슈` trong batch |

Quyết định: `pass` = 3 trục pass + không duplicate; `revise` = partial/duplicate; `reject` = any fail.

## Kết quả từng row

| silver_id | qc_decision | faithfulness | relevancy | groundedness | dup | promotion |
|-----------|-------------|--------------|-----------|--------------|-----|-----------|
| `SV2-P24-0001` | **revise** | pass | pass | pass | True | no |
| `SV2-P24-0002` | **revise** | pass | pass | partial | False | no |
| `SV2-P24-0003` | **pass** | pass | pass | pass | False | yes |
| `SV2-P24-0004` | **revise** | pass | pass | partial | True | no |
| `SV2-P24-0005` | **revise** | pass | pass | partial | False | no |

### Chi tiết review

#### SV2-P24-0001 — `rec_3adad134db5cb9c2`

- **qc_decision:** `revise` — duplicate_same_fact_cluster_in_batch
- **question:** 한샘은 ESG 경영을 위해 어떤 중대 이슈를 선정했나요?…
- **review_notes:** Trùng fact cluster với row khác trong batch (8개 중대 이슈). Giữ 1 row/batch cho fact cluster; cân nhắc giữ bản quantitative (0004) hoặc narrative (0001).

#### SV2-P24-0002 — `rec_41a160ead0ae1be6`

- **qc_decision:** `revise` — single_partial_rubric_score
- **question:** 한샘은 2050년까지 어떤 목표를 달성할 계획인가요?…
- **review_notes:** Unit có news chrome; evidence_span vẫn grounded.

#### SV2-P24-0003 — `rec_5edea297fe4ab1d8`

- **qc_decision:** `pass` — all_rubric_pass_no_duplicate
- **question:** 한샘은 올해 지속가능경영보고서에 어떤 보고서를 수록했나요?…
- **review_notes:** Sẵn sàng promote gold pilot mini-set.

#### SV2-P24-0004 — `rec_2d0cf95b00a0fefc`

- **qc_decision:** `revise` — duplicate_same_fact_cluster_in_batch
- **question:** 한샘은 2025 지속가능경영보고서에서 몇 개의 중대 이슈를 선정했나요?…
- **review_notes:** Trùng fact cluster với row khác trong batch (8개 중대 이슈). Unit có news chrome; evidence_span vẫn grounded. Giữ 1 row/batch cho fact cluster; cân nhắc giữ bản quantitative (0004) hoặc narrative (0001).

#### SV2-P24-0005 — `rec_ba9d092227fde816`

- **qc_decision:** `revise` — single_partial_rubric_score
- **question:** 한샘은 2022년 ESG 경영 평가에서 어떤 등급을 획득했나요?…
- **review_notes:** Unit có news chrome; evidence_span vẫn grounded.

## Tổng hợp

| Chỉ số | Giá trị |
|--------|--------:|
| pass | 1 |
| revise | 4 |
| reject | 0 |
| promotion_candidate=yes | 1 |
| duplicate_flag | 2 |

## Các lỗi còn lại

- `SV2-P24-0001`: duplicate fact cluster (8 material issues)
- `SV2-P24-0002`: news chrome trong unit (`conditional_news_mixed_but_span_grounded`)
- `SV2-P24-0004`: duplicate fact cluster (8 material issues)
- `SV2-P24-0004`: news chrome trong unit (`news_chrome_in_unit_but_span_grounded`)
- `SV2-P24-0005`: news chrome trong unit (`news_chrome_in_unit_but_span_grounded`)

## Kết luận

- **Đủ tạo gold pilot mini-set?** **Chưa đủ** (1 row promote ngay / 5 input).
- **Bước tiếp theo:** **revise trước khi promote**.

### Promotion pilot đề xuất (ngay)

- **SV2-P24-0003** — `qualitative_narrative` — Sẵn sàng promote gold pilot mini-set.

### Cần revise trước promote

- **SV2-P24-0001** — duplicate_same_fact_cluster_in_batch: Trùng fact cluster với row khác trong batch (8개 중대 이슈). Giữ 1 row/batch cho fact cluster; cân nhắc giữ bản quantitative (0004) hoặc narrative (0001).
- **SV2-P24-0002** — single_partial_rubric_score: Unit có news chrome; evidence_span vẫn grounded.
- **SV2-P24-0004** — duplicate_same_fact_cluster_in_batch: Trùng fact cluster với row khác trong batch (8개 중대 이슈). Unit có news chrome; evidence_span vẫn grounded. Giữ 1 row/batch cho fact cluster; cân nhắc giữ bản quantitative (0004) hoặc narrative (0001).
- **SV2-P24-0005** — single_partial_rubric_score: Unit có news chrome; evidence_span vẫn grounded.

### Ghi chú chiến lược

- Gate chính `>=8 usable` vẫn **chưa đạt** — QC pilot này không thay gate production.
- Song song: mở rộng corpus Hansem để tăng unique-body pool.
