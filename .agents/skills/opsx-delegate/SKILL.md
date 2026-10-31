---
name: opsx-delegate
description: Delegates a specific atomic task set from an approved Feature (FEAT-XXX), Change Request (CR-XXX), or Bug (BUG-XXX) to a specialist agent inbox (.agent-inbox/) enforcing Definition of Ready (DoR).
---

# Skill: `opsx-delegate`

Used by `@jarvis` (Tech Lead) to prepare and deposit a work order into a specialist agent's `.agent-inbox/` folder.

## Expected Parameters
- `<agent> <work-item-id>` (e.g. `front-ui CR-004-avatar-engine-dual-representation` or `back-domain FEAT-001-scaffolding`)

## Execution Steps:

1. **Resolve and Validate Specifications**:
   - Determine `<spec-dir>`:
     - `specs/features/<work-item-id>/` for `FEAT-*`
     - `specs/changes/<work-item-id>/` for `CR-*`
     - `specs/bugs/<work-item-id>/` for `BUG-*`
   - Verify that `<spec-dir>/01-spec.md`, `02-tech-spec.md`, and `03-tasks.md` exist.
   - Verify that if `<work-item-id>` is a `FEAT-*`, it is NOT already marked `Done` in `specs/BACKLOG.md` (`RN-SDD-IMMUTABLE-DONE`).
2. **Filter Specialist Tasks**:
   - Identify pending tasks (`- [ ]`) in `<spec-dir>/03-tasks.md` belonging to the target specialist:
     - `db-specialist`: DDL scripts, indexes, extensions, and seeds in `DDBB/scripts/`.
     - `back-domain`: Pure entities, Value Objects, Use Cases, and domain contracts.
     - `back-infra`: Persistence repositories, MCP clients, and CLI runners.
     - `back-api`: FastAPI routers, WebSockets/SSE, OIDC auth, and mirror DTOs.
     - `audio-voice`: Local TTS adapters, Web Audio API, and acoustic processing.
     - `back-test`: Unit and integration tests with pytest and in-memory fakes.
     - `front-logic`: Mirror TypeScript types, TanStack Query, Zustand, Event Bus, and contract adapters.
     - `front-ui`: React 19 components, Three.js / R3F / `@paco/avatar-engine`, Shaders, and Tailwind CSS.
     - `front-test`: Vitest, React Testing Library, ESLint, and type checking.
     - `devops`: Docker Compose, Dockerfiles, server config, and healthchecks.
     - `documentator`: Living documentation, user guides, and FAQs in `docs/`.
3. **Enforce Definition of Ready (DoR) on the Ticket**:
   - `@jarvis` verifies that every task specifies exact file paths, unambiguous types/contracts, and a deterministic verification command.
4. **Generate Inbox Ticket**:
   - Write `.agent-inbox/<agent>/<work-item-id>.md` containing:
     - Target `<spec-dir>` path (`specs/features/...` or `specs/changes/...`).
     - Relevant User Story context and BDD Acceptance Criteria.
     - Atomic tasks with DoR.
     - Mirror technical contracts from `<spec-dir>/02-tech-spec.md`.
     - Exact verification command (DoD).
5. **Confirmation**:
   - Notify that the ticket is ready for pickup by the specialist.
