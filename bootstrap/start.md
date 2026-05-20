Use the bootstrap-session skill (`skills/bootstrap-session/SKILL.md`).

Intent mapping:
- `/start` => guided startup wizard
- `/start maintain` => maintain mode for current folder
- `/start maintain <project-path>` => maintain mode for explicit project path
- `/start create <project-path>` => create mode and bootstrap a new project at target path

`/start create <project-path>` execution contract:
1. Validate/create target folder
2. Create minimum bridge files in target project:
   - `AGENTS.md`
   - `.workflow/config.yaml`
   - `.workflow/START.md`
   - `.planning/` directory
   - `README.md` starter (if missing)
3. Create adapter skeleton in workflow repo:
   - `adapters/<project-slug>.yaml`
4. Continue one-question-at-a-time Q&A in this order:
   - project description / goal / available documents first
   - design checkpoint:
     - if design exists: ask path/link and expected implementation fidelity
     - if design is missing: use `skills/bootstrap-session/design-intake-kit.md`, ask discovery questions, then derive screen list for confirmation
     - offer mockup/wireframe generation before implementation
   - then constraints and integration needs
   - then propose stack options for user confirmation
   - then capture any subsystem-specific tech requirements
5. Stop and show startup summary + suggested next command

Rules:
- Ask exactly one question at a time.
- If opened directly inside a project folder, do not ask project path unless unclear.
- If workflow root cannot be resolved from `.workflow/config.yaml` or env, ask once and store in local bridge config.


Session control:
- /end => close active target session
- /switch <mode> <project-path> => safe context switch with confirmation


Scaffold source of truth:
- `create-project/SCAFFOLD-CONTRACT.md`
- `create-project/templates/AGENTS.template.md`
- `create-project/templates/START.template.md`
- `create-project/templates/workflow-config.template.yaml`

For `/start create <project-path>`, generated project files must be rendered from these templates (not minimal placeholders).
