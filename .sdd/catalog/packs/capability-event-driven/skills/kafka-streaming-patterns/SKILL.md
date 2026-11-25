---
name: kafka-streaming-patterns
description: Production Apache Kafka streaming architecture including topic and partition key design, idempotent and transactional producers, consumer groups, lag control, poison-pill Dead Letter Queues (DLQ), Schema Registry governance, and Debezium CDC pipelines. Use when designing, implementing, or reviewing Kafka topologies, producers, consumers, or CDC connectors under SDD Gate 2 and Gate 4.
---

# Kafka Streaming Patterns

Production-grade Apache Kafka engineering playbook for deterministic event ordering, exactly-once/effectively-once delivery, schema evolution, and fail-closed consumer reliability.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) involves any of the following:

- Designing new Kafka topics, partition counts, retention policies, or compaction strategies.
- Implementing or reviewing Kafka producers, consumer groups, or stream processors (`Kafka Streams`, `Flink`, Python `confluent-kafka` / `aiokafka`, Java/Spring Kafka, Go `franz-go`, Node `kafkajs`).
- Enforcing ordering guarantees per aggregate, tenant, or entity key.
- Handling malformed records (*poison pills*), retry topics, and Dead Letter Queue (DLQ) routing.
- Registering or evolving Avro, Protobuf, or JSON Schema contracts in a Schema Registry.
- Building Change Data Capture (CDC) pipelines with Debezium (PostgreSQL, MySQL, MongoDB) or Outbox Event Router SMTs.
- Investigating consumer lag spikes, rebalance storms, duplicate processing, or WAL/disk growth on CDC sources.

## 2. Production Architecture & Patterns

### 2.1. Topic Naming, Partitioning & Ordering Keys

- **Deterministic Naming:** `<domain>.<bounded-context>.<entity>.<event-type>.v<major>` (e.g., `commerce.orders.order.placed.v1`). Separate command topics (`*.cmd.*`), fact/domain event topics (`*.evt.*`), compacted state topics (`*.state.*`), and DLQ topics (`*.dlq`).
- **Ordering Key Selection:** Kafka guarantees strict order **only within a single partition**. Always key messages by the entity or aggregate identifier (`order_id`, or `tenant_id:account_id` in multi-tenant systems) — never by random UUIDs or timestamps when ordering matters.
- **Hot-Partition Prevention:** Validate key cardinality before production. If a single tenant or celebrity key accounts for `> 15%` of total traffic, either isolate high-volume tenants onto dedicated topics or shard by a composite sub-key (`tenant_id:entity_id`) that preserves aggregate-level ordering without funneling an entire tenant into one partition.
- **Partition Sizing & Durability Baseline:**
  - Start with `partitions = max(target_throughput / single_partition_throughput, max_expected_consumer_instances)` and round up to a power-of-two/friendly multiple (`6`, `12`, `24`). Remember that increasing partitions later breaks key-to-partition affinity for compacted topics.
  - Production durability baseline: `replication.factor=3`, `min.insync.replicas=2`, `unclean.leader.election.enable=false`.
  - Choose `cleanup.policy=delete` with explicit `retention.ms`/`retention.bytes` for immutable event logs, and `cleanup.policy=compact` (or `compact,delete`) for latest-state snapshots with tombstones (`value=null`) for GDPR/deletion semantics.

### 2.2. Idempotent & Transactional Producers

Never accept default producer settings that allow silent data loss or broker-side reordering on retry.

```properties
# Mandatory Producer Baseline (at-least-once without duplicates per session)
acks=all
enable.idempotence=true
max.in.flight.requests.per.connection=5
retries=2147483647
delivery.timeout.ms=120000
request.timeout.ms=30000
linger.ms=10
batch.size=65536
compression.type=zstd
```

- **Why `acks=all` + `enable.idempotence=true`:** Together with `min.insync.replicas=2`, Kafka rejects writes if fewer than two in-sync replicas persist the batch and assigns monotonic Producer ID + Sequence Numbers (`PID`/`Seq`) to deduplicate broker retries without losing partition order.
- **Exactly-Once Consume-Transform-Produce (EOS):** When a service reads from Topic A and writes derived events to Topic B (no external DB side effect), configure a stable `transactional.id` per partition-owner instance, wrap `send()` + `sendOffsetsToTransaction()` inside `beginTransaction()` / `commitTransaction()`, and set downstream consumers to `isolation.level=read_committed`.
- **External DB + Kafka:** Do NOT attempt distributed 2PC between PostgreSQL and Kafka. Use the **Transactional Outbox** pattern (via Debezium CDC or outbox relay) paired with idempotent consumers.

### 2.3. Consumer Groups, Rebalancing & Offset Management

```properties
# Mandatory Consumer Baseline (fail-closed manual offset control)
enable.auto.commit=false
auto.offset.reset=earliest
isolation.level=read_committed
partition.assignment.strategy=org.apache.kafka.clients.consumer.CooperativeStickyAssignor
max.poll.records=100
max.poll.interval.ms=300000
session.timeout.ms=45000
heartbeat.interval.ms=15000
```

- **Commit Strictly After Processing:** Commit offsets (`commitSync` per batch or tracked per partition) **only after** business persistence or DLQ publication succeeds. Auto-committing on a timer causes silent message loss on crash.
- **Prevent Rebalance Storms:** Use `CooperativeStickyAssignor` (incremental rebalancing) and static group membership (`group.instance.id`) for stateful consumers or Kubernetes `StatefulSet` deployments so brief rolling restarts do not trigger stop-the-world rebalances.
- **Poll Loop Hygiene:** Bound `max.poll.records` so worst-case batch processing time stays comfortably below `50%` of `max.poll.interval.ms`. Offload heavy work only when partition ordering and offset tracking remain strictly serialized per partition.

### 2.4. Consumer Lag Control & Backpressure

- **Track Lag Continuously:** Monitor `records-lag-max`, per-partition consumer lag (offset delta AND time-based lag via event timestamp), and commit rate per `group.id`.
- **Scaling Ceiling:** Consumer instances in a group cannot exceed the topic's partition count; extra instances sit idle. Autoscaling rules (e.g., KEDA Kafka scaler) must cap `maxReplicaCount <= partition_count`.
- **Backpressure:** If a downstream dependency degrades, call `pause(partitions)` while continuing to call `poll()` at short intervals (so heartbeats and `max.poll.interval.ms` do not expire), then `resume(partitions)` once downstream health recovers.

### 2.5. Poison Pills, Retry Tiers & Dead Letter Queue (DLQ)

A single undeserializable payload or permanent domain-validation failure must never wedge a partition forever nor be silently discarded.

| Error Classification | Examples | Required Action |
| :--- | :--- | :--- |
| **Non-Retryable / Poison Pill** | Deserialization error, schema mismatch, invalid business invariant (`4xx`), missing `tenant_id` | Route immediately to `<topic>.dlq` with full diagnostic headers; commit offset only after DLQ `acks=all` succeeds. |
| **Transient Infrastructure** | Downstream DB timeout, `503 Service Unavailable`, network blip | Bounded retry with exponential backoff + jitter (in-memory short retry or dedicated retry topic `*.retry.1m` / `*.retry.5m`), then promote to `<topic>.dlq` once `max_retries` is exhausted. |
| **Fatal Local Process** | Out of disk, invalid credentials, corrupted local state | Do NOT commit offset and do NOT send to DLQ; crash fast / alert operator so another healthy instance takes over. |

**Mandatory DLQ Envelope Headers:**
- `x-dlq-origin-topic`, `x-dlq-origin-partition`, `x-dlq-origin-offset`
- `x-dlq-consumer-group`, `x-dlq-error-class`, `x-dlq-error-message` (sanitized: zero PII/secrets)
- `x-dlq-retry-count`, `x-dlq-failed-at` (ISO-8601 UTC), `traceparent`

### 2.6. Schema Registry & Compatibility Governance

- **No Schemaless Critical Streams:** Serialize production payloads with Avro, Protobuf, or strict JSON Schema registered in Schema Registry.
- **Compatibility Mode:** Enforce `BACKWARD` (default minimum: new consumers read old events) or `FULL` (consumers and producers can roll in either order) per subject. Forbid `NONE` in staging and production.
- **Safe Evolution Rules:** Only add optional fields with explicit defaults; never rename fields in-place, change wire types, or reuse Protobuf field tags. Breaking changes require a new topic major version (`*.v2`) with dual-publish/migration window.
- **Subject Naming:** Use `TopicNameStrategy` for single-event-type topics and `TopicRecordNameStrategy` when an aggregate topic carries multiple ordered event schemas under one partition key.

### 2.7. Change Data Capture (CDC) with Debezium

- **Log-Based Capture Only:** Use PostgreSQL `pgoutput` logical replication slots or MySQL binlog (`ROW` format) instead of polling `updated_at` columns (which misses deletes and creates read-load spikes).
- **Prefer Outbox Event Router SMT:** Avoid exposing raw internal DB table schemas as public Kafka contracts. Write domain events to an `outbox_events` table and configure Debezium's `EventRouter` SMT to emit clean, versioned domain events without coupling consumers to internal table columns.
- **Operational Guards for CDC:**
  - Enable `heartbeat.interval.ms` + `heartbeat.action.query` on low-traffic PostgreSQL databases so the replication slot LSN advances and does not fill disk with retained WAL segments.
  - Monitor `pg_replication_slots` lag (`pg_wal_lsn_diff`) with high-severity alerts.
  - Configure `snapshot.mode=initial` (or `when_needed` with `incremental` signaling table) and dedicate a compacted topic for Debezium schema history (`schema.history.internal.kafka.topic`).

```json
{
  "name": "orders-outbox-cdc",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "plugin.name": "pgoutput",
    "slot.name": "orders_outbox_slot",
    "publication.autocreate.mode": "filtered",
    "table.include.list": "orders_ctx.outbox_events",
    "tombstones.on.delete": "false",
    "heartbeat.interval.ms": "30000",
    "transforms": "outbox",
    "transforms.outbox.type": "io.debezium.transforms.outbox.EventRouter",
    "transforms.outbox.table.field.event.id": "event_id",
    "transforms.outbox.table.field.event.key": "aggregate_id",
    "transforms.outbox.table.field.event.payload": "payload",
    "transforms.outbox.route.by.field": "event_type",
    "transforms.outbox.route.topic.replacement": "commerce.orders.${routedByValue}.v1"
  }
}
```

## 3. SDD Gate 2 & Gate 4 Contract Alignment

- **Gate 2 (`02-tech-spec.md`):** Before coding (`@architect`), document for every topic:
  1. Topic name, partition count, replication factor, `min.insync.replicas`, retention/compaction policy, and ordering key.
  2. Schema format (Avro/Protobuf/JSON Schema), compatibility mode (`BACKWARD`/`FULL`), and Schema Registry subject name.
  3. Consumer groups, idempotency strategy, retry budget, and DLQ topic + replay runbook.
  4. Security controls aligned with `.agents/rules/05-security-and-secrets.md` and `sdd-security-audit`: TLS in transit, SASL/mTLS AuthN, per-principal Topic/Group ACLs (least privilege), and PII redaction/encryption.
- **Gate 4 (`@back-engineer` & `@qa-tester`):**
  - Implement producers and consumers strictly matching the Gate 2 topic/schema table; register event contracts in `docs/knowledge/API_CATALOG.md` and state tables (outbox/inbox) in `docs/knowledge/DATA_MODELS.md` during Gate 5 (`@documentator`).
  - Include integration tests (Testcontainers / Redpanda / Kafka test harness) proving: (a) ordering preservation per key, (b) duplicate delivery idempotency, (c) poison-pill routing to DLQ with mandatory headers, and (d) schema compatibility checks.

## 4. Anti-Patterns & Fail-Closed Guards

| Anti-Pattern | Failure Mode | Fail-Closed Guard |
| :--- | :--- | :--- |
| `enable.auto.commit=true` | Offsets advance before DB commit; crashes silently drop events. | Set `enable.auto.commit=false`; commit offsets only after persistence or DLQ write succeeds. |
| Catch-and-log inside consumer loop (`except Exception: log(); commit()`) | Poison pills vanish silently (violates `sdd-silent-failure-audit`). | Publish failed record to `<topic>.dlq` with `acks=all` before committing offset; if DLQ write fails, abort without committing. |
| `acks=1` or `acks=0` on business events | Leader crash loses acknowledged financial/domain records. | Enforce `acks=all`, `enable.idempotence=true`, `min.insync.replicas=2` in config validation at startup. |
| Raw internal DB rows published directly via CDC | Internal schema refactors break downstream microservices. | Use Debezium Outbox `EventRouter` SMT + versioned public schemas in Schema Registry. |
| Unbounded retries on the main consumer thread | One broken message blocks the entire partition indefinitely. | Cap retries with backoff/retry topic and divert to DLQ; never block `poll()` past `max.poll.interval.ms`. |
| Missing `tenant_id` in event key/headers or cross-tenant ACL wildcards | Cross-tenant data leak or noisy-neighbor starvation. | Require `tenant_id` validation on produce/consume and bind strict per-service Kafka ACLs. |

## 5. Deterministic Verification Commands

Use these deterministic commands during Gate 4 DoD verification (adapt binary/container names to `specs/STACK.md`):

```bash
# 1. Verify topic configuration (partitions, RF, min.insync.replicas, cleanup.policy)
kafka-topics --bootstrap-server "${KAFKA_BOOTSTRAP_SERVERS}" --describe --topic "${TOPIC_NAME}"
kafka-configs --bootstrap-server "${KAFKA_BOOTSTRAP_SERVERS}" --entity-type topics --entity-name "${TOPIC_NAME}" --describe

# 2. Verify consumer group lag and partition assignment balance
kafka-consumer-groups --bootstrap-server "${KAFKA_BOOTSTRAP_SERVERS}" --describe --group "${CONSUMER_GROUP}"

# 3. Validate Schema Registry compatibility before deploying a new schema version
curl -fsS -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data @"${SCHEMA_PAYLOAD_JSON}" \
  "${SCHEMA_REGISTRY_URL}/compatibility/subjects/${SUBJECT_NAME}/versions/latest"

# 4. Inspect DLQ records and headers (bounded sample, never unbounded tail in CI)
kafka-console-consumer --bootstrap-server "${KAFKA_BOOTSTRAP_SERVERS}" \
  --topic "${TOPIC_NAME}.dlq" --from-beginning --max-messages 5 --timeout-ms 5000 \
  --property print.headers=true --property print.key=true

# 5. Check PostgreSQL Debezium replication slot WAL lag (prevent disk exhaustion)
psql "${DATABASE_URL}" -c \
  "SELECT slot_name, active, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS wal_lag FROM pg_replication_slots;"
```
