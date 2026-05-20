# Documentation language policy

All **documentation artifacts** produced in this workflow must be written in **Vietnamese (tiếng Việt)**.

> **Agent:** Use Vietnamese for descriptive prose in artifacts below. Keep paths, intents, phase names, and code identifiers in English per *Exceptions*.

**Vietnamese policy (full):** `docs/vi/ngon-ngu-tai-lieu.md`

## Applies to

- `docs/product/`, `docs/architecture/`, `docs/api/`, `docs/tasks/`, `docs/decisions/`
- `docs/review/`, `docs/test-reports/`, `docs/deployment/`, `docs/post-launch/`
- `.planning/<id>/` prose: `task_plan.md` (Goal, HUMAN_NOTES), `findings.md`, `progress.md`, `workflow-state.md`, `audit-trail.md`, `test-scenarios.md`
- Workflow responses: `/status` summaries, review finding descriptions, deploy recommendations

## Exceptions (keep English)

- File paths, directory names, plan slugs
- Intents: `/plan`, `/status`, GO/NO-GO
- `MACHINE_STATE` phase names (Bootstrap, Discovery, …)
- Env vars, API routes, code identifiers
- YAML frontmatter keys
- Verbatim library/RFC/log quotes
- Severity labels: CRITICAL, WARN, INFO (details in Vietnamese)

## Not covered

- Source code identifiers (business comments in Vietnamese when present)
- Bilingual `shared/skills/` and `AGENTS.md` agent contract

See `AGENTS.md` section **Documentation language**.
