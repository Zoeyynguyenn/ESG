# Golden Set ESG — Grounding Contract (Round 1)

Generated: 2026-06-10  
Phạm vi: Phân tích dữ liệu chuẩn bị Silver → Gold · **không** sửa pipeline / không benchmark

---

## Mục tiêu

Xây dựng **Grounding Contract** — bộ quy tắc “cái gì được phép đưa vào Distillation để sinh Silver” — cho bài toán Golden Set ESG hiện tại.

Contract này dựa trên:

- Workflow/state: `.rag/rag-pipeline-practice/` (`findings.md`, `progress.md`, `daily_report.md`)
- Artifact golden set: `data/golden_set/` (v1, v2, cleaning report)
- Lane dataset: `data/rag_dataset/05_company_export_json/`
- Tài liệu quy trình: `docs/golden-set-silver-to-gold-workflow.html`, `docs/GOLDEN_SET_SILVER_TO_GOLD_RUNBOOK.md`
- Báo cáo pilot: `reports/golden-set-cau-hoi-chuan-20260609.md`, `reports/golden_v2_cleaning_report.md`

**Lưu ý truy vết:** Repo không có một file duy nhất liệt kê “6 nguồn”. Danh sách dưới đây được **lập lại chuẩn** từ chuỗi artifact: 2 mẫu CSV ESG (được team cung cấp, tham chiếu ngoài workspace) + 3 company export package + 1 lane taxonomy nhúng trong package.

`TalkFile_golden_worksheet_v1.xlsx` là **mẫu workbook review SME** — hữu ích cho bước Gold, **không** phải tài liệu evidence để Distillation; không tính vào 6 nguồn grounding.

---

## Danh sách 6 tài liệu nguồn

| # | `source_id` | `file_path` (chuẩn) | Vai trò trong Silver→Gold |
|---|-------------|---------------------|---------------------------|
| 1 | `ESG-TAX-Q` | `26.03.27 ESG-정량 - 26.03.27 ESG-정량.csv` *(ngoài workspace)* | Taxonomy định lượng: GRI / SASB / K-ESG / KBIZ, 251 dòng seed câu hỏi metric |
| 2 | `ESG-TAX-QL` | `26.03.27 ESG-정성 - 26.03.27 ESG-정성.csv` *(ngoài workspace)* | Taxonomy định tính: 4 trụ Strategy / Governance / Risk / Metrics, 27 dòng seed |
| 3 | `PKG-HANSSEM-EV` | `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/records/company_evidence.jsonl` | Evidence thực tế công ty 한샘 (605 record) |
| 4 | `PKG-RAYSOLUTION-EV` | `data/rag_dataset/05_company_export_json/레이시온_dataset_package_20260608T055801/records/company_evidence.jsonl` | Evidence thực tế công ty 레이시온 (531 record) |
| 5 | `PKG-MUSINSA-EV` | `data/rag_dataset/05_company_export_json/무신사_dataset_package_20260608T092823/records/company_evidence.jsonl` | Evidence thực tế công ty 무신사 (1604 record) |
| 6 | `PKG-REQ-TAXONOMY` | `.../records/requirement_taxonomy.jsonl` *(mỗi package, 278 record)* | Taxonomy nhúng dataset: mô tả chỉ tiêu K-ESG định lượng, metadata GRI — **không** chứa giá trị công ty |

**Mirror index (RAG lane, không tính là nguồn thứ 7):** `splits/full.jsonl` trong mỗi package trùng nội dung `company_evidence.jsonl` (605 / 531 / 1604 dòng).

**Pipeline v2 hiện tại:** `step1_corpus_units` chỉ export từ `company_evidence.jsonl` (118 unit), **chưa** dùng `requirement_taxonomy.jsonl` — cần áp dụng contract này ở round Distillation tiếp theo.

---

## Phân tích từng tài liệu

### 1. `ESG-TAX-Q` — ESG-정량 (định lượng)

| Trường | Giá trị |
|--------|---------|
| `source_id` | `ESG-TAX-Q` |
| `file_path` | `26.03.27 ESG-정량 - 26.03.27 ESG-정량.csv` |
| `company` | *Không gắn 1 công ty* (taxonomy chuẩn) |
| `document_type` | ESG quantitative taxonomy template |
| `language` | ko |
| `is_primary_esg_narrative` | **no** |
| `contains_esg_metrics` | **yes** (định nghĩa metric, đơn vị, mã GRI/SASB/K-ESG) |
| `contains_navigation_noise` | **no** |
| `contains_listing_or_index_noise` | **no** |
| `contains_news_rewrite_or_secondary_reporting` | **no** |
| `suitable_for_gold_generation` | **conditional** |
| `recommended_use` | **distill_yes_with_filter** |
| `main_risks` | Không có giá trị thực tế của công ty; dùng làm seed câu hỏi dễ sinh Q&A “ảo” nếu distill trực tiếp từ CSV mà không có `company_evidence` |
| `reason` | 251 dòng seed (`영역`, `카테고리`, `항목`, `GRI`, `K-ESG`…). Phù hợp **định hướng câu hỏi** và gắn metadata; Distillation phải **neo vào PKG-*-EV** để có ground truth. |

---

### 2. `ESG-TAX-QL` — ESG-정성 (định tính)

| Trường | Giá trị |
|--------|---------|
| `source_id` | `ESG-TAX-QL` |
| `file_path` | `26.03.27 ESG-정성 - 26.03.27 ESG-정성.csv` |
| `company` | *Không gắn 1 công ty* |
| `document_type` | ESG qualitative taxonomy template |
| `language` | ko |
| `is_primary_esg_narrative` | **no** |
| `contains_esg_metrics` | **no** (mô tả / ví dụ, không phải số liệu) |
| `contains_navigation_noise` | **no** |
| `contains_listing_or_index_noise` | **no** |
| `contains_news_rewrite_or_secondary_reporting` | **no** |
| `suitable_for_gold_generation` | **conditional** |
| `recommended_use` | **distill_yes_with_filter** |
| `main_risks` | Câu hỏi định tính mơ hồ nếu không có đoạn narrative đủ dài trong báo cáo công ty |
| `reason` | 27 dòng theo 4 trụ (`전략`, `거버넌스`, `위험 관리`, `지표`). Dùng làm **khung câu hỏi**; answer phải lấy từ `sustainability_report` / narrative trong PKG-*-EV. |

---

### 3. `PKG-HANSSEM-EV` — 한샘 company evidence

| Trường | Giá trị |
|--------|---------|
| `source_id` | `PKG-HANSSEM-EV` |
| `file_path` | `data/rag_dataset/05_company_export_json/한샘_dataset_package_20260608T042739/records/company_evidence.jsonl` |
| `company` | 한샘 |
| `document_type` | Mixed company evidence bundle |
| `language` | ko (+ en fragments trong PDF) |
| `is_primary_esg_narrative` | **yes** (một phần lớn) |
| `contains_esg_metrics` | **yes** |
| `contains_navigation_noise` | **yes** (một phần `company_website`, TOC) |
| `contains_listing_or_index_noise` | **yes** (Table of Contents, index PDF) |
| `contains_news_rewrite_or_secondary_reporting` | **yes** (`news`: 175/605 ≈ 29%) |
| `suitable_for_gold_generation` | **yes** |
| `recommended_use` | **distill_yes_with_filter** |
| `main_risks` | (1) Nhiều edition báo cáo (2021–2025) → câu “lần thứ mấy” mâu thuẫn; (2) News snapshot không phải disclosure chính thức; (3) `other`+`local_downloader` lẫn annual report cũ |
| `reason` | **Nguồn sạch nhất trong 3 công ty** (`findings.md`, `golden_v2_cleaning_report`: giữ 29/29 câu gold). Có `sustainability_report` (132), `official_sustainability_report` (131 title), narrative E/S/G rõ. Distill **chỉ** `source_type ∈ {sustainability_report, governance_report}` + `title=official_sustainability_report` + `section_path` E/S/G. |

**Thống kê record (`source_type`):** news 175 · other 194 · sustainability_report 132 · annual_report 95 · governance_report 9 · text &lt;200 ký tự: 85.

---

### 4. `PKG-RAYSOLUTION-EV` — 레이시온 company evidence

| Trường | Giá trị |
|--------|---------|
| `source_id` | `PKG-RAYSOLUTION-EV` |
| `file_path` | `data/rag_dataset/05_company_export_json/레이시온_dataset_package_20260608T055801/records/company_evidence.jsonl` |
| `company` | 레이시온 (Raytheon / defense lane trong tên package) |
| `document_type` | Mixed bundle — **nhiễu cross-company nặng** |
| `language` | ko / en |
| `is_primary_esg_narrative` | **no** (đa số không phải SR của 레이시온) |
| `contains_esg_metrics` | **yes** (rải rác) |
| `contains_navigation_noise` | **yes** (cao — website cảng, 민원, 정보공개) |
| `contains_listing_or_index_noise` | **yes** |
| `contains_news_rewrite_or_secondary_reporting` | **yes** (news 328/531 ≈ 62%) |
| `suitable_for_gold_generation` | **no** |
| `recommended_use` | **exclude_from_gold** *(cho đến khi dataset team làm sạch)* |
| `main_risks` | **62 record** chứa tên công ty khác (여수광양항만공사, 삼성전기, 현대트랜시스, 기아…); `official_sustainability_report` trỏ nội dung third-party; gold v2: **0/30 câu** giữ sau cleaning |
| `reason` | `findings.md` (2026-06-09): package mismatch nội dung. Distillation đã sinh Q&A menu/nav và cross-company (`golden_v2_cleaning_report`: toàn bộ 레이시온 bị drop). |

**Thống kê:** news 328 · sustainability_report 71 · annual_report 64 · governance_report 30 · cross-company keyword hits: **62**.

---

### 5. `PKG-MUSINSA-EV` — 무신사 company evidence

| Trường | Giá trị |
|--------|---------|
| `source_id` | `PKG-MUSINSA-EV` |
| `file_path` | `data/rag_dataset/05_company_export_json/무신사_dataset_package_20260608T092823/records/company_evidence.jsonl` |
| `company` | 무신사 |
| `document_type` | Mixed — thiên về filing/listing/analyst note |
| `language` | ko |
| `is_primary_esg_narrative` | **conditional** (chỉ ~8 SR record) |
| `contains_esg_metrics` | **yes** (doanh thu, IPO metadata) |
| `contains_navigation_noise` | **yes** |
| `contains_listing_or_index_noise` | **yes** (cao: `official_annual_report` 1203/1604) |
| `contains_news_rewrite_or_secondary_reporting` | **yes** (news 226; analyst reports trong `other`) |
| `suitable_for_gold_generation` | **conditional** |
| `recommended_use` | **distill_yes_with_filter** |
| `main_risks` | Thiếu báo cáo ESG narrative đầy đủ; nhiều record là **metadata công bố** (ngày, mã, kích thước file) không phải nội dung ESG; trùng câu hỏi doanh thu |
| `reason` | `sustainability_report` chỉ **8** record. Cleaning giữ **12/28** câu. Chỉ distill từ SR + đoạn narrative E/S/G đủ dài; loại `dart_filing` snapshot ngắn và listing. |

**Thống kê:** other 1324 · news 226 · annual_report 29 · sustainability_report **8** · governance_report 17 · text &lt;200: 88.

---

### 6. `PKG-REQ-TAXONOMY` — requirement_taxonomy (mỗi package)

| Trường | Giá trị |
|--------|---------|
| `source_id` | `PKG-REQ-TAXONOMY` |
| `file_path` | `.../records/requirement_taxonomy.jsonl` (278 dòng × 3 package) |
| `company` | Gắn theo package (metadata công ty trong bundle) |
| `document_type` | K-ESG requirement / policy taxonomy row |
| `language` | ko |
| `is_primary_esg_narrative` | **no** |
| `contains_esg_metrics` | **yes** (định nghĩa metric, **không** giá trị) |
| `contains_navigation_noise` | **no** |
| `contains_listing_or_index_noise` | **no** |
| `contains_news_rewrite_or_secondary_reporting` | **no** |
| `suitable_for_gold_generation` | **conditional** |
| `recommended_use` | **distill_yes_with_filter** |
| `main_risks` | Sinh câu hỏi metric nhưng **không có answer** trong taxonomy → hallucination nếu distill độc lập; trùng nội dung giữa 3 package (cùng template K-ESG) |
| `reason` | Mỗi row dạng `[K-ESG 정량 | …]` + `board_structure`. Dùng để **gắn GRI/K-ESG vào unit** và sinh câu hỏi template; **bắt buộc** join với PKG-*-EV có giá trị thực hoặc đánh dấu `not_found_in_dataset`. |

---

## Taxonomy evidence unit

Định nghĩa các loại **evidence unit** (đơn vị nhỏ nhất trước khi Distillation). Mỗi unit = 1 record (hoặc 1 đoạn đã cắt) có `record_id`, `source_type`, `text`.

| Unit type | Định nghĩa | Ví dụ ngắn | Đưa vào Silver? |
|-----------|------------|------------|-----------------|
| `narrative_fact` | Đoạn mô tả ESG có thể trả lời bằng 1–3 câu grounded | “한샘은 2020년부터 지속가능경영보고서를 발간…” | **Có** — ưu tiên cao |
| `metric_fact` | Số liệu/disclosure có đơn vị, năm, phạm vi rõ | “여성 관리자 비율 12.3% (2023)” | **Có** — nếu có value trong text |
| `date_fact` | Ngày/thời hạn gắn sự kiện ESG có ngữ cảnh | “보고기간 2023.01.01–2023.12.31” | **Có** — kèm event; **không** nếu chỉ `rcept_no` |
| `governance_fact` | Cơ cấu quản trị, ủy ban, compliance, ethics | “ESG 위원회 설치…” | **Có** |
| `policy_fact` | Tuyên bố chính sách / cam kết / phạm vi báo cáo | “GRI Standards Core option 적용” | **Có** — dùng cho qualitative |
| `nav_or_menu_noise` | Menu web, 민원, 정보공개 안내, lookup | “온라인민원신청… 신청하고 결과를 조회” | **Không** |
| `listing_or_index_noise` | Mục lục, danh sách file, metadata công bố | “접수번호… 파일크기…”, TOC PDF | **Không** |
| `secondary_news_noise` | News snapshot, RSS, viết lại báo chí | “News snapshot title: … pubDate …” | **Không** (trừ khi có fact độc lập đã verify) |
| `cross_company_mismatch` | Text thuộc công ty/tổ chức khác tên package | 삼성전기 privacy trong package 레이시온 | **Không** |
| `ambiguous_or_unverifiable` | Thiếu context, trùng edition, mâu thuẫn số lần phát hành SR | “5번째” vs “6번째” vs “3번째” báo cáo | **Không** — hoặc tách theo `record_id` + năm báo cáo |

---

## Bộ rule lọc cho Distillation (Round 1)

Áp dụng **trước** khi gọi LLM Distillation (step 2). Thứ tự: deny trước → allow sau.

### Deny (loại cứng)

| Rule ID | Điều kiện | Unit type |
|---------|-----------|-----------|
| `DENY-NAV` | `title ∈ {company_website}` HOẶC text match menu/민원/정보공개/조회하세요/신청 | `nav_or_menu_noise` |
| `DENY-LIST` | `len(text) < 200` VÀ không có câu narrative HOẶC chỉ metadata DART (`rcept_no`, `corp_code`) | `listing_or_index_noise` |
| `DENY-XCO` | `company` trong package ≠ thực thể trong text (heuristic: tên công ty khác trong 80 ký tự đầu) | `cross_company_mismatch` |
| `DENY-DATE-ONLY` | Answer chỉ là ngày/8 số/mã tiếp nhận, không kèm fact ESG | `date_fact` (invalid) |
| `DENY-VENDOR` | Nội dung generic về “지속가능경영보고서 제작”, vendor, training — không thuộc công ty | `secondary_news_noise` / vendor |
| `DENY-NEWS` | `source_type = news` HOẶC `title = local_news \| official_newsroom` | `secondary_news_noise` |
| `DENY-AMBIG-EDITION` | Cùng chủ đề “lần thứ mấy SR” từ record khác năm → chỉ giữ **1 record/năm báo cáo** | `ambiguous_or_unverifiable` |

### Allow (giữ cho Distillation)

| Rule ID | Điều kiện | Unit type |
|---------|-----------|-----------|
| `ALLOW-SR-NARR` | `source_type = sustainability_report` VÀ `title = official_sustainability_report` VÀ `len(text) ≥ 400` | `narrative_fact`, `policy_fact` |
| `ALLOW-GOV` | `source_type = governance_report` VÀ section G/E/S rõ | `governance_fact` |
| `ALLOW-METRIC` | Có số + đơn vị hoặc % trong text, cùng company | `metric_fact` |
| `ALLOW-TAX-SEED` | Từ `PKG-REQ-TAXONOMY` / `ESG-TAX-Q` — **chỉ** sinh câu hỏi; answer phải resolve từ PKG-*-EV hoặc mark insufficient | metadata join |
| `ALLOW-QUAL-SEED` | Từ `ESG-TAX-QL` — map pillar → tìm đoạn narrative tương ứng trong SR | qualitative template |

### Metadata bắt buộc trên mỗi Silver row (output Distillation)

- `source_id`, `record_id`, `company`, `source_type`, `document_type`
- `evidence_unit_type` (từ taxonomy trên)
- `gri_code` / `k_esg` (nếu có từ taxonomy join)
- `forbidden_rule`: không vượt quá `context_excerpt`

---

## Kết luận

### Được phép sinh Silver (`distill_yes` / `distill_yes_with_filter`)

| Nguồn | Khuyến nghị |
|-------|-------------|
| **PKG-HANSSEM-EV** | `distill_yes_with_filter` — nguồn **sạch nhất**; lọc news, TOC, multi-edition |
| **PKG-MUSINSA-EV** | `distill_yes_with_filter` — chỉ SR + narrative E/S/G; loại listing/DART snapshot |
| **ESG-TAX-Q** | `distill_yes_with_filter` — seed câu hỏi metric, **không** distill answer từ CSV alone |
| **ESG-TAX-QL** | `distill_yes_with_filter` — seed qualitative theo 4 trụ |
| **PKG-REQ-TAXONOMY** | `distill_yes_with_filter` — metadata + join value từ company evidence |

### Chỉ có điều kiện / cần dataset fix trước

| Nguồn | Khuyến nghị |
|-------|-------------|
| **PKG-RAYSOLUTION-EV** | `exclude_from_gold` — **62** cross-company records; cleaning v2 loại 100% gold. Chờ team Dataset làm sạch hoặc tách package |

### Phải loại khỏi gold generation (hiện trạng)

| Nguồn / nhóm | Lý do |
|--------------|-------|
| **Toàn bộ 레이시온** (cho đến khi sửa dataset) | Cross-company + nav + vendor content |
| **News / newsroom** trong mọi package | `secondary_news_noise` |
| **Nav / 민원 / 정보공개** | Đã gây answer correctness ≈ 0 trên 레이시온 |
| **Date-only / listing metadata** | 14+ câu drop trong `golden_v2_cleaning_report` |
| **Taxonomy-only Q&A** (không join evidence value) | Metric question không có số trong dataset |

### Rule lọc quan trọng nhất cho Distillation (top 5)

1. **`DENY-XCO`** — không distill nếu text không thuộc đúng `company` của package.  
2. **`DENY-NEWS` + `DENY-NAV`** — loại news snapshot và menu website (nguyên nhân chính answer thấp).  
3. **`ALLOW-SR-NARR` only** — ưu tiên `official_sustainability_report`, độ dài tối thiểu 400 ký tự.  
4. **`DENY-DATE-ONLY` + `DENY-LIST`** — không sinh gold từ metadata công bố / file index.  
5. **Join taxonomy → evidence** — `ESG-TAX-Q` / `PKG-REQ-TAXONOMY` chỉ là **khung câu hỏi**; answer bắt buộc từ PKG-*-EV hoặc `insufficient`.

---

## Phụ lục: Bằng chứng từ artifact hiện có

| Artifact | Phát hiện liên quan |
|----------|---------------------|
| `golden_v2_cleaning_report.md` | 46/87 câu drop; 레이시온 30/30 loại; 한샘 giữ nguyên 29 |
| `findings.md` | 한샘 usable; 레이시온 mismatch; 무신사 listing-heavy |
| `step1_corpus_units` (118 unit) | Chỉ `company_evidence.jsonl`; chưa taxonomy |
| `golden_set_v1` (6 câu) | Toàn 한샘 qualitative — aligned với contract |

---

*Báo cáo phục vụ Round 1 Distillation. Round 2: áp dụng rule vào `step1_prepare` / prompt Distillation mà không đổi retrieval benchmark.*
