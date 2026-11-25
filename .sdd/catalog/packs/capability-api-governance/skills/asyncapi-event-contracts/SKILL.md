---
name: asyncapi-event-contracts
description: Contract-first AsyncAPI 3.0 event governance covering CloudEvents envelopes, Schema Registry compatibility modes (BACKWARD/FULL) for Avro/Protobuf/JSON Schema, deterministic validation, and SDD 02-tech-spec.md traceability.
---

# AsyncAPI Event Contracts

Production standard for specifying, validating, and evolving asynchronous event-driven contracts using **AsyncAPI 3.0**, **CloudEvents 1.0** envelopes, and strict Schema Registry compatibility rules aligned with SDD Gate 2, Gate 4, and Gate 5.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) publishes or consumes asynchronous events or messages:

- Defining new event channels, topics, queues, or message payloads in `02-tech-spec.md`.
- Authoring or updating `asyncapi.yaml` specifications (AsyncAPI 3.0) for Kafka, RabbitMQ, SQS/SNS, NATS, or Redis Streams.
- Establishing CloudEvents envelope standards, tenant propagation, correlation tracing, and schema evolution rules across producers and consumers.
- Configuring Schema Registry compatibility levels (`BACKWARD`, `FULL`) for Avro, Protobuf, or JSON Schema payloads.
- Auditing event contract compliance in Pre-Gate 2 (`santa-method` with `backward-compatibility` lens), Gate 4 (`sdd-spec-compliance-audit`), or Gate 5 (`docs/knowledge/API_CATALOG.md` & `docs/knowledge/DATA_MODELS.md`).

## 2. Production Architecture & Patterns

### 2.1. AsyncAPI 3.0 Contract-First Structure

AsyncAPI 3.0 decouples **channels** (broker addresses and messages) from **operations** (`action: send` for producers, `action: receive` for consumers), enabling reusable multi-service contracts:

- Declare `asyncapi: 3.0.0` with explicit `info.version` (SemVer) and `defaultContentType: application/cloudevents+json`.
- Separate `channels` (logical topic/queue address + message references) from `operations` (`send` / `receive` ownership) so every producer and consumer contract is machine-verifiable.
- Define all reusable envelopes, payloads, headers, correlation IDs, and traits under `components/` via `$ref`.
- Document partition/ordering keys (`key` binding) and delivery semantics (`at-least-once` + consumer idempotency) directly in the contract and `02-tech-spec.md`.

```yaml
asyncapi: 3.0.0
info:
  title: Orders Domain Events
  version: 1.1.0
  description: Canonical domain events emitted by the Orders bounded context.
defaultContentType: application/cloudevents+json
channels:
  orderLifecycle:
    address: orders.lifecycle.v1
    messages:
      orderConfirmed:
        $ref: "#/components/messages/OrderConfirmedEvent"
operations:
  publishOrderConfirmed:
    action: send
    channel:
      $ref: "#/channels/orderLifecycle"
    messages:
      - $ref: "#/channels/orderLifecycle/messages/orderConfirmed"
components:
  messages:
    OrderConfirmedEvent:
      name: OrderConfirmedEvent
      title: Order Confirmed
      contentType: application/cloudevents+json
      correlationId:
        location: "$message.header#/traceparent"
      payload:
        $ref: "#/components/schemas/OrderConfirmedEnvelope"
  schemas:
    OrderConfirmedEnvelope:
      type: object
      required:
        - specversion
        - id
        - event_id
        - source
        - type
        - time
        - occurred_at
        - schema_version
        - tenant_id
        - data
      additionalProperties: false
      properties:
        specversion:
          const: "1.0"
        id:
          type: string
          format: uuid
        event_id:
          type: string
          format: uuid
        source:
          type: string
          format: uri-reference
          example: "/services/orders"
        type:
          const: "com.acme.orders.confirmed.v1"
        time:
          type: string
          format: date-time
        occurred_at:
          type: string
          format: date-time
        schema_version:
          type: string
          pattern: "^[0-9]+\\.[0-9]+\\.[0-9]+$"
          example: "1.1.0"
        tenant_id:
          type: string
          minLength: 1
        traceparent:
          type: string
        data:
          $ref: "#/components/schemas/OrderConfirmedData"
    OrderConfirmedData:
      type: object
      required: [order_id, total_minor_units, currency]
      additionalProperties: false
      properties:
        order_id:
          type: string
          format: uuid
        total_minor_units:
          type: integer
          minimum: 0
        currency:
          type: string
          pattern: "^[A-Z]{3}$"
```

### 2.2. Mandatory CloudEvents Envelope Contract

Every asynchronous event must carry a standardized CloudEvents 1.0 envelope with explicit enterprise governance attributes (whether in structured JSON body or binary protocol headers `ce-*`):

- **Identity & deduplication:** `event_id` (UUIDv7/UUIDv4, mirrored in CloudEvents `id`) serves as the canonical idempotency key for consumer deduplication.
- **Temporal ordering & auditing:** `occurred_at` (RFC 3339 UTC timestamp, mirrored in CloudEvents `time`) records domain occurrence time, distinct from broker ingestion time.
- **Contract evolution:** `schema_version` (`MAJOR.MINOR.PATCH`) plus immutable event `type` (`<reverse-domain>.<context>.<event>.v<major>`) identifies the exact payload contract.
- **Tenant & trace propagation:** `tenant_id` (mandatory non-empty string in multi-tenant systems) and W3C `traceparent` guarantee isolated processing and end-to-end distributed tracing without leaking cross-tenant data.

### 2.3. Schema Compatibility Modes (`BACKWARD` vs. `FULL`)

Enforce compatibility in Schema Registry (or CI schema diffing) according to serialization format and rollout order:

| Mode | Guarantee | Rollout Order | Safe Evolution Rules |
| :--- | :--- | :--- | :--- |
| **`BACKWARD`** | New schema reads data produced with previous schema. | Upgrade consumers first, then producers. | Add optional fields with explicit defaults; delete optional fields no longer required by new readers. |
| **`BACKWARD_TRANSITIVE`** | New schema reads data from *all* historical versions (required for Kafka replay / compacted topics). | Consumers first, then producers. | Same as `BACKWARD`, preserved across every retained topic offset. |
| **`FULL`** | New schema reads old data AND old schema reads new data (`BACKWARD` + `FORWARD`). | Zero-downtime rolling upgrades in any order. | Only add/remove fields that have explicit defaults; never rename fields, change types, or tighten constraints. |
| **`FULL_TRANSITIVE`** | Full compatibility across all historical versions. | Any order + full topic replay. | Strictest production baseline for shared domain event buses. |

Format-specific rules:
- **Avro:** Every newly added field MUST define a `"default"` matching the first branch of its union (e.g., `["null", "string"]` with `"default": null`). Never rename fields without aliases or change primitive types.
- **Protobuf:** Follow tag immutability and `reserved` rules on deleted field numbers/names; never reuse tags or change wire types.
- **JSON Schema:** Treat `additionalProperties` carefully—producers must validate outgoing payloads strictly (`additionalProperties: false` in producer test fixtures), while consumers under `FULL`/`FORWARD` compatibility must tolerate unknown additive fields unless pinned to a closed-envelope contract.

### 2.4. Traceability in `02-tech-spec.md`

Every event introduced or changed in a Work Item MUST have a contract table entry in `02-tech-spec.md`:

| Event Type | AsyncAPI Channel | Producer -> Consumers | Partition Key | Compatibility Mode | Idempotency & DLQ Policy | EARS Trace |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `com.acme.orders.confirmed.v1` | `orders.lifecycle.v1` | `orders-api` -> `billing-worker`, `notifications` | `order_id` | `FULL_TRANSITIVE` | Dedup by `event_id` (7d TTL); 5 retries -> `orders.lifecycle.v1.dlq` | `RF-###`, `CA-###` |

## 3. SDD Gate 2 & Gate 4 Contract Alignment

| SDD Gate | Owner | Mandatory Artifact & Verification |
| :--- | :--- | :--- |
| **Gate 2** | `@architect` | Freeze `asyncapi.yaml` (AsyncAPI 3.0), CloudEvents envelope fields (`event_id`, `occurred_at`, `schema_version`, `tenant_id`), compatibility mode (`BACKWARD`/`FULL`), DLQ policy, and traceability table in `02-tech-spec.md`. Run `sdd-security-audit` STRIDE check for event tampering, spoofing, PII minimization, and tenant isolation. |
| **Pre-Gate 2** | `santa-method` | Execute dual adversarial review (`backward-compatibility` lens) whenever evolving existing channels, event types, or payload schemas. |
| **Gate 4** | `@back-engineer`, `@qa-tester` | Validate AsyncAPI syntax, Schema Registry compatibility, producer serialization tests, consumer deserialization tests (including old/new schema fixtures), and poison-pill DLQ handling (`sdd-spec-compliance-audit`, `sdd-silent-failure-audit`). |
| **Gate 5** | `@documentator` | Register channels, event types, schema versions, and ownership in `docs/knowledge/API_CATALOG.md`, payload entities in `docs/knowledge/DATA_MODELS.md`, and mappings in `docs/traceability/TRACEABILITY-MATRIX.md`. |

## 4. Anti-Patterns & Fail-Closed Guards

- **Unversioned Event Payloads Without Envelopes:** Publishing raw domain dicts without `event_id`, `occurred_at`, `schema_version`, or `tenant_id` breaks deduplication, auditing, and multi-tenant isolation. *Guard:* Validate every outgoing and incoming message against the CloudEvents envelope schema at the messaging boundary.
- **Silent Consumer `ack` on Schema Validation Failure:** Acknowledging malformed or incompatible messages drops production data silently. *Guard:* Reject invalid payloads fail-closed, emit structured error telemetry (`event_id`, `schema_version`, `tenant_id`), and route unrecoverable poison pills to a bounded DLQ (aligned with `sdd-silent-failure-audit`).
- **Breaking Schema Mutation on Shared Topics:** Changing a field's type or removing a required field on a live topic breaks downstream consumers and breaks historical replay. *Guard:* Enforce `BACKWARD_TRANSITIVE` or `FULL_TRANSITIVE` compatibility checks in CI; introduce breaking payload changes only under a new event `type` / channel version (`v2`).
- **Leaking Secrets or Excessive PII in Event Streams:** Event brokers retain logs for days or indefinitely in compacted topics. *Guard:* Minimize PII in payloads, tokenize/reference sensitive records where required, and enforce `.agents/rules/05-security-and-secrets.md`.
- **Missing `02-tech-spec.md` Traceability:** Emitting "shadow events" undocumented in `asyncapi.yaml` or `API_CATALOG.md` creates invisible coupling between services. *Guard:* Fail Gate 4 `sdd-spec-compliance-audit` if any topic or event type in code lacks an approved AsyncAPI 3.0 definition and `02-tech-spec.md` trace row.

## 5. Deterministic Verification Commands

Run these deterministic checks in Gate 4 and CI (adapting paths to `specs/STACK.md`):

```bash
# 1. Validate AsyncAPI 3.0 document structure, refs, channels, and operations
npx --yes @asyncapi/cli validate asyncapi/asyncapi.yaml

# 2. Check breaking changes against the baseline AsyncAPI 3.0 contract
npx --yes @asyncapi/cli diff asyncapi/baseline/asyncapi.yaml asyncapi/asyncapi.yaml --type=breaking

# 3. Verify Schema Registry compatibility mode (BACKWARD/FULL) in dry-run/CI
# (Adapt command to your Avro/Protobuf/JSON Schema registry CLI defined in specs/STACK.md)
uv run python scripts/verify_event_schemas.py --mode FULL_TRANSITIVE --baseline asyncapi/baseline/ --candidate asyncapi/

# 4. Run producer/consumer CloudEvents contract & poison-pill DLQ tests
uv run pytest tests/events/test_asyncapi_contracts.py -q
```

- **Exit criteria (DoD):** AsyncAPI 3.0 validation exits `0`, zero unapproved breaking schema changes exist under the declared compatibility mode (`BACKWARD`/`FULL`), CloudEvents envelope fields (`event_id`, `occurred_at`, `schema_version`, `tenant_id`) are enforced in producer and consumer contract tests, and `02-tech-spec.md` + Gate 5 catalogs are synchronized.
