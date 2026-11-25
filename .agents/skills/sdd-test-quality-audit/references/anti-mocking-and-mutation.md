# Reference `sdd-test-quality-audit`: Anti-Mocking Boundaries, Determinism & Mutation Probes

Load during **Gate 4** (`@qa-tester`, `@back-engineer`, `@front-engineer`) to eliminate tautological green suites, timing/concurrency flakiness, and shallow assertions that survive production defects.

## 1. Forbidden Mock Tautologies ("Mock-Testing-Mock")

Reject as a **Gate 4 Blocker** any test exhibiting these patterns:

1. **Interaction-Only Assertions (`assert_called` without State/Output):**
   - Calling `repo_mock.save.assert_called_once()` or `expect(client.post).toHaveBeenCalled()` without asserting exact return fields, persisted entity state, HTTP status/body, or emitted outbox events.
2. **Partial Mocking of the System Under Test (SUT):**
   - Using `mock.patch.object(OrderService, "_compute_total")` while testing `OrderService.checkout()`. Mocking internal SUT methods validates test setup rather than production branches.
3. **Drifted Hand-Rolled Stubs:**
   - Returning ad-hoc literals (`{"ok": True}`) from fakes that diverge from the typed schema in `02-tech-spec.md` (missing required fields, wrong nullability, or unnormalized formats).
4. **Vacuous Truthiness Checks:**
   - Asserting only `assert res is not None`, `expect(data).toBeDefined()`, or HTTP `200` without checking payload values and invariants.

```python
# FORBIDDEN: interaction tautology — passes even if total is negative or status stays DRAFT
service.checkout(order_id)
repo_mock.save.assert_called_once()

# COMPLIANT: exercises real domain logic against in-memory/ephemeral store and asserts state
receipt = service.checkout(order_id, now=FIXED_UTC)
saved = repo.get(order_id)
assert saved.status == OrderStatus.PAID
assert receipt.total_cents == 4250
```

## 2. Allowed Test-Double Boundary vs. Forbidden Internal Mocking

Apply the **Hexagonal Boundary Rule**: double nondeterministic or out-of-process boundaries in `< 1s` unit suites (`specs/STACK.md §2.5`), never internal domain logic.

| Collaborator Layer | Unit Suite (`< 1s`) | Integration Suite | Rule Rationale |
| :--- | :--- | :--- | :--- |
| **Domain entities, value objects, policies** | **REAL ONLY** | **REAL ONLY** | Pure logic; mocking hides broken invariants. |
| **DTO parsers, serializers, state machines** | **REAL ONLY** | **REAL ONLY** | Detects contract drift against `02-tech-spec.md`. |
| **Clock, monotonic timer, UUID / PRNG** | **Injected Fake** | **Controlled Fake** | Deterministic TTL, DST, leap-year, and retry checks. |
| **External HTTP/gRPC, payments, KMS, SMTP** | **Typed Contract Stub** | **Local Sandbox / Stub** | Avoids network flakiness and live credentials. |
| **SQL queries, transactions, RLS, migrations** | Fake *only* for pure app routing | **REAL Ephemeral DB** | Mocked SQL misses syntax bugs, missing `ROLLBACK`, and `rowcount == 0`. |

## 3. Determinism Against Flakiness, Concurrency & Time

1. **Ban Arbitrary `sleep` Waits:**
   - Prohibit `time.sleep()`, `Thread.sleep()`, and fixed `setTimeout()` delays in tests.
   - Synchronize with explicit primitives (`asyncio.Event`, `threading.Barrier`, `CountDownLatch`, fake timers, or `10ms` condition polling with diagnostic timeouts).
2. **Explicit UTC & Boundary Clocks:**
   - Never invoke `datetime.now()` / `Date.now()` directly in domain rules or test assertions.
   - Inject UTC timestamps covering exact boundaries (`expires_at - 1ms` valid, `expires_at` rejected, leap day `2028-02-29`, DST transitions).
3. **Controlled Concurrency & Race Verification:**
   - Test idempotency keys, optimistic locking, and quota contention by releasing workers simultaneously across a `Barrier(2)` / `Promise.all` over an isolated store and asserting a single winner or idempotent state.
4. **Order-Independent Isolation:**
   - Zero shared mutable globals; isolate filesystem (`tempfile.TemporaryDirectory`), DB file/schema, and TCP ports per worker (`specs/STACK.md §2.5`).

## 4. Mutation Probe Protocol per `Given-When-Then` Scenario

For each acceptance scenario (`CA-XXX` in `01-spec.md`), verify the mapped test turns **Red** under 4 production probes:

```text
[CA-XXX Scenario]
  ├─ Probe 1 (Boundary Flip):    `<` <-> `<=` or `==` <-> `!=` on limits/quotas  ──► Test MUST FAIL
  ├─ Probe 2 (Guard Removal):    Bypass AuthZ / tenant / input validation check  ──► Negative test MUST FAIL
  ├─ Probe 3 (Side-Effect Drop): Skip state mutation or outbox/event persistence ──► State assertion MUST FAIL
  └─ Probe 4 (Constant Return):  Return hardcoded `{}` / `True` / `200 OK`       ──► Field assertion MUST FAIL
```

- **Remediation:** Any probe that stays **Green** proves a tautological or under-asserted test; strengthen assertions before Gate 4 closure (never commit the probe mutation).
- **Optional Runners (if configured in `specs/STACK.md`):** `mutmut` (Python), `Stryker` (TS/JS/C#), `PIT` (JVM), `cargo-mutants` (Rust) scoped to changed files.

## 5. Gate 4 QA Sign-Off Checklist

- [ ] Every `Given-When-Then` in `01-spec.md` (happy + negative `400`/`401`/`403`/`409`) maps to an automated test.
- [ ] Zero tests assert only `assert_called*` / `toHaveBeenCalled*` or mock internal SUT methods.
- [ ] Zero `sleep` waits, unseeded randomness, or host-timezone dependencies.
- [ ] All 4 mutation probes (`Boundary`, `Guard`, `Side-Effect`, `Constant`) fail deterministically.
