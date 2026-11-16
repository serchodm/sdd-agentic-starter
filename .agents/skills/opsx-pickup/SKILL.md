---
name: opsx-pickup
description: Picks up a pending task ticket from the specialist agent's inbox (.agent-inbox/), audits Definition of Ready (DoR), implements within allowed boundaries, and validates Definition of Done (DoD).
---

# Skill: `opsx-pickup`

Executed by specialist/builder agents to process `.agent-inbox/{agent-name}/<work-item-id>.md`.

## Execution Steps
1. **Locate Ticket:** Open `.agent-inbox/{agent-name}/<work-item-id>.md` (`FEAT-*`, `CR-*`, or `BUG-*`) and resolve `<spec-dir>`.
2. **Mandatory DoR Audit (Fail-Closed):** Verify exact file paths, unambiguous contracts, 100% Ownership Map boundary fit, executable DoD command, and non-`Done` `FEAT-*` (`RN-SDD-IMMUTABLE-DONE`). If any check fails, stop and write `.agent-inbox/{agent-name}/BLOCKED_DOR_{work-item-id}.md`.
3. **Implement:** Write code strictly within your permitted Ownership Map directory/worktree.
4. **Validate DoD:** Run your assigned verification command (max 3 self-correction attempts). On spec contradiction, write `BLOCKED_{work-item-id}.md` and stop.
5. **Close Task:** Mark completed tasks `[x]` in `<spec-dir>/03-tasks.md`, delete the inbox ticket, and report to `@orchestrator`.
