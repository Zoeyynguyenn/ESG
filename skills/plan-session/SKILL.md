---
name: plan-session
description: Start or resume a planning session using the file-backed workflow. Use for `/plan`, plan requests, or resume. VI - Bắt đầu hoặc resume planning session.
---

> **Agent:** Execute numbered steps in **Procedure** exactly. **VI** explains intent for humans only. **Artifacts (plan prose, test-scenarios content): Vietnamese** — `docs/vi/ngon-ngu-tai-lieu.md`.

## Inputs / Đầu vào

- **Resume:** `.planning/current_plan` exists
- **New:** user provides a short slug plus enough intake context for the requested phase

## New Plan Intake / Câu hỏi đầu vào cho plan mới

Before creating a new plan, identify the requested phase from the user message, existing repo state, or explicit phase text. If the phase is unclear, ask which phase the user wants.

Ask only for missing information, but do not reduce intake to a generic goal. Required minimum questions by phase:

| Phase | Required intake before proceeding |
|-------|----------------------------------|
| Phase 0 Bootstrap | repo status (empty/workflow-only/existing code), available product docs, available design files, desired Phase 0 gate (`0a` workflow bootstrap or `0b` runnable bootstrap), rough stack/deploy target if known, confidentiality/secret constraints |
| Phase 1 Discovery | exact PDF/source path or pasted content, supporting notes, known users/roles, unclear business rules, desired output docs |
| Phase 2 Architecture & Planning | approved requirements path, design file/path or note that no design exists, preferred stack constraints, integration/API/DB constraints, non-functional constraints |
| Phase 3 Test Strategy | approved requirements/tasks/API docs, critical flows, target test levels, known risk areas |
| Phase 4 Project Setup | approved architecture/tasks, stack/package manager, local runtime requirements, DB/migration choice, CI/deploy target |
| Phase 5+ Implementation/Maintenance | task ID or scope, linked docs, acceptance criteria, test expectations, files/modules likely in scope |

If required input is missing and cannot be safely inferred from repo files, ask concise questions and stop. Record unknowns as open questions in the plan only after the human answers enough to proceed.

## Procedure / Quy trình

**Resume:**
1. Read `.planning/current_plan` to get plan ID
2. Read `.planning/<id>/task_plan.md` MACHINE_STATE phases table
3. Read `.planning/<id>/workflow-state.md` if it exists
4. Read `.planning/<id>/test-scenarios.md` if it exists
5. Output: plan ID, current phase, next pending phase, test-scenario status, blockers or recent errors
6. Stop; human decides next action

**New plan:**
1. Determine requested phase; if unclear, ask the human to choose a phase
2. Ask for missing required intake for that phase using **New Plan Intake**
3. If required input remains missing, stop with a short list of missing inputs and suggested next action
4. Create `.planning/YYYY-MM-DD-<slug>/`
5. Copy all workflow templates: `task_plan.md`, `findings.md`, `progress.md`, `workflow-state.md`, `audit-trail.md`, and `test_scenarios.md` as `test-scenarios.md`
6. Fill metadata dates, goal line, phase, known inputs, assumptions, and open questions
7. Write plan ID to `.planning/current_plan`
8. Run the test-strategy procedure automatically for this plan unless the request is explicitly Phase 0 bootstrap-only:
   - infer initial scenarios from the goal and existing specs
   - write them to `.planning/<id>/test-scenarios.md`
   - mark unknowns as open questions instead of leaving silent gaps
9. For Phase 0 bootstrap-only, create `test-scenarios.md` as a placeholder explaining that full test strategy starts after Phase 1/2 inputs exist
10. Set the current phase to the requested phase and set Test Strategy to `pending_human_approval` when scenarios were created
11. Output: plan ID + phase list + known inputs + open questions + test scenario artifact path/status
12. Stop; human approves or edits the plan/test strategy before implementation

### VI — Resume
1. Đọc `current_plan` lấy plan ID
2. Đọc bảng phase trong `task_plan.md`
3–4. Đọc `workflow-state.md`, `test-scenarios.md` nếu có
5. Trả plan ID, phase hiện tại, phase kế tiếp, trạng thái test scenarios, blocker
6. Dừng; chờ human quyết định bước tiếp

### VI — Plan mới
1. Xác định phase user muốn làm; nếu chưa rõ thì hỏi phase
2. Hỏi input bắt buộc còn thiếu theo phase; không chỉ hỏi Goal chung chung
3. Nếu vẫn thiếu input quan trọng, dừng và trả danh sách thông tin cần bổ sung
4–7. Tạo plan, copy template, điền metadata/goal/phase/input/assumption/open questions, ghi `current_plan`
8–10. Tự chạy test-strategy nếu không phải Phase 0 bootstrap-only; Phase 0 thì tạo placeholder `test-scenarios.md`
11–12. Trả plan ID + phase + input đã biết + open questions + trạng thái test scenarios; **không implementation** trước khi human approve

## Output / Kết quả

Plan ID + phase status + test scenario status. No implementation before test strategy approval.

Không code trước khi test strategy được approve.
