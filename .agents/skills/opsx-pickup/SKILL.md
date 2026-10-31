---
name: opsx-pickup
description: Picks up a pending task ticket from the specialist agent's inbox (.agent-inbox/), audits Definition of Ready (DoR), implements the code within allowed boundaries, and validates Definition of Done (DoD).
---

# Skill: `opsx-pickup`

Executed by any specialist agent on the development team to process the assigned ticket in its `.agent-inbox/` folder.

## Execution Steps:

1. **Locate Inbox Ticket**:
   - Inspect `.agent-inbox/{agent-name}/`.
   - Locate the pending ticket (`<work-item-id>.md`, which may be a `FEAT-XXX`, `CR-XXX`, or `BUG-XXX`).
   - Identify the target `<spec-dir>` (`specs/features/<work-item-id>/`, `specs/changes/<work-item-id>/`, or `specs/bugs/<work-item-id>/`).
2. **🛑 Mandatory Definition of Ready (DoR) Audit**:
   - Are the exact files to create or modify defined?
   - Are all fields, types, and contracts specified without ambiguity?
   - Does the work belong 100% to my permitted directory boundary?
   - Is the verification command clear and executable?
   - Is the target specification either an active `CR-XXX`, an active `BUG-XXX`, or an in-progress `FEAT-XXX` (never a `Done` `FEAT-XXX`)?
   - *If any answer is NO*: Stop immediately and write `BLOCKED_DOR_{work-item-id}.md` in your inbox.
3. **Implementation**:
   - With DoR verified, write code strictly within your permitted architectural boundary.
4. **Automated Definition of Done (DoD) Validation**:
   - Run the verification command assigned to your role (e.g., `dotnet test`, `pytest`, `npm run lint`, `npm test`, `docker compose config`).
   - If it fails, self-correct autonomously (up to 3 attempts).
5. **Inconsistency Check**:
   - If an unresolvable contradiction with the spec arises, write `BLOCKED_{work-item-id}.md` and stop execution (Stop-the-Line).
6. **Task Closure**:
   - With 100% green validation:
     - Mark completed tasks with `[x]` in `<spec-dir>/03-tasks.md` (never modifying a `Done` feature's `03-tasks.md`).
     - Remove the ticket `.agent-inbox/{agent-name}/<work-item-id>.md`.
     - Report completion to `@orchestrator`.
