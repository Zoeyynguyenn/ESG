# Enterprise internal-doc — Answerability classification (câu không rõ / không có thông tin)

Ngày: 2026-06-22
Artifact: `reports/enterprise_docs_answerability_classification_20260622`

## Vấn đề

Bộ phân loại natural-case cũ gộp **mọi** câu "không tìm được candidate" vào
`corpus_limited_no_candidate`. Một câu hỏi *không rõ / lạc đề / không thuộc metric family
nào* bị nhầm thành "thiếu tài liệu", khiến reviewer đi thu thập thêm tài liệu trong khi
vấn đề thật nằm ở **câu hỏi**.

Cải tiến này thêm trục thứ ba còn thiếu: **khả năng trả lời của câu hỏi**.

## Thay đổi

- Thêm `test_type = "answerability_probe"` + capability `answerability_classification`.
- Bộ phân loại dùng đúng `_family_for_probe` (routing của lane) để quyết định:
  - `out_of_scope` — câu không map được vào metric family nào.
  - `no_information` — family hợp lệ nhưng giá trị không công bố → honest abstain.
  - `answerable` — family hợp lệ và giá trị có trong corpus.
- Thêm `abstain_safety_rate`: tỷ lệ câu *không trả lời được* mà hệ thống không trả lời bừa.
- Các case answerability **không** mang 5 tín hiệu regression → **gate giữ nguyên 100%**.

## Kết quả trên eval set (18 case, gồm cả case khó)

| Chỉ số | Giá trị |
|---|---:|
| answerability_accuracy | 83.3% (15/18) |
| abstain_safety_rate | 90.9% (10/11) |
| Regression gate (5 metric) | 100% — không đổi |

Confusion (expected → predicted):

- answerable → answerable 6, no_information 1
- out_of_scope → out_of_scope 5
- no_information → no_information 4, out_of_scope 1, answerable 1

Lưu ý: đây là eval khởi đầu tự xây (smoke + adversarial), **chưa phải benchmark trên dữ
liệu thật**. Mục tiêu là kiểm chứng cơ chế và lộ giới hạn, không phải con số PR.

## Giới hạn đã biết (3 case adversarial cố tình để lộ)

1. `ADV-NO-KEYWORD` — câu ESG không có từ khóa → routing trả None → bị xếp `out_of_scope`
   thay vì `no_information` (heuristic phụ thuộc từ khóa).
2. `ADV-TOKEN-FALSEPOS` — corpus nhắc "Scope 3" nhưng không có giá trị → bị xếp
   `answerable` (so token bỏ qua việc có giá trị thật). Đây là case **abstain-unsafe**.
3. `ADV-PHRASING` — giá trị có nhưng diễn đạt khác → `no_information` thay vì `answerable`
   (so khớp item theo chuỗi chính xác).

## Bước tiếp theo (khi có dữ liệu thật)

- Thay so-token bằng kiểm tra có giá trị số gắn với metric (giảm false-positive abstain-unsafe).
- Mở rộng từ điển/registry family để giảm phụ thuộc từ khóa.
- Mở rộng eval bằng câu hỏi thật từ corpus doanh nghiệp.
