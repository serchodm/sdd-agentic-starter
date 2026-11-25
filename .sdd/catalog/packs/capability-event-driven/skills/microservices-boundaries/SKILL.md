---
name: microservices-boundaries
description: Domain-Driven Design (DDD) Bounded Contexts, Sync (REST/gRPC) vs. Async (Events) decision matrix, strict database-per-service isolation verified with verify_architecture_boundaries.py, resilience patterns (circuit breaker, bulkhead, explicit timeouts), and W3C traceparent/correlation-id propagation. Use when defining service boundaries, cross-service contracts, or fault-isolation guards under SDD Gate 2 and Gate 4.
---

# Microservices Boundaries & Resilience

Architectural boundary and fault-isolation playbook for preventing distributed monoliths, enforcing strict data ownership, choosing synchronous vs. asynchronous integration, and preserving end-to-end distributed observability.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) involves:

- Decomposing a domain into microservices or modular bounded contexts, or evaluating whether a new capability belongs in an existing service vs. a new service.
- Deciding between synchronous APIs (REST/gRPC) and asynchronous messaging (domain events/commands) across service edges.
- Reviewing cross-service data access, shared libraries, or database schemas to eliminate shared-table coupling.
- Adding resilience policies (timeouts, circuit breakers, bulkheads, bounded retries) to outbound HTTP, gRPC, or broker clients.
- Implementing or verifying end-to-end `traceparent`, `tracestate`, and `x-correlation-id` propagation across service hops.

## 2. Production Architecture & Patterns

### 2.1. Bounded Contexts (DDD) & Context Mapping

A microservice boundary must align with a **DDD Bounded Context** (cohesive business capability, ubiquitous language, independent deployment cadence, and clear team ownership) — never with technical horizontal layers (e.g., "the database service" or "the validation service").

| Context Map Pattern | When to Apply | Boundary Implementation |
| :--- | :--- | :--- |
| **Open Host Service + Published Language** | Upstream serves many downstream consumers | Versioned REST/gRPC API or versioned domain events documented in `docs/knowledge/API_CATALOG.md`. |
| **Anti-Corruption Layer (ACL)** | Integrating legacy monoliths, external SaaS, or unstable upstream domains | Dedicated inbound adapter translating foreign schemas into local domain value objects; never leak foreign DTOs into domain logic. |
| **Customer-Supplier** | One internal downstream team depends on one upstream team | Shared contract tests in CI (consumer-driven or OpenAPI/Protobuf breaking-change checks) before upstream deploys. |
| **Conformist** | Upstream cannot be modified and its model fits local needs | Explicitly mark as Conformist in Gate 2 ADR; isolate behind an internal interface so it can be replaced later. |
| **Separate Ways** | Cost of integration exceeds duplicating minor utility behavior | Keep bounded contexts decoupled; avoid forced shared libraries for trivial value objects. |

- **Aggregate Ownership:** Exactly one service is the System of Record for each aggregate's write model. Other services may hold read-only projections updated via versioned domain events, never mutate foreign aggregates directly.
- **Modular Monolith First Guardrail:** If two components require synchronous ACID joins on every request and always deploy together, keep them as isolated modules inside one deployable unit before paying distributed network overhead.

### 2.2. Integration Matrix: Sync (REST / gRPC) vs. Async (Events)

| Criterion | Synchronous (`REST` / `gRPC`) | Asynchronous (`Domain Events` / `Queues`) |
| :--- | :--- | :--- |
| **User Experience** | Caller needs immediate authoritative answer (login, checkout quote, read-after-write query) | Work can complete eventually (invoice PDF, notifications, search indexing, analytics) |
| **Temporal Coupling** | High — both caller and callee must be online simultaneously | Low — broker buffers spikes and absorbs downstream downtime |
| **Fan-Out** | `1:1` point-to-point request/response | `1:N` pub/sub where publisher has zero knowledge of subscribers |
| **Blast Radius** | Latency/failure cascades upstream unless shielded by timeouts + circuit breakers | Isolated per consumer group; failing consumer lags or routes to DLQ without blocking publisher |
| **Protocol Choice** | `REST/JSON` for public/external/browser edges; `gRPC/Protobuf` for low-latency internal service-to-service RPC | Kafka/Redpanda for ordered high-throughput event streams; SQS/RabbitMQ/NATS for task queues & routing |

**Rule of Thumb:** Never build synchronous call chains deeper than `2` internal hops on a critical user path. Replace cross-service synchronous read fan-outs with local event-driven materialized read models (CQRS projections).

### 2.3. Zero Shared Database Tables (Strict Data Ownership)

Sharing a database table across two services creates an undocumented, unversioned coupling that breaks independent deploys and schema migrations.

- **Database / Schema Per Service:** Each service owns its dedicated database instance (or isolated PostgreSQL schema + distinct DB role with zero `SELECT`/`INSERT`/`UPDATE`/`DELETE` grants on foreign schemas).
- **Least-Privilege Schema Isolation (PostgreSQL Baseline):**

```sql
-- Dedicated schema and role per bounded context (zero cross-schema grants)
CREATE SCHEMA IF NOT EXISTS orders_ctx;
CREATE ROLE orders_svc LOGIN PASSWORD '***';
REVOKE ALL ON SCHEMA public FROM orders_svc;
GRANT USAGE ON SCHEMA orders_ctx TO orders_svc;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA orders_ctx TO orders_svc;
ALTER ROLE orders_svc SET search_path = orders_ctx;
```

- **Forbidden Cross-Boundary Imports:** Service A must never import Service B's repository classes, SQLAlchemy/Prisma/TypeORM models, or internal domain modules. Cross-boundary communication occurs solely through declared API/event contracts.
- **Read-Model Projections Instead of Cross-DB Joins:** When Service A needs summary data owned by Service B (e.g., customer tier or product title), subscribe to Service B's domain events and maintain a local, eventually consistent read-model table owned by Service A.
- **Automated Architectural Enforcement:** Enforce import and package boundaries in CI using `.agents/scripts/verify_architecture_boundaries.py` so violations fail Gate 4 deterministically before merge.

### 2.4. Resilience Patterns: Timeouts, Circuit Breakers & Bulkheads

Every network call crosses an unreliable boundary and MUST declare explicit fault-isolation limits.

1. **Explicit Timeouts (Mandatory on Every Outbound Client):**
   - Always configure `connect_timeout`, `read_timeout`, and overall `deadline` / `request_timeout`.
   - Enforce **deadline propagation**: an outbound call timeout must never exceed the remaining time budget of the inbound request (`outbound_timeout < remaining_inbound_deadline`).
   - Example baseline for internal HTTP/gRPC calls: `connect=500ms`, `read=2000ms`, `total=3000ms` (adjust per Gate 2 SLA).
2. **Circuit Breaker (Fail-Fast Under Downstream Outage):**
   - Transitions: `CLOSED` (normal traffic) -> `OPEN` (trips when failure rate `>= 50%` or slow-call rate `>= 50%` over a sliding window of `>= 20` calls; short-circuits immediately with deterministic fallback or `503` without hitting the failing downstream) -> `HALF-OPEN` (after `open_duration`, e.g., `30s`, permits `3–5` probe calls to decide whether to close or reopen).
   - Never count caller validation errors (`400`, `404`, `422`) as downstream infrastructure failures that trip the breaker.
3. **Bulkhead (Resource Pool Isolation):**
   - Isolate connection pools, worker threads, and concurrency semaphores **per downstream dependency** (e.g., `max_concurrent_calls=20` for Payment Gateway, separate pool for Inventory Service).
   - A slow or hanging non-critical dependency (e.g., Recommendations) must saturate only its own bulkhead and shed load immediately (`429`/`503` or degraded fallback), never exhausting the caller's global HTTP/DB pool.
4. **Bounded Retries Only on Idempotent Calls:**
   - Retry only safe (`GET`, `HEAD`, `OPTIONS`) or explicitly idempotent operations carrying an `Idempotency-Key`, capped at `<= 2` retries on synchronous paths with short jittered backoff and remaining-deadline check.

```yaml
# Example Outbound Dependency Resilience Policy (declared per downstream in Gate 2)
downstream: payments-api
timeouts:
  connect_ms: 500
  read_ms: 2000
  total_budget_ms: 3000
circuit_breaker:
  sliding_window_calls: 20
  failure_rate_threshold_pct: 50
  slow_call_duration_ms: 1500
  open_state_duration_sec: 30
  half_open_probe_calls: 3
  ignore_http_statuses: [400, 404, 409, 422]
bulkhead:
  max_concurrent_calls: 25
  max_wait_ms: 100
retry:
  max_attempts: 2
  only_when_header_present: Idempotency-Key
  backoff_base_ms: 100
  jitter: full
```

### 2.5. Distributed Tracing & Correlation Propagation

Every request and asynchronous message must remain traceable from edge ingress to deepest worker.

```text
Edge Ingress -> Extract/Generate W3C `traceparent` + `tracestate` + `x-correlation-id`
             -> Bind to Request Context + Structured JSON Logger (`trace_id`, `span_id`, `correlation_id`, `tenant_id`, `service`)
             -> Inject into Outbound HTTP Headers / gRPC Metadata / Async Message Headers
             -> Never log secrets, Authorization tokens, or raw PII
```

- **W3C Trace Context Standard:** Propagate `traceparent: 00-<32-hex-trace-id>-<16-hex-parent-id>-<2-hex-flags>` and `tracestate` via OpenTelemetry instrumentation across HTTP, gRPC, and broker headers.
- **Business Correlation ID:** Preserve `x-correlation-id` across async chains (including Outbox rows, Saga instances, and DLQ headers) so operators can correlate a single user action across synchronous and asynchronous spans.
- **Structured Observability Baseline:** Emit RED metrics (*Rate, Errors, Duration*) per outbound dependency, circuit-breaker state transitions, bulkhead rejections, and structured JSON logs containing `trace_id`, `correlation_id`, `service`, `tenant_id`, and `error_code`.

## 3. SDD Gate 2 & Gate 4 Contract Alignment

- **Gate 2 (`02-tech-spec.md`):** Before implementation (`@architect`), document:
  1. Context Map & Bounded Context ownership table aligned with `docs/knowledge/SYSTEM_TOPOLOGY.md`.
  2. Sync vs. Async integration decision table with explicit timeouts, retry caps, circuit-breaker thresholds, and bulkhead concurrency limits per downstream dependency.
  3. Confirmation of zero shared DB tables and explicit DB role/schema isolation in `docs/knowledge/DATA_MODELS.md`.
  4. Zero-trust service-to-service AuthN/AuthZ (mTLS / scoped JWT / SPIFFE) and `tenant_id` propagation aligned with `.agents/rules/05-security-and-secrets.md` and `sdd-security-audit`.
- **Gate 4 (`@back-engineer` & `@qa-tester`):**
  - Run `.agents/scripts/verify_architecture_boundaries.py` to enforce zero forbidden cross-context imports.
  - Ship automated fault-injection tests verifying: (a) outbound client enforces explicit timeout instead of hanging, (b) circuit breaker opens after threshold and fails fast, (c) bulkhead rejects excess concurrent calls to one dependency without degrading unrelated endpoints, and (d) `traceparent` + `x-correlation-id` survive HTTP/gRPC and async broker hops.

## 4. Anti-Patterns & Fail-Closed Guards

| Anti-Pattern | Failure Mode | Fail-Closed Guard |
| :--- | :--- | :--- |
| Shared database tables across microservices | Undocumented schema coupling; one migration breaks multiple services. | Enforce DB/schema per service with separate least-privilege DB roles and `.agents/scripts/verify_architecture_boundaries.py`. |
| Unbounded HTTP/gRPC clients (no timeout) | Slow downstream exhausts caller threads/sockets and triggers cascading outage. | Reject client wrappers without explicit `connect`, `read`, and `total` timeouts in unit tests and code review. |
| Retrying non-idempotent `POST` without `Idempotency-Key` | Network timeout causes duplicate orders or double billing. | Forbid automatic retries on mutating requests unless an `Idempotency-Key` contract is enforced end-to-end. |
| Deep synchronous chains (`A -> B -> C -> D`) | Multiplicative availability drop (`0.99^4 = 96.0%`) and tail-latency amplification. | Cap sync depth at `<= 2` hops; materialize read projections from domain events for cross-context reads. |
| Silent fallback returning empty list `[]` on downstream `500` | Hides outages and corrupts user/business decisions (violates `sdd-silent-failure-audit`). | Fail closed (`503` / explicit error) on critical paths; allow degraded fallback ONLY when explicitly specified in Gate 2 with metric + warning header. |
| Dropping `traceparent` at async queue boundary | Distributed traces fracture into disconnected islands during incidents. | Serialize `traceparent`, `tracestate`, and `x-correlation-id` into outbox/message headers and restore span links on consume. |

## 5. Deterministic Verification Commands

Use these deterministic commands during Gate 4 DoD verification (adapt target paths to `specs/STACK.md`):

```bash
# 1. Enforce architecture & bounded-context import boundaries (fail-closed)
uv run python .agents/scripts/verify_architecture_boundaries.py

# 2. Verify zero cross-schema DB privileges on service roles (PostgreSQL)
psql "${DATABASE_URL}" -c \
  "SELECT grantee, table_schema, privilege_type FROM information_schema.role_table_grants WHERE grantee = '${SERVICE_DB_ROLE}' AND table_schema <> '${OWNED_SCHEMA}';"

# 3. Verify W3C traceparent & correlation-id echo/propagation on health/contract endpoint
curl -fsS -D - -o /dev/null \
  -H "traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01" \
  -H "x-correlation-id: verify-corr-001" \
  "${SERVICE_BASE_URL}/health"

# 4. Run targeted resilience & boundary test suite (timeouts, circuit breaker, bulkhead)
uv run pytest tests/ -k "boundary or resilience or circuit_breaker or traceparent" -q
```
