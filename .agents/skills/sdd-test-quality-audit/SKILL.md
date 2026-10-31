---
name: sdd-test-quality-audit
description: Audits unit, integration, and E2E tests to eliminate "suspicious green tests", mock-only tautologies, and missing BDD acceptance coverage. Inspired by morluto/rea (rea-ci-tests-audit & mutation verification).
---

# Skill: `sdd-test-quality-audit`

Activate this skill during Phase 6 (`back-test`), Phase 9 (`front-test`), and Phase 11.5 (`pipeline-run`) to ensure tests provide genuine semantic guarantees rather than superficial green checkmarks.

## 1. BDD Scenario Traceability Matrix
1. List every `Given-When-Then` scenario in `<spec-dir>/01-spec.md`.
2. Map each scenario to at least one concrete test function in `backend/tests/` or `frontend/src/**/*.test.{ts,tsx}`.
3. Any `Given-When-Then` scenario without a corresponding automated test is a **Gate 5 Blocker**.

## 2. "Suspicious Green Test" Audit (`morluto/rea` Protocol)
Audit every new test against the following 4 failure modes:
1. **Mock-Testing-Mock Tautology:** Does the test mock the very class/function under test and then assert that the mock returned its configured value? (Forbidden: mock only external I/O boundaries; exercise real domain/application/adapter logic).
2. **Weak / Vacuous Assertions:** Does the test only check `expect(result).toBeDefined()` or `assert response is not None` instead of asserting the exact output fields, state transitions, and emitted events?
3. **Missing Negative & Boundary Cases:** Does the test suite verify invalid inputs, unauthorized roles (`401`/`403`), disconnected streams, and malformed payloads as specified in `01-spec.md`?
4. **Semantic Perturbation Check (Mental or Live Mutation):**
   - Verify that if the key conditional or transformation in the production function were inverted or commented out, the test would deterministically fail (`Red`).
