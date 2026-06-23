# Answerability eval mở rộng (~200 case synthetic)

Ngày: 2026-06-22
Generator: `scripts/eval_answerability_suite.py` (seed=7, tái lập được)

## Mục đích

Mở rộng quy mô eval cho answerability classification (trước đó 18 case) lên **201 case**,
trải rộng trên 4 family ESG + câu ngoài phạm vi + tầng adversarial, để có độ phủ tốt hơn.

## Cảnh báo trung thực

Đây là **eval tự sinh (synthetic)**, không phải 200 câu thật/golden. Vì ground-truth do
mình kiểm soát, **tầng "easy" đạt 100% là do thiết kế** — nó chỉ xác nhận cơ chế chạy đúng
trên nhiều tổ hợp family/metric, KHÔNG phải bằng chứng độ chính xác trên dữ liệu thật.
Tín hiệu thật sự là **tầng adversarial** (đo lỗi đã biết) và **abstain_safety_rate**.

## Kết quả

| Hạng mục | Giá trị |
|---|---:|
| Tổng số case | 201 |
| Overall accuracy | 85.6% (172/201) |
| Tier easy | 100% (172/172) — đúng theo thiết kế |
| Tier adversarial | 0% (0/29) — đo lỗi đã biết |
| abstain_safety_rate | 94.3% |

Confusion (expected → predicted):

- answerable → answerable 63, no_information 15
- no_information → no_information 49, out_of_scope 7, answerable 7
- out_of_scope → out_of_scope 60

## Diễn giải

- Cơ chế phân loại hoạt động ổn định trên nhiều family/metric (tier easy).
- 29 case adversarial fail toàn bộ — đúng 3 nhóm lỗi đã biết: phụ thuộc từ khóa, so token
  bỏ qua giá trị thật (abstain-unsafe), và so khớp item theo chuỗi chính xác.
- `overall_accuracy` chỉ có nghĩa trong ngữ cảnh hỗn hợp synthetic này; con số sẽ thay đổi
  theo tỷ lệ câu khó. Không nên dùng làm headline so sánh trực tiếp với eval câu hỏi thật.

## Bước tiếp theo

- Đánh giá trên **câu hỏi thật** từ corpus doanh nghiệp khi có dữ liệu (đây mới là test có
  giá trị tương đương eval lớn của các lane khác).
- Sửa 3 nhóm lỗi adversarial: kiểm tra có giá trị số gắn metric, mở rộng từ điển family,
  matching item linh hoạt hơn.
