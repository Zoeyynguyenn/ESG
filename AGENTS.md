# ai-native-flow for Codex / Workflow file-backed cho Codex

> **Agent contract (EN â€” authoritative):** Follow the English rules, paths, intents, and skill **procedure steps** below exactly. If EN and VI procedural text differ, **English wins** for agent behavior.
>
> **Documentation outputs:** All artifact prose must be **Vietnamese** â€” see **Documentation language** below and `docs/vi/ngon-ngu-tai-lieu.md`.
>
> **HÆ°á»›ng dáº«n tiáº¿ng Viá»‡t:** `docs/vi/README.md`, `docs/vi/workflow-guide.md`, `docs/vi/project-lifecycle.md`

This repository uses a file-backed workflow for long-running Codex sessions. Workflow state lives on disk, not only in model context.

Repo dÃ¹ng workflow lÆ°u trÃªn file cho session Codex dÃ i. Tráº¡ng thÃ¡i náº±m trÃªn disk, khÃ´ng chá»‰ trong context model.

## Session State / Tráº¡ng thÃ¡i phiÃªn

Read these files first when starting substantial work, resuming a task, or re-orienting after context compaction:

Äá»c cÃ¡c file sau khi báº¯t Ä‘áº§u viá»‡c lá»›n, resume task, hoáº·c re-orient sau compaction:

- Active plan: `.planning/current_plan` -> `.planning/<id>/task_plan.md`
- Session log: `.planning/<id>/progress.md`
- Knowledge base: `.planning/<id>/findings.md`
- Workflow state: `.planning/<id>/workflow-state.md`
- Decision trail: `.planning/<id>/audit-trail.md`
- Test scenarios: `.planning/<id>/test-scenarios.md`

If `.planning/current_plan` is missing, do not create a plan unless the user asks to start one.

Náº¿u thiáº¿u `.planning/current_plan`, khÃ´ng táº¡o plan trá»« khi user yÃªu cáº§u.

## Commands / Intent workflow

Codex may receive slash-style text or natural language. Treat them as workflow intents:

Codex cÃ³ thá»ƒ nháº­n slash hoáº·c cÃ¢u tá»± nhiÃªn. Coi Ä‘Ã³ lÃ  workflow intent:

| Intent | Action |
|--------|--------|
| `/plan` or plan request | Use `shared/skills/plan-session/SKILL.md`; new plans must also create test scenarios |
| `/status` or status request | Show goal, current phase, blockers, and next step |
| `/review` | Use `shared/skills/review-code/SKILL.md` |
| `/test plan` | Use `shared/skills/test-strategy/SKILL.md` |
| `/test run` | Use `shared/skills/test-run/SKILL.md` |
| `/deploy` | Use `shared/skills/deploy-check/SKILL.md` |
| `/log` or decision log request | Use `shared/skills/decision-log/SKILL.md` |
| compact preparation | Use `shared/skills/session-compact/SKILL.md` |

| Intent | HÃ nh Ä‘á»™ng (VI) |
|--------|----------------|
| `/plan` | DÃ¹ng skill plan-session; plan má»›i pháº£i cÃ³ test scenarios |
| `/status` | Tráº£ goal, phase hiá»‡n táº¡i, blocker, bÆ°á»›c tiáº¿p theo |
| `/review` | Skill review-code |
| `/test plan` | Skill test-strategy |
| `/test run` | Skill test-run |
| `/deploy` | Skill deploy-check |
| `/log` | Skill decision-log |
| compact preparation | Skill session-compact |

## Documentation language / NgÃ´n ngá»¯ tÃ i liá»‡u

**All documentation artifacts must be written in Vietnamese (tiáº¿ng Viá»‡t).**

Applies to: committed `docs/` (product, architecture, api, tasks, decisions, review, test-reports, deployment, post-launch) and `.planning/<id>/` prose (`task_plan.md` Goal/notes, `findings.md`, `progress.md`, `workflow-state.md`, `audit-trail.md`, `test-scenarios.md`). Workflow replies to humans (`/status`, review/deploy summaries) use Vietnamese.

**Keep in English:** file paths, plan slugs, intents (`/plan`, GO/NO-GO), `MACHINE_STATE` phase names, code/env/API identifiers, YAML keys, verbatim technical quotes; severity labels CRITICAL/WARN/INFO (describe findings in Vietnamese).

Full policy: `docs/documentation-language.md` Â· `docs/vi/ngon-ngu-tai-lieu.md`

**Má»i káº¿t quáº£ tÃ i liá»‡u pháº£i báº±ng tiáº¿ng Viá»‡t** (trá»« ngoáº¡i lá»‡ trÃªn).

## Rules / Quy táº¯c

1. Write findings to `findings.md` after every 2 research operations. / Ghi `findings.md` sau má»—i 2 láº§n research â€” **ná»™i dung tiáº¿ng Viá»‡t**.
2. Update `progress.md` after completing any meaningful work block. / Cáº­p nháº­t `progress.md` sau má»—i work block â€” **tiáº¿ng Viá»‡t**.
3. Log decisions immediately with rationale. / Ghi quyáº¿t Ä‘á»‹nh ngay kÃ¨m rationale â€” **tiáº¿ng Viá»‡t** trong `audit-trail.md`.
4. Await human confirmation before phase transitions. / Chá» human confirm trÆ°á»›c khi chuyá»ƒn phase.
5. After every new plan, create or update `.planning/<id>/test-scenarios.md` using the test-strategy workflow before implementation. / Plan má»›i pháº£i cÃ³ `test-scenarios.md` trÆ°á»›c implementation.
6. Require explicit human GO/NO-GO before deployment. / Deploy cáº§n GO/NO-GO rÃµ rÃ ng.
7. Do not run autonomous loops or self-schedule future work. / KhÃ´ng tá»± cháº¡y vÃ²ng láº·p hoáº·c lÃªn lá»‹ch viá»‡c tÆ°Æ¡ng lai.
8. Before broad edits, read the active plan if one exists. / TrÆ°á»›c khi sá»­a rá»™ng, Ä‘á»c plan active.

## Codex Adapter Notes / Ghi chÃº Codex

- Do not rely on Claude Code hooks, slash-command registration, or the Claude Task tool.
- Workflow skills in `shared/skills/` are repository-local instructions. Open the relevant `SKILL.md` only when the user asks for that workflow.
- Perform review, test analysis, deploy checks, and decision formatting locally unless the user explicitly asks for parallel agents or delegation.
- Store active workflow files under `.planning/<id>/`, not `.claude/`.
- Keep shared, team-wide knowledge in `docs/`; keep per-task state in `.planning/<id>/`.
- Use `docs/workflows/project-lifecycle.md` (EN) or `docs/vi/project-lifecycle.md` (VI) as the full project lifecycle from bootstrap to deploy.
- New project from PDF + design: `docs/workflows/new-project-from-zero.md` (EN) or `docs/vi/new-project-from-zero.md` (VI) â€” **Phase 0 (repo bootstrap) before Phase 1 (Discovery)**.

- KhÃ´ng dá»±a vÃ o Claude hooks, Ä‘Äƒng kÃ½ slash runtime, hoáº·c Claude Task tool.
- Skill trong `shared/skills/`: chá»‰ má»Ÿ `SKILL.md` khi user gá»i workflow tÆ°Æ¡ng á»©ng.
- Review, test, deploy check, decision log lÃ m local trá»« khi user yÃªu cáº§u delegate.
- State active: `.planning/<id>/`, khÃ´ng `.claude/`.
- Kiáº¿n thá»©c team: `docs/`; state task: `.planning/<id>/`.

## Context Discipline / Ká»· luáº­t context

- Re-orient by reading `.planning/current_plan`, then targeted sections of `task_plan.md`, `progress.md`, and `findings.md`.
- Keep `task_plan.md` under 50 lines when practical.
- Keep `findings.md` under 100 lines when practical.
- Before a user-requested compaction/reset, run the session-compact workflow and make sure state is flushed to files.

- Re-orient: `current_plan` -> `task_plan.md`, `progress.md`, `findings.md`.
- `task_plan.md` nÃªn dÆ°á»›i 50 dÃ²ng; `findings.md` dÆ°á»›i 100 dÃ²ng khi cÃ³ thá»ƒ.
- TrÆ°á»›c compaction/reset: cháº¡y session-compact vÃ  flush state ra file.

## Bootstrap Intent

- `/start` triggers guided bootstrap Q&A using `skills/bootstrap-session/SKILL.md`.
- Ask one question at a time and wait for answer.
- If current folder is already a project root, skip asking project path.
- For create mode with no adapter, create adapter skeleton first, then proceed to planning.

- `/end` closes active target session and clears active context.
- `/switch <mode> <project-path>` performs safe target switching with confirmation.
- Maintain one active target at a time via `bootstrap/session-state.yaml`.
