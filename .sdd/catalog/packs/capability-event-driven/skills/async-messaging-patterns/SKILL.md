---
name: async-messaging-patterns
description: Production asynchronous messaging reliability patterns covering Transactional Outbox, Inbox and Idempotency Keys with TTL, Choreography vs. Orchestration Sagas with explicit compensations, exponential backoff with jitter, and mandatory Dead Letter Queues across RabbitMQ, AWS SQS/SNS, NATS JetStream, and Redis Streams. Use when designing or implementing decoupled workers, queues, or distributed workflows under SDD Gate 2 and Gate 4.
---

# Asynchronous Messaging Patterns

Broker-agnostic reliability playbook for atomic event publication, deduplicated consumption, multi-step distributed workflows (Sagas), bounded retries, and fail-closed Dead Letter Queue (DLQ) handling.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) involves:

- Publishing domain events or commands reliably alongside database mutations (avoiding the dual-write bug).
- Building idempotent workers or webhooks that receive at-least-once deliveries.
- Coordinating multi-service business processes spanning multiple transactions (Sagas with compensations).
- Configuring retry policies, visibility timeouts, backoff/jitter, and Dead Letter Queues on RabbitMQ, AWS SQS/SNS, NATS JetStream, or Redis Streams.
- Auditing asynchronous workers for swallowed errors, duplicate side effects, or missing DLQ/replay paths.

## 2. Production Architecture & Patterns

### 2.1. Transactional Outbox (Eliminating Dual-Writes)

Never write to a database and then call `broker.publish()` outside an atomic boundary: if the process crashes between DB commit and broker ack, the event is lost forever; if the broker publish succeeds and the DB rolls back, downstream services act on phantom state.

```sql
CREATE TABLE outbox_events (
  event_id        UUID PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  aggregate_type  TEXT NOT NULL,
  aggregate_id    TEXT NOT NULL,
  event_type      TEXT NOT NULL,
  schema_version  INTEGER NOT NULL DEFAULT 1,
  payload         JSONB NOT NULL,
  headers         JSONB NOT NULL DEFAULT '{}'::jsonb,
  occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  published_at    TIMESTAMPTZ NULL,
  attempt_count   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_outbox_unpublished
  ON outbox_events (occurred_at ASC)
  WHERE published_at IS NULL;
```

- **Atomic Write:** Insert domain entity changes and the `outbox_events` row inside the **exact same local ACID database transaction**.
- **Relay Mechanisms:**
  1. **Log-Based CDC (Preferred at scale):** Debezium tails the WAL and routes `outbox_events` rows straight to the broker with sub-second latency and zero polling load.
  2. **Polling Publisher (Simple & portable):** Worker claims batches with `SELECT ... FROM outbox_events WHERE published_at IS NULL ORDER BY occurred_at ASC LIMIT 100 FOR UPDATE SKIP LOCKED`, publishes with broker confirms, and updates `published_at = NOW()`.
- **Retention & Pruning:** Partition `outbox_events` by day/week or run a scheduled retention job deleting rows where `published_at < NOW() - INTERVAL '7 days'` to prevent table bloat.

### 2.2. Inbox & Idempotency Key (Effectively-Once Consumption)

All production message brokers deliver **at-least-once** across retries, redeliveries, and crash recoveries. Every consumer must be mathematically idempotent.

```sql
CREATE TABLE inbox_processed_messages (
  consumer_group  TEXT NOT NULL,
  message_id      TEXT NOT NULL,
  tenant_id       TEXT NOT NULL,
  payload_hash    TEXT NOT NULL,
  processed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at      TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (consumer_group, message_id)
);

CREATE INDEX idx_inbox_expires_at ON inbox_processed_messages (expires_at);
```

- **Single-Transaction Deduplication:** Inside one local DB transaction:
  1. Attempt `INSERT INTO inbox_processed_messages (consumer_group, message_id, tenant_id, payload_hash, expires_at) VALUES (...) ON CONFLICT (consumer_group, message_id) DO NOTHING RETURNING message_id`.
  2. If `0` rows returned: message was already processed — verify `payload_hash` (alert if same `message_id` arrived with different payload), skip side effects, and `ack` the message cleanly.
  3. If `1` row returned: execute business state mutation and commit. If business logic fails, the transaction rolls back both the domain change and the inbox marker so the retry can execute cleanly.
- **TTL Discipline:** Set `expires_at` strictly longer than the maximum broker retention + DLQ replay window (typically `7–30 days`) and prune expired rows in bounded batches.
- **External Side Effects (Payments/Emails):** Propagate `message_id` (or deterministic `idempotency_key = sha256(tenant_id + operation + entity_id)`) to external APIs that support `Idempotency-Key` headers.

### 2.3. Sagas: Choreography vs. Orchestration & Explicit Compensations

Avoid distributed XA/2PC locks across microservices. Model long-running workflows as Sagas with explicit compensating actions.

| Dimension | Choreography (Event-Driven) | Orchestration (Central Coordinator) |
| :--- | :--- | :--- |
| **Best Fit** | `2–3` decoupled steps, simple fan-out notifications, low branching | `>= 3` steps, conditional branches, timeouts, human/payment approvals |
| **Visibility** | Distributed across event streams (requires tracing correlation) | Explicit persisted saga state machine (`saga_instances` table) |
| **Failure Handling** | Each service listens for failure events and self-compensates | Orchestrator drives deterministic reverse compensation order |
| **Risk** | Cyclic event dependencies and hidden implicit coupling | Putting domain business logic inside the orchestrator (keep it thin) |

**Saga Step Classification (Mandatory in Gate 2):**
1. **Compensatable Steps (before pivot):** Must define an idempotent semantic undo action (e.g., `ReserveInventory` -> `ReleaseInventory`; `AuthorizePayment` -> `VoidAuthorization`). Compensations are semantic reversals, not database rollbacks.
2. **Pivot Transaction (point of no return):** Single atomic step deciding whether the saga succeeds or must compensate (e.g., `CapturePayment`).
3. **Retryable Steps (after pivot):** Must be guaranteed to succeed eventually via bounded retries + DLQ/operator replay (e.g., `IssueReceipt`, `DispatchShipment`); they never roll back the pivot.

**Mandatory Saga State Machine:** Persist `saga_id`, `tenant_id`, `current_step`, `status` (`RUNNING`, `COMPENSATING`, `COMPLETED`, `COMPENSATED`, `FAILED_MANUAL`), `step_history`, and `deadline_at` with optimistic locking (`version`).

```sql
CREATE TABLE saga_instances (
  saga_id       UUID PRIMARY KEY,
  tenant_id     TEXT NOT NULL,
  saga_type     TEXT NOT NULL,
  current_step  TEXT NOT NULL,
  status        TEXT NOT NULL CHECK (status IN ('RUNNING','COMPENSATING','COMPLETED','COMPENSATED','FAILED_MANUAL')),
  version       INTEGER NOT NULL DEFAULT 1,
  state_payload JSONB NOT NULL,
  step_history  JSONB NOT NULL DEFAULT '[]'::jsonb,
  deadline_at   TIMESTAMPTZ NOT NULL,
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_saga_active_deadlines
  ON saga_instances (deadline_at ASC)
  WHERE status IN ('RUNNING', 'COMPENSATING');
```

### 2.4. Exponential Backoff with Full Jitter

Synchronized retries after a downstream outage create retry storms (*thundering herd*).

```python
import random

def compute_backoff_seconds(attempt: int, base_sec: float = 0.5, cap_sec: float = 60.0) -> float:
    """Full jitter exponential backoff: uniform random in [0, min(cap, base * 2^attempt)]."""
    if attempt < 0:
        raise ValueError("attempt must be non-negative")
    ceiling = min(cap_sec, base_sec * (2 ** attempt))
    return random.uniform(0.0, ceiling)
```

- **Retry Budget:** Cap total retry attempts (e.g., `max_attempts = 5`) and total retry elapsed time. Never retry permanent errors (`ValidationError`, `400`, `401`, `403`, `404`, schema parse failure).
- **Visibility Timeout Alignment:** Ensure queue lock/visibility timeout (`VisibilityTimeout` in SQS, `AckWait` in NATS, `consumer_timeout` in RabbitMQ) exceeds worst-case handler execution time plus margin, or extend leases explicitly while work is in progress.

### 2.5. Mandatory DLQ Baseline Across Brokers

Every production queue/stream MUST declare a Dead Letter destination and an explicit alerting + replay strategy:

| Broker | Required Reliability & DLQ Configuration |
| :--- | :--- |
| **RabbitMQ** | Quorum queues (`x-queue-type: quorum`), publisher confirms (`confirm.select`), manual ack (`auto_ack=False`), explicit `x-dead-letter-exchange` + `x-dead-letter-routing-key`, and `x-delivery-limit` (e.g., `5`). Reject poison pills with `basic_nack(requeue=False)`. |
| **AWS SQS / SNS** | Standard or FIFO (`ContentBasedDeduplication` / `MessageDeduplicationId` + `MessageGroupId`), `RedrivePolicy` pointing to dedicated `<queue>-dlq` with `maxReceiveCount` (`3–5`), SNS subscription `RedrivePolicy` for undeliverable fan-out, and `StartMessageMoveTask` for controlled DLQ redrive. |
| **NATS JetStream** | WorkQueue or Limits stream with `MaxDeliver` (`5`), explicit `AckExplicit`, `AckWait` sized to handler SLA, and a durable monitor consuming `$JS.EVENT.ADVISORY.CONSUMER.MAX_DELIVERIES.<STREAM>.<CONSUMER>` to persist failed payloads/metadata into `<STREAM>_DLQ`. |
| **Redis Streams** | Consumer groups (`XGROUP CREATE` + `XREADGROUP`), explicit `XACK` only after commit, periodic `XPENDING` + `XAUTOCLAIM` to recover crashed-worker messages, and explicit delivery-count check (`times_delivered > max_retries`) writing to `<stream>:dlq` via `XADD` before `XACK`. |

## 3. SDD Gate 2 & Gate 4 Contract Alignment

- **Gate 2 (`02-tech-spec.md`):** Document for every async workflow:
  1. Message envelope contract (`event_id`, `event_type`, `schema_version`, `occurred_at`, `tenant_id`, `traceparent`, `idempotency_key`).
  2. Outbox/Inbox table DDL and retention/TTL schedule (tracked in `docs/knowledge/DATA_MODELS.md`).
  3. Saga diagram identifying compensatable steps, pivot step, retryable steps, and timeout/escalation behavior.
  4. Exact broker retry counts, backoff formula, visibility timeout, DLQ name, alert threshold (`dlq_depth > 0`), and redrive procedure.
- **Gate 4 (`@back-engineer` & `@qa-tester`):**
  - Prove atomicity of Outbox writes (simulated rollback leaves `0` outbox rows), idempotency of Inbox consumers (delivering the same `message_id` twice produces identical state and single side effect), Saga compensation execution on mid-flight failure, and DLQ routing after `max_retries`.
  - Enforce `.agents/rules/05-security-and-secrets.md` and `sdd-security-audit`: authenticate broker connections (TLS + IAM/mTLS/SCRAM), sign or validate `tenant_id`, and strip secrets/PII from DLQ error metadata.

## 4. Anti-Patterns & Fail-Closed Guards

| Anti-Pattern | Failure Mode | Fail-Closed Guard |
| :--- | :--- | :--- |
| Dual-write (`db.commit()` then `broker.publish()`) | Crash between calls creates permanent split-brain state. | Use `outbox_events` written in the same DB transaction as domain state. |
| `basic_nack(requeue=True)` on poison pills | Infinite hot-loop saturates CPU, broker, and logs. | Route to DLQ (`requeue=False`) after bounded delivery limit or immediately on schema/validation error. |
| Non-idempotent consumer assuming "exactly-once" delivery | Network timeout on `ack` causes duplicate charges, emails, or stock deductions. | Guard every mutating consumer with `inbox_processed_messages` unique constraint + transactional commit. |
| Silent catch + `ack()` on unhandled exception | Message permanently lost with green metrics (violates `sdd-silent-failure-audit`). | Never `ack` on unhandled failure unless the record has been durably persisted to the DLQ first. |
| Saga without persisted state or idempotent compensations | Crash mid-compensation leaves orphaned reservations or double refunds. | Persist every transition in `saga_instances` and make every forward and compensating command idempotent by `saga_id + step`. |
| Unbounded DLQ without alerts or redrive tooling | DLQ becomes a silent graveyard of lost customer operations. | Alert on `dlq_depth > 0` and ship an idempotent, rate-limited DLQ replay command. |

## 5. Deterministic Verification Commands

Use these deterministic commands during Gate 4 DoD verification (adapt service/queue identifiers to `specs/STACK.md`):

```bash
# 1. Verify Outbox backlog and Inbox TTL/uniqueness health in PostgreSQL
psql "${DATABASE_URL}" -c \
  "SELECT COUNT(*) AS unpublished, MIN(occurred_at) AS oldest FROM outbox_events WHERE published_at IS NULL;"
psql "${DATABASE_URL}" -c \
  "SELECT COUNT(*) AS active_inbox_keys, COUNT(*) FILTER (WHERE expires_at < NOW()) AS expired_pending_prune FROM inbox_processed_messages;"

# 2. Verify RabbitMQ queue durability, DLX policy, and DLQ depth
rabbitmqctl list_queues name type durable messages arguments

# 3. Verify AWS SQS RedrivePolicy and DLQ depth
aws sqs get-queue-attributes --queue-url "${SQS_QUEUE_URL}" \
  --attribute-names RedrivePolicy VisibilityTimeout ApproximateNumberOfMessages

# 4. Verify NATS JetStream stream/consumer MaxDeliver and AckWait
nats consumer info "${NATS_STREAM}" "${NATS_CONSUMER}"

# 5. Verify Redis Streams consumer group pending count and DLQ length
redis-cli XPENDING "${REDIS_STREAM}" "${REDIS_GROUP}"
redis-cli XLEN "${REDIS_STREAM}:dlq"
```
