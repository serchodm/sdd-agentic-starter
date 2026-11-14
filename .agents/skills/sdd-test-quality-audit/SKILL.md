---
name: sdd-test-quality-audit
description: Audits unit, integration, and E2E tests to eliminate suspicious green tests, mock-only tautologies, and missing BDD acceptance coverage (morluto/rea).
---

# Skill: `sdd-test-quality-audit`

Run during Gate 4 QA verification to guarantee real semantic test coverage rather than superficial green runs.

## 1. BDD Traceability
- Map every `Given-When-Then` scenario in `<spec-dir>/01-spec.md` to at least one automated test; any uncovered scenario is a **Gate 5 Blocker**.

## 2. "Suspicious Green Test" Audit
1. **No Mock-Testing-Mock Tautologies:** Mock only external I/O boundaries; exercise real domain/application/adapter logic.
2. **No Vacuous Assertions:** Assert exact output fields, state transitions, and emitted events (never just `is not None` / `toBeDefined()`).
3. **Negative & Boundary Cases:** Cover invalid inputs, auth failures (`401`/`403`), disconnected streams, and malformed payloads from `01-spec.md`.
4. **Mutation Resistance:** Inverting or deleting the core production conditional must make the test fail (`Red`).
