---
name: opsx-delegate
description: Delegates an atomic task set from an approved Feature (FEAT-XXX), Change Request (CR-XXX), or Bug (BUG-XXX) to a specialist agent inbox (.agent-inbox/) enforcing Definition of Ready (DoR).
---

# Skill: `opsx-delegate`

Used by `@orchestrator` to write a DoR-verified work order into `.agent-inbox/<agent>/`.

## Expected Parameters
- `<agent> <work-item-id>` (e.g. `back-engineer FEAT-001-scaffolding` or `front-ui CR-002-checkout-flow`)

## Execution Steps
1. **Resolve & Validate Specs:**
   - Map `<spec-dir>` to `specs/features/<id>/`, `specs/changes/<id>/`, or `specs/bugs/<id>/`.
   - Verify `01-spec.md`, `02-tech-spec.md`, and `03-tasks.md` exist, and confirm any `FEAT-*` is NOT `Done` in `specs/BACKLOG.md` (`RN-SDD-IMMUTABLE-DONE`).
2. **Filter Tasks by Target Role:** Extract pending `- [ ]` tasks for the specialist in the active preset (`compact`: `back-engineer`, `front-engineer`, `qa-tester`, `devops`, `documentator`, `security-reviewer`; `granular`: `db-specialist`, `back-domain`, `back-infra`, `back-api`, `back-test`, `front-logic`, `front-ui`, `front-test`, plus active pack specialists).
3. **Enforce DoR:** Confirm exact file paths, unambiguous contracts from `02-tech-spec.md`, UI design refs (`SCR-XXX`, `MASTER@versión`) when applicable, and deterministic DoD command.
4. **Write Inbox Ticket:** Create `.agent-inbox/<agent>/<work-item-id>.md` with `<spec-dir>`, BDD context, atomic tasks, contracts, and DoD command, then notify completion.
