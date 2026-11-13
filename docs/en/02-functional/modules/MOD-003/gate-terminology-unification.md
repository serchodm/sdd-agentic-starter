<p align="right">
  <strong>🇬🇧 English (EN-GB)</strong> | <a href="../../../../es/02-functional/modules/MOD-003/gate-terminology-unification.md">🇪🇸 Español (ES-ES)</a>
</p>

# `MOD-003`: Gate Terminology, Status, and DAG Graph Unification

- **Module Identifier:** `MOD-003`
- **Source Work Item / RFC:** `FWK-004-gate-terminology-unification` ([`RFC-002`](../../../../../.sdd/framework/rfcs/RFC-002-gate-terminology-unification.md))
- **Functional Status:** `Verified` (Confirmed and verified by 67 offline unit tests)
- **Master Index:** [DOCUMENTATION-INDEX.md](../../../00-governance/DOCUMENTATION-INDEX.md)

---

## 1. Purpose and Scope

### 1.1. Purpose (Confirmed)
This module eliminates normative ambiguities, numeric collisions (`Gate 00` vs `Gate 0`), bilingual status divergence (`Done`/`Completado`), and conceptual cross-contamination (`Gate` vs `Block` vs `Session Phase`) across the starter.

It guarantees that human engineers and AI agents share an unambiguous mental model backed by strict zero-breaking dual-acceptance and fail-closed validation.

### 1.2. In-Scope Features (Confirmed)
- **Canonical Gate Table:** `Gate S0` for project-level Stack Lock (`specs/STACK.md`) and `Gate 0..5` for Work Items (including conditional `Sub-Gate 2V` for visual validation on `SCR-###` screens).
- **Orthogonal Conceptual Separation:**
  - `Gate`: Formal quality and SDD governance gates (`Gate S0`, `Gate 0..5`).
  - `Block` / `DAG Block`: Atomic batches of concurrent or sequential tasks in `03-tasks.md`.
  - `Session Phase`: Conversation context partitions (`Session Phase A: Gates 0–3` / `Session Phase B: Gates 4–5`).
- **Fail-Closed Dual-Acceptance:**
  - `scripts/sdd_pack_registry.py` and `.agents/scripts/sdd_stack_gate_guard.py` accept canonical markers (`[x] Gate S0 Approved`, `stack_approved`) and legacy aliases (`[x] Gate 00 Approved`, `gate00_approved`).
  - Detection of boolean inconsistency between `stack_approved` and `gate00_approved` aborting with `StackConfigError`.
  - `StackConfig` and `squad.lock.json` retain backward compatibility via compatibility aliases.
- **Status Normalisation and CR Template Consolidation:**
  - Work Items: `Candidate` → `Backlog` → `In Progress` → `In Review` → `Done` (or `Blocked`).
  - Specs: `Draft` → `In Review` → `Approved` → `Done`.
  - Consolidation of Change Request templates into [`specs/templates/04-change-request-spec.template.md`](../../../../../specs/templates/04-change-request-spec.template.md) and removal of `04-change-spec.template.md`.
  - Fixed legacy broken links pointing to `03-ears-requirements.md`.

### 1.3. Out-of-Scope (Explicitly Excluded)
- Mutating historical completed items (`FWK-001`, `FWK-002`, `FWK-003`, `RFC-001`) protected by `RN-SDD-IMMUTABLE-DONE`.
- Upstream vendored files in `.sdd/catalog/packs/capability-ui-design/vendor/`.
- Production application code in `src/`.

---

## 2. Actors and Authority

| Actor | Responsibility | Key Constraint |
| :--- | :--- | :--- |
| **Human User / Tech Lead** | Authorises formal gates via explicit human sign-off (`[x] Gate S0 Approved`, `[x] Gate 1 Approved`, `[x] Gate 2 Approved`, `[x] Gate 2 Visual Sign-off`, `[x] Gate 3 Approved`). | AI agents never auto-approve gates (`RN-SDD-HUMAN-GATE-OWNERSHIP`). |
| **`@orchestrator`** | Structures the task DAG (`03-tasks.md`) into parallel and sequential blocks (`Block`), dispatches tasks to specialists, and monitors context session limits. | Does not write production code in the main thread (`RN-SDD-ORCHESTRATOR-SUBAGENTS`). |
| **`@back-engineer` / `@qa-tester`** | Implement executable contracts and test suites respecting modularity ($\le 500$ lines per file). | Must execute deterministic DoD verification commands without blind exploration. |
| **`@documentator`** | Maintains bilingual living documentation (0DD) and updates technical catalogues and traceability matrices at Gate 5. | Cannot close Gate 5 without certifying 1:1 bilingual consistency. |

---

## 3. Canonical Matrix of Gates and Statuses

| ID | Scope | EN Term | ES Term | Sign-off Criterion |
| :--- | :--- | :--- | :--- | :--- |
| `Gate S0` | Project | Stack Lock | Bloqueo de Stack | `[x] Gate S0 Approved (Human Sign-off)` / `stack_approved: true` |
| `Gate 0` | Work Item | Backlog Intake | Registro en Backlog | Unique ID in `specs/BACKLOG.md` + spec folder in `specs/` |
| `Gate 1` | Work Item | Functional Spec | Especificación Funcional | `[x] Gate 1 Approved (Human Sign-off)` |
| `Gate 2` | Work Item | Technical Spec | Especificación Técnica | `[x] Gate 2 Approved (Human Sign-off)` |
| *Sub-Gate 2V* | Work Item (`SCR-###`) | Visual Sign-off | Validación Visual | `[x] Gate 2 Visual Sign-off (Human)` |
| `Gate 3` | Work Item | Task Graph (DAG) | Plan de Tareas (DAG) | `[x] Gate 3 Approved (Human Sign-off)` |
| `Gate 4` | Work Item | Implementation & QA | Implementación y QA | Tests + 4 quality audits passing green |
| `Gate 5` | Work Item | Living Docs (0DD) & Closure | Documentación Viva (0DD) y Cierre | `docs/`, `TRACEABILITY-MATRIX.md`, `git push` |
