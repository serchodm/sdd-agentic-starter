---
name: grpc-protobuf-patterns
description: Enterprise gRPC and Protocol Buffers governance covering proto3/Editions schema design, Buf linting and breaking-change detection, reserved tags and names, mandatory deadlines, canonical status codes, and streaming backpressure.
---

# gRPC & Protobuf Patterns

Production standard for designing, linting, evolving, and operating gRPC services and Protocol Buffers schemas (`proto3` and Protobuf Editions) with deterministic **Buf** governance and fail-closed runtime semantics.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) touches gRPC services or `.proto` contracts:

- Authoring or evolving `.proto` files, service definitions, or Protobuf message schemas in `02-tech-spec.md`.
- Configuring `buf.yaml`, `buf.gen.yaml`, code generation pipelines, or CI breaking-change checks.
- Implementing gRPC servers, clients, interceptors, error mapping, retry policies, or streaming RPCs.
- Auditing wire compatibility during Pre-Gate 2 (`santa-method` with `backward-compatibility` lens) or Gate 4 (`sdd-spec-compliance-audit`).

## 2. Production Architecture & Patterns

### 2.1. Schema Design (`proto3` & Protobuf Editions)

Design `.proto` contracts for long-term binary and JSON wire compatibility:

- **Versioned packages:** Place every service in an explicit major-versioned package (`package acme.billing.v1;`) matching its directory tree (`proto/acme/billing/v1/billing.proto`).
- **Dedicated request/response wrappers:** Every RPC takes a unique `<Method>Request` and returns a unique `<Method>Response` message so fields can be added later without breaking method signatures. Never reuse domain entity messages directly as RPC inputs or outputs.
- **Explicit presence & standard types:** In `proto3`, use `optional` for scalar fields where unset vs. zero-value matters (or declare `edition = "2023";` where explicit presence is the default). Use `google.protobuf.Timestamp`, `google.protobuf.Duration`, and `google.protobuf.FieldMask` for partial updates instead of ad-hoc strings or integers.
- **Enums with zero unspecified sentinel:** Every enum must start with `<ENUM_NAME>_UNSPECIFIED = 0` so uninitialized wire values are detected and rejected fail-closed.

```protobuf
syntax = "proto3";

package acme.billing.v1;

import "google/protobuf/field_mask.proto";
import "google/protobuf/timestamp.proto";

enum InvoiceStatus {
  INVOICE_STATUS_UNSPECIFIED = 0;
  INVOICE_STATUS_DRAFT = 1;
  INVOICE_STATUS_ISSUED = 2;
  INVOICE_STATUS_PAID = 3;
  // Tag 4 ("INVOICE_STATUS_LEGACY_VOID") was removed in v1.3.0
  reserved 4;
  reserved "INVOICE_STATUS_LEGACY_VOID";
}

message Invoice {
  string invoice_id = 1;
  string tenant_id = 2;
  InvoiceStatus status = 3;
  google.protobuf.Timestamp issued_at = 5;
  optional string external_reference = 6;

  // Never reuse deleted field numbers or JSON field names
  reserved 4, 7 to 9;
  reserved "legacy_tax_code", "deprecated_note";
}

message UpdateInvoiceRequest {
  Invoice invoice = 1;
  google.protobuf.FieldMask update_mask = 2;
}

message UpdateInvoiceResponse {
  Invoice invoice = 1;
}

service BillingService {
  rpc UpdateInvoice(UpdateInvoiceRequest) returns (UpdateInvoiceResponse);
}
```

### 2.2. Wire-Safe Evolution & `reserved` Discipline

- Whenever a field or enum value is retired, **always reserve both its numeric tag and its identifier name** (`reserved 4; reserved "legacy_tax_code";`). Tag reuse corrupts binary payloads in flight; name reuse breaks ProtoJSON serialization and generated SDKs.
- Never change a field's tag number, wire type (e.g., `int32` to `string`), or `singular` vs. `repeated` cardinality inside an existing package version.
- Never move an existing field into or out of a `oneof` block without a major package bump (`v2`).

### 2.3. Buf Linting & Breaking-Change Configuration (`buf.yaml` v2)

Enforce schema hygiene and wire compatibility automatically via `buf.yaml` (version `v2`):

```yaml
version: v2
modules:
  - path: proto
lint:
  use:
    - STANDARD
  disallow_comment_ignores: true
breaking:
  use:
    - FILE
```

- Use `FILE` breaking mode for internal/SDK-generated libraries (protects source and wire compatibility) and at minimum `WIRE_JSON` for cross-language wire + ProtoJSON consumers.
- Enable `disallow_comment_ignores: true` so developers cannot silently suppress lint rules without explicit review in `buf.yaml`.

### 2.4. Mandatory Deadlines & Context Propagation

- **Every gRPC call MUST carry a bounded deadline:** Clients attach an explicit deadline (`context.WithTimeout` / `timeout=...`) scaled to the SLA budget documented in `02-tech-spec.md`.
- **Fail-closed server deadline guard:** Install a server unary/stream interceptor that rejects calls missing a deadline (or clamps/rejects budgets exceeding the service maximum) and propagates remaining time budget to downstream RPCs and database queries.
- Always check context cancellation (`ctx.Err()` / `context.is_active()`) inside loops and long-running handlers so aborted client requests stop consuming CPU and DB connections immediately.

### 2.5. Canonical gRPC Status Codes & Retry Semantics

Map domain and boundary errors deterministically to canonical gRPC codes (`google.rpc.Code`) with structured `google.rpc.Status` details (`BadRequest`, `ErrorInfo`, `ResourceInfo`):

| Scenario | Canonical gRPC Code | Retryable? | Notes |
| :--- | :--- | :---: | :--- |
| Schema/input validation error | `INVALID_ARGUMENT` | No | Attach `google.rpc.BadRequest` field violations. |
| Missing/invalid credentials | `UNAUTHENTICATED` | No | Never leak token verification internals. |
| Valid identity lacking scope/tenant | `PERMISSION_DENIED` | No | Enforce tenant/object AuthZ fail-closed. |
| Entity does not exist | `NOT_FOUND` | No | Avoid leaking cross-tenant existence. |
| Unique constraint / idempotency conflict | `ALREADY_EXISTS` | No | Include conflict resource metadata. |
| Invalid state transition | `FAILED_PRECONDITION` | No | Attach `PreconditionFailure` details. |
| Concurrency / optimistic lock conflict | `ABORTED` | Conditional | Safe only with idempotent re-read/retry. |
| Rate limit / quota exceeded | `RESOURCE_EXHAUSTED` | Backoff | Respect `RetryInfo` delay + jitter. |
| Budget expired | `DEADLINE_EXCEEDED` | Conditional | Only if operation is strictly idempotent. |
| Transient upstream/network outage | `UNAVAILABLE` | Yes | Exponential backoff + jitter + circuit breaker. |
| Unexpected invariant failure | `INTERNAL` | No | Log internally with `traceparent`; sanitize client message. |

### 2.6. Streaming Backpressure & Flow Control

- **Respect HTTP/2 flow control:** Never spawn unbounded goroutines, tasks, or in-memory buffers per incoming stream message; apply bounded channels/queues so slow consumers exert backpressure directly onto the gRPC transport window.
- **Bound message sizes & chunk payloads:** Keep individual stream messages well below the default 4 MiB limit (typically `64 KiB–512 KiB` chunks for file/batch transfers) and configure explicit `MaxRecvMsgSize` / `MaxSendMsgSize`.
- **Keepalive & graceful draining:** Configure HTTP/2 keepalive pings conservatively (aligned between client and server to prevent `ENHANCE_YOUR_CALM` disconnects) and drain active streams before shutdown (`GracefulStop` with hard fallback timer).

## 3. SDD Gate 2 & Gate 4 Contract Alignment

| SDD Gate | Owner | Mandatory Artifact & Verification |
| :--- | :--- | :--- |
| **Gate 2** | `@architect` | Freeze `.proto` package version, RPC signatures, `buf.yaml` rules, deadline budgets, status code mapping, and streaming chunk limits in `02-tech-spec.md`. Run `sdd-security-audit` STRIDE review for mTLS/JWT metadata and tenant propagation. |
| **Pre-Gate 2** | `santa-method` | Apply dual adversarial verification (`backward-compatibility` lens) on any evolution of existing `.proto` packages. |
| **Gate 4** | `@back-engineer`, `@qa-tester` | Generate stubs deterministically (`buf generate`), verify `buf lint` + `buf breaking`, and run integration tests covering deadline expiry, canonical error codes, AuthN/AuthZ interceptors, and streaming backpressure (`sdd-spec-compliance-audit`, `sdd-silent-failure-audit`). |
| **Gate 5** | `@documentator` | Update `docs/knowledge/API_CATALOG.md` (gRPC services, packages, RPCs, SLAs) and `docs/traceability/TRACEABILITY-MATRIX.md`. |

## 4. Anti-Patterns & Fail-Closed Guards

- **Reusing Deleted Field Numbers:** Reassigning tag `4` after deleting an old field silently decodes corrupt data on rolling deployments. *Guard:* Enforce `reserved` tags and names on every deletion and gate CI with `buf breaking`.
- **Unbounded Calls Without Deadlines:** A single hung downstream RPC exhausts worker pools and cascades across services. *Guard:* Require explicit client deadlines and enforce a server-side deadline interceptor.
- **Returning `OK` with an Error Field Inside the Payload:** Embedding `bool success = 1; string error = 2;` inside `200/OK` responses blinds observability, retries, and circuit breakers. *Guard:* Always signal failures via canonical gRPC status codes and `google.rpc.Status` details.
- **Retrying Non-Idempotent Mutations on `DEADLINE_EXCEEDED` or `UNAVAILABLE`:** Causes duplicate charges or double writes. *Guard:* Require explicit idempotency keys for mutating RPCs and restrict automatic retries to idempotent methods and transient codes.
- **Unbounded Stream Fan-Out:** Reading a stream into an unbounded slice or spawning one worker per message triggers OOM kills under burst traffic. *Guard:* Cap concurrency with bounded worker pools and backpressure-aware send/recv loops.
- **Swallowing `UNSPECIFIED = 0` Enum Values:** Treating `0` as a valid default business state masks missing client fields. *Guard:* Reject `*_UNSPECIFIED` with `INVALID_ARGUMENT` at the handler boundary.

## 5. Deterministic Verification Commands

Run these deterministic checks in Gate 4 and CI (adapting paths to `specs/STACK.md`):

```bash
# 1. Verify canonical .proto formatting without mutating files
buf format --diff --exit-code

# 2. Enforce Buf STANDARD lint rules across all modules
buf lint

# 3. Fail-closed wire and source breaking-change detection against main
buf breaking --against '.git#branch=main'

# 4. Verify generated stubs match committed .proto sources (zero drift)
buf generate
git diff --exit-code gen/

# 5. Execute gRPC contract, deadline, status-code, and streaming backpressure tests
uv run pytest tests/grpc/test_billing_service_contract.py -q
```

- **Exit criteria (DoD):** `buf format --diff --exit-code`, `buf lint`, and `buf breaking` exit `0`, generated stubs have zero uncommitted drift, contract tests validate deadlines + canonical codes + backpressure, and `docs/knowledge/API_CATALOG.md` reflects all gRPC services at Gate 5.
