---
name: session-compact
description: Verify state is flushed before compaction, reset, or handoff. VI - Kiểm tra state trước compaction/reset.
---

> **Agent:** Execute **Procedure** steps exactly. **Replies to human: Vietnamese**.

## Inputs / Đầu vào

- None

## Procedure / Quy trình

1. Read active plan from `.planning/current_plan`
2. Read `task_plan.md`; confirm phase statuses are current
3. Read `progress.md`; confirm last actions are logged
4. Read `findings.md`; confirm research is captured
5. If gaps exist: list them; stop for human to address
6. If ready: confirm state is safe for compaction, reset, or handoff

**VI:** Đọc plan active → kiểm tra `task_plan.md`, `progress.md`, `findings.md` còn mới → liệt kê gap hoặc xác nhận an toàn để compact/reset/handoff.

## Output / Kết quả

Ready for compaction/reset/handoff OR list of gaps to address first.

Sẵn sàng compact/reset HOẶC danh sách gap cần xử lý trước.
