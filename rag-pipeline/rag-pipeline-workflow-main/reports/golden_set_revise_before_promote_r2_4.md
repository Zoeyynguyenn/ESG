# Golden Set — Revise Before Promote R2.4

Generated: 2026-06-11T09:56:37

## Mục tiêu revise

Xử lý 4 row `revise` từ Silver QC pilot để nâng số row **promote-ready** cho gold pilot mini-set, ưu tiên chất lượng hơn số lượng.

## 4 row revise là gì

| silver_id | revise_group | qc_reason |
|-----------|--------------|-----------|
| `SV2-P24-0001` | `duplicate_cluster_conflict` | `duplicate_same_fact_cluster_in_batch` |
| `SV2-P24-0002` | `partial_grounding_but_salvageable` | `single_partial_rubric_score` |
| `SV2-P24-0004` | `duplicate_cluster_conflict` | `duplicate_same_fact_cluster_in_batch` |
| `SV2-P24-0005` | `news_chrome_partial` | `single_partial_rubric_score` |

## Chiến lược xử lý từng nhóm lỗi

### duplicate_cluster_conflict (`0001` / `0004`)

- Chỉ giữ **1** row cho fact cluster **8개 중대 이슈**.
- **Giữ `SV2-P24-0001`** (unit `rec_3adad134`, noise=0, primary body).
- **Loại `SV2-P24-0004`**: trùng fact + unit news chrome (백세경제).

### partial_grounding_but_salvageable (`0002` Net Zero)

- Rewrite câu hỏi neo năm **2023** + **탄소중립**; giữ answer/span verbatim từ unit.

### news_chrome_partial (`0005` KGCS)

- Thử rewrite Q neo **KGCS**; sau validate vẫn **không promote** vì unit noise=16 và tail unrelated.

## Kết quả từng row

| silver_id | revise_action | revised_decision | promotion | ghi chú |
|-----------|---------------|------------------|-----------|---------|
| `SV2-P24-0001` | `keep_as_duplicate_winner` | `promote_ready` | `yes` | Giữ thay 0004: unit rec_3adad134 sạch (noise=0), span ground… |
| `SV2-P24-0002` | `rewrite_question_anchor_year` | `promote_ready` | `yes` | Cứu được: thêm anchor năm 2023 + Net Zero; Q/A/span bám verb… |
| `SV2-P24-0003` | `none` | `promote_ready` | `yes` | QC pass — giữ nguyên TCFD row.… |
| `SV2-P24-0004` | `drop_duplicate_loser` | `do_not_promote` | `no` | Loại khỏi mini-set: trùng fact 8 issues với SV2-P24-0001; un… |
| `SV2-P24-0005` | `rewrite_minimal_fact_strip` | `do_not_promote` | `no` | Không promote: unit rec_ba9d092 noise=16, chrome dài + unrel… |

### Row cứu được / có điều kiện / không promote

**Cứu được (promote-ready):**
- `SV2-P24-0001` — Giữ thay 0004: unit rec_3adad134 sạch (noise=0), span grounded; 0004 trùng fact cluster và unit news
- `SV2-P24-0002` — Cứu được: thêm anchor năm 2023 + Net Zero; Q/A/span bám verbatim unit rec_41a160ead; unit conditiona
- `SV2-P24-0003` — QC pass — giữ nguyên TCFD row.

**Không promote:**

- `SV2-P24-0004` — Loại khỏi mini-set: trùng fact 8 issues với SV2-P24-0001; unit rec_2d0cf95b có news chrome (백세경제); g
- `SV2-P24-0005` — Không promote: unit rec_ba9d092 noise=16, chrome dài + unrelated tail; fact KGCS có thể dùng sau khi

## So sánh trước/sau revise

| Metric | Trước QC | Sau QC | Sau revise |
|--------|----------:|-------:|-----------:|
| promotion_candidate | 1 | 1 | **3** |
| revise row salvaged | — | — | **2** |
| duplicate dropped | — | — | **1** |

## Kết quả cuối

- **Tổng promote-ready sau revise: 3**
- IDs: `SV2-P24-0001`, `SV2-P24-0002`, `SV2-P24-0003`

## Kết luận

- **Đủ tạo gold pilot mini-set?** **Có** — 3 row sạch đủ cho mini-set thử nghiệm (không phải gate production).
- **Bước tiếp theo:** `promote mini-set` (step 6 pilot, không full promotion).

### Mini-set candidates

| silver_id | unit_id | question (revised) | recommendation |
|-----------|---------|-------------------|----------------|
| `SV2-P24-0001` | `한샘_dataset_package_20260608T042739::rec_3adad134db5cb9c2` | 한샘은 2025 지속가능경영보고서에서 이중 중대성 평가를 통해 선정한 8개 중대 이슈는 무엇인가요?… | **promote** |
| `SV2-P24-0002` | `한샘_dataset_package_20260608T042739::rec_41a160ead0ae1be6` | 한샘은 2023년 지속가능경영보고서에서 공개한 2050년 탄소중립 목표는 무엇인가요?… | **promote** |
| `SV2-P24-0003` | `한샘_dataset_package_20260608T042739::rec_5edea297fe4ab1d8` | 한샘은 올해 지속가능경영보고서에 어떤 보고서를 수록했나요?… | **promote** |
