# Bao cao 22: Lane enterprise internal-doc san sang cho du lieu that

Ngay: 2026-06-19

## 1. Muc tieu

Lane `enterprise internal-doc` duoc xay dung de xu ly tai lieu doanh nghiep nhieu dinh dang va chuyen thanh du lieu ESG co cau truc, thay vi chi dung cho truy van tai lieu don le.

Muc tieu chinh cua lane gom:

1. Tiep nhan va xu ly tai lieu doanh nghiep o nhieu dinh dang nhu `markdown`, `html`, `xml`, `pdf`, `json`, `csv`.
2. Dua noi dung da xu ly vao quy trinh RAG de trich xuat du lieu ESG co cau truc, co gan evidence va readiness state.
3. Nang cap kha nang xu ly cau hoi can tong hop nhieu tai lieu, bao gom so khop metric cung nghia, hop nhat evidence va phan biet `corpus_limited` voi `system_gap`.

## 2. Cach thuc hien

Lane duoc thuc hien theo 4 lop nang luc chinh:

### 2.1. Xu ly tai lieu nhieu dinh dang

He thong da bo sung parser va ingest flow cho cac dinh dang chinh, dua tai lieu ve dang `corpus_units`, co tach section va logical document.

### 2.2. Chuan hoa ESG structured data

He thong da xay dung `esg_target_schema`, `normalizer` va `structured_esg_mapper` de dua ket qua ve cac truong co y nghia van hanh nhu:

- `family_id`
- `metric_name`
- `value`
- `unit`
- `year`
- `evidence`
- `readiness_state`
- `conflict_status`

### 2.3. Truy hoi va tong hop theo family / logical document

He thong da bo sung:

- retrieval scope narrowing
- family-scoped retrieval pool
- logical-document routing
- overlap registry

Muc tieu la giam retrieval noise va xac dinh metric nen duoc tim o nhom tai lieu nao.

### 2.4. Hardening capability cot loi va dong goi van hanh

Lane da duoc harden theo cac lop:

1. `cross-role extraction`
2. `equivalence collapse`
3. `evidence fusion`
4. `conflict classification`
5. `readiness promotion`

Sau do lane duoc dong goi thanh:

- onboarding gate
- bootstrap kit cho cong ty moi
- SOP / runbook
- templates probes, natural cases, review
- script khoi tao skeleton cong ty moi

## 3. Ket qua da dat duoc

### 3.1. Ket qua ky thuat

Lane da dat cac moc chinh:

- Co parser va ingest flow cho cac dinh dang tai lieu chinh.
- Co ESG schema va output structured theo `field/value/evidence/readiness`.
- Co retrieval theo logical document va family.
- Co overlap / equivalence / fusion infrastructure cho bai toan nhieu tai lieu.
- Co regression gate cho capability cot loi tren `constructed suite`.

Ket qua regression gate hien tai:

- `cross_role_extraction_alignment_rate = 100%`
- `cross_doc_equivalence_match_rate = 100%`
- `evidence_fusion_success_rate = 100%`
- `conflict_classification_accuracy = 100%`
- `single_source_to_multi_source_promotion_rate = 100%`
- `ghost_pass_count = 0`

Dieu nay cho thay core capability cua lane da san sang cho du lieu doanh nghiep that.

### 3.2. Ket qua van hanh

Lane da co day du thanh phan de van hanh voi cong ty that:

- `docs/ENTERPRISE_INTERNAL_DOC_OPERATIONAL_RUNBOOK.md`
- `docs/ENTERPRISE_INTERNAL_DOC_NEW_COMPANY_BOOTSTRAP.md`
- templates probes / natural capability cases / review
- `scripts/bootstrap_enterprise_company.py`
- `scripts/run_enterprise_docs_natural_onboarding_gate.py`

Trang thai hien tai da duoc chot:

`done_until_real_data`

Nghia la lane da hoan tat phan chuan bi ky thuat va van hanh, chi con cho du lieu doanh nghiep that de onboarding theo SOP.

## 4. Cac yeu cau chinh va cach da hien thuc hoa

### 4.1. Chuyen doi du lieu tu nhieu dinh dang tai lieu doanh nghiep

Da hien thuc hoa bang parser cho `markdown/html/xml/pdf/json/csv`, ingest flow va logical-document mapping.

### 4.2. Dua tai lieu vao he thong RAG de trich xuat thong tin chinh xac

Da hien thuc hoa bang retrieval scope, family-scoped pool, extraction theo family va logical document, cung readiness gate cho ket qua trich xuat.

### 4.3. Chuan hoa du lieu da trich xuat thanh ESG structured data

Da hien thuc hoa bang `esg_target_schema`, `esg_field_normalizer`, `structured_esg_mapper` va cac truong conflict / readiness trong output.

### 4.4. Xu ly cau hoi can tong hop nhieu tai lieu ket hop

Da hien thuc hoa bang overlap registry, metric equivalence registry, cross-role extraction hardening, fusion equivalence hardening, conflict classification va readiness promotion.

### 4.5. Phan biet loi do du lieu voi loi do he thong

Da hien thuc hoa bang natural onboarding gate, co che tach `corpus_limited` va `system_gap`, va runbook review sau khi chay gate.

### 4.6. San sang van hanh ngay khi co du lieu doanh nghiep that

Da hien thuc hoa bang bootstrap kit, onboarding templates, SOP 7 buoc, gate runner va review templates.

## 5. Ket luan

Lane `enterprise internal-doc` da hoan tat phan chuan bi cho bai toan xu ly tai lieu doanh nghiep thanh du lieu ESG co cau truc.

Core capability da duoc harden va khoa lai bang regression gate. Phan van hanh da duoc dong goi thanh runbook, bootstrap kit, templates va script khoi tao. O thoi diem hien tai, lane nay khong can mo rong theo huong LangGraph, synthesis, hoac toi uu diem tren du lieu demo.

Trang thai hien tai:

`done_until_real_data`

Buoc tiep theo khi co du lieu doanh nghiep that:

1. bootstrap cong ty moi
2. ingest tai lieu
3. tao probes va natural cases
4. chay onboarding gate
5. review theo SOP va phan loai `corpus_limited` / `system_gap`

Lane da san sang dua vao van hanh khi co du lieu that.
