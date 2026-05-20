# New Project from Zero (PDF + Design)

Guide for newcomers with a **project description PDF** and a **design file** (Figma, PDF export, PNG, etc.), following `docs/workflows/project-lifecycle.md`.

> **Agent:** Execute phases and intents per `AGENTS.md`. Human must confirm before each phase transition. Do not skip phases.
>
> **Language:** All produced documentation artifacts must be **Vietnamese** — `docs/documentation-language.md`.

**Vietnamese:** `docs/vi/new-project-from-zero.md`

## Phase 0 vs Phase 1

| | Phase 0 — Bootstrap | Phase 1 — Discovery |
|---|---------------------|-------------------|
| Purpose | Prepare **repository** and working conventions | Turn **PDF** into **product scope** |
| Inputs | Repo name, rough stack (optional), folder layout | Description PDF, business Q&A |
| Do not | Read PDF into requirements; implement features | Scaffold app; detailed architecture |
| Main artifacts | `README.md`, `docs/product/source/`, `.env.example`, workflow | `docs/product/brief.md`, `requirements.md` |

**PDF and design files are not Phase 0 work.** Phase 0 creates **placement** and **README** for next steps. Phase 1 reads the PDF; Phase 2 maps design to architecture/tasks.

### Two Phase 0 gate levels

| Level | When | Gate (human confirm) |
|-------|------|----------------------|
| **0a — Workflow bootstrap** | Idea + PDF only, no app yet | Clone OK; know where to put PDF/design under `docs/product/source/`; README explains Phase 0→1→2; `.env.example`; planning templates |
| **0b — Runnable bootstrap** | After Phase 4 (Project Setup) | Install deps and start app from README (full lifecycle gate) |

Do not block Phase 1 because `pnpm dev` does not work yet — that belongs to Phase 4.

---

## Overall path

```
Phase 0  →  [confirm]  →  Phase 1  →  [confirm]  →  Phase 2  →  [confirm]  →  Phase 3
    →  [confirm]  →  Phase 4  →  Phase 5  →  …  →  Phase 10
```

Phases 6–11: see `docs/workflows/project-lifecycle.md`.

---

## Before Codex (~15 min manual)

1. Clone repo (or create repo with `AGENTS.md` + workflow `docs/`).
2. Copy PDF to `docs/product/source/` (e.g. `project-brief.pdf`).
3. Copy or export design into the same folder — do not commit NDA/restricted assets if policy forbids.
4. Keep real `.env` local; never commit.

---

## Phase 0 — Bootstrap repository

### Codex intake before work

If the user only says “run Phase 0” or “bootstrap the repo”, Codex must ask for any missing minimum intake before creating the plan:

- Is this repo empty, workflow-only, or does it already contain application code?
- What product documents already exist: PDF, brief, notes, links?
- What design artifacts already exist: Figma, images, PDF export, wireframes?
- Are those files already in the repo, or should Phase 0 create `docs/product/source/` for the user to place them?
- Which Phase 0 gate should this stop at: `0a` workflow bootstrap or `0b` runnable bootstrap?
- Is the stack/deploy target known, or should later phases decide?
- Are there secret/NDA/restricted files that must not be committed?

If PDF/design do not exist yet, Phase 0 may still run, but README and `docs/product/README.md` must document them as missing inputs for Phase 1/2.

### Tasks

| # | Task | Output |
|---|------|--------|
| 0.1 | Workflow baseline | `AGENTS.md`, `docs/`, `templates/`, `shared/skills/` |
| 0.2 | Newcomer README | `README.md` (layout, 12 phases, link this doc) |
| 0.3 | Input folder | `docs/product/source/` + `docs/product/README.md` |
| 0.4 | Env template | `.env.example` |
| 0.5 | Planning templates | `templates/`; runtime `.planning/<id>/` (usually gitignored) |

**Not in Phase 0:** PDF → `brief.md`; design → API; scaffold `apps/`; `/test plan`; code.

### Codex prompt (Phase 0)

```
/plan repo-bootstrap

Phase 0 Bootstrap only:
- Before creating the plan, ask/confirm: repo status, existing documents, existing design, gate 0a/0b, stack/deploy target if known, secret/NDA constraints.
- Create docs/product/source/ and docs/product/README.md (where to put PDF + design files).
- Create or update README.md: repo layout, 12 phases, link docs/workflows/new-project-from-zero.md.
- Do not read the PDF into requirements.
- Do not scaffold app or write feature code.
- Update .planning/<id>/task_plan.md (phase = Bootstrap); stop for human Phase 0a confirm.
```

### Phase 0a checklist

- [ ] `docs/product/source/` exists; PDF/design placed
- [ ] `README.md` explains next step (Phase 1)
- [ ] No `.env` / `node_modules` committed
- [ ] Ready to open Phase 1 plan

**Confirm phrase:** `Phase 0a approved — proceed to Phase 1.`

---

## Phase 1 — Discovery (from PDF)

### Codex intake before work

- What PDF/source path should be read, or will the user paste content?
- Are there supporting docs outside the PDF?
- Are the primary users/roles known?
- Are any business rules known to be unclear or easy to misread?
- Should outputs be limited to `brief.md`/`requirements.md`, or include separate user stories/flows?

### Tasks

| # | Task | Output |
|---|------|--------|
| 1.1 | Read PDF (+ user notes) | Capture in `findings.md` |
| 1.2 | Brief | `docs/product/brief.md` |
| 1.3 | Requirements | `docs/product/requirements.md` |
| 1.4 | Scope clarity | User flows, acceptance criteria, Definition of Done |
| 1.5 | Unknowns | Open questions |

**Not:** detailed architecture; task breakdown; code.

### Codex prompt (Phase 1)

```
/plan product-discovery

Phase 1 Discovery only:
- Read docs/product/source/<pdf-filename> (or pasted content).
- Create docs/product/brief.md and docs/product/requirements.md (Vietnamese prose).
- Include user flows, acceptance criteria, Definition of Done, open questions.
- No architecture/tasks. No code. Stop for human scope approval.
```

### Phase 1 gate checklist

- [ ] Scope and out-of-scope clear
- [ ] Definition of Done sufficient for Phase 2 tasks
- [ ] Open questions answered or risk accepted

**Confirm phrase:** `Phase 1 approved — proceed to Phase 2.`

---

## Phase 2 — Architecture & Planning (from design)

### Codex intake before work

- Has `requirements.md` been approved?
- Where are the design files, or is there no design yet?
- Are there stack/framework/database/auth/deploy constraints?
- Are there third-party APIs, import/export, payment, notification, or integration needs?
- Are there priority non-functional requirements?

### Tasks

| # | Task | Output |
|---|------|--------|
| 2.1 | Screens → flows | Update/link in `requirements.md` if needed |
| 2.2 | System design | `docs/architecture/overview.md` |
| 2.3 | API contracts | `docs/api/contracts.md` or `openapi.yaml` |
| 2.4 | Major decisions | `docs/decisions/ADR-*.md`; `/log` → `audit-trail.md` |
| 2.5 | Task breakdown | `docs/tasks/TASK-*.md`, `docs/tasks/_wave-plan.md` |

### Codex prompt (Phase 2)

```
/plan architecture-planning

Phase 2 only:
- Read docs/product/* and docs/product/source/<design-files>.
- Create docs/architecture/overview.md, docs/api/contracts.md,
  docs/tasks/_wave-plan.md and TASK-001, TASK-002...
- No implementation. Stop for human approval of architecture + tasks.
```

**Confirm phrase:** `Phase 2 approved — proceed to Phase 3.`

---

## Phase 3 — Test Strategy

### Codex intake before work

- Which requirements, API contract, and task breakdown are authoritative?
- Which flows are critical?
- Which test levels are expected: unit, integration, API contract, E2E, smoke?
- Are auth/permission, payment, migration, sensitive data, or error paths needed?
- May any tests be deferred, and what is the impact?

See `shared/skills/test-strategy/SKILL.md`.

```
/test plan
```

Based on `requirements.md` and API contracts → `.planning/<id>/test-scenarios.md`. **No implementation** before human approval.

**Confirm phrase:** `Phase 3 approved — proceed to Phase 4.`

---

## Phase 4 — Project Setup

### Codex intake before work

- Has the setup architecture/task been approved?
- Which stack, package manager, and runtime version should be used?
- Which services should be scaffolded: web, API, worker, DB, cache, queue?
- Which local env vars are required and which are secrets?
- What CI/deploy target is expected?

Scaffold, package manager, DB migrations, CI, rollback docs, README run instructions.

**Phase 0b gate:** build/typecheck pass; migrations local; README start works.

**Confirm phrase:** `Phase 4 approved — proceed to Phase 5.`

---

## Phase 5 onward

Per `docs/tasks/TASK-xxx.md`: `/status`, implement, `progress.md`, `findings.md`, `/log`, `/test run` as needed.

| Phase | Must ask/confirm | Must write | Human gate |
|-------|------------------|------------|------------|
| 5 Implementation | Task ID, acceptance criteria, test scenarios, files/modules in scope | code/tests, `.planning/<id>/progress.md`, `findings.md`, changelog if user-facing | Acceptance criteria + related tests pass |
| 6 Review | review scope, diff/base, release vs narrow review, known risks | `docs/review/code-review-YYYY-MM-DD.md` for release/pre-merge | No unresolved CRITICAL/WARN without fix/defer/accept |
| 7 Test Run | test command, release vs narrow run, env/seed data, critical flows | `docs/test-reports/test-report-YYYY-MM-DD.md` or `.planning/<id>/test-run-YYYY-MM-DD-HHmm.md` | Critical flows pass or failures documented |
| 8 Deploy Check | target env, intended commit/version, latest test report, rollback/monitoring/env readiness | `docs/deployment/deploy-check-YYYY-MM-DD.md` | Human GO / NO-GO |
| 9 Deploy | explicit GO, deploy command/procedure, migrations, rollback, smoke tests | `docs/deployment/deploy-YYYY-MM-DD-HHmm.md` | Smoke pass; else rollback status documented |
| 10 Verify & Release | production URL/version, critical flows, deferred issues, changelog/tag need | production verification notes, `CHANGELOG.md`, release tag, `docs/post-launch/known-issues.md` | Production OK |
| 11 Maintenance | bug/change type, impact/severity, affected version, rollback need | impact assessment, patch plan, updated tests/review/test/deploy artifacts | Repeat 6–10 gates |

If a phase changes blocker/status/next step, update `.planning/<id>/workflow-state.md`. After each meaningful work block, update `.planning/<id>/progress.md`. Approved decisions go to `.planning/<id>/audit-trail.md`.

---

## One plan vs multiple plans

| Approach | Pros | Cons |
|----------|------|------|
| Multiple plans (`repo-bootstrap`, `product-discovery`, …) | Clear gates | More `.planning/` folders |
| Single `kickoff` plan with phases in `task_plan.md` | One timeline | Easy to drift without phase updates |

Recommend newcomers: **separate plans for Phase 0 and Phase 1**.

---

## Anti-patterns

- Single prompt “read PDF and build the whole app” — skips gates 1–3.
- Skip Phase 0; scatter PDF outside `docs/product/source/`.
- Commit `.env`, secrets, `node_modules`.
- Deploy without `/deploy` + explicit human GO.
