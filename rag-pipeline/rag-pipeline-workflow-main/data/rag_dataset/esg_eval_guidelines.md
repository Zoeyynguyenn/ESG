# ESG Eval Guidelines

## 1. Muc tieu

Huong dan danh gia chat luong cau tra loi RAG tren bo ESG dataset theo 4 truc:

- answer correctness
- expected source matching
- groundedness
- citation quality

## 2. Danh gia dung/sai cau tra loi

### 2.1 Correct

- Tra loi dung thong tin cot loi theo `Expected Answer Notes`.
- Khong them khang dinh khong co trong context.

### 2.2 Partially correct

- Dung y chinh nhung thieu so lieu/ngo canh quan trong.
- Co sai nho khong anh huong ket luan chinh.

### 2.3 Incorrect

- Sai du kien quan trong (so lieu, nam, policy, threshold).
- Tra loi lac de, hoac suy doan khong co bang chung.

## 3. Danh gia expected source

### 3.1 Matched

- Co it nhat 1 citation dung tai lieu trong `Expected Source`.
- Neu la cau multi-hop, can cover tat ca tai lieu chinh trong expected set.

### 3.2 Weak match

- Citation co lien quan nhung chua trung tai lieu expected.
- Hoac trung tai lieu nhung khong trung section quan trong.

### 3.3 Mismatch

- Khong co citation hoac citation sai nguon.

## 4. Danh gia groundedness

- High: moi khang dinh chinh deu co bang chung trong context.
- Medium: phan lon co bang chung, con 1-2 y suy dien nhe.
- Low: nhieu y khong co bang chung, de hallucinative.

## 5. Danh gia citation

- Day du: trich dan du tai lieu (va section/page neu co).
- Thieu: co citation nhung thieu vi tri hoac qua chung chung.
- Kem: khong citation, citation sai, hoac citation khong lien quan.

## 6. Quy tac cho cau hoi "khong du thong tin"

Voi nhom cau hoi `insufficient`:

1. Cau tra loi dung phai neu ro "khong du thong tin trong context/tai lieu".
2. Khong duoc suy doan so lieu/ten rieng/ket qua khong co.
3. Neu muon de xuat buoc tiep, chi de xuat can them tai lieu nguon, khong ket luan thay.

## 7. De xuat rubric nhanh (0-2)

- Correctness: 0 sai, 1 mot phan, 2 dung.
- Source match: 0 sai, 1 mot phan, 2 dung.
- Groundedness: 0 thap, 1 trung binh, 2 cao.
- Citation: 0 kem, 1 thieu, 2 day du.

Tong 8 diem/cau de so sanh giua cac version.
