# Pipeline eval sheet v1 - 2026-06-09

## Muc tieu

Tao workbook de team co the do output pipeline vao va doi chieu truc tiep voi `gold_answer` cua `golden_set_v1`.

## Artifact

- `data/golden_set/pipeline_eval_sheet_v1_20260609.xlsx`
- `data/golden_set/pipeline_eval_input_v1_20260609.csv`

## Cau truc workbook

- `Info`: huong dan cach dung nhanh.
- `GoldSet`: ban sao `golden_set_v1` de doi chieu.
- `PipelineInput`: sheet de dan output pipeline vao cac cot mau vang.
- `Score`: sheet doi chieu theo tung `question_id`, co auto check exact match va evidence record match.
- `Summary`: tong hop so cau da tra loi, exact match va diem trung binh.

## Ghi chu

- Auto check trong `Score` chi la check ky thuat muc co ban (`EXACT` text va `evidence_record_id`).
- Cac cau tra loi dien dat khac nhung van dung can reviewer dien `manual_answer_score` / `manual_evidence_score`.
- `manual_forbidden_violation = 1` se keo `final_score` ve `0`.
- Workbook nay phu hop de bat dau phase cham pipeline voi tap `golden_set_v1` hien tai (6 cau).
