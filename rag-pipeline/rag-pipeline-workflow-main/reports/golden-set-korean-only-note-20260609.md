# Golden Set - Korean only nguyen tac (2026-06-09)

## Ket luan moi

Tu buoc nay tro di, bo golden set uu tien **Korean-only** cho cac truong truc tiep anh huong den danh gia:

- question
- ground truth answer
- evidence text
- prohibited claims
- reviewer notes chinh

Ly do:

1. Giam sai lech do dich qua lai giua Korean va Vietnamese.
2. Giam nguy co mat y trong cau hoi dinh tinh.
3. Giam nguy co trich dan sai do span/evidence bi doi nghia khi doi ngon ngu.
4. Phu hop hon voi corpus Nexteye va cac bao cao goc dang o Korean.

## Bai hoc rut ra tu file mau Excel

File mau `TalkFile_golden_worksheet_v1.xlsx.xlsx` cho thay 3 diem nen hoc theo:

1. Golden set nen duoc quan ly bang `worksheet` co quy trinh review, khong chi la CSV ky thuat.
2. Moi dong nen co dong thoi:
   - seed / cau hoi
   - facts tuple
   - acceptable disclosure
   - prohibited claims
   - reviewer / status / notes
3. `prohibited_claims` la truong bat buoc, vi day la cach ngan mo hinh "noi qua" hoac "suy dien qua muc".

## Tac dong den artifact hien tai

1. Shortlist review chuyen sang ban Korean-only:
   - `data/golden_set/pilot_question_bank_shortlist_ko_20260609.csv`
2. Ban bilingual truoc do chi giu de doi chieu noi bo, khong dung lam worksheet chinh.
3. Golden worksheet sap toi nen dung ten cot va noi dung review bang Korean.

## Buoc tiep theo de xuat

1. Dung shortlist Korean-only lam input review chinh.
2. Tao workbook `.xlsx` theo tinh than file mau:
   - `안내`
   - `작성`
   - `참조`
3. Sau khi chot cau hoi moi di tiep sang:
   - `정답(gold answer)`
   - `근거 위치`
   - `금지 주장`
   - `채점 규칙`
