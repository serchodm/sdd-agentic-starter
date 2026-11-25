---
name: multi-tenant-isolation
description: End-to-end multi-tenant data isolation patterns covering immutable tenant_id propagation across HTTP, SQL/ORM, async workers, Redis, and S3, fail-closed PostgreSQL Row-Level Security (ENABLE + FORCE RLS), transaction-scoped SET LOCAL on pooled connections, and mandatory cross-tenant anti-BOLA/IDOR negative test suites. Use when designing or implementing shared-database multi-tenant systems under SDD Gate 2 and Gate 4.
---

# Multi-Tenant Data Isolation

Defense-in-depth playbook for strict tenant isolation across relational databases, connection pools, caches, object storage, and asynchronous background workers. Complements `postgres-patterns`, `database-migrations`, `prisma-patterns`, `redis-patterns`, and `sdd-security-audit`, and pairs with the `database-reviewer` specialist during Gate 4 reviews.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) involves:

- Designing or modifying shared-database, shared-schema multi-tenant tables, indexes, or foreign keys.
- Extracting, validating, and propagating `tenant_id` from JWT claims or signed gateway headers into application services, ORMs, queues, caches, or object storage.
- Authoring PostgreSQL Row-Level Security (`ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY`) policies and application database roles.
- Configuring pooled database connections (PgBouncer, RDS Proxy, Supavisor, SQLAlchemy, Prisma, `node-postgres`) for multi-tenant workloads.
- Writing or auditing anti-BOLA / anti-IDOR negative integration tests verifying that Tenant A can never read, update, or delete Tenant B's records.

## 2. Production Architecture & Patterns

### 2.1. End-to-End Immutable `tenant_id` Propagation

Treat `tenant_id` as an immutable security principal attribute bound at the ingress trust boundary and carried explicitly across every synchronous and asynchronous hop:

1. **Ingress Trust Boundary (JWT / Signed Gateway Header):** Extract `tenant_id` exclusively from a cryptographically verified JWT claim (`tid` / `org_id` validated against JWKS issuer and audience) or an mTLS/HMAC-authenticated API gateway header. Never trust `tenant_id` from client query parameters, URL paths, JSON request bodies, or unsigned `X-Tenant-ID` headers.
2. **Immutable Request Context:** Bind a frozen `TenantContext` (`@dataclass(frozen=True)` in Python `contextvars.ContextVar` or `Object.freeze` in Node.js `AsyncLocalStorage`) immediately after authentication. Reject requests missing a valid `tenant_id` with HTTP `401`/`403` before reaching domain handlers.
3. **SQL & ORM Persistence:** Inject `tenant_id` into both transaction-scoped database session settings (`SET LOCAL` / `set_config(..., true)`) and explicit `WHERE tenant_id = ...` predicates for query-planner index pruning.
4. **Async Messages & Background Jobs:** Persist `tenant_id` as a required non-null column in Transactional Outbox rows and message envelopes (CloudEvents `tenantid`). Background consumers must validate and re-hydrate `TenantContext` per message before opening any database transaction.
5. **Redis Cache & S3 Object Prefixes:** Enforce deterministic namespace prefixes (`tenant:{tenant_id}:<domain>:<key>` in Redis; `tenants/{tenant_id}/<category>/<object_id>` in S3/GCS) through centralized builders that reject empty or traversal-tainted identifiers.

```python
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True, slots=True)
class TenantContext:
    tenant_id: UUID
    actor_id: UUID

_current_tenant: ContextVar[TenantContext | None] = ContextVar("current_tenant", default=None)

def require_tenant_context() -> TenantContext:
    """Fail-closed accessor: raises immediately if called outside an authenticated tenant scope."""
    ctx = _current_tenant.get()
    if ctx is None:
        raise PermissionError("Missing authenticated TenantContext (fail-closed).")
    return ctx
```

### 2.2. PostgreSQL Row-Level Security (`ENABLE` + `FORCE` — Fail-Closed)

Application-layer `WHERE` clauses alone fail open the moment a developer forgets one filter or adds a new join. PostgreSQL RLS enforces isolation at the storage engine layer:

- **Dedicated Non-Bypass Role:** Connect from application services as a least-privilege role (`NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS`). PostgreSQL superusers and roles with `BYPASSRLS` silently skip every RLS policy.
- **`ENABLE` + `FORCE ROW LEVEL SECURITY`:** Always declare both statements so even the table owner cannot bypass policies outside explicit migration scripts.
- **Fail-Closed `current_setting(..., true)` Expression:** `current_setting('app.current_tenant', true)` returns `NULL` when never set in the session and `''` (empty string) after `RESET` or `set_config(..., '', true)`. Wrapping it in `(SELECT NULLIF(current_setting('app.current_tenant', true), '')::uuid)` achieves two critical guarantees:
  1. **Fail-Closed Default:** When unset or empty, `NULLIF` returns `NULL`, `tenant_id = NULL` evaluates to `UNKNOWN` (`false`), and PostgreSQL returns `0` rows on `SELECT`/`UPDATE`/`DELETE` while rejecting `INSERT` with `42501` (`new row violates row-level security policy`).
  2. **Single-Evaluation `initPlan`:** Wrapping the expression in a scalar `(SELECT ...)` subquery lets PostgreSQL cache the cast once per query instead of re-evaluating per scanned row.
- **Composite Keys & Foreign Keys:** Include `tenant_id` as the leading column of B-tree indexes `(tenant_id, ...)` and enforce composite `UNIQUE (tenant_id, id)` + composite `FOREIGN KEY (tenant_id, parent_id)` constraints so child rows can never reference a parent belonging to another tenant.

```sql
-- 1. Least-privilege runtime role (never superuser, never BYPASSRLS)
CREATE ROLE app_user LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;

-- 2. Tenant-scoped parent and child tables with composite relational integrity
CREATE TABLE projects (
  id          UUID NOT NULL,
  tenant_id   UUID NOT NULL,
  name        TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (id),
  UNIQUE (tenant_id, id)
);

CREATE TABLE invoices (
  id          UUID NOT NULL PRIMARY KEY,
  tenant_id   UUID NOT NULL,
  project_id  UUID NOT NULL,
  amount_cents BIGINT NOT NULL CHECK (amount_cents >= 0),
  status      TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT fk_invoices_project_same_tenant
    FOREIGN KEY (tenant_id, project_id) REFERENCES projects (tenant_id, id) ON DELETE RESTRICT
);

CREATE INDEX idx_invoices_tenant_status_created
  ON invoices (tenant_id, status, created_at DESC);

-- 3. Mandatory ENABLE + FORCE RLS with fail-closed USING and WITH CHECK clauses
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects FORCE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_projects ON projects
  AS RESTRICTIVE
  FOR ALL
  TO app_user
  USING (tenant_id = (SELECT NULLIF(current_setting('app.current_tenant', true), '')::uuid))
  WITH CHECK (tenant_id = (SELECT NULLIF(current_setting('app.current_tenant', true), '')::uuid));

CREATE POLICY tenant_isolation_invoices ON invoices
  AS RESTRICTIVE
  FOR ALL
  TO app_user
  USING (tenant_id = (SELECT NULLIF(current_setting('app.current_tenant', true), '')::uuid))
  WITH CHECK (tenant_id = (SELECT NULLIF(current_setting('app.current_tenant', true), '')::uuid));
```

### 2.3. Safe `SET LOCAL` Inside Transactions for Pooled Connections

Connection poolers (PgBouncer `pool_mode = transaction`, AWS RDS Proxy, Supabase Supavisor, SQLAlchemy `AsyncEngine`, Prisma, `pg.Pool`) multiplex physical PostgreSQL backends across concurrent tenants:

- **Never Use Session-Level `SET`:** Executing `SET app.current_tenant = '...'` or `set_config('app.current_tenant', $1, false)` mutates connection-wide state. When the connection returns to the pool, the next caller inherits the previous tenant's context if setup fails or runs a non-tenant query.
- **Always Bind Inside an Explicit Transaction (`is_local = true`):** Parameterized `SELECT set_config('app.current_tenant', $1, true)` (equivalent to `SET LOCAL`) automatically resets on `COMMIT` or `ROLLBACK`. Never run `SET LOCAL` in autocommit mode outside `BEGIN ... COMMIT` — PostgreSQL immediately discards the setting after that statement.

**SQLAlchemy 2.0 (`AsyncSession` + PgBouncer Transaction Pool):**

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

@asynccontextmanager
async def tenant_db_transaction(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    ctx = require_tenant_context()
    async with session_factory() as session:
        async with session.begin():
            await session.execute(
                text("SELECT set_config('app.current_tenant', :tid, true)"),
                {"tid": str(ctx.tenant_id)},
            )
            yield session
```

**TypeScript (`Prisma` `$extends` & `node-postgres` `pg.Pool`):**

```typescript
import { Pool, PoolClient } from "pg";

export async function withTenantTransaction<T>(
  pool: Pool,
  tenantId: string,
  work: (client: PoolClient) => Promise<T>,
): Promise<T> {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(tenantId)) {
    throw new Error("Invalid tenantId format (fail-closed).");
  }
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    await client.query("SELECT set_config('app.current_tenant', $1, true)", [tenantId]);
    const result = await work(client);
    await client.query("COMMIT");
    return result;
  } catch (err) {
    await client.query("ROLLBACK");
    throw err;
  } finally {
    client.release();
  }
}
```

For Prisma (`prisma-patterns`), wrap every tenant operation in `prisma.$transaction(async (tx) => { await tx.$executeRaw\`SELECT set_config('app.current_tenant', ${tenantId}, true)\`; return fn(tx); })` so both queries share one pooled transaction.

### 2.4. Cache, Object Storage & Background Worker Namespace Guards

Database RLS does not protect Redis keys, S3 buckets, or in-memory caches. Centralize key construction behind fail-closed helpers:

```python
import re
from uuid import UUID

_SAFE_SEGMENT_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}$")

def build_tenant_redis_key(namespace: str, entity_id: str, tenant_id: UUID | None = None) -> str:
    tid = tenant_id or require_tenant_context().tenant_id
    if not _SAFE_SEGMENT_RE.match(namespace) or not _SAFE_SEGMENT_RE.match(entity_id):
        raise ValueError("Unsafe Redis key segment rejected (fail-closed).")
    return f"tenant:{tid}:{namespace}:{entity_id}"

def build_tenant_s3_key(category: str, filename: str, tenant_id: UUID | None = None) -> str:
    tid = tenant_id or require_tenant_context().tenant_id
    if ".." in filename or "/" in filename or "\\" in filename or not _SAFE_SEGMENT_RE.match(category):
        raise ValueError("Path traversal or invalid S3 segment rejected (fail-closed).")
    return f"tenants/{tid}/{category}/{filename}"
```

When generating S3 presigned URLs (`PutObject` / `GetObject`), derive the object key server-side from `require_tenant_context().tenant_id` and verify ownership in PostgreSQL under RLS before signing.

### 2.5. Mandatory Cross-Tenant Negative Test Suite (Anti-BOLA / IDOR)

Every multi-tenant feature MUST include integration tests against a real PostgreSQL instance (`Testcontainers` or CI service container — never mocked repositories, per `sdd-test-quality-audit`) proving all 6 negative invariants:

1. **Cross-Tenant Read (`SELECT` / `GET`):** Authenticated as Tenant A, fetching `invoice_b_id` owned by Tenant B returns `0` rows / HTTP `404` (preventing ID existence enumeration).
2. **Cross-Tenant Update (`UPDATE` / `PATCH`):** Authenticated as Tenant A, updating `invoice_b_id` affects `0` rows and leaves Tenant B's persisted state unchanged.
3. **Cross-Tenant Delete (`DELETE`):** Authenticated as Tenant A, deleting `invoice_b_id` affects `0` rows and Tenant B can still read its record.
4. **Cross-Tenant Write / FK Forgery (`INSERT` / `POST`):** Authenticated as Tenant A, inserting a row with `tenant_id = tenant_b` or referencing `project_b_id` fails closed (`42501` RLS violation or composite FK failure).
5. **Unset Context Fail-Closed Check:** Querying `invoices` as `app_user` without `set_config('app.current_tenant', ..., true)` returns `0` rows and rejects `INSERT`.
6. **Connection Pool Reuse Check:** Executing a Tenant A transaction followed by an unauthenticated or Tenant B transaction on a `max_size=1` pool exhibits zero residual `app.current_tenant` state.

## 3. SDD Gate 2 & Gate 4 Contract Alignment

- **Gate 2 (`02-tech-spec.md` — `@architect`):**
  - Specify the exact `tenant_id` source of truth (JWT claim vs. signed gateway header) and STRIDE mitigations for *Spoofing*, *Information Disclosure*, and *Elevation of Privilege* (`sdd-security-audit`).
  - Document every tenant-scoped table, composite `(tenant_id, ...)` index/FK, RLS policy, and legitimate cross-tenant administrative workflow (explicitly audited role + immutable audit log) in `docs/knowledge/DATA_MODELS.md` and `docs/knowledge/API_CATALOG.md`.
- **Gate 4 (`@back-engineer`, `@qa-tester`, `@security-reviewer`, `database-reviewer`):**
  - Enforce `.agents/rules/05-security-and-secrets.md` and `.agents/rules/07-engineering-baseline.md`: zero string interpolation in `SET LOCAL` (always parameterized `set_config($1, $2, true)`), immutable `TenantContext`, and zero swallowed RLS/authz errors (`sdd-silent-failure-audit`).
  - Require green execution of the 6-point cross-tenant negative test matrix before `santa-method` Gate 4 sign-off.

## 4. Anti-Patterns & Fail-Closed Guards

| Anti-Pattern | Failure Mode | Fail-Closed Guard |
| :--- | :--- | :--- |
| Reading `tenant_id` from request body, query param, or unsigned `X-Tenant-ID` | Trivial BOLA/IDOR cross-tenant account takeover. | Extract `tenant_id` solely from verified JWT claims or mTLS/HMAC-signed gateway headers. |
| Enabling RLS without `FORCE ROW LEVEL SECURITY` or running app as table owner / `BYPASSRLS` | Queries silently bypass all RLS policies in production, exposing all tenants. | Connect as `NOSUPERUSER NOBYPASSRLS` role and enforce both `ENABLE` and `FORCE ROW LEVEL SECURITY`. |
| Session-level `SET app.current_tenant = ...` or `set_config(..., false)` on pooled connections | Pooled connection retains Tenant A context and leaks data to subsequent requests. | Use `SELECT set_config('app.current_tenant', $1, true)` strictly inside `BEGIN ... COMMIT`. |
| Missing `NULLIF(..., '')` in RLS policy expression | Empty string `''` causes runtime cast errors or unexpected behavior on `text` tenant IDs. | Always write `(SELECT NULLIF(current_setting('app.current_tenant', true), '')::uuid)`. |
| Unprefixed Redis keys (`user:42`) or client-controlled S3 object keys | Cache poisoning across tenants or presigned URL cross-tenant file read/overwrite. | Build keys exclusively via `build_tenant_redis_key()` and `build_tenant_s3_key()` using `TenantContext`. |
| Mocking ORM repositories in multi-tenant authorization tests | Tests pass while SQL migrations lack RLS or composite FKs (`sdd-test-quality-audit`). | Run cross-tenant negative tests against real PostgreSQL under the `app_user` role. |

## 5. Deterministic Verification Commands

Run these deterministic checks during Gate 4 DoD verification (adapt schema/test paths to `specs/STACK.md`):

```bash
# 1. Fail if any tenant-bearing table in public schema lacks ENABLE + FORCE ROW LEVEL SECURITY
psql "${DATABASE_URL}" -Atc "
SELECT c.relname
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'tenant_id' AND NOT a.attisdropped
WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
  AND (NOT c.relrowsecurity OR NOT c.relforcerowsecurity);
"

# 2. Verify runtime application role has neither rolsuper nor rolbypassrls privileges
psql "${DATABASE_URL}" -Atc "
SELECT rolname, rolsuper, rolbypassrls
FROM pg_roles
WHERE rolname = 'app_user' AND (rolsuper OR rolbypassrls);
"

# 3. Hunt unsafe session-scoped SET app.current_tenant or set_config(..., false) in source code
git grep -nE "SET[[:space:]]+app\.current_tenant|set_config\([^)]*'app\.current_tenant'[^)]*false\)" -- src/ || true

# 4. Execute cross-tenant negative anti-BOLA/IDOR integration test suite
uv run pytest -k "multi_tenant or cross_tenant" -q
```
