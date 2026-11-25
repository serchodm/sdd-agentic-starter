---
name: dbt-modeling-patterns
description: Production dbt analytics modeling including the staging to intermediate to marts layered DAG, idempotent incremental models (merge, insert_overwrite, unique_key), strict source() and ref() usage, enforced model contracts, SQL and schema tests, and semantic layer alignment. Use when designing, implementing, or reviewing dbt projects, models, sources, or metrics under SDD Gate 2 and Gate 4.
---

# dbt Modeling Patterns

Production-grade dbt engineering playbook for deterministic, idempotent, contract-enforced analytics models that remain reproducible across environments and safe to rebuild at any time.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) involves any of the following:

- Creating or refactoring dbt models, sources, seeds, snapshots, macros, or packages (`dbt-core` / `dbt Fusion` / dbt Cloud).
- Designing the layered transformation DAG (`staging`, `intermediate`, `marts`) for a warehouse or lakehouse (Snowflake, BigQuery, Databricks, Redshift, PostgreSQL, DuckDB).
- Converting full-refresh tables into incremental models, or debugging duplicated / missing rows after incremental runs.
- Publishing a mart that downstream BI dashboards, reverse-ETL syncs, ML features, or APIs consume (requires an enforced model contract).
- Defining semantic models, dimensions, measures, and metrics for the dbt Semantic Layer (MetricFlow).
- Investigating failing `dbt build` runs, slow CI, schema drift, or broken lineage in `manifest.json`.

## 2. Production Architecture & Patterns

### 2.1. Layered DAG (`staging -> intermediate -> marts`)

| Layer | Naming | Materialization | Responsibility | May Reference |
| :--- | :--- | :--- | :--- | :--- |
| **Staging** | `stg_<source>__<entity>` | `view` (or `ephemeral`) | 1:1 with a raw source table. Rename, cast types, normalize timezones to UTC, light cleaning. No joins, no aggregations. | `source()` only |
| **Intermediate** | `int_<entity>__<verb>` | `ephemeral` / `view` / `table` | Reusable business logic: joins, deduplication, pivots, fan-out control, window functions. Not exposed to BI. | `ref()` to staging / intermediate |
| **Marts** | `fct_<process>` / `dim_<entity>` | `table` / `incremental` | Consumer-facing facts and dimensions at a documented grain, with enforced contracts and access control. | `ref()` to intermediate / staging / other marts |

- **Directional Flow Only:** Staging never refers to intermediate or marts; marts never call `source()` directly. Enforce this with `dbt-project-evaluator` or a CI `dbt ls` selector check.
- **One Grain per Model:** Document the grain in the model description (for example, "one row per `order_id` per `line_number`") and back it with a `unique` / `unique_combination_of_columns` test.
- **Group & Access Modifiers:** Assign marts to `groups` with an owner, set `access: public` only on contract-enforced marts, and keep staging / intermediate `access: private` or `protected` so other projects cannot couple to unstable internals (dbt Mesh).

### 2.2. Strict `source()` and `ref()` Usage

Never hardcode warehouse table paths (`analytics.prod.orders`, `"RAW"."SHOPIFY"."ORDERS"`). Hardcoded identifiers break lineage, environment isolation (dev / CI / prod schemas), `state:modified` selection, and `--defer`.

```yaml
# models/staging/shopify/_shopify__sources.yml
sources:
  - name: shopify
    database: "{{ env_var('DBT_RAW_DATABASE', 'raw') }}"
    schema: shopify
    loader: fivetran
    loaded_at_field: _fivetran_synced
    freshness:
      warn_after: {count: 6, period: hour}
      error_after: {count: 24, period: hour}
    tables:
      - name: orders
        identifier: orders
```

```sql
-- models/staging/shopify/stg_shopify__orders.sql
with source as (
    select * from {{ source('shopify', 'orders') }}
),

renamed as (
    select
        cast(id as varchar)                    as order_id,
        cast(customer_id as varchar)           as customer_id,
        lower(financial_status)                as financial_status,
        cast(total_price as numeric(18, 2))    as order_total_amount,
        convert_timezone('UTC', created_at)    as ordered_at_utc,
        _fivetran_synced                       as loaded_at_utc
    from source
    where not coalesce(_fivetran_deleted, false)
)

select * from renamed
```

### 2.3. Idempotent Incremental Models

An incremental model must produce exactly the same table as a full refresh for the same input data. Re-running the same window twice must never duplicate rows.

| Strategy | Use When | Mandatory Guards |
| :--- | :--- | :--- |
| `merge` | Mutable entities with a stable business key (orders, subscriptions). | `unique_key` (single or composite list), lookback window for late-arriving updates, `unique` test on the key. |
| `delete+insert` | Warehouses without efficient `MERGE`, or key-range replacement. | `unique_key` + bounded predicate to avoid full-table deletes. |
| `insert_overwrite` | Immutable, partitioned event data (BigQuery, Spark / Databricks). | `partition_by` + replace whole partitions only; recompute a fixed lookback (`3` days) of partitions. |
| `microbatch` | Large time-series facts with backfill needs (dbt 1.9+). | `event_time`, `batch_size`, `begin`, `lookback`; upstream models declare `event_time` for automatic filtering. |
| `append` | Strictly append-only, deduplicated upstream logs. | Proof of upstream uniqueness; never use for mutable data. |

```sql
-- models/marts/finance/fct_orders.sql
{{
    config(
        materialized='incremental',
        incremental_strategy='merge',
        unique_key='order_id',
        on_schema_change='append_new_columns',
        cluster_by=['ordered_at_utc']
    )
}}

select
    o.order_id,
    o.customer_id,
    o.financial_status,
    o.order_total_amount,
    o.ordered_at_utc,
    o.loaded_at_utc
from {{ ref('int_orders__deduplicated') }} as o

{% if is_incremental() %}
where o.loaded_at_utc > (
    select dateadd('hour', -{{ var('orders_lookback_hours', 72) }}, max(loaded_at_utc))
    from {{ this }}
)
{% endif %}
```

- **Lookback, Not `max()` Alone:** Filtering on `> max(loaded_at)` silently drops late-arriving rows. Always subtract a documented lookback window and rely on `unique_key` deduplication.
- **Deterministic Deduplication:** Use `row_number() over (partition by <key> order by <updated_at> desc, <tiebreaker>)` with a deterministic tiebreaker column; never `select distinct *` to hide fan-out.
- **No Non-Deterministic Functions in Keys:** Avoid `current_timestamp()`, `random()`, or `uuid()` in business keys or filters; inject run context via `var()` or `invocation_id` only for audit columns.
- **Schema Change Policy:** Prefer `on_schema_change='append_new_columns'` or `'fail'`; never `'ignore'` on contract-enforced marts.

### 2.4. Enforced Model Contracts

Every consumer-facing mart (`access: public`, BI, reverse-ETL, API, ML features) must declare `contract: { enforced: true }` with explicit column names, data types, and constraints.

```yaml
# models/marts/finance/_finance__models.yml
models:
  - name: fct_orders
    description: "One row per order_id. Source of truth for recognized order revenue."
    access: public
    group: finance
    config:
      contract:
        enforced: true
      meta:
        owner: "finance-analytics"
    constraints:
      - type: primary_key
        columns: [order_id]
    columns:
      - name: order_id
        data_type: varchar
        constraints:
          - type: not_null
        data_tests:
          - unique
          - not_null
      - name: customer_id
        data_type: varchar
        data_tests:
          - relationships:
              arguments:
                to: ref('dim_customers')
                field: customer_id
      - name: financial_status
        data_type: varchar
        data_tests:
          - accepted_values:
              arguments:
                values: ['pending', 'paid', 'refunded', 'voided']
      - name: order_total_amount
        data_type: numeric(18, 2)
      - name: ordered_at_utc
        data_type: timestamp
      - name: loaded_at_utc
        data_type: timestamp
```

- **Breaking Changes Require Versions:** Removing or retyping a contracted column requires a new model version (`versions:` with `latest_version`) plus a `deprecation_date` on the old version; never mutate a public contract in place.
- **Constraints vs. Tests:** Many warehouses do not enforce `primary_key` / `foreign_key` constraints; always pair them with `unique`, `not_null`, and `relationships` data tests.

### 2.5. SQL Tests, Unit Tests & Semantic Layer Alignment

- **Generic Data Tests:** `unique`, `not_null`, `accepted_values`, `relationships`, plus `dbt_utils` / `dbt_expectations` (`unique_combination_of_columns`, `recency`, `expression_is_true`).
- **Singular Tests:** SQL files in `tests/` that return failing rows (for example, negative revenue or orphaned refunds). Configure `severity`, `warn_if`, and `error_if` deliberately; never downgrade a failing gate to `warn` to make CI green.
- **Unit Tests (dbt 1.8+):** Use `unit_tests:` with mocked `given` inputs and `expect` rows to prove complex CASE logic, window functions, and incremental branches (`overrides: macros: {is_incremental: true}`).
- **Semantic Layer:** Define `semantic_models` (entities, dimensions, measures) only on marts and declare `metrics` (simple, ratio, cumulative, derived) once. BI tools must query governed metrics via the Semantic Layer API instead of re-implementing revenue formulas in dashboards. Validate with `dbt sl validate` (or `mf validate-configs`).

## 3. SDD Gate 2 & Gate 4 Contract Alignment

- **Gate 2 (`02-tech-spec.md`):** Before coding (`@architect`), document for every new or changed model:
  1. Layer, materialization, grain, `unique_key`, and incremental strategy with explicit lookback window.
  2. Upstream `source()` declarations (database, schema, loader, `loaded_at_field`, freshness SLA) and downstream consumers (exposures, BI, APIs).
  3. Contract column table (name, `data_type`, nullability, constraints, PII classification) aligned with `docs/knowledge/DATA_MODELS.md`.
  4. Versioning and deprecation plan for any breaking change, plus semantic metric definitions.
  5. Security controls aligned with `.agents/rules/05-security-and-secrets.md` and `sdd-security-audit`: least-privilege warehouse roles, credentials via environment variables or secret managers (never in `profiles.yml` committed to Git), and PII masking.
- **Gate 4 (`@back-engineer` & `@qa-tester`):**
  - Implement models strictly matching the Gate 2 contract table; `dbt build` must pass contract enforcement, data tests, and unit tests for the modified selection and its children (`state:modified+`).
  - Prove idempotency by running the incremental model twice over the same window and asserting identical row counts and key uniqueness, and compare one full refresh against the incremental result in CI.
  - Apply `sdd-test-quality-audit` to reject tautological tests and `sdd-spec-compliance-audit` to confirm columns and types match `02-tech-spec.md` 1:1. Gate 5 (`@documentator`) registers marts and metrics in `docs/knowledge/DATA_MODELS.md`.

## 4. Anti-Patterns & Fail-Closed Guards

| Anti-Pattern | Failure Mode | Fail-Closed Guard |
| :--- | :--- | :--- |
| Hardcoded `from raw.shopify.orders` | Lineage gaps, prod data read from dev, broken `--defer`. | CI grep rejecting three-part identifiers in `models/`; require `source()` / `ref()` exclusively. |
| Marts selecting directly from `source()` | Raw schema changes ripple into consumers without a cleaning layer. | `dbt-project-evaluator` rule `fct_direct_join_to_source` set to `error`. |
| Incremental filter `> max(updated_at)` without lookback or `unique_key` | Late-arriving rows lost or duplicated silently. | Mandatory `unique_key`, lookback `var()`, and `unique` test on every incremental model. |
| Public mart without `contract: { enforced: true }` | Silent column drops / type changes break dashboards and APIs. | Fail CI when `access: public` models lack enforced contracts (manifest check). |
| `select distinct *` to hide join fan-out | Masks grain violations and inflates cost. | Explicit deduplication with deterministic `row_number()` and grain tests. |
| Tests downgraded to `severity: warn` to unblock merges | Known-bad data reaches production (violates `sdd-silent-failure-audit`). | Require `@architect` approval in `02-tech-spec.md` for any `warn` severity on contracted columns. |
| `on_schema_change='ignore'` on marts | New upstream columns silently dropped; contract drift. | Use `append_new_columns` or `fail`, plus contract enforcement. |
| Metric formulas duplicated in BI tools | Conflicting revenue numbers across teams. | Single metric definition in the Semantic Layer; dashboards query governed metrics. |

## 5. Deterministic Verification Commands

Use these deterministic commands during Gate 4 DoD verification (adapt target names and state paths to `specs/STACK.md`):

```bash
# 1. Parse the project and fail on any compilation, YAML, or contract syntax error
dbt parse --warn-error

# 2. Build only modified models and their children against production state (Slim CI)
dbt build --select "state:modified+" --defer --state ./prod-artifacts --fail-fast

# 3. Verify source freshness SLAs declared in sources YAML
dbt source freshness --select "source:shopify"

# 4. Prove incremental idempotency (second run must not change counts or duplicate keys)
dbt run --select fct_orders && dbt run --select fct_orders
dbt test --select fct_orders

# 5. Reject hardcoded three-part warehouse identifiers inside models
! grep -rEni --include='*.sql' '\b(from|join)[[:space:]]+"?[a-z_]+"?\."?[a-z_]+"?\."?[a-z_]+' models/

# 6. Validate semantic models and metrics
dbt sl validate

# 7. Lint SQL style deterministically
sqlfluff lint models/ --dialect "${SQLFLUFF_DIALECT}"
```
