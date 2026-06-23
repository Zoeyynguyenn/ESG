# Bao cao tom tat gui sep - 2026-06-17

## 1. Muc tieu cua team RAG

Team `RAG pipeline` nhan du lieu tu team Dataset, xu ly source, chay RAG, so ket qua voi `gold answer`, sau do bao cao bang `metrics` va `score`.

## 2. Flow cong viec

1. Nhan workbook Excel ESG va bo file JSON/DART di kem tu team Dataset.
2. Chuan hoa du lieu thanh `questions`, `gold_answers`, `sources`.
3. Lam sach bo eval thanh:
   - `answerable_gold`
   - `abstain_gold`
   - `needs_review`
4. Chia source thanh 2 lane:
   - `crawl_web`
   - `resolve_local_file_first`
5. Parse, chunk, build corpus.
6. Chay RAG.
7. So voi gold va bao cao:
   - `retrieval_hit_rate`
   - `answer_accuracy`
   - `abstain_accuracy`
   - `source_match_rate`
   - `overall_score`
8. Neu score chua dat, cai thien pipeline va chay lai.

## 3. Tien do hien tai

Team da hoan tat tang du lieu va source intake, chua den buoc chay RAG benchmark cuoi cung.

### Eval-ready hien tai

- `goldns`: `24 answerable`, `227 abstain`, `0 needs_review`
- `emni`: `43 answerable`, `236 abstain`, `0 needs_review`

### Source intake hien tai

- tong unique source: `18`
- `crawl_web`: `4`
- `resolve_local_file_first`: `14`
- local JSON collect: `14/14 ok`

## 4. Ket qua quan trong hom nay

1. Da xu ly lai workbook `이엠앤아이_Final_ESG_Data.xlsx` ban moi nhat.
2. Da dua ca 2 cong ty ve trang thai `0 needs_review`.
3. Da noi local JSON/DART package vao source lane dung cach.
4. Da co raw local source san sang cho buoc chunk/index.

## 5. Luu y

- Chua co `metrics/score` cuoi cung, vi he thong chua chay xong buoc `chunk -> index -> RAG -> eval`.
- Co 1 diem can theo doi nghiep vu:
  - `emni-0237` da du provenance, nhung semantic mapping van nen SME audit them.

## 6. Buoc tiep theo

1. Hop nhat local JSON va web raw source.
2. Chunk/index corpus.
3. Noi eval runner theo `question_id`.
4. Chay RAG va bao cao `metrics/score`.
