# Workflow Guide

> **Tiếng Việt:** `docs/vi/workflow-guide.md` — Agent behavior: follow this file (EN) and `AGENTS.md` when EN/VI differ on **procedure**. **Documentation outputs: Vietnamese** — `docs/documentation-language.md`.

This repository uses a Codex-native file-backed workflow. The short version is:

1. Plan the work.
2. Create test scenarios immediately.
3. Build in small documented tasks.
4. Review and run tests.
5. Run deploy readiness checks.
6. Deploy only after explicit human GO.
7. Verify production and close the release.

For the full lifecycle, see `docs/workflows/project-lifecycle.md`.

**New project from PDF + design:** do **Phase 0 (repo bootstrap) before Phase 1 (Discovery)** — `docs/workflows/new-project-from-zero.md` (EN) · `docs/vi/new-project-from-zero.md` (VI).

## Phases

| Phase | Name | Primary intent | Required artifact |
|-------|------|----------------|-------------------|
| 0 | Bootstrap | Initialize repo and workflow; **place** PDF/design files | `AGENTS.md`, `README.md`, `docs/product/source/`, `.planning/` — gate 0a: app need not run yet |
| 1 | Discovery | Read **PDF** → product scope and done criteria | `docs/product/brief.md`, `docs/product/requirements.md` |
| 2 | Architecture & Planning | Decide structure, contracts, task breakdown | `docs/architecture/`, `docs/api/`, `docs/tasks/` |
| 3 | Test Strategy | Define test scenarios before implementation | `.planning/<id>/test-scenarios.md` |
| 4 | Project Setup | Scaffold app, env, DB, CI, rollback | `.env.example`, CI config, rollback script |
| 5 | Implementation | Build tasks by wave | source code, tests, task sign-off |
| 6 | Review | Risk-focused code review | `docs/review/code-review-YYYY-MM-DD.md` |
| 7 | Test Run | Run unit, integration, E2E, API contract tests | `docs/test-reports/test-report-YYYY-MM-DD.md` |
| 8 | Deploy Check | Verify release readiness | `docs/deployment/deploy-check-YYYY-MM-DD.md` |
| 9 | Deploy | Deploy and smoke test | `docs/deployment/deploy-YYYY-MM-DD-HHmm.md` |
| 10 | Verify & Release | Verify production and close changelog | `CHANGELOG.md`, release tag, known issues |
| 11 | Maintenance | Handle post-release changes | impact assessment, patch plan, test scenarios |

## Human Checkpoints

These require explicit confirmation before proceeding:

- Goal or scope changes.
- Phase transitions from discovery to build, and from build to ship.
- Architecture decisions before recording as approved.
- Test strategy approval before writing tests or implementation.
- Deployment GO/NO-GO.

Never proceed silently past a checkpoint.

## File Responsibilities

| File | Update when |
|------|-------------|
| `.planning/<id>/task_plan.md` | Phase status changes and scope changes |
| `.planning/<id>/test-scenarios.md` | Immediately after plan creation and whenever scope changes |
| `.planning/<id>/findings.md` | After every 2 research operations |
| `.planning/<id>/progress.md` | After each meaningful work block |
| `.planning/<id>/workflow-state.md` | Phase transitions, blockers, next step changes |
| `.planning/<id>/audit-trail.md` | Each approved technical or workflow decision |
| `docs/` | Team-wide knowledge that should survive the task |

All active task state lives in `.planning/<id>/`. Team-wide documentation lives in `docs/`.

## Intents

| Intent | Use when |
|--------|----------|
| `/plan` | Starting or resuming any task; new plans must auto-create test scenarios |
| `/status` | Re-orienting after any interruption |
| `/review` | Before merging code or shipping a task |
| `/test plan` | Creating or refreshing test scenarios |
| `/test run` | Running and analyzing tests |
| `/deploy` | Checking deployment readiness |
| `/log` | Recording a significant decision |

Codex treats slash-style input as text intent. Implementation details live in `AGENTS.md` and `shared/skills/`.
