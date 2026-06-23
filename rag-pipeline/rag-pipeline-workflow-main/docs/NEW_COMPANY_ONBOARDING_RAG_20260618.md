# Onboarding công ty mới — Dataset-Excel Extractive RAG

Tài liệu này mô tả cách đưa **công ty thứ 3** (hoặc dataset mới tương tự `goldns`/`emni`) vào pipeline extractive RAG đã freeze ở **baseline v5**, mà không bắt đầu lại từ đầu.

**Baseline v5 (mốc freeze):**

| Metric | Giá trị |
|---|---:|
| retrieval_hit_top1 | 0.9403 |
| answer_accuracy | 1.0 |
| abstain_accuracy | 1.0 |
| overall_score | 0.9702 |

**Module rule:** `src/dataset_excel/`  
**Rule inventory:** `data/dataset_excel/rule_inventory.json`

---

## 1. Công ty mới cần cung cấp gì

### Bắt buộc

1. **Eval set** theo format `dataset_excel_eval_ready`:
   - `answerable_gold.jsonl`, `abstain_gold.jsonl`
   - Mỗi câu: `question_id`, `company_id`, `question_text`, `year`, `gold_answer_*`, `doc_title`, `source_url`, `file_url`, `scoring_rule`
2. **Source manifest** (intake):
   - DART filings: `empSttus`, `exctvSttus`, `outcmpnyDrctrNdChangeSttus`, `재무_*` (OFS/CFS)
   - Web sanction lanes: `safetykorea.kr`, `pipc.go.kr`, `case.ftc.go.kr` (nếu có câu hỏi compliance)
   - National sources: `minimumwage.go.kr` (nếu có câu minimum wage)
3. **Raw sources** đã download hoặc local collect:
   - `data/source_raw/<batch>/<company>/`
   - `download_status.jsonl` ghi rõ blocked/failed URLs

### Khuyến nghị

- Clone cấu trúc thư mục từ `data/dataset_excel_eval_ready/20260617_goldns_emni/`
- Ghi `company_id` ngắn, ổn định (ví dụ `goldns`, `emni`)
- Đảm bảo `doc_title` trong gold khớp convention corpus (xem mục 2)

---

## 2. Map source → family

| Family | Routing hint (câu hỏi) | Preferred doc / schema | Extractor |
|---|---|---|---|
| **employee** | 구성원, 성별, 정규직, 급여 | `empSttus` / `dart_employee_status` | KV sum, ratio, avg salary |
| **executive** | 임원, 다양성, 여성 | `exctvSttus` / `dart_executive_status` | Female executive % |
| **board_director** | 사외이사, 사내이사, 이사 | `outcmpnyDrctrNdChangeSttus` | inside/outside count |
| **financial** | 매출, 이자, 유형자산 취득, 세금 | `재무_*` / `dart_financial_statement` | account + period offset |
| **sanction_fair_trade** | 리콜, 개인정보, 공정거래 | `제재이력_{lane}.json` / `web_html` | zero-signal, empty list |
| **minimum_wage** | 최저임금 | `최저임금` / `web_html` | year token parse |

Chi tiết đầy đủ: `src/dataset_excel/rule_registry.py` → `FAMILY_SPECS`.

### Corpus build

Chạy (hoặc adapt) `scripts/build_goldns_emni_chunked_corpus.py`:

- `제재이력.json` → tách lane: `제재이력_safetykorea.json`, `제재이력_pipc.json`, `제재이력_ftc.json`
- Local raw ưu tiên hơn web khi trùng `(company_id, doc_title)`
- Metadata: `year`, `schema`, `sanction_lane`, `canonical_doc_title`

---

## 3. Khi nào reuse rule cũ vs thêm pattern mới

### Reuse trực tiếp (`reusable_generic_rule` + `pattern_specific_rule`)

- Công ty Hàn Quốc có DART filings cùng tên file (`empSttus`, `exctvSttus`, …)
- Câu hỏi map được vào một trong 5 nhóm family trên
- Sanction web HTML cùng portal (safetykorea / pipc / ftc)

→ Chỉ cần: intake source → build corpus → chạy eval. **Không sửa extractor.**

### Cần pattern mới

- Schema field khác (tên account DART khác, không có `제 N 기`)
- Portal HTML structure khác (không phải recall list safetykorea)
- Metric mới không có routing hint trong `infer_question_profile`

→ Thêm vào `src/dataset_excel/family_router.py` + `extractors.py`, đăng ký trong `rule_registry.py`.

### Không nên productize (`company_specific_rule`)

- Hardcode `question_id`
- Clone source chỉ cho một công ty (ví dụ minimum wage goldns từ emni)
- Boost score tuned trên 2 công ty hiện tại

→ Ghi vào `decisions.md` là `not worth productizing`.

### SME / Dataset team (`semantic_or_coverage_exception`)

- Label workbook vs account OFS không khớp (tax ambiguity)
- Source blocked (FTC `self_redirect_loop_blocked_by_site`)
- Không có raw HTML → **coverage gap**, không phải extractor gap

---

## 4. Checklist trước benchmark

- [ ] `company_id` có trong eval JSONL và corpus
- [ ] Mọi `doc_title` / `file_url` trong gold có raw tương ứng hoặc marked blocked
- [ ] Sanction URLs map đúng lane (domain → `sanction_lane`)
- [ ] Năm (`year`) trên corpus unit khớp câu hỏi
- [ ] `data/dataset_excel/rule_inventory.json` đã export (tự động khi chạy eval)
- [ ] Không có hardcode case mới chỉ để tăng score

**Lệnh benchmark:**

```bash
python scripts/run_goldns_emni_rag_eval.py \
  --corpus data/corpus/<batch>/corpus_units.jsonl \
  --eval-root data/dataset_excel_eval_ready/<batch> \
  --company <new_company_id>
```

**Audit reusability:**

```bash
python scripts/audit_dataset_excel_rule_reusability.py \
  --results-jsonl reports/goldns_emni_rag_eval_<run_id>/results.jsonl
```

---

## 5. Checklist sau benchmark — phân loại gap

| Triệu chứng | Phân loại | Hành động |
|---|---|---|
| `answer_fail` + `rule_extractor_gap` | Extractor gap | Sửa `extractors.py` / thêm sub-plan |
| `answer_fail` + không tag extractor | Retrieval hoặc routing | `family_router.py`, corpus metadata |
| `retrieval_top1_miss` + `answer_correct` | Retrieval metric only | Có thể chấp nhận nếu answer đúng; xem rerank |
| `coverage_gap` / FTC blocked | Coverage gap | Dataset team bổ sung raw source |
| `semantic_ambiguity` | SME | Không vá rule; audit label mapping |
| `abstain` sai | Abstain threshold / provenance | Kiểm tra `scoring_rule`, source_url trong gold |

**Diagnostic view mới (không thay metric v5):**

- `reusable_system_coverage` — tỷ lệ câu answerable dùng reusable family, không có exception tag
- `company_specific_dependency` — câu phụ thuộc FTC blocked, tax ambiguity, hoặc tuning riêng

Xem trong `summary.json` → `generalization_hardening`.

---

## 6. Khuyến nghị trước khi đưa công ty thứ 3

1. **Chọn công ty “gần emni/goldns”** — cùng DART + cùng bộ sanction portals để đo reuse thật.
2. **Intake FTC sớm** — nếu blocked, ghi `coverage_gap` ngay; đừng tune extractor cho gold=0 giả định.
3. **Chạy eval per-company trước** (`--company`) để so `by_company` vs pooled.
4. **So sánh `generalization_hardening`** giữa v5 freeze và run mới — mục tiêu là reuse % cao, không chase overall_score.
5. **Freeze rule** sau mỗi mốc — cập nhật `rule_inventory.json`, không vá case-by-case.

---

## 7. Artifact liên quan

| File | Mục đích |
|---|---|
| `src/dataset_excel/rule_registry.py` | Inventory + phân loại rule |
| `src/dataset_excel/family_router.py` | Routing + retrieval boost |
| `src/dataset_excel/extractors.py` | Family extractors |
| `data/dataset_excel/rule_inventory.json` | Export JSON cho audit |
| `reports/dataset_excel_reusability_audit.json` | Reusability diagnostic |
| `docs/NEW_COMPANY_ONBOARDING_RAG_20260618.md` | Tài liệu này |

**Baseline artifact v5:** `reports/goldns_emni_rag_eval_20260618-094903/`
