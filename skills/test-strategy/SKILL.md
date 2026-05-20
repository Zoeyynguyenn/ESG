---
name: test-strategy
description: Create a test plan before implementation. Use for `/test plan` or test planning requests. VI - Lập chiến lược test trước khi implement.
---

> **Agent:** Execute **Procedure** steps exactly. **Artifact prose: Vietnamese** — `docs/documentation-language.md`.

## Inputs / Đầu vào

- Feature spec or relevant code files
- Active plan from `.planning/current_plan` when available

## Procedure / Quy trình

1. Identify scope; ask only if unclear
2. Analyze relevant files locally using `shared/agents/tester.md` as the role guide
3. Create or update `.planning/<id>/test-scenarios.md` when an active plan exists; otherwise create `docs/test-reports/test-plan-YYYY-MM-DD.md`
4. Include: source requirement, scenario, test level, setup, steps, expected result, priority, pass criteria, status
5. Present summary table: area | approach | pass criteria | artifact path
6. Stop; human approves before tests or implementation are written

**VI:** Xác định scope → phân tích file → ghi artifact test scenarios → bảng tóm tắt → dừng chờ human approve trước khi viết test hoặc code.

## Output / Kết quả

Test scenario artifact path + summary table. Human approves before proceeding.

Đường dẫn artifact + bảng tóm tắt. Human approve trước khi tiếp tục.
