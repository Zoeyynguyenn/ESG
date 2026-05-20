Use the bootstrap-session skill (`skills/bootstrap-session/SKILL.md`).

Intent mapping:
- `/end` => close active target session safely

`/end` execution contract:
1. Read `bootstrap/session-state.yaml` (or create from template if missing)
2. Echo current active target (project path, mode, adapter)
3. Ask user confirmation to close
4. Set:
   - `session_status: closed`
   - move current active values to `last_*`
   - clear `active_*`
5. Output confirmation and suggest next command:
   - `/start maintain <path>` or `/start create <path>`

Safety:
- Do not switch to another target until `/end` closes current session, unless user explicitly confirms forced switch.
