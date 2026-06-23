# Working set v1 - 20 cau thuc dung - 2026-06-09

## Muc tieu

Tao mot `working set` lon hon `golden_set_v1` de workbook cham pipeline dung duoc thuc te hon, nhung van ghi ro muc do tin cay cua tung cau.

## Nguyen tac chon

- Khong dung `dataset_issue` cua `레이시온` va `무신사`.
- Lay toan bo `20` cau shortlist cua `한샘`.
- Mapping trang thai:
  - `filled_from_dataset` -> `grounded`
  - `partial_from_dataset` -> `partial`
  - `not_found_in_current_dataset` -> `needs_review`

## Ket qua

- Tong so cau: 20
- Cong ty: `한샘`
- Phan bo trang thai: grounded (6), needs_review (12), partial (2)

## Danh sach

| Question ID | Type | Area | Working Status | Review Action |
|---|---|---|---|---|
| QT-001 | quantitative | 사회 | needs_review | review_before_scoring |
| QT-002 | quantitative | 사회 | needs_review | review_before_scoring |
| QT-005 | quantitative | 사회 | needs_review | review_before_scoring |
| QT-006 | quantitative | 사회 | needs_review | review_before_scoring |
| QT-009 | quantitative | 사회 | needs_review | review_before_scoring |
| QT-010 | quantitative | 환경 | needs_review | review_before_scoring |
| QT-011 | quantitative | 환경 | needs_review | review_before_scoring |
| QT-013 | quantitative | 환경 | needs_review | review_before_scoring |
| QT-014 | quantitative | 거버넌스 | needs_review | review_before_scoring |
| QT-015 | quantitative | 거버넌스 | needs_review | review_before_scoring |
| QL-001 | qualitative | 일반 | grounded | use_for_eval_now |
| QL-003 | qualitative | 일반 | grounded | use_for_eval_now |
| QL-004 | qualitative | 사회 | grounded | use_for_eval_now |
| QL-006 | qualitative | 사회 | needs_review | review_before_scoring |
| QL-008 | qualitative | 사회 | grounded | use_for_eval_now |
| QL-009 | qualitative | 사회 | needs_review | review_before_scoring |
| QL-011 | qualitative | 환경 | grounded | use_for_eval_now |
| QL-012 | qualitative | 환경 | grounded | use_for_eval_now |
| QL-013 | qualitative | 거버넌스 | partial | review_before_scoring |
| QL-014 | qualitative | 거버넌스 | partial | review_before_scoring |

## Cach dung

- `grounded`: co the dung de cham ngay.
- `partial`: co the dua vao eval sheet, nhung reviewer nen xac nhan truoc khi ket luan.
- `needs_review`: giu lai de du 20 cau cho vong lam viec; chua nen coi la gold answer hoan chinh.
