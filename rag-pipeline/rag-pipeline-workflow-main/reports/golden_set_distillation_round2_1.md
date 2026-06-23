# Golden Set ESG — Distillation Round 2.1

Generated: 2026-06-10  
Phạm vi: Thiết kế Distillation production-grade cho Cursor workflow · **không** sửa retrieval/benchmark · **không** chạy Evol/Judge ở bước này

Tham chiếu: `reports/golden_set_method_round2.md`, `reports/golden_v2_cleaning_report.md`, audit `reports/_distill_pattern_audit.json`

---

## 1. Mục tiêu Distillation Round 2.1

Tái sinh **silver sạch hơn** từ corpus unit đã lọc, với nguyên tắc:

1. **Chặn sớm** — unit noisy không được gọi LLM (pre-filter deterministic).
2. **Drop by design** — LLM được phép (và bắt buộc) trả `decision=drop` thay vì luôn sinh câu hỏi.
3. **Một unit → tối đa một silver** — tránh `duplicate same fact`.
4. **Grounding cứng** — mọi silver `keep` phải có `evidence_span` trích trực tiếp từ `text`.
5. **Giữ kiến trúc v2** — vẫn ghi `step2_silver/silver_distilled.jsonl`; chỉ thay prompt + pre-filter + schema output (implement sau).

**KPI thiết kế (ước lượng sau khi chạy):**

| Chỉ số | v2 hiện tại | Mục tiêu R2.1 |
|--------|-------------|---------------|
| Unit gọi LLM / 118 unit | 118 (100%) | ~45–60 (sau pre-filter) |
| Silver `keep` / unit gọi LLM | ~100% | ≥70% `keep` trong số eligible |
| Gold clean / silver keep (ước lượng) | 41/95 pass QC | ≥80% không cần denylist post-hoc |

---

## 2. Root cause silver bẩn ở v2

### 2.1. Prompt Distillation v2 quá mỏng

Prompt hiện tại (`src/golden_set/step2_distill.py`) chỉ yêu cầu sinh JSON `question` + `answer`, **không có**:

- `decision` / `drop_reason`
- hard constraint denylist
- `evidence_span` bắt buộc
- cấm câu hỏi nav/date-only/cross-company

→ LLM **luôn** sinh câu hỏi cho 118/118 unit; QC và clean sau mới loại.

### 2.2. Corpus unit chưa lọc đủ (Step 1)

`step1_prepare.py` chỉ loại `news` và record không có `esg_tags` / không reportish. Hệ quả:

| Vấn đề | Bằng chứng |
|--------|------------|
| TOC / menu trong chunk báo cáo | `rec_fcab1197`, `rec_65c50bed` — `TABLE OF CONTENTS`, page numbers |
| Portal nav | `rec_b54d398775fdb14b` — menu tin tức Naver (QC reject overlap 0) |
| Cross-company trong package 레이시온 | 26/40 unit có tên công ty khác (삼성전기, 여수광양항만…) |
| Listing DART / metadata | 무신사 GV2-069–074 — hỏi ngày 공시, file size |
| Vendor generic | 레이시온 GV2-050–054 — quy trình làm báo cáo, đào tạo ESG |
| Secondary news rewrite | `rec_f01cb7ee8b222ec9` — UI bài báo, không phải report body |
| Non-ESG annual marketing | `rec_38e861b93b09aaf1` — ANNUAL REPORT 2014 prologue tiếng Anh |

### 2.3. Hậu kiểm không đủ sớm

- Silver QC (step 4) bắt overlap thấp cho một số case, nhưng **95/118 vẫn pass**.
- AI SME approve 87/95 → promote Gold trước khi denylist clean loại 46/87.

**Kết luận root cause:** Distillation v2 **không từ chối** unit xấu; denylist chỉ áp **sau** Gold. Round 2.1 phải đưa 6 rule vào **pre-filter + prompt**.

---

## 3. Phân tích pattern corpus unit (v2)

Nguồn: 118 unit trong `corpus_units.jsonl`, đối chiếu 46 gold bị drop (`golden_v2_cleaning_report.md`).

### 3.1. Taxonomy đầu vào — phân loại và hành động

| Taxonomy | Mô tả | Số unit (heuristic, multi-label) | Hành động |
|----------|--------|----------------------------------|-----------|
| `primary_esg_narrative` | Đoạn thân báo cáo 지속가능경영 / Sustainability Report có nội dung ESG | 50 | **Ưu tiên keep** — Distillation chính |
| `metric_disclosure` | Có số liệu + đơn vị (%, 명, tCO2, …) | 40 | **Ưu tiên keep** — sinh `quantitative_*` |
| `governance_or_policy_statement` | 거버넌스, 윤리, 이사회, policy | 50 | **Ưu tiên keep** — sinh `qualitative_governance` |
| `risk_strategy_narrative` | 전략, 리스크, 중대성, 이해관계자, TCFD | 51 | **Ưu tiên keep** — sinh `qualitative_strategy` / `qualitative_risk` |
| `nav_or_menu_noise` | TOC nặng, 정보공개, 민원, portal menu | 35 | **Chặn pre-LLM** hoặc LLM `drop` |
| `listing_or_index_noise` | DART metadata, 접수번호, 공시일, file listing | 24 | **Chặn pre-LLM** nếu không có metric ESG |
| `date_only_disclosure` | Chủ yếu ngày tháng, không fact ESG | (subset listing) | **Chặn** — cấm hỏi "언제" trống nghĩa |
| `secondary_news_rewrite` | News UI, press rewrite, không report body | ~5 (trong QC reject) | **Chặn pre-LLM** |
| `vendor_or_training_content` | Vendor làm báo cáo, đào tạo, promotional | 10 | **Chặn pre-LLM** |
| `cross_company_mismatch` | Tên/tổ chức khác `company` package | 29 (레이시온 26) | **Chặn pre-LLM** |
| `duplicate_fact_cluster` | Nhiều silver/gold cùng fact/record | 6 gold dropped | **Dedupe post-LLM** theo `(company, evidence_span_norm)` |

### 3.2. Pattern gây silver bẩn (phải chặn)

| Pattern | Ví dụ record / GV2 | Cơ chế v2 | Fix R2.1 |
|---------|-------------------|-----------|----------|
| Portal nav | `rec_b54d398775fdb14b` | LLM hỏi "언제부터 발간" từ menu | Pre-filter `nav_or_menu_noise` |
| TOC-only chunk | `rec_65c50bede5bb66da` | Evol multi-context từ mục lục | Pre-filter TOC ratio |
| Cross-company | 레이시온 + 삼성전기 | LLM hỏi về 삼성전기 | Pre-filter tên công ty |
| DART listing | 무신사 GV2-069–074 | Hỏi ngày 공시 / file size | Pre-filter + prompt cấm `date-only` |
| Vendor generic | GV2-050–054 | Hỏi quy trình vendor | Pre-filter `vendor_or_training` |
| News chrome | `rec_f01cb7ee8b222ec9` | Answer từ UI news | Pre-filter `secondary_news_rewrite` |
| Analyst / non-ESG | `rec_5635cde14183931b` | "영업이익 67 Wbn" — không phải ESG gold | Pre-filter `source_type` / keyword Equity Research |
| Duplicate fact | GV2-078/080/085 | Cùng "어떤 ESG 리포트" | Dedupe + prompt "một fact một câu" |

### 3.3. Pattern nên giữ (ưu tiên Distillation)

| Pattern | Company | Ví dụ |
|---------|---------|-------|
| Report overview có fact cụ thể | 한샘 | `rec_ea632bae09735059` — "다섯 번째 발간" |
| ESG strategy body | 한샘 | `rec_2ac36b6aa8233480`, `rec_66100907c00656ec` |
| Metric trong report | 한샘, 무신사 | Units có `metric_disclosure` không nav |
| Governance section | 한샘 | `rec_abdc38fe1d1a8be1` — 거버넌스 / 윤리 |

**한샘:** 29/40 unit có `primary_esg_narrative`; đây là nguồn silver sạch chính (khớp 29/41 gold clean).

**무신사:** chỉ ~6 unit `primary_esg_narrative`; nhiều unit là DART/listing → cần pre-filter mạnh, giữ ~12 câu tương đương clean set.

**레이시온:** 26/40 `cross_company_mismatch` → **không gọi LLM** cho các unit này trong R2.1 trừ khi dataset được làm sạch.

### 3.4. Pattern `conditional` (cho qua có điều kiện)

| Pattern | Điều kiện cho qua | Ràng buộc Distillation |
|---------|-------------------|------------------------|
| Report intro + TOC lẫn fact | Có ≥1 câu fact ESG rõ (lần phát hành, 보고기간, GRI) **và** TOC không chiếm >40% token đầu | Chỉ hỏi fact cụ thể; `drop` nếu chỉ còn mục lục |
| `listing_or_index_noise` + `metric_disclosure` | Có số liệu ESG trong cùng chunk | Chỉ sinh câu **metric**; cấm hỏi metadata file |
| `primary_esg_narrative` + `문의처` block | Phần thân có strategy/governance | Không hỏi địa chỉ/email/홈페이지 |
| Stakeholder / materiality (정성 seed) | Narrative ≥3 câu tiếng Hàn có chủ ngữ công ty | Answer tóm tắt 1–3 câu, `evidence_span` bắt buộc |

---

## 4. Taxonomy đầu vào cho Distillation

Mỗi corpus unit sau Step 1 (và **sau pre-filter R2.1**) mang nhãn:

```json
{
  "unit_id": "한샘_dataset_package_20260608T042739::rec_ea632bae09735059",
  "company": "한샘",
  "package_name": "한샘_dataset_package_20260608T042739",
  "record_id": "rec_ea632bae09735059",
  "record_role": "company_evidence",
  "source_type": "other",
  "section_path": "Company Evidence/Environment (E)",
  "source_file": "records/company_evidence.jsonl",
  "text": "...",
  "eligibility": "eligible | blocked | conditional",
  "unit_taxonomy": ["primary_esg_narrative", "risk_strategy_narrative"],
  "block_reasons": [],
  "conditional_notes": ""
}
```

**`eligibility`:**

| Giá trị | Ý nghĩa |
|---------|---------|
| `blocked` | Không gọi LLM; ghi log `pre_filter_drop.jsonl` |
| `conditional` | Gọi LLM với flag `strict_mode=true` |
| `eligible` | Gọi LLM bình thường |

---

## 5. Pre-filter rules (trước khi gọi LLM)

Thứ tự áp dụng — **rule đầu match → block**:

| # | Rule ID | Điều kiện block | `drop_reason` |
|---|---------|-----------------|---------------|
| 1 | `PF_CROSS_COMPANY` | `text` chứa tên công ty/tổ chức khác alias của `company` (danh sách mở rộng theo package) | `cross_company_mismatch` |
| 2 | `PF_NAV_MENU` | ≥30% dòng đầu là TOC/menu HOẶC match keyword: `정보공개`, `민원`, `Table of Contents`, `지면보기`, `메뉴`, `바로가기` **và** không có metric ESG | `nav_or_menu_noise` |
| 3 | `PF_LISTING_INDEX` | Match `접수번호`, `파일 크기`, `공시`, `DART` listing **và** không có `metric_disclosure` | `listing_or_index_noise` |
| 4 | `PF_DATE_ONLY` | ≥3 token ngày tháng, <40 cụm Hàn 4+ ký tự, không số metric | `date_only_disclosure` |
| 5 | `PF_VENDOR_TRAINING` | Match `제작 과정`, `제작 교육`, `업체`, `검증 대응 교육`, `배포` (vendor context) | `vendor_or_training_content` |
| 6 | `PF_SECONDARY_NEWS` | `source_type=news` HOẶC UI news (`뉴스 듣기`, `기사 공유`, `네이버 채널`) | `secondary_news_rewrite` |
| 7 | `PF_ANALYST_NON_ESG` | `Equity Research`, `Target price`, `Analysts who prepared` | `non_esg_financial_research` |
| 8 | `PF_TOO_SHORT` | `len(text.strip()) < 200` hoặc không có câu Hàn/ESG substantive | `insufficient_substance` |
| 9 | `PF_LEGACY_ANNUAL` | `ANNUAL REPORT` + không có `지속가능` / `Sustainability` trong 500 ký tự đầu | `non_esg_annual_report` |

**Alias công ty (ví dụ PF_CROSS_COMPANY cho `레이시온`):** 삼성전기, 여수광양항만, 현대트랜시스, 기아, 에이피알, 공사는, … — maintain trong config, không hard-code trong prompt.

**Ước lượng sau pre-filter:** ~50–65 unit `eligible`/`conditional` (từ 118); 레이시온 giảm mạnh.

---

## 6. Prompt design cho Distillation

### 6.1. Tổng quan

- **System + User** message (OpenAI chat).
- Temperature **0.1** (thấp hơn v2 `0.2`).
- Model đề xuất: `gpt-4o-mini` (giữ như v2) hoặc `gpt-4o` cho pilot 10 unit.
- Prompt đầy đủ: `reports/golden_set_distillation_prompt_round2_1.md`

### 6.2. Khác biệt so với v2

| Khía cạnh | v2 | R2.1 |
|-----------|-----|------|
| Output | Luôn Q+A | `decision` keep/drop |
| Drop | Không có | `drop_reason` bắt buộc khi drop |
| Evidence | `context_excerpt` post-hoc | `evidence_span` + `why_grounded` bắt buộc khi keep |
| Ngôn ngữ | KO | KO (giữ) |
| Denylist | Không | Hard constraints trong prompt |
| Question type | Mặc định `simple` | Enum có kiểm soát |
| Một unit | Một silver | Một silver hoặc drop |

---

## 7. Output schema cho silver row

### 7.1. LLM raw output (một lần gọi / unit)

```json
{
  "decision": "keep",
  "drop_reason": null,
  "question": "㈜한샘의 지속가능경영 보고서는 몇 번째 발간되는 것인가요?",
  "ground_truth_answer": "다섯 번째 발간하는 지속가능경영 보고서입니다.",
  "question_type": "quantitative_fact",
  "difficulty": "easy",
  "evidence_span": "해당 보고서는 ㈜한샘이 다섯 번째 발간하는 지속가능경영 보고서입니다.",
  "why_grounded": "Câu trả lời trích nguyên văn một mệnh đề trong unit; không thêm số liệu ngoài span."
}
```

Khi `decision=drop`:

```json
{
  "decision": "drop",
  "drop_reason": "nav_or_menu_noise",
  "question": null,
  "ground_truth_answer": null,
  "question_type": null,
  "difficulty": null,
  "evidence_span": null,
  "why_grounded": null
}
```

### 7.2. Silver row trong `silver_distilled.jsonl` (pipeline v2 tương thích)

```json
{
  "silver_id": "SV2-D2-0001",
  "pipeline_stage": "silver_distilled",
  "distillation_version": "2.1.0",
  "decision": "keep",
  "drop_reason": null,
  "question": "...",
  "ground_truth_answer": "...",
  "ground_truth_context_ids": ["한샘_dataset_package_20260608T042739::rec_ea632bae09735059"],
  "ground_truth_record_id": "rec_ea632bae09735059",
  "question_type": "quantitative_fact",
  "difficulty": "easy",
  "company": "한샘",
  "package_name": "한샘_dataset_package_20260608T042739",
  "gri_code": "",
  "evidence_span": "...",
  "why_grounded": "...",
  "context_excerpt": "...",
  "source_file": "records/company_evidence.jsonl",
  "pre_filter_eligibility": "eligible",
  "unit_taxonomy": ["primary_esg_narrative"]
}
```

**Ghi chú:** Row `decision=drop` có thể ghi vào `step2_silver/silver_distilled_dropped.jsonl` (artifact mới, không thay đổi contract step 3–6).

### 7.3. `question_type` enum (R2.1)

| Giá trị | Nguồn taxonomy |
|---------|----------------|
| `quantitative_fact` | 정량 |
| `quantitative_metric` | 정량 |
| `qualitative_strategy` | 정성 — Strategy |
| `qualitative_governance` | 정성 — Governance |
| `qualitative_risk` | 정성 — Risk |
| `qualitative_narrative` | 정성 — Metrics (định tính) |
| `simple` | Fallback fact ngắn |

---

## 8. Acceptance criteria cho silver (`keep`)

Một silver row **chấp nhận** khi **tất cả** điều kiện sau đúng:

| # | Tiêu chí | Cách kiểm |
|---|----------|-----------|
| AC-1 | `decision=keep` | Schema |
| AC-2 | `question` và `ground_truth_answer` tiếng Hàn (KO) | Regex / heuristic |
| AC-3 | `len(question) ≥ 15`, `len(answer) ≥ 8` | Code |
| AC-4 | `evidence_span` là substring của `text` (sau normalize whitespace) | Code — **bắt buộc** |
| AC-5 | CJK bigram overlap(answer, evidence_span) ≥ 0.25 | Code (reuse step4) |
| AC-6 | `drop_reason` null | Schema |
| AC-7 | Không match denylist 6 rule trên question+answer | Code + keyword |
| AC-8 | `question` chứa tên `company` hoặc đại từ rõ ràng chỉ công ty | LLM + heuristic |
| AC-9 | Không trùng `(company, normalize(evidence_span))` với silver đã keep | Dedupe registry |
| AC-10 | `question_type` khớp nội dung (metric hỏi phải có số trong answer nếu type quantitative_*) | Heuristic |

**Reject sau Distillation (không vào step 3):** fail bất kỳ AC → chuyển `decision` thành `drop` programmatic với `drop_reason=post_distill_validation_failed`.

---

## 9. Bảng `drop_reason` taxonomy

| `drop_reason` | Giai đoạn | Mô tả | Map denylist 6 rule |
|---------------|-----------|--------|---------------------|
| `cross_company_mismatch` | pre-filter / LLM | Nội dung về công ty khác | ✓ company mismatch |
| `nav_or_menu_noise` | pre-filter / LLM | Menu, TOC, portal, lookup | ✓ nav/menu |
| `listing_or_index_noise` | pre-filter / LLM | Index file, DART listing | ✓ listing/index |
| `date_only_disclosure` | pre-filter / LLM | Chỉ ngày tháng, không ESG fact | ✓ date-only |
| `vendor_or_training_content` | pre-filter / LLM | Vendor, đào tạo, promotional | ✓ secondary/vendor |
| `duplicate_same_fact` | post-dedupe | Trùng evidence_span với silver đã có | ✓ duplicate |
| `secondary_news_rewrite` | pre-filter | News UI / rewrite | (mở rộng) |
| `non_esg_financial_research` | pre-filter | Báo cáo phân tích tài chính | (mở rộng) |
| `non_esg_annual_report` | pre-filter | Annual report không ESG | (mở rộng) |
| `insufficient_substance` | pre-filter | Chunk quá ngắn / không substantive | — |
| `unanswerable_from_unit` | LLM | LLM không tìm được fact grounded | — |
| `ambiguous_grounding` | LLM | Fact mơ hồ, không trích span được | — |
| `question_answer_type_mismatch` | post-validation | Hỏi "ý nghĩa" nhưng answer chỉ date | ✓ (related) |
| `post_distill_validation_failed` | post-validation | Fail AC-1..AC-10 | — |

---

## 10. Checklist reviewer — audit nhanh silver output

Dùng cho SME / engineer review mẫu 10–20 row sau pilot Distillation R2.1:

| # | Câu hỏi audit | Pass? |
|---|---------------|-------|
| R1 | `evidence_span` có xuất hiện nguyên văn (hoặc gần nguyên văn) trong `text` unit không? | ☐ |
| R2 | Câu hỏi có thể trả lời **chỉ** từ unit này, không cần record khác? | ☐ |
| R3 | Có phải câu hỏi nav/menu ("어디서 확인", "정보공개제도") không? | ☐ |
| R4 | Có phải câu hỏi chỉ hỏi ngày tháng / 공시 metadata không? | ☐ |
| R5 | `company` trong metadata có khớp chủ thể câu hỏi/answer không? | ☐ |
| R6 | Answer có thêm số/chỉ tiêu không có trong `evidence_span` không? | ☐ |
| R7 | Có trùng fact với silver khác cùng company không? | ☐ |
| R8 | `question_type` có phù hợp (metric vs narrative)? | ☐ |
| R9 | Với 무신사/레이시온: record có phải sustainability body thật không? | ☐ |
| R10 | Nếu `drop` — `drop_reason` có đúng nhãn taxonomy không? | ☐ |

**Ngưỡng pilot:** ≥8/10 checklist pass trên mẫu 20 row `keep` → mở rộng full corpus eligible.

---

## 11. Những gì chưa làm ở bước này

| Hạng mục | Lý do |
|----------|--------|
| Sửa `step2_distill.py` / chạy pipeline | Chỉ thiết kế; implement ở bước sau |
| Sửa `step1_prepare.py` pre-filter code | Tách artifact `corpus_units_eligible.jsonl` ở bước implement |
| Evol-Instruct (step 3) | Ngoài scope user |
| LLM-as-a-judge (step 5) | Ngoài scope user |
| Benchmark / retrieval | Ràng buộc |
| Làm sạch dataset 레이시온 gốc | Phụ thuộc team Dataset; R2.1 chặn bằng pre-filter |

---

## 12. Đề xuất bước kế tiếp

1. **Implement pre-filter** — script `scripts/prefilter_corpus_units_r2_1.py` → `step1_corpus_units/corpus_units_eligible.jsonl` + `pre_filter_drop.jsonl`.
2. **Gắn prompt R2.1** vào `step2_distill.py` (hoặc config YAML `distillation_prompt_version: 2.1`).
3. **Pilot** `--limit 15` trên 한샘 eligible units; audit bằng checklist §10.
4. **Post-validation** AC-1..AC-10 trong code step 2.
5. **Full run** step 2 trên eligible corpus → so sánh số lượng / mẫu với `golden_set_clean.jsonl` (41 câu).
6. **Sau khi silver ổn:** mới mở Silver QC (step 4) và cân nhắc Evol/Judge.

---

## Phụ lục: Thống kê audit v2

Từ `reports/_distill_pattern_audit.json`:

```
unit_count: 118 (한샘 40, 레이시온 40, 무신사 38)
tag_counts: primary_esg_narrative 50, cross_company_mismatch 29, nav_or_menu_noise 35
dirty_gold: 46 dropped — cross_company 14, nav 11, listing/date 8, vendor 5, duplicate 6
pre_filter_block (heuristic): 47 unit không nên gọi LLM nếu không có primary_esg
```
