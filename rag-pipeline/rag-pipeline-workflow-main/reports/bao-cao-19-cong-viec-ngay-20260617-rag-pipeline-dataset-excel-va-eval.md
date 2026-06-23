# Bao cao cong viec ngay 2026-06-17

## 1. Muc tieu cua workstream

Muc tieu cua team `RAG pipeline` trong workstream nay la bien bo du lieu do team Dataset ban giao thanh mot quy trinh co the danh gia duoc chat luong. Dau vao khong chi gom workbook Excel ESG, ma con gom cac file JSON/DART ma team Dataset thu thap them de bo sung provenance va noi dung goc.

Ket qua cuoi cung ma team RAG can bao cao khong chi la "tra loi duoc hay khong", ma phai kem theo:

- `retrieval_hit_rate`
- `answer_accuracy`
- `abstain_accuracy`
- `source_match_rate`
- `overall_score`

Trong giai doan hien tai, team dang hoan tat tang du lieu va source intake de dam bao khi chay RAG va tinh diem, ket qua se dang tin.

## 2. Flow tong quat cua team RAG pipeline

### Buoc 1. Nhan du lieu tu team Dataset

Dau vao hien tai gom 2 lop:

1. Workbook Excel ESG
   - chua danh sach cau hoi
   - dap an do team Dataset da tim duoc
   - trang thai `Not disclosed`
   - thong tin source nhu `Source URL`, `File URL`, `Source document/page`
2. Bo file JSON/DART di kem
   - cac file `DART_주요정보`
   - cac file `DART_재무`
   - cac local source duoc dung de bo sung provenance va phuc vu parser lane rieng

### Buoc 2. Chuan hoa du lieu thanh artifact may xu ly duoc

Workbook duoc tach thanh 3 nhom artifact:

- `questions`
- `gold_answers`
- `sources`

Muc tieu cua buoc nay la bien dau vao thu cong thanh bo du lieu co cau truc, co the benchmark va lap lai duoc.

### Buoc 3. Lam sach bo eval truoc khi chay RAG

Khong phai tat ca dong trong workbook deu san sang de benchmark ngay. Vi vay team RAG chia bo du lieu thanh:

- `answerable_gold`
- `abstain_gold`
- `needs_review`

Buoc nay giup tach ro:

- cau co dap an va co source de doi chieu
- cau ma he thong can abstain
- cau can xem lai provenance hoac nghia nghiep vu

### Buoc 4. Source intake

Sau khi co `sources`, team RAG chia source thanh 2 lane:

- `crawl_web`
- `resolve_local_file_first`

Day la buoc quan trong de tranh nham lan giua:

- filing page tren web
- va file local JSON/DART moi la noi dung goc can parse va chunk

### Buoc 5. Parse, chunk, va xay dung corpus

Moi source sau khi vao dung lane se duoc:

1. parse raw content
2. chuan hoa metadata
3. tach thanh chunk
4. dua vao corpus/index de phuc vu retrieval

### Buoc 6. Chay RAG

Khi corpus da san sang, team RAG moi chay:

1. retrieval
2. evidence selection
3. answer generation hoac abstain
4. gan lai source/provenance

### Buoc 7. So voi gold va bao cao metrics/score

Ket qua RAG se duoc doi chieu theo `question_id` voi bo `answerable_gold` va `abstain_gold`.

Bao cao cuoi cung se gom 2 lop:

1. Coverage
   - tong so cau
   - so cau answerable
   - so cau abstain
   - so cau da chay
   - so cau bi skip/block
2. Metrics va score
   - `retrieval_hit_rate`
   - `answer_accuracy`
   - `abstain_accuracy`
   - `source_match_rate`
   - `overall_score`

### Buoc 8. Cai thien va chay lai

Neu score chua dat, team RAG se cai thien tung lop:

- source mapping
- parser/chunking
- retrieval
- reranking
- generation guardrails

Sau do chay lai eval va cap nhat metrics/score.

## 3. Tien do hien tai

Tinh den hom nay, team RAG da hoan tat:

- tiep nhan va ingest workbook Excel ESG
- tiep nhan va noi local JSON/DART package vao source lane
- tao bo `eval-ready`
- chuan bi xong web source va local source cho buoc parse/chunk

Team chua o buoc chay RAG benchmark cuoi cung, nen chua bao cao score tong hop. Tuy nhien, tang du lieu va source intake da dat muc san sang de di tiep sang buoc chunk/index va chay RAG.

## 4. Ket qua hien tai

### 4.1. Dau vao da duoc xu ly lai

Hai workbook dang duoc dung:

- `C:\Users\nguye\Downloads\data-company\dataset-excel\골드앤에스_Final_ESG_Data.xlsx`
- `C:\Users\nguye\Downloads\data-company\dataset-excel\이엠앤아이_Final_ESG_Data.xlsx`

Ngoai workbook, team Dataset da bo sung them local JSON trong:

- `C:\Users\nguye\Downloads\data-company\dataset-excel\output_restart_emni_20260617\output_restart_emni_20260617\이엠앤아이_일반자료_20260617\02_재무_신용`
- `C:\Users\nguye\Downloads\data-company\dataset-excel\output_restart_goldns_20260616\output_restart_goldns_20260616\골드앤에스_일반자료_20260616\02_재무_신용`

### 4.2. Bo eval-ready hien tai

Sau khi xu ly lai workbook `emni` moi va chay lai chuoi `ingest -> reconcile -> validate`, ket qua hien tai la:

- `goldns`
  - `24 answerable`
  - `227 abstain`
  - `0 needs_review`
- `emni`
  - `43 answerable`
  - `236 abstain`
  - `0 needs_review`

Nghia la ca hai cong ty hien da co bo eval-ready co the dung cho benchmark.

### 4.3. Tinh trang source intake

Sau khi chay lai source prep:

- tong unique source: `18`
- `crawl_web`: `4`
- `resolve_local_file_first`: `14`
- `needs_review`: `0`

Phan bo theo company:

- `emni`: `13` source
  - `1` web
  - `12` local JSON
- `goldns`: `5` source
  - `3` web
  - `2` local JSON

### 4.4. Tinh trang local JSON collect

Sau khi chay local source collector tren manifest moi nhat:

- tong local source: `14`
- collect thanh cong: `14/14`
- fail: `0`

Phan bo schema:

- `dart_financial_statement`: `3`
- `dart_employee_status`: `5`
- `dart_executive_status`: `3`
- `dart_board_director_change`: `3`

Artifact da duoc tao tai:

- `data/source_raw/20260617_goldns_emni_local/`

Moi source local sau khi collect co:

- `source_manifest.json`
- `extracted.txt`
- `records.jsonl`
- `raw.json`

### 4.5. Tinh trang web source

Tren lane web, team da tai raw source truoc do:

- tong web source: `9`
- tai thanh cong: `8`
- con `1` source bi block boi redirect loop cua site FTC

Backlog nay khong chan local JSON lane, nhung van can xu ly de hoan tat corpus web.

## 5. Ghi chu nghiep vu quan trong

Trong bo `emni`, team Dataset bo sung du du lieu 2024, nhung doi voi lane tai chinh:

- khong co `2024_재무_CFS.json`
- co `2024_재무_OFS.json`

Team RAG da xu ly provenance theo huong do va dua cac cau lien quan ve `answerable_gold`.

Tuy nhien, van con mot diem can giu de SME audit:

- `emni-0237`
  - gia tri `1487` trong `2024_재무_OFS.json`
  - hien khop voi account `당기순이익(손실)`
  - chua co bang chung du manh de khang dinh map nghiep vu "세금 및 공과 + 법인세" la hoan toan dung

Noi cach khac, provenance da du, nhung semantic mapping cua row nay van nen duoc theo doi rieng.

## 6. Ket luan va buoc tiep theo

Tinh den hom nay, team RAG da hoan tat phan "du lieu va source intake" cho 2 cong ty. Day la tang nen bat buoc truoc khi chay RAG benchmark co metrics va score.

Buoc tiep theo cua team la:

1. chunk/index hop nhat local JSON va web raw source
2. noi eval runner theo `question_id`
3. chay RAG tren bo `answerable_gold` va `abstain_gold`
4. bao cao `retrieval_hit_rate`, `answer_accuracy`, `abstain_accuracy`, `source_match_rate`, `overall_score`
5. neu ket qua chua dat thi cai thien pipeline va chay lai
