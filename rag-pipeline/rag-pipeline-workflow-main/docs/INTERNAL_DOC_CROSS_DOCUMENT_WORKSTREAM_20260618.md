# Workstream: Internal-Document + Cross-Document RAG

Tài liệu mô tả lane **bổ sung** cho team RAG — không thay thế lane `dataset_excel` / `goldns-emni` public-source.

## 1. Vì sao đây là bổ sung đúng hướng, không phải đổi hướng

| Lane hiện tại (giữ nguyên) | Lane mới (bổ sung) |
|---|---|
| Dataset team → public source (DART, portal, manifest) | RAG team → enterprise / internal mixed-format docs |
| `goldns` / `emni` benchmark v5 freeze | `demo_company` → prototype cross-doc |
| Rule/pattern reusable (`src/dataset_excel/`) | Structured ESG extraction → handoff LangGraph |
| Excel compare cho SME review | Evidence plan + synthesis bottleneck study |

Luồng tổng thể:

```text
[Public lane]  Excel/DART/web → corpus → extractive rules → metrics v5 → Excel review
[Internal lane] PDF/MD/HTML/JSON/... → evidence units → cross-doc retrieval → structured fields → LangGraph
```

Hai lane **nối nhau** tại:
- Chuẩn evidence unit (text, metadata, provenance)
- Phân loại gap (parser / retrieval / aggregation / synthesis)
- Rule family (employee, financial, governance…) — reuse ý tưởng, không reuse hardcode `goldns/emni`
- Review artifact (owner hint, SME vs Dataset vs RAG)

## 2. Phạm vi lane mới (vòng prototype)

**Mục tiêu vòng này:** không chase score cao.

1. Ingest mixed-format → normalized `EvidenceUnit`
2. Phân loại câu hỏi `single_document_answer` vs `cross_document_answer`
3. Evidence plan: doc A/B roles, merge/conflict flag
4. Đo bottleneck cross-document retrieval + synthesis

**Không làm:** tune `goldns/emni`, đổi metric v5, sửa workbook compare.

## 3. Kiến trúc module (repo)

```text
src/enterprise_docs/
  models.py          # EvidenceUnit, EvidencePlan, DocumentDescriptor
  parsers.py         # md/html/json/csv/pdf (prototype)
  ingest.py          # scan + chunk → units
  doc_router.py      # heuristic doc routing + evidence plan

scripts/
  audit_enterprise_doc_inventory.py
  classify_demo_company_questions.py
  build_demo_company_enterprise_corpus.py

data/enterprise_docs/
  file_inventory.json
  demo_company/
    corpus_units.jsonl
    question_evidence_plans.jsonl
    question_analysis_summary.json
```

**Module mới cần thêm (vòng sau):**
- `cross_doc_retriever.py` — retrieve per sub-query, merge evidence sets
- `evidence_aggregator.py` — table row alignment, year join, conflict detect
- `structured_extractor.py` — field binding + confidence
- `langgraph_handoff.py` — payload schema cho LangGraph

## 4. Data mẫu — audit nhanh

### demo_company (ưu tiên)

| Thành phần | Nội dung |
|---|---|
| RTX 7-step MD | 7 file `.md` (사업보고서, 온실가스, 재생에너지, 인사, 사회공헌, 지배구조, 인증) |
| Evidence CSV | `26.03.27_ESG_quant_RTX_EEO_CDP_evidence...csv` |
| Questions | `quantitative.json` (251), `qualitative.json` (27) |

### 한샘 / 무신사 (mixed-format thực tế)

- Chủ yếu **HTML** capture, **JSON**, **MD**, **PDF** (xem `data/enterprise_docs/file_inventory.json`)
- Phù hợp vòng 2: parser noise, OCR, web capture quality
- **Không** dùng làm benchmark chính vòng 1 (quá nhiễu)

## 5. Phân loại câu hỏi demo_company (heuristic v1)

Chạy: `python scripts/classify_demo_company_questions.py`

Phân loại dựa trên `domain` / `category` / `item` → map tới `doc_01`…`doc_07` + `doc_evidence_csv`.

| Nhóm | Ý nghĩa |
|---|---|
| `single_document_answer` | Một bảng MD chính đủ trả lời (vd. metric HR trong `04_인사`) |
| `cross_document_answer` | Cần ≥2 tài liệu hoặc narrative synthesis (hầu hết qualitative) |

**Qualitative (27):** mặc định cross-doc — strategy/governance/social narrative trải trên nhiều file.

**Quantitative (251):** heuristic route theo domain; cross khi:
- Nhiều doc cùng điểm cao (environment + renewable)
- Metric span business + workforce
- Cần CSV summary bổ sung series năm

Artifact: `data/enterprise_docs/demo_company/question_evidence_plans.jsonl`

## 6. Evidence plan (ví dụ)

**Single-doc:** `QUANT-0001` 총 구성원 수  
- Primary: `doc_04_hr_safety` — workforce table  
- Mode: `single_document_answer`

**Cross-doc:** `QUAL-0001` ESG 비전 및 전략  
- Primary: `doc_01_business`, `doc_06_governance`, `doc_05_social`  
- Supporting: `doc_evidence_csv`  
- Roles: strategy narrative / governance / social context  
- `needs_merge: true`

## 7. Benchmark plan (đề xuất)

### Phase A — Parser / unit quality (không score QA)

| Check | Pass criteria |
|---|---|
| Ingest coverage | 100% file trong demo 7-step → units |
| Section metadata | MD sections preserved |
| Year inference | ≥1 year on environment/HR docs |

### Phase B — Single-document retrieval

| Metric | Mô tả |
|---|---|
| `doc_hit@1` | Top-1 unit thuộc đúng `primary_document_ids` |
| `field_presence` | Evidence text chứa signal trả lời (số / câu) |
| `parser_fail_rate` | Unit rỗng / garbage |

Subset: câu `single_document_answer` only (~ước lượng từ summary JSON).

### Phase C — Cross-document retrieval + synthesis

| Metric | Mô tả |
|---|---|
| `multi_doc_recall` | % required docs có ≥1 unit trong top-k |
| `aggregation_success` | Join đúng year/metric khi cần 2 bảng |
| `conflict_detected` | Phát hiện `Not disclosed` vs số khác doc |
| `synthesis_groundedness` | (vòng sau) citation đủ doc trong plan |

Subset: `cross_document_answer` + ưu tiên qualitative.

**Không dùng overall_score v5** — metric lane riêng.

## 8. Bottleneck dự đoán

| Thứ tự | Bottleneck | Lý do |
|---|---|---|
| 1 | **Cross-document retrieval** | BM25/semantic top-k thiên về 1 doc mạnh; qualitative cần 3+ doc |
| 2 | **Evidence aggregation** | Cùng metric khác năm / `Not disclosed` / đơn vị khác nhau |
| 3 | **Synthesis / answering** | Narrative qualitative không có extractor rule đơn giản |
| 4 | **Parser / conversion** | HTML/PDF 한샘·무신사; demo MD ít rủi ro hơn |

## 9. Reuse từ lane hiện tại

| Reuse được | Không reuse trực tiếp |
|---|---|
| Chunking pattern (`rag_common.split_chunks`) | `dataset_excel` family router hardcoded DART |
| Fail taxonomy (coverage / semantic / retrieval) | `source_row_index` Excel mapping |
| Review owner model (SME/Dataset/RAG) | goldns/emni eval metrics |
| Rule **families** (employee, financial, governance) | Portal sanction lanes |
| Workflow file-backed notes | v5 benchmark scripts as-is |

## 10. Handoff LangGraph (target)

Payload đề xuất mỗi câu:

```json
{
  "item_id": "QUAL-0001",
  "answer_mode": "cross_document_answer",
  "evidence_plan": { "primary_document_ids": [], "roles": {} },
  "evidence_units": [ { "unit_id", "document_id", "evidence_text", "score" } ],
  "structured_fields": [ { "field", "value", "status", "citations" } ],
  "diagnostics": { "parser", "retrieval", "aggregation", "synthesis" }
}
```

## 11. Lệnh chạy prototype

```bash
python scripts/audit_enterprise_doc_inventory.py
python scripts/classify_demo_company_questions.py
python scripts/build_demo_company_enterprise_corpus.py
```

## 12. Bước tiếp theo đề xuất

1. Chốt subset benchmark: 20 single-doc + 15 cross-doc từ `question_evidence_plans.jsonl`
2. Implement `cross_doc_retriever` (multi-query per evidence plan role)
3. Chạy diagnostic eval — log bottleneck counts, không tune score
4. Mở rộng parser stub → Word/PPT/image OCR khi có file thật
