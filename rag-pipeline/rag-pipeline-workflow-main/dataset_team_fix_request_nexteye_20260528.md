# Yeu Cau Dieu Chinh Package Dataset Nexteye

Package duoc review:

`data/rag_dataset/05_company_export_json/넥스트아이_dataset_package_20260528T082146`

## Huong Bai Toan

Muc tieu cua dataset khong phai xep hang ESG chinh thuc, khong phai tao ESG Passport, va khong phai thay cong viec cua co quan bao cao ESG.

Muc tieu dung la giup SME nhanh chong chuan bi du lieu phan hoi ESG co bang chung cho khach hang, to chuc tai chinh, nha dau tu va nguoi mua xuat khau.

## Ket Luan Ngan

Package da dung format contract v1.1 va co the dung de ingest/smoke test. Cac diem can sua ben duoi nham giu dung huong "ESG response data readiness", khong day team Dataset sang huong ESG rating.

## Can Dieu Chinh Truoc Khi Benchmark Chinh

1. Tach ro `company_evidence`, `requirement_taxonomy`, va `ai_extracted_response`
   - Hien tai `splits/full.jsonl` la derived summary lane (`is_raw_text=false`, `is_derived_summary=true`).
   - Derived summary/AI response la can thiet cho bai toan nay, nhung khong nen tron voi evidence goc trong cung lane.
   - De xuat tach thanh cac lane/file:
     - `company_evidence`: du lieu cong khai/noi bo toi thieu cua doanh nghiep.
     - `requirement_taxonomy`: yeu cau ESG tu khach hang/finance/export buyer/framework.
     - `ai_extracted_response`: cau tra loi/field duoc AI trich xuat, bat buoc co `derived_from_doc_ids`.

2. Bo sung traceability cho public/internal source
   - Hien tai gan nhu tat ca `source_url=null`.
   - Voi internal source co the null, nhung voi news/web/public source can map URL goc.
   - Neu khong co URL, can co `metadata.source_path`, `source_system`, va ly do null ro trong `known_issues.md`.

3. Lam ro loai gia tri trong `metric`
   - Khong yeu cau chi co ESG metric dinh luong chinh thuc.
   - Nhung can tach ro:
     - `company_reported_metric`: so lieu doanh nghiep cong bo.
     - `requirement_metric`: chi so/yeu cau can phan hoi.
     - `internal_score`: relevance/confidence/completeness score.
   - Cac score noi bo nhu confidence/completeness `100%` khong nen nam trong `metric` nhu ESG metric cua doanh nghiep; nen de trong `metadata`.

4. Chuan hoa lai `source_type`
   - Mot so record DART/news/taxonomy/requirement dang bi gan source type chua dung nghia, vi du `annual_report` hoac `policy`.
   - Can map theo nguon that, vi source type se duoc dung de route truy xuat va giai thich bang chung.
   - Neu record la requirement/framework/taxonomy, nen co source type rieng hoac metadata `record_role=requirement`, khong xem nhu evidence cong ty.

5. Giu taxonomy/requirement, nhung dat dung vai tro
   - Cac record dang mo ta requirement/K-ESG taxonomy khong phai evidence cong bo cua cong ty.
   - Khong bo cac record nay, vi bai toan can biet doanh nghiep phai phan hoi yeu cau nao.
   - Tuy nhien chung phai o lane/vai tro rieng de pipeline co the match `requirement -> company evidence -> AI response`.

6. Xem lai `doc_id` granularity
   - Manifest ghi `273 records`, `272 documents`, gan nhu moi record la mot document.
   - Neu nhieu record den tu cung mot file goc, nen dung chung `doc_id` de trace citation va debug de hon.

## Co The Chap Nhan Tam Thoi

- Dung `splits/dev.jsonl` va `splits/validation.jsonl` de smoke test ingest/retrieval.
- Dung summary/AI response lane de test extraction/reporting, nhung khong dung no de cham retrieval evidence goc.
- Chua dung `splits/full.jsonl` de chot model retrieval cho den khi vai tro raw/summary/requirement duoc tach ro.

## Definition of Ready

Package duoc xem la benchmark-ready khi:

1. Co lane raw company evidence de benchmark retrieval/citation.
2. Co lane requirement/taxonomy de benchmark kha nang map yeu cau ESG ben ngoai.
3. Co lane AI extracted response/summary co `derived_from_doc_ids` de benchmark extraction/reporting.
4. `source_url` hoac `metadata.source_path/source_system` du truy vet.
5. `metric` phan biet company metric, requirement metric va internal score.
6. `source_type`, `record_role`, va `doc_id` duoc map dung nguon.
