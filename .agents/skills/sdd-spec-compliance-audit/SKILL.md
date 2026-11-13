---
name: sdd-spec-compliance-audit
description: Audits 1:1 compliance between approved 02-tech-spec.md contracts and implemented code across Backend (Pydantic/FastAPI), Frontend (TypeScript/React), and external packages. Inspired by morluto/rea (Producing-Boundary Ownership & Obsolete Code Removal) and affaan-m/ecc (type-design-analyzer & code-reviewer).
---

# Skill: `sdd-spec-compliance-audit`

Activate this skill during Block D of `pipeline-run` (or before declaring any Feature `FEAT-XXX` or Change Request `CR-XXX` Done at Gate 5) to perform a fresh-context compliance review.

## 1. Mirror Contract & Type Invariant Audit (`type-design-analyzer`)
1. Read `<spec-dir>/02-tech-spec.md` and extract every declared:
   - Domain Entity / Value Object (`backend/src/domain/`)
   - Input/Output Pydantic DTO (`backend/src/api/`)
   - TypeScript Interface / Store Contract (`frontend/src/types/`, `frontend/src/stores/`)
   - Event Bus / External Package Contract (e.g. `avatar.*` events for `@paco/avatar-engine`)
2. Compare against the actual files on disk:
   - Verify 1:1 field name, alias (`camelCase` vs `snake_case`), and type correspondence.
   - Verify **zero usage of `any`**, `as unknown as ...` bypasses, or `# type: ignore` without documented justification in `02-tech-spec.md`.

## 2. Producing-Boundary Ownership Audit (`morluto/rea`)
1. Confirm that every external payload or event contract is parsed and normalized at **one single producing boundary** (e.g., an explicit adapter module), rather than being re-parsed or guessed across multiple UI components or services.
2. Run the deterministic boundary checker:
   ```powershell
   c:\Projects\sdd-agentic-starter\backend\.venv\Scripts\python.exe c:\Projects\sdd-agentic-starter\.agents\scripts\verify_architecture_boundaries.py
   ```

## 3. Obsolete & Superseded Code Cleanup Audit (`morluto/rea`)
1. When auditing a **Change Request (`CR-XXX`)** that replaces a library, shader, component, or contract:
   - Verify that superseded files, dead wrappers, and unused imports identified in `02-tech-spec.md` have been **completely removed** in the same change.
   - Never leave dead fallback paths or zombie modules behind.
