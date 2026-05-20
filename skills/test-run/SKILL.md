---
name: test-run
description: Run tests and analyze results. Use for `/test run` or test execution requests. VI - Chạy test và phân tích kết quả.
---

> **Agent:** Execute **Procedure** steps exactly. **Test report prose: Vietnamese**.

## Inputs / Đầu vào

- Test command; infer from package scripts when obvious, otherwise ask
- Test scope: narrow task run or release/full-suite run
- Required env/services/seed data when not obvious
- Active plan from `.planning/current_plan` when available

## Procedure / Quy trình

1. Confirm or infer the test command
2. Confirm whether this is a narrow task run or release/full-suite run when unclear
3. Confirm required env/services/seed data when missing or risky
4. Run the command with the local shell
5. Analyze output using `shared/agents/tester.md` as the role guide
6. Write a test report:
   - use `docs/test-reports/test-report-YYYY-MM-DD.md` for release-level or full-suite runs
   - use `.planning/<id>/test-run-YYYY-MM-DD-HHmm.md` for narrow task runs
7. If failures exist: present root causes and suggested fixes
8. Stop; human approves fixes unless they already asked Codex to fix them

**VI:** Xác nhận lệnh test/scope/env → chạy shell → phân tích theo `tester.md` → ghi report (release hoặc task) → root cause nếu fail → dừng trừ khi user đã yêu cầu fix.

## Output / Kết quả

Pass/fail count + root causes per failure + test report path. Human decides fixes.

Số pass/fail + root cause + path report. Human quyết định sửa gì.
