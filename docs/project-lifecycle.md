# Project Lifecycle Workflow

> **Tiếng Việt:** `docs/vi/project-lifecycle.md` — Agent behavior: follow this file (EN) and `AGENTS.md` when EN/VI differ.

This workflow covers a project from an empty repository to production and maintenance. It adapts the stronger lifecycle from `E:\Documents\sample-banthe` to this repository's Codex workflow.

## Operating Rules

- **All documentation artifacts** (committed `docs/` and `.planning/<id>/` prose) **must be written in Vietnamese** — see `docs/documentation-language.md` and `docs/vi/ngon-ngu-tai-lieu.md`.
- A new plan is not complete until test scenarios exist.
- Every phase has documented input, output, gate, and handoff.
- Implementation starts only after scope, architecture, and test strategy are approved.
- Tests run before deploy readiness checks.
- Deployment requires explicit human GO.
- Rollback is prepared before deployment, not after failure.
- Production verification closes the release; smoke test alone is not enough.

## Phase Execution Contract

For every phase, Codex must do three things in order:

1. **Ask/confirm missing inputs** before creating or changing artifacts. If required input is missing and cannot be inferred safely, ask and stop.
2. **Write results to files** while working. Do not leave decisions, blockers, test results, or deploy status only in chat.
3. **Stop at the gate**. Phase transitions require human confirmation.

| Phase | Intent | Must write results to | Stop/gate |
|-------|--------|-----------------------|-----------|
| 0 Bootstrap | `/plan` | `README.md`, `docs/product/README.md`, `.env.example`, `.planning/<id>/task_plan.md`, `workflow-state.md`, `progress.md` | Human approves gate `0a` or `0b` |
| 1 Discovery | `/plan` | `docs/product/brief.md`, `docs/product/requirements.md`, `.planning/<id>/findings.md`, `progress.md`, `workflow-state.md` | Human approves scope and Definition of Done |
| 2 Architecture & Planning | `/plan` | `docs/architecture/`, `docs/api/`, `docs/tasks/`, `docs/decisions/` or `.planning/<id>/audit-trail.md` | Human approves architecture, contracts, and tasks |
| 3 Test Strategy | `/test plan` | `.planning/<id>/test-scenarios.md` and optional `docs/test-reports/test-plan-YYYY-MM-DD.md` | Human approves test strategy |
| 4 Project Setup | `/plan` | source scaffold, `.env.example`, setup docs, migration baseline, CI config, rollback docs, `progress.md` | Build/typecheck/migration/CI baseline pass or blocker documented |
| 5 Implementation | task plan or `/plan <feature>` | source code, tests, `.planning/<id>/progress.md`, `.planning/<id>/findings.md`, changelog/release notes if user-facing | Acceptance criteria and related tests pass |
| 6 Review | `/review` | `docs/review/code-review-YYYY-MM-DD.md` for release/pre-merge, or review findings in chat for narrow review | Human chooses fix/defer/accept for findings |
| 7 Test Run | `/test run` | `docs/test-reports/test-report-YYYY-MM-DD.md` for release runs, or `.planning/<id>/test-run-YYYY-MM-DD-HHmm.md` for narrow runs | Critical flows pass or failures have impact/root cause |
| 8 Deploy Check | `/deploy` | `docs/deployment/deploy-check-YYYY-MM-DD.md` | Human gives explicit GO; otherwise stop |
| 9 Deploy | explicit deploy request after GO | `docs/deployment/deploy-YYYY-MM-DD-HHmm.md` | Smoke test passes or rollback status documented |
| 10 Verify & Release | release verification request | production verification notes, `CHANGELOG.md`, release tag if used, `docs/post-launch/known-issues.md` | Critical production flows pass |
| 11 Maintenance | `/plan <change>` | impact assessment, patch plan, test scenarios, review/test/deploy artifacts as applicable | Re-run gates 6-10 for shipped changes |

Always update `.planning/<id>/workflow-state.md` when phase, blocker, status, or next step changes. Update `.planning/<id>/progress.md` after each meaningful work block. Use `.planning/<id>/audit-trail.md` for approved decisions with rationale.

## Phase 0 - Bootstrap

**Goal:** Make the repo reproducible for a new contributor or a fresh Codex session — **working conventions**, not product discovery from PDF.

**Inputs:** project root, preferred stack if known, folder conventions. *Product description PDF is Phase 1 input, not Phase 0.*

**Codex must ask/confirm before work:**
- Is this repo empty, workflow-only, or does it already contain application code?
- What product documents already exist: PDF, brief, notes, links, transcripts?
- What design artifacts already exist: Figma, images, PDF export, wireframes?
- Are those files already in the repo, or should Phase 0 only create placement folders?
- Which Phase 0 gate is expected: `0a` workflow bootstrap or `0b` runnable bootstrap?
- Is the stack/deploy target known, or should later phases decide?
- Are there secrets, NDA files, or restricted data that must not be committed?

**Outputs:**
- `AGENTS.md`
- `README.md`
- `.env.example`
- `docs/README.md`
- `docs/workflow-guide.md`
- `docs/product/source/` and `docs/product/README.md` (where PDF + design files go)
- `.planning/` templates
- package manager and workspace files *(may be completed in Phase 4 if no app yet)*

**Gate 0a (workflow bootstrap):** Contributor can clone; knows where to put PDF/design; README explains Phase 0→1; `.env.example` and planning templates exist. *App does not need to run yet.*

**Gate 0b (runnable bootstrap):** After Phase 4 — install dependencies and start the project from README.

**Full step-by-step (PDF + design, phases 0–5):** `docs/workflows/new-project-from-zero.md`

## Phase 1 - Discovery

**Goal:** Convert the **product PDF / description** into a clear product scope (no code).

**Outputs:**
- `docs/product/brief.md`
- `docs/product/requirements.md`
- user flows and acceptance criteria
- Definition of Done
- open questions

**Gate:** Human approves product scope and Definition of Done.

**Codex must ask/confirm before work:**
- What exact PDF/source path should be read, or will the user paste content?
- Are there notes, emails, tickets, transcripts, or business rules outside the PDF?
- Who are the primary users/roles if the PDF is unclear?
- Are additional output docs needed beyond `brief.md` and `requirements.md`?
- Which areas are known uncertain and should become open questions?

## Phase 2 - Architecture & Planning

**Goal:** Turn product scope into buildable system design and tasks. **Design files (UI)** are mapped here, not in Phase 0.

**Outputs:**
- `docs/architecture/overview.md`
- `docs/api/contracts.md` or `docs/api/openapi.yaml`
- `docs/decisions/ADR-*.md`
- `docs/tasks/TASK-ID.md`
- `docs/tasks/_wave-plan.md`

**Gate:** Human approves architecture, API contracts, and task breakdown.

**Codex must ask/confirm before work:**
- Has `requirements.md` been approved by the human?
- Where are the design files/links, or is there no design yet?
- Are there stack, framework, database, auth, or deploy constraints?
- Are external systems or third-party APIs required?
- Which non-functional requirements matter: performance, security, accessibility, audit log, backup?

## Phase 3 - Test Strategy

**Goal:** Define how the plan will be proven before code is treated as done.

**Outputs:**
- `.planning/<id>/test-scenarios.md`
- Optional shared version in `docs/test-reports/test-plan-YYYY-MM-DD.md`

**Minimum scenarios:**
- Happy path for every accepted user flow.
- At least one validation/error case for each write flow.
- Auth/authorization cases if protected resources exist.
- API contract cases for public endpoints.
- E2E coverage for critical product flows.
- Regression cases for changed behavior.

**Gate:** Human approves test strategy before implementation or test writing.

**Codex must ask/confirm before work:**
- Which requirements, task breakdown, and API contract are authoritative?
- Which flows are critical and must not fail?
- Which test levels are expected: unit, integration, API contract, E2E, smoke?
- Are auth/permission, payment, sensitive data, or migration cases needed?
- Which tests may be deferred and what risk is accepted?

## Phase 4 - Project Setup

**Goal:** Create a buildable foundation.

**Outputs:**
- app scaffold
- `.env.example`
- local setup docs
- database migration baseline
- CI config
- rollback script or rollback instructions

**Gate:** build/typecheck pass, DB migration works locally, CI is green or locally reproducible.

**Codex must ask/confirm before work:**
- Has the setup architecture/task been approved?
- Which stack, package manager, and runtime versions should be used?
- Which services are needed: web, API, worker, DB, cache, queue?
- Which local env vars are required and which must never be committed?
- What CI/deploy target is expected?

## Phase 5 - Implementation

**Goal:** Build by small tasks and waves.

**Per-task requirements:**
- Read the task file and linked docs before editing.
- Keep changes inside the task scope.
- Add or update tests listed in test scenarios.
- Update progress after each work block.
- Update changelog or release notes when user-facing behavior changes.

**Gate:** Each task satisfies acceptance criteria and relevant tests pass.

**Codex must ask/confirm before work:**
- What is the task ID or exact scope?
- Where are the related acceptance criteria and test scenarios?
- Which files/modules are likely in scope, and is there parallel ownership?
- Which existing behavior must not change?

## Phase 6 - Review

**Goal:** Find behavioral, security, contract, and maintainability risks before merge.

**Outputs:**
- `docs/review/code-review-YYYY-MM-DD.md` for release or pre-merge reviews
- finding list ordered by severity
- fix/defer/accept decisions

**Gate:** No unresolved blocker remains.

**Codex must ask/confirm before work:**
- What is the review scope: specific files, current diff, staged diff, release candidate, or full feature?
- Is this pre-merge/release-level review, requiring `docs/review/code-review-YYYY-MM-DD.md`?
- Which base branch/commit or task should findings be compared against?
- Are there known risk areas: auth, data migration, payments, security, performance?
- Should Codex only report findings, or has the human explicitly asked for fixes too?

## Phase 7 - Test Run

**Goal:** Verify the system with the right test depth for the release risk.

**Outputs:**
- `docs/test-reports/test-report-YYYY-MM-DD.md`
- pass/fail counts
- root cause for failures
- coverage gaps and skipped tests with reasons

**Gate:** Critical flows pass. Any deferred failure is documented with impact.

**Codex must ask/confirm before work:**
- What test command should run, or should Codex infer it from package scripts?
- Is this a narrow task test or release/full-suite run?
- Are required services/env vars/seed data available?
- Which test scenarios or critical flows must be covered?
- Where should the report be written: release report or active-plan task report?

## Phase 8 - Deploy Check

**Goal:** Decide whether deployment is ready.

**Outputs:**
- `docs/deployment/deploy-check-YYYY-MM-DD.md`
- GO/NO-GO recommendation

**Gate:** Human gives explicit GO. Without GO, do not deploy.

**Codex must ask/confirm before work:**
- What deployment target is being checked: local, staging, production, or specific platform?
- Which commit/version is intended for deployment?
- Where is the latest test report and are any failures deferred?
- Are env vars, migrations, rollback, monitoring, and secrets handling documented?
- Has the human requested readiness only, or an actual deployment after GO?

## Phase 9 - Deploy

**Goal:** Release to staging or production with rollback ready.

**Outputs:**
- `docs/deployment/deploy-YYYY-MM-DD-HHmm.md`
- deployed version or commit
- migration result
- smoke test result
- rollback status if triggered

**Gate:** Smoke test passes. If smoke test fails, rollback first and debug after.

**Codex must ask/confirm before work:**
- Has Phase 8 produced GO and has the human explicitly confirmed deploy?
- What exact deployment command/procedure and target should be used?
- Are migrations required, and what is the rollback command/procedure?
- What smoke tests must run immediately after deploy?
- Who owns rollback decision if smoke fails?

## Phase 10 - Verify & Release

**Goal:** Confirm production behavior and close the release.

**Outputs:**
- production verification notes
- `CHANGELOG.md` update
- release tag if applicable
- `docs/post-launch/known-issues.md`

**Gate:** Critical production flows work and no unresolved release blocker remains.

**Codex must ask/confirm before work:**
- What production URL/environment and version should be verified?
- Which critical flows must be checked?
- Where are deploy log, test report, and known deferred issues?
- Should `CHANGELOG.md` and release tag be updated now?
- What monitoring/errors should be checked after release?

## Phase 11 - Maintenance

**Goal:** Make post-release changes without losing traceability.

**Outputs per change:**
- impact assessment
- plan
- test scenarios
- review notes
- test report
- deploy log if shipped

**Gate:** Same review, test, deploy, and verify gates apply.

**Codex must ask/confirm before work:**
- Is this a bugfix, patch, feature change, dependency update, or incident response?
- What production impact, severity, affected version, and workaround are known?
- Is rollback needed before a patch?
- Which docs, tests, and release notes must be updated?
- Does the change need the full Phase 6-10 path before shipping?
