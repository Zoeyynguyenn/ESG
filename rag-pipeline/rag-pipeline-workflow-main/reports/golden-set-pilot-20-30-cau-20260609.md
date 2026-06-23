# Golden Set - Danh sach pilot cau hoi chuan (2026-06-09)

## Muc tieu

Chon mot bo pilot nho de bat dau voi team Dataset truoc khi di sang buoc `ground_truth_answer`.

Bo pilot nay duoc trich tu:

- `26.03.27 ESG-정량 - 26.03.27 ESG-정량.csv`
- `26.03.27 ESG-정성 - 26.03.27 ESG-정성.csv`

## Ket qua chon pilot

- Tong so cau: `29`
- Dinh luong: `15`
- Dinh tinh: `14`

## Nguyen tac chon

1. Co du `E / S / G`
2. Co du cau hoi de cham tu dong de (`number`, `percentage`)
3. Co du cau hoi can rubric danh gia mo ta (`long_text`)
4. Uu tien nhung chu de business de gap:
   - nhan su
   - an toan
   - moi truong
   - dao duc / compliance
   - bao mat thong tin

## File chinh

Danh sach pilot da duoc dua vao:

- `data/golden_set/pilot_question_bank_20260609.csv`

## Co cau pilot

### Dinh luong

- Social:
  - tong nhan su
  - ty le nu
  - ty le chinh thuc
  - ty le lao dong khuyet tat
  - tong tuyen moi
  - ty le nghi viec tu nguyen
  - ty le quay lai sau nghi thai san/cham soc con
  - so nhan su tham gia dao tao an toan
  - LTIFR
- Environment:
  - tong phat thai khi nha kinh
  - ty le nang luong tai tao
  - ty le tai che chat thai
  - so vu vi pham moi truong
- Governance:
  - so vu to cao dao duc
  - ty le hoan thanh dao tao dao duc

### Dinh tinh

- General ESG:
  - tam nhin va chien luoc ESG
  - co che quan tri ESG
  - co che quan ly rui ro ESG
- Social:
  - chinh sach va muc tieu an toan
  - to chuc quan ly an toan
  - phong ngua rui ro an toan lao dong
  - chinh sach lao dong va nhan quyen
  - he thong quan ly lao dong va nhan quyen
  - chinh sach bao mat thong tin
  - quan ly rui ro an toan va chat luong san pham
- Environment:
  - chinh sach va muc tieu moi truong
  - quan ly tac dong va rui ro moi truong
- Governance:
  - co che quan tri dao duc
  - quan ly rui ro dao duc va tuan thu

## Ghi chu

1. Buoc nay chi chot wording cau hoi pilot.
2. Chua tim dap an dung.
3. Chua gan evidence page/chunk.
4. Chua cham pipeline.

## Buoc tiep theo

1. Team Dataset/SME review wording 29 cau.
2. Chot cau nao giu, cau nao bo, cau nao tach nho.
3. Sau do moi di sang:
   - `ground_truth_answer`
   - `evidence_anchor`
   - `scoring_rule`
   - file Excel review
