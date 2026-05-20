---
name: deploy-check
description: Pre-deployment readiness and GO/NO-GO. Use for `/deploy` or deploy readiness. VI - Kiểm tra sẵn sàng deploy.
---

> **Agent:** Execute **Procedure** steps exactly. Never deploy without explicit human GO. **Deploy-check prose: Vietnamese**.

## Inputs / Đầu vào

- Deployment target: local, staging, production, or platform
- Intended commit/version when known
- Latest test report path or command to verify tests
- Rollback procedure, env var documentation, and monitoring docs when not obvious

## Procedure / Quy trình

1. Ask for missing target/version/test-report/rollback/env/monitoring inputs when they cannot be inferred
2. Run the checklist locally using `shared/agents/deployer.md` as the role guide
3. Create or update `docs/deployment/deploy-check-YYYY-MM-DD.md`
4. Present checklist results: GO or NO-GO with blockers
5. Stop; human must explicitly confirm before any deployment proceeds

**VI:** Hỏi input deploy còn thiếu → checklist theo `deployer.md` → ghi deploy-check → GO/NO-GO + blocker → dừng; **không deploy** nếu chưa có GO rõ ràng.

## Output / Kết quả

Deploy-check artifact path + checklist table + GO/NO-GO. No deployment without human confirmation.

Path artifact + bảng checklist + GO/NO-GO. Cấm deploy khi chưa human confirm.
