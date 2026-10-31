---
name: pipeline-run
description: Executes the full autonomous SDD development lifecycle for an approved Feature (specs/features/FEAT-XXX) or Change Request (specs/changes/CR-XXX) across specialist agents, culminating in independent compliance/test audits and full holistic regression verification.
---

# Skill: `pipeline-run`

Executes the end-to-end development lifecycle for a formally approved **Feature** (`FEAT-XXX`), **Change Request** (`CR-XXX`), or **Bug** (`BUG-XXX`) that has passed Gates 1, 2, and 3 with explicit user approval.

## Expected Parameters
- `<work-item-id>`: Either a Feature ID (e.g. `FEAT-001-scaffolding`), a Change Request ID (e.g. `CR-001-update-auth`), or a Bug ID.

## Pre-Flight Governance Check (Mandatory)
1. Resolve the target specification folder (`<spec-dir>`):
   - If `<work-item-id>` starts with `FEAT-`: `specs/features/<work-item-id>/`
   - If `<work-item-id>` starts with `CR-`: `specs/changes/<work-item-id>/`
   - If `<work-item-id>` starts with `BUG-`: `specs/bugs/<work-item-id>/`
2. Verify that `01-spec.md`, `02-tech-spec.md`, and `03-tasks.md` exist in `<spec-dir>` and have been approved by the user (`RN-SDD-GATE2-CODE-LOCK`).
3. Verify that `.agents/active_work_item.json` is configured with `active_work_item_id = <work-item-id>` and `approved_by_human = true`.
4. If the target is a `FEAT-XXX` that is already marked `Done` in `specs/BACKLOG.md`, **ABORT IMMEDIATELY** (`RN-SDD-IMMUTABLE-DONE`) and require a `CR-XXX` instead.

---

## Multi-Agent DAG Execution Model (OpenSpec / Harness Engineering)

`@orchestrator` orchestrates the implementation strictly without writing production code directly (`RN-SDD-ORCHESTRATOR-SUBAGENTS`), processing `<spec-dir>/03-tasks.md` block by block:

```mermaid
graph TD
    subgraph DAG_Execution ["Grafo de Ejecución por Bloques"]
        B1["Bloque A [PARALLEL]: @back-domain & @front-logic<br/>(Contratos, DTOs & Interfaces Espejo)"] 
        --> S1["Barrera de Sincronización A"]
        S1 --> B2["Bloque B [SEQUENTIAL]: @back-infra, @db-specialist & @back-api<br/>(Persistencia, Repositorios, Migraciones & Endpoints)"]
        B2 --> S2["Barrera de Sincronización B"]
        S2 --> B3["Bloque C [PARALLEL]: @front-ui<br/>(Componentes Visuales, Vistas & Estilos)"]
        B3 --> S3["Barrera de Sincronización C"]
        S3 --> B4["Bloque D [SEQUENTIAL]: @back-test, @front-test & @qa-tester<br/>(Regresión 100% verde + Auditorías de Calidad)"]
        B4 --> B5["Bloque E [CONSOLIDATE]: @documentator<br/>(docs/ living docs + docs/knowledge/ & Matriz 0DD)"]
    end
```

### Operational Protocol per Block:
1. `@orchestrator` reads `<spec-dir>/03-tasks.md` and identifies the active execution block.
2. **If the block is marked `[PARALLEL]`**:
   - For each task in the block, `@orchestrator` dispatches a dedicated specialist subagent:
     - **In Antigravity**: Uses `invoke_subagent` passing:
       - `TypeName`: Agent role (e.g. `self` or specialist name).
       - `Role`: Specific specialist title (e.g. `Backend Domain Specialist`).
       - `Prompt`: Complete operational task order pointing to `.agent-inbox/<agent>/<work-item-id>.md`, mirror contracts from `02-tech-spec.md`, rules from `.agents/agents/<agent>.md`, and DoD command.
     - **In other environments**: Uses `runSubAgent` with equivalent payload.
   - `@orchestrator` waits at the **Synchronization Barrier** for all parallel subagents to complete and report green output (reactive notification, zero polling).
3. **If the block is marked `[SEQUENTIAL]`**:
   - Tasks execute sequentially, ensuring prerequisite contracts and services are running and verified before downstream components start.
4. Verify that each specialist has marked its task completed (`- [x]`) in `<spec-dir>/03-tasks.md` with zero unhandled errors and removed its ticket from `.agent-inbox/`.
5. **Quality & Boundary Audit (Phase D - Gate 4)**:
   - Run `sdd-spec-compliance-audit` (1:1 contract isomorphism, zero `any`, obsolete code cleanup).
   - Run `sdd-silent-failure-audit` (zero swallowed exceptions or silent fallbacks).
   - Run `sdd-test-quality-audit` (100% BDD scenario coverage, no mock-only tautologies).
   - Run the official test commands defined in `specs/STACK.md` (e.g. `dotnet test`, `pytest`, `npm test`).
   - Run `python .agents/scripts/sdd_healthcheck.py` (100% green).
6. **Consolidation of Living Knowledge (Phase E - Gate 5)**:
   - `@documentator` updates `docs/knowledge/API_CATALOG.md`, `docs/knowledge/DATA_MODELS.md`, `docs/knowledge/ADRS.md` and `docs/traceability/TRACEABILITY-MATRIX.md`.
   - `@documentator` updates bilingual user/architecture documentation in `docs/es/` and `docs/en/` (`RN-SDD-0DD`).
7. Upon confirming 100% compliance with the Definition of Done (DoD):
   - Update the status of `<work-item-id>` (`FEAT-XXX` or `CR-XXX`) to `Done` in `specs/BACKLOG.md` without mutating any historical `Done` feature baseline.
   - Reset `.agents/active_work_item.json` back to locked (`active_work_item_id: null`, `approved_by_human: false`).
   - Stage all changes (`git add -A`), create a semantic commit (`git commit -m "feat(<work-item-id>): ..."`), and push to remote (`git push origin main`).
