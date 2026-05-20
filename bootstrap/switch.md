Use the bootstrap-session skill (`skills/bootstrap-session/SKILL.md`).

Intent mapping:
- `/switch maintain <project-path>` => close or force-close current session, then start maintain on target
- `/switch create <project-path>` => close or force-close current session, then start create on target

`/switch` execution contract:
1. Read `bootstrap/session-state.yaml`
2. If an active session exists and target differs:
   - ask double confirmation before switching
3. Perform `/end` flow (normal or forced by explicit user confirmation)
4. Start equivalent `/start ...` flow on new target
5. Write updated active session values to `session-state.yaml`

Safety:
- Always echo target path before any file write.
- Always state write boundary: "I will only modify <target-path>".
