# Golden Set — Distillation Pilot Hansem Round 2.1

Generated: 2026-06-10  
Run: `scripts/run_distill_pilot_hanssem_r2_1.py`

---

## Mục tiêu pilot

Kiểm tra Distillation R2.1 (`decision` keep/drop, `evidence_span`, post-validation) trên **15** corpus unit `한샘` đã pre-filter, trước khi mở full step 2.

---

## Input pilot

- File: `data/golden_set/v2/step1_corpus_units/pilot_hanssem_15_eligible.jsonl`
- Số unit: **15** (tất cả `prefilter_decision=keep`, chủ yếu `R8_primary_esg_narrative_keep`)

| # | record_id | prefilter_rule | Ghi chú nhanh |
|---|-----------|----------------|---------------|
| 1 | `rec_2ac36b6aa8233480` | R8 | News article + ESG body lẫn unrelated news |
| 2 | `rec_2d0cf95b00a0fefc` | R8 | News UI chrome + nội dung ESG tốt |
| 3 | `rec_6d11be8f9ba7006c` | R8 | News UI + ESRS/materiality |
| 4 | `rec_80928c7327855bfa` | R8 | Corporate site nav/menu |
| 5 | `rec_80472635b427982e` | R8 | Article URL chrome only |
| 6 | `rec_86c98b945fc03e6d` | R8 | News duplicate chrome |
| 7 | `rec_adf521a49feec751` | R8 | Report intro (About this report) |
| 8 | `rec_abdc38fe1d1a8be1` | R8 | News + Net Zero fact |
| 9 | `rec_0f7c7247e048a21e` | R8 | JSON metadata + news lead |
| 10 | `rec_770c772d010352ff` | R9 | IR portal listing |
| 11 | `rec_ce1fb6e4651850d3` | R8 | News title repeat chrome |
| 12 | `rec_39fe9a810a0d6923` | R8 | Clean excerpt — 8 material issues |
| 13 | `rec_cece4f8f062194a3` | R8 | News chrome |
| 14 | `rec_030916ba7f52fe4d` | R8 | Report archive listing |
| 15 | `rec_41a160ead0ae1be6` | R8 | Trùng fact Net Zero với #8 |

**Nhận xét input:** pilot hiện chứa nhiều unit **news rewrite / portal nav / listing** mà prefilter R8 vẫn `keep` vì có keyword `지속가능경영보고서`. Đây là nguyên nhân yield thấp.

---

## Prompt / setup đã dùng

| Tham số | Giá trị |
|---------|---------|
| Module | `src/golden_set/step2_distill_r2_1.py` |
| Prompt | `reports/golden_set_distillation_prompt_round2_1.md` |
| Model | `gpt-4o-mini` |
| Temperature | `0.1` |
| max_chars | `4000` |
| Output | `data/golden_set/v2/step2_silver/pilot_hanssem_15_distilled.jsonl` |

Post-validation code:
- `evidence_span` ⊆ unit text
- answer–span CJK overlap
- dedupe `(company, evidence_span)` trong batch
- heuristic weak/generic question

---

## Kết quả tổng quan

| Chỉ số | Giá trị |
|--------|--------:|
| Input units | 15 |
| Output rows | 15 |
| `decision=keep` | **3** |
| `decision=drop` | **12** |
| Usable (audit) | **3** |
| LLM errors | 0 |

### Breakdown `question_type` (keep)

| question_type | count |
|---------------|------:|
| `qualitative_governance` | 1 |
| `qualitative_strategy` | 1 |
| `quantitative_fact` | 1 |

### Breakdown `difficulty` (keep)

| difficulty | count |
|------------|------:|
| `easy` | 3 |

### Drop reasons

| drop_reason | count | Nguồn |
|-------------|------:|-------|
| `insufficient_substance / unanswerable_from_unit` | 8 | LLM drop |
| `nav_or_menu_noise` | 2 | LLM drop |
| `unanswerable_from_unit` | 1 | Post-validation (`generic_paraphrase`) |
| `duplicate_same_fact` | 1 | Post-validation (trùng Net Zero với SV2-P21-0008) |

### Field completeness (keep)

| Field | Thiếu |
|-------|------:|
| `ground_truth_answer` | 0 |
| `evidence_span` | 0 |
| `why_grounded` | 0 |

---

## Phân tích chất lượng output

### 3 silver usable

| silver_id | Câu hỏi (rút gọn) | Đánh giá |
|-----------|-------------------|----------|
| `SV2-P21-0001` | 2021 이사회 중심 경영 체제 | Grounding tốt; unit vẫn news-mixed |
| `SV2-P21-0008` | 2050 탄소중립 목표 | Fact rõ, span khớp |
| `SV2-P21-0012` | 이중 중대성 8개 이슈 | Fact metric tốt; unit tương đối sạch |

Cả 3 row đều có `good_grounding_keep` và pass validation.

### Pattern lỗi chính

1. **Prefilter chưa đủ cho pilot selection (root cause)**  
   - 8/15 unit bị LLM drop `insufficient_substance` — phần lớn là news chrome, nav portal, listing archive.  
   - Prefilter R8 `keep` quá rộng với keyword `지속가능경영보고서` trên article rewrite.

2. **LLM drop đúng hướng (precision cao)**  
   - Nav (`rec_80928c`, `rec_770c772d`) — LLM drop `nav_or_menu_noise`.  
   - URL-only chrome (`rec_80472635`) — drop.

3. **LLM drop có thể quá conservative**  
   - `rec_2d0cf95b00a0fefc` có đoạn ESG đủ fact (8 material issues, ESRS) nhưng LLM drop — có thể do news UI ở đầu chunk.

4. **Post-validation hoạt động**  
   - `rec_41a160ead0ae1be6`: LLM keep Net Zero nhưng bị dedupe vì trùng `rec_abdc38fe1d1a8be1`.  
   - `rec_6d11be8f9ba7006c`: LLM keep câu generic “보고서 발간” → post-validation reject.

5. **Duplicate same fact trong pilot input**  
   - Hai unit cùng fact 2050 Net Zero — cần loại ở bước chọn pilot, không chỉ dedupe sau Distillation.

6. **News-mixed keeps**  
   - 3/3 keep đến từ unit có `기자` / article chrome — vẫn dùng được nhưng retrieval có thể nhiễu nếu chunk không tách sạch.

---

## Các lỗi còn gặp

| Pattern | Số lượng | Đề xuất xử lý |
|---------|----------|----------------|
| News/article UI trong eligible pilot | ~10/15 input | **Siết prefilter R6** + chọn pilot từ unit sạch hơn |
| Portal nav / report listing | 3 input | **Siết prefilter R2** (đã drop ở LLM) |
| Trùng fact giữa pilot units | 1 cặp | **Chọn pilot** dedupe trước Distillation |
| LLM drop nội dung ESG hợp lệ (false negative) | ~1–2 | Có thể nới nhẹ prompt cho “news body có fact” — **sau** khi prefilter sạch |
| Generic “발간” questions | 1 | Giữ post-validation; không nới prompt |

---

## Đánh giá

| Câu hỏi | Kết luận |
|---------|----------|
| Đủ sạch để mở Silver QC? | **Chưa** — chỉ 3/15 usable (~20%); chưa đủ coverage cho QC có ý nghĩa |
| Siết prompt Distillation? | **Ưu tiên thấp** — prompt + post-validation đang giữ precision tốt; vấn đề chính là **input pilot bẩn** |
| Siết prefilter? | **Có — ưu tiên cao** — loại news UI, portal nav, listing archive khỏi eligible/pilot |
| Downstream QC xử lý? | QC chỉ nên chạy **sau** khi có ≥8–10 keep sạch; hiện tại QC không thay thế prefilter |

---

## Kết luận và bước kế tiếp

1. **Distillation R2.1 hoạt động đúng hướng:** keep có `evidence_span`/`why_grounded`; drop chiếm 80% trên input noisy.
2. **Bottleneck là pilot input**, không phải prompt guardrails.
3. **Bước kế tiếp hợp lý nhất: quay lại prefilter + tái chọn pilot**
   - Siết R6/R2 trên news chrome và portal listing
   - Ưu tiên unit từ `corpus_units_conditional_r2_1.jsonl` có fact rõ (vd. `rec_ea632bae`, `rec_fcab1197`) hoặc eligible không có `기자`/nav
   - Dedupe fact trước khi chọn 15 unit
4. **Sau pilot input sạch hơn (~10+ keep kỳ vọng):** mở **Silver QC** trên subset keep — vẫn chưa Evol/Judge/benchmark.
5. Chưa chạy full step 2 trên 40 eligible cho đến khi pilot pass ngưỡng chất lượng.

---

## Artifact

- Silver pilot: `data/golden_set/v2/step2_silver/pilot_hanssem_15_distilled.jsonl`
- Summary JSON: `reports/_distill_pilot_hanssem_round2_1_summary.json`
