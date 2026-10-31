---
name: sdd-change-gate
description: Mandatory Spec-Driven Development (SDD) Pre-Edit Decision Gate. Activate whenever the user requests changes to existing features, integrates a new library/engine/contract, modifies requirements, or updates specifications in specs/. Enforces RN-SDD-IMMUTABLE-DONE (Done features are read-only) and RN-SDD-1-TO-1-CR (1 Change Request per affected Done feature).
---

# Skill: `sdd-change-gate` (SDD Pre-Edit Decision & Change Request Gate)

Use this skill **before** editing any file in `specs/` or any production source file whenever a user request touches existing system capabilities, integrates an external package/contract, or alters functional/technical requirements.

## 1. Mandatory Pre-Edit Audit Protocol

1. **Read `specs/BACKLOG.md` First:**
   - Identify every Feature (`FEAT-XXX`) impacted by the user's request.
   - Check the current status of each impacted `FEAT-XXX` (`Pending`, `In Progress`, or `Done` / `Completado`).

2. **Apply the Cardinality & Immutability Decision Matrix:**

| Target Feature Status in `specs/BACKLOG.md` | Nature of Request | Permitted Action | Prohibited Action |
| :--- | :--- | :--- | :--- |
| **Does not exist** | Net-new capability | Register `FEAT-XXX` in `specs/BACKLOG.md` (Gate 0) and create `specs/features/FEAT-XXX-<slug>/` | Writing code before Gate 2 approval |
| **`Pending` / `In Progress`** (Gate 5 NOT passed) | Scope adjustment or refinement | Update `specs/features/FEAT-XXX-<slug>/` following Stop-the-Line protocol | Writing code before updated Gate 2 approval |
| **`Done` / `Completado`** (Gate 5 PASSED) | Evolution, library swap, new contract, UI/UX redesign | Create **1 Change Request per affected Feature** in `specs/changes/CR-<NUM>-<slug>/` (`01-spec.md`, `02-tech-spec.md`, `03-tasks.md`) | **NEVER edit or overwrite `specs/features/FEAT-XXX-*/`** (`RN-SDD-IMMUTABLE-DONE`) |
| **`Done` / `Completado`** (Gate 5 PASSED) | Defect / deviation from approved spec | Create `specs/bugs/BUG-<NUM>-<slug>/` (`01-bug-report.md`, `02-fix-spec.md`, `03-tasks.md`) | Mutating `specs/features/FEAT-XXX-*/` or fixing code before red test |

## 2. 1:1 Change Request Creation Checklist (`RN-SDD-1-TO-1-CR`)

When $N$ completed features (`Done`) are impacted by a change (for example, `FEAT-004` for rendering and `FEAT-005` for event bus contracts):
1. Create **$N$ separate folders** under `specs/changes/`:
   - `specs/changes/CR-<NUM-1>-<kebab-case-name>/` targeting the first feature.
   - `specs/changes/CR-<NUM-2>-<kebab-case-name>/` targeting the second feature.
2. Inside **each** `CR-<NUM>-<slug>/` directory, generate:
   - `01-spec.md`: Explicitly state `Target Feature: FEAT-XXX`, the functional delta (Before in `FEAT-XXX` vs. After in `CR-XXX`), User Stories, and Given-When-Then Acceptance Criteria.
   - `02-tech-spec.md`: Explicitly state the architectural delta, affected files, TypeScript/Python contracts, performance invariants, and regression risks.
   - `03-tasks.md`: Atomic tasks ordered by architectural layer, each with its deterministic verification command.
3. Register each `CR-XXX` in `specs/BACKLOG.md` under the Change Requests section with status `Spec Ready (Gate 1-3 Pending Approval)`.
4. **Stop for Human Gate Sign-Off (`RN-SDD-HUMAN-GATE-OWNERSHIP`):** Present the Change Request artifacts to the user and wait for explicit approval before modifying any production code.
