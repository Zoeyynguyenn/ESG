---
name: review-code
description: Risk-focused code review. Use for `/review`, pre-merge, or review requests. VI - Review code tập trung rủi ro.
---

> **Agent:** Execute **Procedure** steps exactly. **Review report prose: Vietnamese** (keep CRITICAL/WARN/INFO labels).

## Inputs / Đầu vào

- Explicit file list, OR
- Recent changes via `git diff --staged` or `git diff`
- Review type: narrow task review, pre-merge review, or release review
- Base branch/commit when relevant
- Known risk areas when the human has them

## Procedure / Quy trình

1. Identify scope; ask only if it cannot be inferred
2. Ask whether this is narrow, pre-merge, or release-level if it cannot be inferred
3. Review locally using `shared/agents/reviewer.md` as the role guide
4. For release or pre-merge reviews, write `docs/review/code-review-YYYY-MM-DD.md`
5. Present findings: CRITICAL -> WARN -> INFO
6. Stop; human decides: fix now, defer, or accept

**VI:** Xác định scope → hỏi loại review nếu chưa rõ → review theo `reviewer.md` → ghi file review nếu release/pre-merge → trình bày CRITICAL → WARN → INFO → dừng để human quyết định.

## Output / Kết quả

Findings list + review artifact path when written. Human decides next action.

Danh sách finding + path artifact. Human chọn fix/defer/accept.
