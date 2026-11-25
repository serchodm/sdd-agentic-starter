---
name: sdd-test-quality-audit
description: Audits unit, integration, and E2E tests to eliminate suspicious green tests, mock-only tautologies, and missing BDD acceptance coverage (morluto/rea).
---

# Skill: `sdd-test-quality-audit`

Run during Gate 4 QA verification to guarantee real semantic test coverage rather than superficial green runs.

> **Reference (load on demand):** [references/anti-mocking-and-mutation.md](references/anti-mocking-and-mutation.md) (mock tautologies, test-double boundaries, time/concurrency determinism, mutation probes).

## 1. BDD Traceability
- Map every `Given-When-Then` scenario in `<spec-dir>/01-spec.md` to at least one automated test; any uncovered scenario is a **Gate 5 Blocker**.

## 2. "Suspicious Green Test" Audit
1. **No Mock-Testing-Mock Tautologies:** Mock only external boundaries (clock, network, third-party APIs); never mock domain logic or assert `mock.assert_called` without verifying state/output.
2. **No Vacuous Assertions:** Assert exact output fields, state transitions, and emitted events (never just `is not None` / `toBeDefined()`).
3. **Negative, Boundary & Determinism:** Cover invalid inputs, auth failures (`401`/`403`), malformed payloads, and deterministic clocks/concurrency without `sleep`.
4. **Mutation Resistance:** Inverting or deleting the core production conditional must fail (`Red`); apply probes in [references/anti-mocking-and-mutation.md](references/anti-mocking-and-mutation.md).
