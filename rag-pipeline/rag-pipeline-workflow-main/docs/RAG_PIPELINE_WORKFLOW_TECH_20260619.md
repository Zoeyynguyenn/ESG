# RAG Pipeline — Workflow & Kỹ thuật (cập nhật 2026-06-19)

> Tài liệu này **cập nhật** `RAG_PIPELINE_OPERATING_MODEL_20260617.md` theo feedback sếp ngày
> 2026-06-19. Khi có mâu thuẫn, ưu tiên bản này.
> Ngôn ngữ: tiếng Việt cho prose; giữ tiếng Anh cho định danh kỹ thuật (file, tool, metric, model).

---

## 1. Nguồn cập nhật — feedback sếp 2026-06-19

Sếp chốt 2 điều:

1. **Phạm vi team RAG được mở rộng chính thức:** ngoài dữ liệu do team Dataset cấp, team RAG
   chịu trách nhiệm chuyển đổi **file thô do doanh nghiệp cung cấp trực tiếp** (Excel, PDF,
   PowerPoint, Image, Word, và các định dạng khác) → trích xuất bằng RAG → chuẩn hóa và nhập vào
   **hạng mục ESG tương ứng** → handoff cho team LangGraph.
   - Ranh giới: **dữ liệu công khai = team Dataset**; **xử lý tài liệu nội bộ doanh nghiệp bằng
     RAG = team RAG**. Phần mơ hồ → nêu ý kiến nội bộ để thống nhất.
2. **Hướng nghiên cứu khi chờ data thật:** sếp sẽ cấp data doanh nghiệp thật sau. Trong lúc chờ,
   team RAG tiếp tục nghiên cứu cách **cải thiện hiệu suất chuyển file tài liệu → dữ liệu có cấu
   trúc**. Vấn đề lớn nhất sếp từng gặp: hiệu suất **không cải thiện** khi phải trả lời 1 câu hỏi
   dựa trên **nhiều tài liệu kết hợp** thay vì 1 tài liệu đơn lẻ → đây là hạn chế lõi của RAG với
   bài toán **cross-document retrieval**.

Kết luận: feedback **trùng khít** lane `enterprise internal-doc` đã mở 2026-06-18. Đây là xác
nhận đúng hướng + chốt trọng tâm, không phải đổi hướng.

---

## 2. Mô hình vận hành 2 lane (cập nhật)

| | **Lane A — Public benchmark** | **Lane B — Enterprise internal-doc** |
|---|---|---|
| Nguồn vào | Package Dataset `.zip` (Data Contract v1.1) | File thô doanh nghiệp đa định dạng |
| Chủ sở hữu thu thập | Team Dataset | Doanh nghiệp → sếp cấp cho team RAG |
| Gold answer | Có (chuyên gia xác nhận) | **Không có sẵn** → cần cơ chế eval khác |
| Trạng thái | **Freeze** (`goldns`/`emni`, score 0.97) | Đang phát triển (prototype → framework) |
| Metric | 5-metric + `overall_score` v5 | Metric cross-doc riêng (mục 6) |
| Mục tiêu vòng này | Giữ ổn định, tái sử dụng rule/pattern | **Đo & gỡ bottleneck cross-doc**, chưa chase score |

Hai lane nối nhau ở: chuẩn `EvidenceUnit`, phân loại gap (parser/retrieval/aggregation/synthesis),
rule **families** (employee/financial/governance — reuse ý tưởng, không reuse hardcode goldns/emni),
và contract handoff LangGraph.

---

## 3. Luồng workflow Lane B (chi tiết — bám module hiện có)

| Bước | Việc cần làm | Module / artifact | Trạng thái |
|---|---|---|---|
| B1. Intake file | Nhận file thô doanh nghiệp đa định dạng | `data/enterprise_docs/<company>/raw/` | Chờ data thật; dùng `demo_company` để luyện |
| B2. Parse | Đọc Excel/PDF/PPT/Word/Image/HTML/JSON | `enterprise_docs/parsers.py`, `ingest.py` | md/html/json/csv OK; **PDF/Word/PPT/OCR còn stub** |
| B3. Normalize → EvidenceUnit | text + metadata + provenance + `section_path` | `enterprise_docs/models.py` | OK |
| B4. Index | chunk + vector index | `retrieval_index.py` (reuse `rag_common.split_chunks`) | OK |
| B5. Phân loại câu hỏi | `single_document` vs `cross_document` | `doc_router.py` | OK (heuristic v1) |
| B6. Evidence Plan | doc roles, supporting docs, `needs_merge` | `doc_router.py` → `EvidencePlan` | OK |
| B7. **Cross-doc Retrieval ⭐** | sub-query theo role + diversification per-doc | `cross_doc_retriever.py` | **Trọng tâm cải tiến** |
| B8. Evidence Aggregation | join (metric, year), bắt conflict `Not disclosed` | `evidence_aggregator.py`, `conflict_classifier.py` | Có khung, cần tăng cường |
| B9. Structured Extraction | field + value + status + confidence + citations | `structured_extractor.py` | OK, chưa mở synthesis |
| B10. Map hạng mục ESG | bind field vào schema ESG | `structured_esg_mapper.py` | Cần chốt schema đích |
| B11. Handoff LangGraph | payload chuẩn | `langgraph_handoff.py` | Contract đã draft |

---

## 4. Kỹ thuật — vấn đề cross-document retrieval

Triệu chứng (sếp nêu): trả lời 1 câu cần ≥2 tài liệu thì hiệu suất **không cải thiện**. Ba nguyên
nhân kỹ thuật trong bài toán này:

1. **Top-k thiên về 1 doc mạnh.** Retrieval xếp hạng theo relevance thuần → doc nhiều keyword
   chiếm hết slot top-k; các doc phụ trong evidence plan không bao giờ vào context.
2. **Aggregation thất bại.** Cùng metric khác năm / khác đơn vị / `Not disclosed` ở doc này nhưng
   có số ở doc kia → không join và không phát hiện mâu thuẫn được.
3. **Synthesis khó.** Câu qualitative (narrative) trải trên 3+ doc, không có rule extractive đơn
   giản để ghép.

---

## 5. Kỹ thuật — 4 hướng cải tiến (xếp theo đòn bẩy)

### H1. Query decomposition theo role — đòn bẩy lớn nhất
- **Hiện trạng:** `cross_doc_retriever` đã có "role-aware sub-queries" nhưng còn dùng 1 query gộp.
- **Cải tiến:** sinh sub-query **riêng cho từng `primary_document_id`** trong evidence plan, retrieve
  độc lập theo từng doc rồi **union** kết quả. Ép doc phụ vào context thay vì để 1 doc nuốt hết.
- **Đo bằng:** `multi_doc_recall`, `role_coverage` (đã có field trong `RetrievalResult`).

### H2. Diversification / per-document quota
- Đảm bảo top-k có **hạn ngạch tối thiểu cho mỗi logical doc bắt buộc** (round-robin theo doc hoặc
  MMR) để doc mạnh không chiếm hết slot.
- Tận dụng `top_docs` / `required_doc_hit_rate` đã có trong `RetrievalResult`.

### H3. Tăng cường Evidence Aggregation
- Khóa join rõ ràng theo **(metric_name, year)**; chuẩn hóa đơn vị trước khi so.
- Dùng `conflict_classifier` để bắt `Not disclosed` vs số ở doc khác, gắn `conflict_detected`.
- Trả về `AggregatedCandidate` có `row_match_score` + `is_primary_doc` để xếp ưu tiên.

### H4. Synthesis gate (mở sau, có kiểm soát)
- Giữ nguyên nguyên tắc hiện tại: **chưa mở generative/synthesis** cho tới khi
  `synthesis_groundedness` (citation đủ doc trong plan) đạt ngưỡng.
- Ưu tiên extractive trước; chỉ synthesize khi evidence plan đã được retrieve đầy đủ.

---

## 6. Eval harness cross-doc (KHÔNG dùng overall_score v5)

Mục tiêu vòng này: **đo bottleneck, không chase score** (đúng tinh thần sếp).

| Phase | Kiểm tra | Pass criteria |
|---|---|---|
| A — Parser/unit quality | 100% file demo → units; section metadata giữ; year inference ≥1 | không score QA |
| B — Single-doc retrieval | `doc_hit@1`, `field_presence`, `parser_fail_rate` | subset `single_document_answer` |
| C — Cross-doc retrieval + synthesis | `multi_doc_recall`, `aggregation_success`, `conflict_detected`, `synthesis_groundedness` | subset `cross_document_answer` |

**Subset benchmark đề xuất:** 20 câu `single_doc` + 15 câu `cross_doc` lấy từ
`data/enterprise_docs/demo_company/question_evidence_plans.jsonl`.

---

## 7. Roadmap khi chờ data thật

1. **Mở rộng parser** PDF/Word/PPT/Image-OCR từ stub → chạy được (luyện trên `demo_company` +
   `한샘`/`무신사` mixed-format đã có trong `file_inventory.json`).
2. **Implement H1 + H2** trong `cross_doc_retriever.py`, log diagnostic theo Phase C.
3. **Tăng cường H3** trong `evidence_aggregator.py` (join key + conflict).
4. **Dựng corpus proxy đa định dạng** để test parser trước khi data thật về.
5. Khi sếp cấp data doanh nghiệp thật → swap corpus, giữ nguyên harness, đo lại.

---

## 8. Điểm còn mơ hồ — cần nêu nội bộ để thống nhất

1. **Schema ESG đích** cho `structured_fields`: dùng schema Data Contract v1.1 hay schema riêng của
   LangGraph? → cần chốt trước khi hoàn thiện `structured_esg_mapper`.
2. **File "bán công khai"** (báo cáo PDF doanh nghiệp đã publish): thuộc Dataset hay RAG?
3. **Eval khi không có gold:** doc nội bộ không có gold answer từ Dataset → thống nhất cơ chế
   (holdout self-check / SME review) thay vì so gold như Lane A.
4. **Handoff payload** `langgraph_handoff`: xác nhận với team LangGraph để họ chỉ trình bày, không
   chấm retrieval quality.

---

## 9. Next step (checklist)

- [ ] Nêu 4 điểm mục 8 cho sếp/team → chốt schema + ranh giới.
- [ ] Chốt subset 20 single + 15 cross từ `question_evidence_plans.jsonl`.
- [ ] Mở rộng parser PDF/Word/PPT/OCR (Phase A).
- [ ] Implement H1 (sub-query theo role) + H2 (per-doc quota) trong `cross_doc_retriever.py`.
- [ ] Tăng cường H3 (join + conflict) trong `evidence_aggregator.py`.
- [ ] Chạy diagnostic eval Phase B/C, log bottleneck counts (không tune score).

---

## 10. CẬP NHẬT theo kiến trúc 3 lớp của team (2026-06-19)

Team leader đã nâng mô hình lên **3 lớp** (xem `TONG_HOP_2_LANE...md`, `UNIFIED_ESG_ANSWER_RESOLUTION_WORKFLOW.md`):
**2 nguồn (dataset / internal-doc) → 2 lane → 1 lớp hợp nhất `Unified ESG answer resolution`**.
Lớp hợp nhất join theo `question_id` (fallback `company_id::family_id::metric_name::year`), chọn
`best_answer` + origin, gắn status `MATCH_CONFIRMED / BACKFILL_FROM_DATASET / BACKFILL_FROM_INTERNAL /
CONFLICT_REVIEW_REQUIRED / INSUFFICIENT_EVIDENCE / NO_ANSWER_FOUND`, xuất `unified_answers.jsonl` +
`unified_esg_review.xlsx` (không ghi đè Excel gốc).

### Đề xuất cũ của mình — phần lớn team ĐÃ làm

| Đề xuất mục 5 | Module team đã có | Trạng thái |
|---|---|---|
| H1 role-aware sub-query | `cross_doc_retriever._role_subqueries` | ✅ Done |
| H2 per-doc diversification | `cross_doc_retriever` (doc score + table inject) | ✅ Done |
| H3 aggregation join + conflict | `evidence_aggregator`, `fusion_equivalence`, `conflict_classifier` | ✅ Done |
| Eval harness Phase A/B/C | `run_enterprise_docs_natural_onboarding_gate.py` (constructed regression, ghost_pass=0) | ✅ Done |
| Value equivalence | `value_equivalence.py`, `unified_esg_resolution_policy.py` | ✅ Done |

→ Phần research cross-doc gần như đã được đóng gói. Doc này từ đây chỉ giữ lại các điểm **team CHƯA có**.

---

## 11. ĐỀ XUẤT CẢI TIẾN v2 (chỉ nêu cái team chưa có, có cơ sở)

### P0 — giá trị cao, làm được ngay

**C1. Thêm status `CONFIRMED_NOT_DISCLOSED` (tách khỏi `NO_ANSWER_FOUND`).**
Trong bộ goldns+emni, **463/530 = 87% câu là abstain**. Policy hiện đặt `treat_abstain_as_no_answer=true`
→ cả 2 nguồn abstain bị gộp thành `NO_ANSWER_FOUND`. Nhưng "cả dataset lẫn internal-doc đều xác nhận
không công bố" là **một sự thật nghiệp vụ có giá trị** (cho LangGraph/báo cáo), khác hẳn "chưa nguồn nào
trả lời". Tách ra giúp: (a) khỏi review lại 87% câu vô ích, (b) LangGraph trình bày "không công bố"
có evidence thay vì để trống. → thêm 1 nhánh rule trong `unified_esg_resolution_policy.py`.

**C2. A/B đo uplift cross-doc THẬT trên `demo_company` (đúng nỗi đau sếp).**
Team đã xây plumbing cross-doc nhưng lane `done_until_real_data` và "không synthesis" → **chưa chứng minh
bằng số** rằng role-decomposition cải thiện multi-doc. Làm được ngay không cần data thật:
chạy A/B trên subset `cross_document_answer` — baseline 1 query gộp vs role-decomposed retrieval —
report Δ`multi_doc_recall`, Δ`aggregation_success`. Đây là bằng chứng định lượng cho câu hỏi sếp lo nhất.

### P1 — giảm rủi ro sai ở lớp hợp nhất

**C3. Family alignment chắc hơn.** `FAMILY_ALIASES` đang hardcode thô
(`financial`/`financial_tax`/`board_director` → đều `governance`). Với fallback key
`family_id::metric_name::year`, map sai family → **join sai → MATCH/CONFLICT giả**. Đề xuất: thêm
alias cấp `metric_name` + `family_alignment_confidence`; join cross-family confidence thấp → **không
auto-confirm**, đẩy review. (Cơ sở: case `goldns-0214 financial_tax` team đã phải gắn semantic_ambiguity.)

**C4. Value equivalence theo đơn vị.** `numeric_tolerance=0.01` là **một ngưỡng global** + `strip_commas`,
chưa chuẩn hóa đơn vị (%, 억원 vs 백만원, tCO2e, headcount). Rủi ro: MATCH nhầm khi khác đơn vị, hoặc
CONFLICT nhầm khi chỉ khác format. Đề xuất: chuẩn hóa đơn vị qua `esg_field_normalizer` trước khi so,
tolerance theo `family_id`; lệch đơn vị → CONFLICT chứ không MATCH.

**C5. Confirm gate theo metric-type cho count/boolean.** Với metric đếm/nhị phân (vi phạm = 0/1),
match số trần rất mong manh (đúng như test BM25 của mình HIT giả số "1"). Đề xuất: gắn `metric_type`
(count/date/ratio/currency/text) và yêu cầu match nhãn dòng nguồn trước khi auto-confirm với count/boolean.

### P2 — bền vững dài hạn

**C6. Regression gate cho CHÍNH lớp hợp nhất.** Internal-doc có constructed regression (ghost_pass=0),
nhưng lớp unified (mới nhất, rủi ro nhất) chưa thấy golden/CI. Đề xuất golden ~10–15 case cố định phủ
mỗi status, làm CI để sửa policy không âm thầm lật status.

**C7. Theo dõi drift phân bố status.** Khi onboard nhiều công ty, log `status_breakdown` theo thời gian
(tỉ lệ CONFLICT/INSUFFICIENT tăng?) → mở rộng `production_monitoring.md`.

### Ưu tiên gợi ý
`C1` và `C2` làm trước (giá trị cao, không phụ thuộc data thật) → `C3/C4/C5` (giảm sai lớp hợp nhất)
→ `C6/C7` (CI + monitoring).
