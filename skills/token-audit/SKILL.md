---
name: token-audit
description: Advise on Codex context budget and when to compact. VI - Tư vấn context budget và khi nên compact.
---

> **Agent:** Give advice only; human decides to compact or continue. **Advice: Vietnamese**.

## Signals of context pressure / Dấu hiệu context căng

- 50+ tool calls in current session
- Responses slowing or degrading
- Large files loaded (> 200 lines)
- Multiple delegated agent tasks without re-orientation

## Advice / Khuyến nghị

- Run session-compact skill first
- Then compact/reset the session if needed
- After compaction/reset: run `/status` to re-orient
- Keep `task_plan.md` under 50 lines
- Keep `findings.md` under 100 lines

**VI:** Chạy session-compact trước → compact/reset nếu cần → `/status` → giữ `task_plan.md` < 50 dòng, `findings.md` < 100 dòng.

## Stop at / Dừng tại

Advice given. Human decides to compact or continue.

Chỉ đưa lời khuyên; human quyết định compact hay tiếp tục.
