---
name: decision-log
description: Record a technical decision in audit-trail. Use for `/log` or decision logging. VI - Ghi quyết định kỹ thuật.
---

> **Agent:** Execute **Procedure** steps exactly. **Decision record: Vietnamese** in `audit-trail.md`.

## Inputs / Đầu vào

- What was decided
- What alternatives were rejected
- Why this option

## Procedure / Quy trình

1. Collect inputs; ask for missing fields only
2. Read `.planning/current_plan`
3. Format the decision using `shared/agents/architect.md` as the role guide
4. Append to `.planning/<id>/audit-trail.md`
5. Confirm: decision title + date logged
6. Stop

**VI:** Thu thập quyết định / phương án bị loại / lý do → đọc `current_plan` → format theo `architect.md` → append `audit-trail.md` → xác nhận tiêu đề + ngày.

## Output / Kết quả

Confirmation with decision title and date. No further action.

Xác nhận tiêu đề quyết định và ngày ghi. Không làm thêm bước khác.
