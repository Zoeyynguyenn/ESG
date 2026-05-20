---
name: bootstrap-session
description: Start a guided Q&A bootstrap for maintain/create modes with adapter detection and project bridge support.
---

## Purpose
Run a one-question-at-a-time startup wizard when user sends `/start` or asks to begin workflow setup.

## Design intake reference
For create mode design intake, use:
- `skills/bootstrap-session/design-intake-kit.md`

## Supported commands
- `/start`
- `/start maintain`
- `/start maintain <project-path>`
- `/start create <project-path>`

## Command parsing
1. Read user message and parse mode + optional target path.
2. If mode omitted:
   - use bridge config `default_mode` when available
   - otherwise ask user to choose `create` or `maintain`.
3. If target path omitted:
   - use current working directory as project root.

## Procedure
1. Detect current working directory as candidate project root.
2. Try to load project bridge config from `.workflow/config.yaml` in current directory.
3. Resolve workflow root using this order:
   - `.workflow/config.yaml` -> `workflow_root`
   - environment variable `AI_WORKFLOWS_ROOT`
   - ask user for workflow root path
4. Resolve mode/path from parsed command, then bridge defaults, then ask user.
5. If mode is `maintain`:
   - if adapter path exists in bridge config, use it
   - else ask for adapter path
   - if adapter missing, ask to create adapter skeleton first
6. If mode is `create`:
   - ensure target project path exists (create if missing)
   - derive project slug from folder name
   - create minimum project bridge files:
     - `AGENTS.md`
     - `.workflow/config.yaml`
     - `.workflow/START.md`
     - `.planning/`
     - `README.md` starter when missing
   - create adapter skeleton at `<workflow_root>/adapters/<slug>.yaml`
   - run intake one question at a time in this order:
     1) project description and business context
     2) primary goal and success criteria
     3) available materials (PRD, PDF, design links/files, API docs, data samples)
     4) design checkpoint:
        - if user already has design: ask for the design path/link and preferred fidelity to implement from
        - if user has no design: ask design discovery questions one-by-one (target users, core user flows, style direction, brand constraints, device priorities, accessibility level)
        - then propose the required screen list and ask for confirmation
        - after confirmation, offer to generate initial UI mockups/wireframes before coding
     5) constraints (timeline, budget, compliance, integrations)
     6) only then propose recommended stack/architecture options for user confirmation
     7) ask whether user wants specific technologies for any subsystem
7. Ask exactly one question at a time and wait for user answer.
8. After bootstrap inputs are complete, output a startup summary:
   - workflow root
   - project root
   - mode
   - adapter path
   - next command (`/status` or `/plan <slug>`)
9. Stop and wait for user confirmation before running any implementation workflow.

## Rules
- Do not ask project path if current folder is already the target project and user confirms it.
- Ask only one question per turn.
- For new projects, adapter skeleton creation is mandatory before planning.
- Do not modify source code during bootstrap unless user explicitly asks.

## Session control
- `/end`
- `/switch maintain <project-path>`
- `/switch create <project-path>`

### Session state file
Use `bootstrap/session-state.yaml` in workflow root. If missing, create it from `bootstrap/session-state.template.yaml`.

### Required switching safety
1. If `session_status: active` and new target != `active_project_path`, ask double confirmation.
2. Before any write after switching, echo: `I will only modify <target-path>`.
3. Update `session-state.yaml` immediately after `/start`, `/end`, or `/switch`.

## Strict create scaffolding
For `/start create <project-path>`, scaffold files must be rendered from:
- `create-project/templates/AGENTS.template.md`
- `create-project/templates/START.template.md`
- `create-project/templates/workflow-config.template.yaml`

Reject incomplete scaffolding that does not include `/start` intent in generated project `AGENTS.md`.
