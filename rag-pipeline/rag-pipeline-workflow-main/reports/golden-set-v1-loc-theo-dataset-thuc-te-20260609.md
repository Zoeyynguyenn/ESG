# Golden set V1 loc theo dataset thuc te - 2026-06-09

## Muc tieu

Chot mot `golden set v1` nho, chi gom cac cau hoi co the doi chieu chac chan voi dataset `05_company_export_json` hien tai.

## Tieu chi giu lai

- Chi giu cac dong co `fill_status = filled_from_dataset`.
- Loai bo toan bo `partial_from_dataset`, `not_found_in_current_dataset`, `dataset_issue`.
- Khong co dich thuat; `question`, `gold_answer`, `evidence_excerpt` giu Korean-only.
- Moi dong phai tro duoc ve `company_evidence` bang `evidence_record_id`.

## Ket qua loc

- Tong so dong trong `golden_set_v1`: 6
- Pham vi cong ty: 한샘 (6)
- Phan bo theo vung: 사회 (2), 일반 (2), 환경 (2)
- Tat ca cau hoi trong v1 hien la `qualitative`.

## Danh sach cau giu lai

| Company | Question ID | Area | Category | Question (KO) | Evidence Record |
|---|---|---|---|---|---|
| 한샘 | QL-001 | 일반 | ESG 경영 | 회사의 ESG 비전 및 중장기 전략은 무엇인가요? | rec_66100907c00656ec |
| 한샘 | QL-003 | 일반 | ESG 경영 | 회사는 ESG 리스크를 어떻게 식별하고 관리하나요? | rec_86c98b945fc03e6d |
| 한샘 | QL-004 | 사회 | 안전 보건 | 안전보건 정책 및 목표는 무엇인가요? | rec_66100907c00656ec |
| 한샘 | QL-008 | 사회 | 노동 및 인권 | 노동 및 인권 관리 체계는 어떻게 운영되나요? | rec_86c98b945fc03e6d |
| 한샘 | QL-011 | 환경 | 환경경영 | 환경경영 정책 및 목표는 무엇인가요? | rec_66100907c00656ec |
| 한샘 | QL-012 | 환경 | 환경경영 | 환경 영향과 환경 리스크를 어떻게 평가하고 관리하나요? | rec_86c98b945fc03e6d |

## Ghi chu van hanh

- Tap v1 nay dung de chay thu pipeline accuracy tren cac cau hoi dinh tinh co bang chung ro.
- Khong nen dung tap nay de ket luan nang luc dinh luong, do hien chua co cau dinh luong nao duoc chung minh chac chan.
- Khong nen xem tap nay la representative cho du 3 cong ty; hien tai no phan anh phan dataset co chat luong dung duoc ngay.
