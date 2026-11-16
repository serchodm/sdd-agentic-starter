---
name: sdd-spec-compliance-audit
description: Audits 1:1 compliance between approved 02-tech-spec.md contracts and implemented code across Backend, Frontend, and external packages (morluto/rea & affaan-m/ecc).
---

# Skill: `sdd-spec-compliance-audit`

Run during QA verification before declaring `FEAT-XXX` or `CR-XXX` `Done` at Gate 5.

## 1. Mirror Contract & Type Audit
- Extract every Domain Entity/VO, backend DTO, frontend TypeScript interface/store, and event/external package contract from `<spec-dir>/02-tech-spec.md`.
- Verify 1:1 field names, aliases (`camelCase`/`snake_case`), and types on disk, with **zero `any`**, `as unknown as`, or undocumented `# type: ignore`.

## 2. Producing-Boundary & Boundary Check (`morluto/rea`)
- Confirm external payloads/events are normalized at **one producing boundary** (explicit adapter), never guessed across multiple consumers.
- Run: `uv run python .agents/scripts/verify_architecture_boundaries.py`.

## 3. Superseded Code Cleanup
- In `CR-XXX` replacements, verify dead wrappers, superseded files, and unused imports listed in `02-tech-spec.md` are **deleted** (no zombie fallbacks).
