---
name: sdd-change-gate
description: Mandatory Spec-Driven Development (SDD) Pre-Edit Decision Gate. Activate whenever changes touch existing features, packages/contracts, or specs/. Enforces RN-SDD-IMMUTABLE-DONE and RN-SDD-1-TO-1-CR.
---

# Skill: `sdd-change-gate` (SDD Pre-Edit Decision & Change Request Gate)

Run **before** editing `specs/` or `src/` whenever requests modify existing capabilities, libraries, or requirements.

## 1. Decision Matrix (Check `specs/BACKLOG.md` First)
| Target Feature Status | Nature of Request | Permitted Action | Prohibited Action |
| :--- | :--- | :--- | :--- |
| **Not registered** | Net-new capability | Register `FEAT-XXX` (Gate 0) + `specs/features/FEAT-XXX-<slug>/` | Coding before Gate 2 approval |
| **`Backlog` / `In Progress` / `In Review`** | Scope adjustment | Update `specs/features/FEAT-XXX-<slug>/` (Stop-the-Line) | Coding before updated Gate 2 |
| **`Done` / `Completado`** | Evolution / library or UI change | Create **1 CR per affected Feature** (`specs/changes/CR-<NUM>-<slug>/`) | **NEVER edit `specs/features/FEAT-XXX-*/`** (`RN-SDD-IMMUTABLE-DONE`) |
| **`Done` / `Completado`** | Defect vs approved spec | Create `specs/bugs/BUG-<NUM>-<slug>/` | Mutating `Done` feature or skipping red test |

## 2. 1:1 Change Request Checklist (`RN-SDD-1-TO-1-CR`)
When $N$ `Done` features are impacted, create **$N$ separate `specs/changes/CR-<NUM>-<slug>/` folders**, each with:
- `01-spec.md`: `Target Feature: FEAT-XXX`, functional delta (Before vs After), User Stories, Given-When-Then.
- `02-tech-spec.md`: architectural delta, affected files, contracts, performance/regression risks.
- `03-tasks.md`: atomic tasks by layer with deterministic DoD commands.
Register each `CR-XXX` in `specs/BACKLOG.md` and wait for explicit human Gate 1–3 sign-off (`RN-SDD-HUMAN-GATE-OWNERSHIP`) before coding.
