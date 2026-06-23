# Reset Golden Set Theo Workbook Tham Chieu (2026-06-11)

## Muc tieu

Kiem tra lai workstream Golden Set hien tai sau khi doi chieu voi 2 artifact tham chieu ben ngoai:

- `golden_set_3companies_v4.xlsx`
- `golden_eval_report_en_ko.docx`

Va sua huong thuc thi ngay trong repo de tranh tiep tuc toi uu sai muc tieu.

## Ket luan chinh

Van de khong nam o viec "AI khong tim ra ESG fact". Van de nam o viec workflow hien tai da troi sang mot bai toan khac:

1. Workflow tham chieu la `workbook-first`, khong phai `single-unit hard gate`.
2. Mot `passage_text` tot co the sinh nhieu seed:
   - `quantitative`
   - `trend`
   - `qualitative`
   - `unanswerable`
3. Workbook tham chieu dung cac truong:
   - `passage_text`
   - `facts_tuple`
   - `acceptable_disclosure`
   - `prohibited_claims`
4. Bao cao tham chieu dat `23/24 pass` chu yeu nho:
   - query strategy dung (`facts_tuple` / `passage_text`)
   - eval strategy dung
   - khong tu sat yield bang `1 unit -> 1 QA -> duplicate hard drop`

## Hien trang workstream trong repo

Nhanh tien do `R2.1 -> R2.4` da toi uu qua muc cho precision:

1. Ep `1 unit -> 1 QA hoac drop`.
2. Hard-drop duplicate theo `evidence_span`, trong khi cung mot passage ESG hop le co the sinh nhieu seed khac nhau.
3. Dung gate nho theo `Hansem-only pilot`, roi suy rong thanh ket luan ve toan bo workflow.
4. Trut bo qua nhieu unit qua cac lop:
   - prefilter
   - pilot selector
   - distillation validation
   - QC gate

He qua la metric "1 row pass" khong phan anh kha nang tim ESG fact cua he thong, ma phan anh mot workflow dang choke chinh no.

## Doi chieu truc tiep voi artifact tham chieu

### Workbook tham chieu

Workbook `v4` co 4 sheet va 24 dong seed. No khong bat buoc phai bien moi evidence unit thanh 1 QA duy nhat. No xem moi dong la mot `evaluation seed` de viet/kiem tra disclosure.

### Bao cao tham chieu

Bao cao E2E cho thay huong cai tien tap trung vao:

1. query strategy
2. tokenizer / normalization
3. cross-language retrieval
4. evaluation logic

Khong thay dau hieu cua viec dung `single-unit keep/drop` la gate chinh.

## Sua ngay trong repo

Da them builder moi:

- `src/golden_set/build_reference_seed_workbook.py`
- `scripts/build_reference_seed_workbook.py`

Builder moi reset huong theo workbook tham chieu:

1. `multi-seed per passage`
2. `workbook-first review flow`
3. `softer dedupe`
4. xuat:
   - JSONL candidate
   - XLSX workbook

Artifact moi:

- `data/golden_set/v2/reference_style/reference_seed_candidates_v1.jsonl`
- `data/golden_set/v2/reference_style/reference_seed_workbook_v1.xlsx`

## Ket qua chay that

### Vong builder dau tien

- Input: `118` corpus units
- Raw candidates: `180`
- Dedupe mem: `162`
- Selected rows: `24`

Dieu nay xac nhan he thong van co kha nang sinh ra mot pool seed co kich thuoc tuong duong workbook tham chieu.

### Sau khi siet contamination

Khi them rule chan `financial/news/listing/contact noise`, selected rows giam manh.

Dieu nay cho thay mot su that quan trong:

1. Bai toan khong chi la prompt hay distillation.
2. `corpus_units.jsonl` hien tai dang tron nhieu loai nguon khong nen vao lane Golden Set:
   - news chrome
   - report listing / archive page
   - contact / satisfaction page
   - analyst / financial commentary
   - cross-company contamination

## Quyet dinh reset

### Dung tiep tuc dung nhanh R2.1-R2.4 lam gate chinh

Nhanh nay van co gia tri de hoc ve contamination, nhung khong duoc phep dai dien cho "Golden Set pipeline chinh".

### Chuyen gate chinh sang workbook-first

Tu nay gate hop ly hon la:

1. xay `seed workbook`
2. reviewer/AI loc seed thuc su ESG
3. refine `acceptable_disclosure`
4. sau do moi dung de chay E2E va cham pass/fail

### Vi sao huong nay dung hon

1. Bám sat artifact tham chieu da co `23/24 pass`.
2. Khong danh dong `yield` de lay `precision` gia.
3. Phu hop ban chat ESG reporting: mot bang / mot doan co the cho nhieu evaluation seed hop le.

## Buoc tiep theo de lam dung

1. Dung `reference_seed_workbook_v1.xlsx` lam artifact reset, khong dung `pilot 5 row` lam thong diep chinh nua.
2. Loc lai candidate workbook theo 3 nhom contamination:
   - `news chrome`
   - `listing/archive`
   - `financial/non-ESG`
3. Chot mot tap seed workbook nho nhung dung muc tieu, thay vi tiep tuc squeeze `single-unit QA`.
4. Chi sau do moi quay lai E2E benchmark.

## Ket luan

Phat hien lon nhat la workflow hien tai da toi uu sai bai toan. He thong khong "vo dung"; no dang bi van hanh bang mot gate sai muc tieu.

Reset dung la:

- tu `single-unit QA hard gate`
- sang `reference-style seed workbook`

Builder moi da duoc them va da chay that. Output cho thay co the khoi phuc lai quy mo seed tuong duong workbook tham chieu, dong thoi phoi bay ro contamination cua corpus hien tai de xu ly dung lop.
