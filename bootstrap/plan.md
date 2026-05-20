Use the plan-session skill (`shared/skills/plan-session/SKILL.md`).

Dùng skill plan-session.

If argument provided: create a new plan with that argument as the slug.
Nếu có tham số: tạo plan mới với slug đó.

If no argument: resume the active plan from `.planning/current_plan`.
Không tham số: resume plan từ `.planning/current_plan`.

For a new plan, do phase-specific intake first. Do not ask only for a generic goal if phase inputs are missing.
Với plan mới, hỏi input theo phase trước. Không chỉ hỏi Goal chung chung nếu còn thiếu tài liệu/thiết kế/constraint cần thiết.

After creating a new plan, auto-create `.planning/<id>/test-scenarios.md` using the test-strategy skill and stop for human approval before implementation.

Sau plan mới: tự tạo `test-scenarios.md` bằng test-strategy; dừng chờ human approve trước implementation.
