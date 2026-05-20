# AGENTS.md

## Workflow Bridge

Project này dùng workflow core tại: `{{WORKFLOW_ROOT}}`.

## Start Intent

Khi user nhập `/start`, agent phải chạy bootstrap wizard với các quy tắc bắt buộc:
1. Hỏi đúng 1 câu mỗi lượt, chờ user trả lời rồi mới hỏi tiếp.
2. Toàn bộ câu hỏi và tóm tắt bootstrap bằng tiếng Việt.
3. Đọc bridge config từ `.workflow/config.yaml`.
4. Nếu mode là `create`, intake theo thứ tự: mô tả dự án, goal, tài liệu hiện có.
5. Hỏi checkpoint design: nếu đã có design thì lấy đường dẫn/link; nếu chưa có thì hỏi discovery design từng câu và tổng hợp danh sách màn cần thiết để user xác nhận.
6. Có thể đề xuất/tạo mockup hoặc wireframe ban đầu trước khi code khi user đồng ý.
7. Khi chưa có design, dùng `skills/bootstrap-session/design-intake-kit.md` làm bộ câu hỏi chuẩn.
8. Sau phần design mới hỏi ràng buộc, đề xuất stack/architecture để user xác nhận, rồi hỏi yêu cầu công nghệ cụ thể theo từng subsystem (web/backend/data/auth/hạ tầng).
9. Không viết code ứng dụng trước khi intake bootstrap hoàn tất và user xác nhận.

## Intent Mapping

- `/start` => bootstrap-session wizard
- `/status` => trạng thái hiện tại (goal, phase, blockers, next step)
- `/plan` => lập kế hoạch theo workflow
- `/review` => review theo workflow
- `/test plan` => lập test scenarios
- `/test run` => chạy test và báo cáo
- `/deploy` => deploy check, yêu cầu GO/NO-GO

## Safety

- Chỉ sửa file trong project root hiện tại trừ khi user yêu cầu khác.
- Trước khi sửa, echo write-boundary rõ ràng.
