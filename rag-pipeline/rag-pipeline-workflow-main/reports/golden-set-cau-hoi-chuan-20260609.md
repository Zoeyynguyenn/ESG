# Golden Set - Cau hoi chuan (nhap 1)

## Muc tieu

Chot mot bo cau hoi chuan o muc co the dung ngay de giu dung muc tieu:

1. Ra de truoc.
2. Chot dap an dung sau.
3. Chay pipeline de lay bai lam cua he thong.
4. So sanh voi dap an dung de cham diem.

Tai lieu nay chi chot phan **cau hoi chuan** dua tren 2 file mau:

- Dinh luong: `26.03.27 ESG-정량 - 26.03.27 ESG-정량.csv`
- Dinh tinh: `26.03.27 ESG-정성 - 26.03.27 ESG-정성.csv`

Chua di sang buoc tim `ground_truth_answer`.

## Tom tat dau vao

### 1. Mau dinh luong

- So dong: `251`
- Cot chinh:
  - `영역`
  - `카테고리`
  - `서브카테고리`
  - `항목`
  - `기준 및 설명`
  - `단위`
  - `GRI`
  - `SASB`
  - `KBIZ`
  - `K-ESG`
- Nhom lon nhieu dong:
  - `사회 / 구성원 현황`
  - `사회 / 일과 삶의 균형 지원`
  - `거버넌스 / 윤리 모니터링`
  - `환경 / 수자원`
  - `환경 / 온실가스 및 에너지`

### 2. Mau dinh tinh

- So dong: `27`
- Cot chinh:
  - `영역`
  - `카테고리`
  - `구분 (4 Pillars)`
  - `항목`
  - `설명`
  - `예시`
- 4 tru cot ro rang:
  - `전략 (Strategy)`
  - `거버넌스 (Governance)`
  - `위험 관리 (Risk Management)`
  - `지표 (Metrics)`

## Nguyen tac chot cau hoi

1. Moi dong trong file mau la **mot seed de bai**, nhung chua chac da la cau hoi cuoi cung.
2. Cau hoi chuan phai viet theo goc nhin nguoi review/SME, khong giu nguyen ten truong ky thuat neu kho doc.
3. Chua nhung thong tin nao thuoc ve dap an dung trong phan cau hoi.
4. Moi cau hoi phai co `answer_type` ro rang ngay tu dau:
   - `number`
   - `percentage`
   - `boolean`
   - `short_text`
   - `long_text`
   - `list`
5. Moi cau hoi phai duoc danh dau:
   - `quantitative`
   - `qualitative`
6. Moi cau hoi phai du kien truoc kha nang "cam tra loi" hoac "phai tra insufficient".

## Bo cau hoi chuan - Dinh luong

### 1. Dinh dang cau hoi de xuat

Cong thuc uu tien:

`[Cong ty] trong [nam/ky bao cao], [chi so] la bao nhieu?`

Neu can tach theo thanh phan:

`[Cong ty] trong [nam/ky bao cao], [chi so] cua [doi tuong/thanh phan] la bao nhieu?`

### 2. 6 mau cau hoi dinh luong chuan

1. Gia tri tong:
   - Vi du: `Tong so nhan su cua cong ty trong nam bao cao la bao nhieu?`

2. Ty le / phan tram:
   - Vi du: `Ty le nhan su nu trong tong lao dong la bao nhieu phan tram?`

3. Co cau theo nhom:
   - Vi du: `So lao dong chinh thuc nu la bao nhieu?`

4. Chi so theo don vi ESG:
   - Vi du: `Luong nuoc su dung trong nam bao cao la bao nhieu?`

5. Chi tieu compliance / incident:
   - Vi du: `So vu vi pham bao mat thong tin ca nhan trong nam la bao nhieu?`

6. Chi so target / progress:
   - Vi du: `Muc tieu giam phat thai Scope 1 va 2 la bao nhieu?`

### 3. Quy tac viet lai tu file mau

- Neu `서브카테고리` co gia tri va `항목` rong:
  - Cau hoi dua tren `서브카테고리`
- Neu `서브카테고리` va `항목` deu co gia tri:
  - Cau hoi dua tren ca hai
- Neu `단위` la `%`:
  - Uu tien wording `ty le ... la bao nhieu phan tram?`
- Neu `단위` la `명`:
  - Uu tien wording `so luong ... la bao nhieu?`
- Neu la metric moi truong:
  - Nho giu ro don vi trong metadata du khong can dua het vao cau hoi

### 4. Khong nen lam luc nay

- Chua tranh luan dung/sai theo source.
- Chua chot evidence page/chunk.
- Chua gop cac cau hoi gan nhau neu chua co SME review.

## Bo cau hoi chuan - Dinh tinh

### 1. Dinh dang cau hoi de xuat

Cong thuc uu tien:

`Cong ty mo ta [chu de] nhu the nao?`

Hoac:

`Cong ty co nhung noi dung nao lien quan den [chu de]?`

Tuy tru cot 4 Pillars:

- `Strategy`: hoi ve dinh huong, muc tieu, chien luoc
- `Governance`: hoi ve to chuc, vai tro, co che ra quyet dinh
- `Risk Management`: hoi ve cach nhan dien, danh gia, quan ly rui ro
- `Metrics`: hoi ve KPI, chi tieu, ket qua, cach theo doi

### 2. 4 mau cau hoi dinh tinh chuan theo 4 Pillars

1. Strategy:
   - `Cong ty mo ta chien luoc [chu de ESG] nhu the nao?`

2. Governance:
   - `Co che quan tri va ra quyet dinh lien quan den [chu de ESG] duoc to chuc ra sao?`

3. Risk Management:
   - `Cong ty nhan dien va quan ly rui ro lien quan den [chu de ESG] nhu the nao?`

4. Metrics:
   - `Cong ty su dung chi tieu nao de theo doi [chu de ESG], va bao cao ket qua ra sao?`

### 3. Quy tac viet lai tu file mau

- `항목` se la hat nhan cau hoi.
- `설명` dung de lam ro muc tieu cua cau hoi.
- `예시` chi la tham khao de hieu y, khong duoc coi la dap an dung.
- Neu cau hoi qua rong:
  - Tach thanh 2 cau nho hon truoc khi di toi giai doan dap an dung.

## Schema toi thieu cho question bank

Bo cau hoi chuan chua can dap an dung, nhung nen co cac cot sau ngay tu dau:

- `question_id`
- `question_type`
- `domain`
- `category`
- `subcategory`
- `pillar`
- `item`
- `question_text_ko`
- `question_text_vi`
- `answer_type`
- `unit`
- `framework_refs`
- `forbidden_rule`
- `must_return_insufficient_if_missing`
- `notes`
- `status`

## Tieu chi de goi la "cau hoi chuan"

Mot cau hoi duoc xem la chuan khi:

1. Doc doc lap van hieu duoc khong can xem ten cot goc.
2. Biet ro can tra ve dang dap an nao.
3. Khong lo dap an vao trong cau hoi.
4. Co the giao cho team Dataset di tim dap an dung.
5. Co the dua vao Excel review sau nay.

## Pham vi chot o buoc nay

Da chot:

- Khung cau hoi dinh luong
- Khung cau hoi dinh tinh
- Schema toi thieu cho question bank
- Nguyen tac de chuyen tu file mau thanh bo de bai chuan

Chua chot:

- Dap an dung
- Evidence position
- Rubric cham diem chi tiet
- Mapping 1-1 toan bo 251 + 27 dong thanh final golden set

## Buoc tiep theo de xuat

1. Dung template CSV de bat dau nhap bo cau hoi chuan.
2. Chon 20-30 cau dai dien de lam pilot truoc:
   - 10-15 cau dinh luong
   - 10-15 cau dinh tinh
3. Sau khi khoa wording cau hoi, moi sang buoc tim `ground_truth_answer`.
