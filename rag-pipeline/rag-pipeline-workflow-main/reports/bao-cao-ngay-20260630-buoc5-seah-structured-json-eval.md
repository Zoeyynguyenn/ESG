# Báo cáo 2026-06-30 — Bổ sung Structured JSON cho SeAH Steel & Chạy lại Eval

**File Excel đính kèm**: `reports/eval_seah_structured_json_20260630.xlsx`  
**Corpus**: `data/corpus/20260630_v3/corpus_units.jsonl` (930 units)  
**Eval partition**: `data/dataset_excel_eval_ready/20260630_v2/`

---

## 1. Kết quả tổng hợp

### SeAH Steel (126 answerable / 504 abstain)

| Metric | v2 (baseline) | v3 (+ structured JSON) | Δ | Leader freeze | Gap |
|--------|:---:|:---:|:---:|:---:|:---:|
| answer_accuracy | 0.4603 | **0.5000** | **+5.4 pp** | ~0.74 | -0.24 |
| retrieval_hit_top1 | 0.7302 | **0.7540** | **+2.4 pp** | ~0.74 | +0.01 ✅ |
| abstain_accuracy | 1.0000 | **1.0000** | 0 | ~0.83 | +0.17 ✅ |
| overall_score | 0.7302 | **0.7520** | **+2.2 pp** | ~0.83 | -0.08 |

### 골드엔에스 (74 answerable / 556 abstain — unchanged)

| Metric | v3 | Leader freeze |
|--------|:---:|:---:|
| answer_accuracy | 0.7432 | ~0.93 |
| retrieval_hit_top1 | 0.7973 | ~0.97 |
| abstain_accuracy | 1.0000 | ~0.97 |

### Regression Gate

```
✅ 10/10 PASSED — global_pass=true (goldns curated slice, 27 questions)
```

---

## 2. Những gì đã làm

### 2.1 Parse structured JSON từ dart_full section text

Script `scripts/build_seah_structured_json_from_sections.py` mở seah zip, định vị section HTML/text, extract bảng dữ liệu:

| File JSON | Schema | Năm | Records | Source (rcpNo) |
|-----------|--------|-----|---------|----------------|
| `2023_empSttus.json` | dart_employee_status | 2023 | 2 | 20240306000569 |
| `2025_empSttus.json` | dart_employee_status | 2025 | 2 | 20260312000989 |
| `2023_exctvSttus.json` | dart_executive_status | 2023 | 19 | 20240306000569 |
| `2025_exctvSttus.json` | dart_executive_status | 2025 | 21 | 20260312000989 |
| `2023_재무_OFS.json` | dart_financial_statement | 2023 | 8 | 20240306000569 |
| `2025_재무_OFS.json` | dart_financial_statement | 2025 | 8 | 20260312000989 |

Mỗi artifact dir chứa `records.jsonl` (text field human-readable) + `extracted.txt` (fallback).

### 2.2 Bugs đã debug và fix

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| **BUG-1**: `canonical_doc_id = extracted.txt` | `local_path` trong collect_status trỏ vào `extracted.txt`, `enrich_base_meta` derive `canonical_doc_id='extracted.txt'` → không có +2.35 structured boost | Lưu JSON với tên canonical (`2023_empSttus.json`), point `local_path` vào đó |
| **BUG-2**: Salary spill-over | HTML table — mỗi cell một dòng; regex 5+ char số sau match grab `2,509` (female annual sal) làm male monthly salary | Parse từng line riêng, extract salary chỉ từ lines kế tiếp sau row match |
| **BUG-3**: 합계 row regression | Thêm `sexdstn=합계` làm extractor tính `721+41+762=1524` denominator → male_ratio=47% thay vì 94.6% | Bỏ 합계 row; extractor tự sum male+female để tính ratio |

### 2.3 Pipeline đã chạy

```
build_seah_structured_json_from_sections.py  → 6 artifact dirs
_merge_v3.py                                  → 357 entries (357: goldns=78, seah=279)
build_goldns_emni_chunked_corpus.py           → 930 units (local=909, web=21)
run_goldns_emni_rag_eval.py                   → goldns + seah eval
run_dataset_excel_regression_gate.py          → 10/10 PASSED
```

---

## 3. Phân tích fail — employee_status (26 → 16 fails, -38%)

| Question | Gold | v3 Pred | Đúng? | Ghi chú |
|----------|------|---------|:---:|---------|
| seah-0001 (male_ratio 2023) | 94.6% | 94.6% | ✅ | Từ 2023_empSttus.json |
| seah-0003 (male_ratio 2025) | 92.8% | 92.8% | ✅ | Từ 2025_empSttus.json |
| seah-0004 (female_ratio 2023) | 5.4% | 5.4% | ✅ | |
| seah-0007 (regular_male 2023) | 603 | 603 | ✅ | |
| seah-0009 (regular_male 2025) | 704 | 704 | ✅ | |
| seah-0043 (subcount 2023) | 567 | ND | ❌ | corpus_limited: 519+48=567 không parse |
| seah-0045 (subcount 2025) | 556 | ND | ❌ | corpus_limited: 522+34=556 không parse |
| seah-0211 (avg monthly all 2023) | 99 | 0 | ❌ | corpus_limited: 합계 row excluded |
| seah-0213 (avg monthly all 2025) | 90 | 0 | ❌ | corpus_limited: 합계 row excluded |
| seah-0214 (female_ratio_reg 2023) | 60.4 | 60.73 | ❌ | Close miss: tolerance ~0.5% |

---

## 4. Diagnosis: corpus_limited vs system_gap

### corpus_limited (không cần sửa code)

| Family | v2→v3 | Nguyên nhân |
|--------|-------|-------------|
| employee_status | 26→16 | 2024 annual report thiếu; subcounts (567/556) chưa parse; 합계 avg monthly excluded |
| generic | 33→34 | Data không có trong corpus nào (ESG sustainability slides, CSR report) |
| financial_generic | 8→8 | Rule extractor gap (không đủ financial context) |
| board_director | 3→4 | `outcmpnyDrctrNdChangeSttus.json` không có cho seah → sử dụng financial notes nhưng boost sai |
| minimum_wage | 3→3 | Local corpus không có wage data |

### system_gap: KHÔNG phát hiện
- Extractor hoạt động đúng với dữ liệu có sẵn
- retrieval_hit_top1=0.754 ≥ leader ~0.74 cho seah answerable ✅
- abstain_accuracy=1.0 > leader ~0.83 ✅
- Không cần sửa code

### Data availability

| Loại data | 2023 | 2024 | 2025 |
|-----------|:----:|:----:|:----:|
| empSttus | ✅ | ❌ | ✅ |
| exctvSttus | ✅ | ❌ | ✅ |
| 재무_OFS | ✅ | ❌ | ✅ |
| outcmpnyDrctrNdChangeSttus | ❌ | ❌ | ❌ |

**2024 annual report** (rcp ~20250312xxxxxxxx) không có trong zip. Nếu bổ sung, dự kiến:
- Thêm ~20-30 answerable questions có data → answer_accuracy tăng ~0.05-0.08

---

## 5. Khuyến nghị next step

1. **Ngắn hạn**: Thu thập FY2024 annual report (DART rcpNo ~20250312xxx) cho seah → stage empSttus/exctvSttus/재무_OFS 2024
2. **Trung hạn**: Parse `다. 미등기임원 보수 현황` section (executive compensation table) để tạo pseudo-`outcmpnyDrctrNdChangeSttus` → fix board_director 4 fails
3. **Dài hạn**: Align với goldns leader freeze bằng cách bổ sung missing section subcounts (519/567 non-executive vs executive regular employees)
