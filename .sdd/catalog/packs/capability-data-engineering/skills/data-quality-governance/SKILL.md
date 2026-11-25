---
name: data-quality-governance
description: Data quality and governance contracts for analytics platforms including producer-consumer data contracts, freshness, completeness, volume, and uniqueness SLAs (dbt tests, Soda, Great Expectations), column-level lineage, backward-compatible analytical schema evolution, and PII anonymization and tokenization aligned with docs/knowledge/DATA_MODELS.md. Use when defining, implementing, or reviewing data contracts, quality checks, lineage, schema changes, or PII handling under SDD Gate 2 and Gate 4.
---

# Data Quality & Governance

Production-grade data governance playbook for explicit producer-consumer contracts, measurable quality SLAs, traceable lineage, safe schema evolution, and privacy-by-design handling of personal data.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) involves any of the following:

- Publishing a new dataset, table, topic, or mart that another team, dashboard, ML model, or API consumes.
- Defining or changing freshness, completeness, volume, uniqueness, or validity expectations for a dataset.
- Adding, renaming, retyping, or removing columns in analytical schemas (warehouse tables, lakehouse tables, Parquet / Iceberg / Delta datasets).
- Ingesting, transforming, or exposing personal data (PII), special-category data, or regulated identifiers (GDPR, CCPA, HIPAA, PCI DSS).
- Implementing lineage (OpenLineage, dbt manifest, Unity Catalog, Dataplex, DataHub, OpenMetadata) or impact analysis for a change.
- Investigating silent data incidents such as stale dashboards, duplicated rows, null spikes, volume drops, or leaked personal data.

## 2. Production Architecture & Patterns

### 2.1. Producer-Consumer Data Contracts

A data contract is a versioned, machine-readable agreement owned by the producer and validated in CI on both sides. Prefer the Open Data Contract Standard (ODCS) or dbt model contracts as the canonical format.

```yaml
# contracts/commerce/orders.v1.yaml (ODCS-style)
apiVersion: v3.0.0
kind: DataContract
id: commerce.orders
version: 1.2.0
status: active
owner: commerce-data-producers
consumers: [finance-analytics, growth-ml]
schema:
  - name: fct_orders
    physicalName: analytics.marts.fct_orders
    properties:
      - name: order_id
        logicalType: string
        required: true
        unique: true
        primaryKey: true
      - name: customer_token
        logicalType: string
        required: true
        classification: pii-tokenized
      - name: order_total_amount
        logicalType: number
        required: true
quality:
  - type: freshness
    column: loaded_at_utc
    mustBeLessThan: 6h
  - type: rowCount
    mustBeGreaterThan: 1000
slaProperties:
  - property: availability
    value: "09:00 UTC daily"
  - property: retention
    value: "7 years"
```

- **Producer Ownership:** The producing team owns the contract, its tests, and its version. Consumers declare their dependency and receive change notifications; they never patch producer tables.
- **Semantic Versioning:** `PATCH` for documentation or tighter checks, `MINOR` for additive optional columns, `MAJOR` for any breaking change (removal, rename, retype, grain change, semantic change).
- **Contract as Code:** Store contracts next to the producing code, validate them in CI (`datacontract test`, `dbt build` with `contract: { enforced: true }`), and publish them to the catalog.

### 2.2. Quality SLAs: Freshness, Completeness, Volume & Uniqueness

| Dimension | Definition | dbt | Soda (SodaCL) | Great Expectations |
| :--- | :--- | :--- | :--- | :--- |
| **Freshness** | Max age of the newest record vs. SLA. | `dbt source freshness` (`warn_after` / `error_after`), `dbt_utils.recency` | `freshness(loaded_at_utc) < 6h` | `expect_column_max_to_be_between` on timestamp |
| **Completeness** | Required columns populated; no missing partitions. | `not_null`, `dbt_utils.at_least_one` | `missing_count(customer_token) = 0` | `expect_column_values_to_not_be_null` |
| **Volume** | Row count within expected band per interval. | `dbt_expectations.expect_table_row_count_to_be_between` | `row_count > 1000`, `anomaly detection for row_count` | `expect_table_row_count_to_be_between` |
| **Uniqueness** | Declared grain has no duplicates. | `unique`, `dbt_utils.unique_combination_of_columns` | `duplicate_count(order_id) = 0` | `expect_column_values_to_be_unique` |
| **Validity** | Values within domain, ranges, formats. | `accepted_values`, `expression_is_true` | `invalid_count(status) = 0` with `valid values` | `expect_column_values_to_be_in_set` |

```yaml
# soda/checks/fct_orders.yml
checks for fct_orders:
  - freshness(loaded_at_utc) < 6h
  - row_count > 1000
  - anomaly detection for row_count
  - duplicate_count(order_id) = 0
  - missing_count(customer_token) = 0
  - invalid_count(financial_status) = 0:
      valid values: [pending, paid, refunded, voided]
  - schema:
      fail:
        when required column missing: [order_id, customer_token, order_total_amount]
        when wrong column type:
          order_id: varchar
```

- **Severity Tiers:** `error` blocks downstream publication (circuit breaker), `warn` pages the owner without blocking. Contracted SLAs are always `error`.
- **Write-Audit-Publish (WAP):** Build into a staging schema or branch (Iceberg / Delta / Nessie / BigQuery clone), run checks, and swap or publish only when every blocking check passes.
- **Quarantine, Never Drop:** Rows failing row-level validation go to a quarantine table with reason codes and counts; never filter them out silently.
- **Measure SLOs:** Track SLA attainment per dataset (percentage of intervals delivered on time and passing checks) and report it to owners.

### 2.3. Column-Level Lineage

- **Emit Lineage Automatically:** Enable the OpenLineage integration for Airflow (`apache-airflow-providers-openlineage`), Spark, and dbt (`dbt-ol` wrapper) so every run emits input and output datasets with column-level facets.
- **Catalog of Record:** Ingest `manifest.json` and `catalog.json` (`dbt docs generate`) plus OpenLineage events into the platform catalog (DataHub, OpenMetadata, Marquez, Dataplex, Unity Catalog).
- **Impact Analysis Before Change:** Any Gate 2 proposal that modifies a column lists every downstream model, exposure, dashboard, and contract consumer obtained from lineage (`dbt ls --select "fct_orders+" --resource-type model exposure`).
- **PII Propagation:** Lineage must propagate classification tags so derived columns from PII inputs inherit the strictest classification until explicitly anonymized.

### 2.4. Backward-Compatible Analytical Schema Evolution

| Change | Compatibility | Required Procedure |
| :--- | :--- | :--- |
| Add nullable / defaulted column | Backward compatible (`MINOR`). | Add to contract and tests; announce to consumers. |
| Widen type (`int` to `bigint`, `varchar(50)` to `varchar(255)`) | Usually compatible. | Verify warehouse and file-format rules (Parquet / Avro promotion). |
| Rename column | Breaking (`MAJOR`). | Expand-contract: add new column, dual-write, migrate consumers, deprecate, then remove. |
| Remove or retype column, change grain | Breaking (`MAJOR`). | New model / contract version with `deprecation_date`; parallel run window agreed with consumers. |
| Change semantics with same name | Breaking and dangerous. | Forbidden; introduce a new column or metric name. |

- **Expand-Contract Only:** Breaking changes ship as a new version (dbt `versions:` with `latest_version`, `_v2` tables, or a new contract `MAJOR`) running in parallel until every registered consumer migrates.
- **Table Format Guarantees:** For Iceberg / Delta, rely on column IDs for safe renames at the storage layer, but still treat renames as breaking for SQL consumers.
- **Automated Detection:** Run contract diffing in CI (`datacontract breaking`, dbt contract enforcement, Schema Registry `BACKWARD` / `FULL` checks for streamed sources) and fail on undeclared breaking changes.

### 2.5. PII Anonymization, Pseudonymization & Tokenization

- **Classify at Ingestion:** Tag every column in `meta` (`pii: direct | indirect | sensitive | none`) matching the classification taxonomy in `docs/knowledge/DATA_MODELS.md`. Unclassified columns from new sources fail CI.
- **Tokenize Direct Identifiers Early:** Replace emails, phone numbers, national IDs, and payment data in staging with deterministic tokens (`HMAC-SHA256` with a key held in KMS / Vault, or a tokenization vault service) so joins still work without exposing raw values. Plain unsalted hashes (`md5(email)`, `sha256(email)`) are reversible by dictionary attack and are forbidden.
- **Anonymize for Analytics:** Use generalization (age bands, truncated postcodes), aggregation thresholds (k-anonymity, minimum cohort size), or noise for published aggregates. Pseudonymized data remains personal data under GDPR.
- **Masking at Query Time:** Apply warehouse-native controls (Snowflake masking and row access policies, BigQuery policy tags and data masking, Databricks column masks, PostgreSQL RLS) bound to roles, never to ad hoc views.
- **Minimization, Retention & Erasure:** Load only columns with a documented purpose, enforce retention via partition expiry, and support right-to-erasure by deleting the token mapping (crypto-shredding) plus reprocessing affected partitions.
- **Non-Production Environments:** Dev and CI use synthetic or tokenized data only; production PII never lands in developer sandboxes, logs, or test fixtures.

## 3. SDD Gate 2 & Gate 4 Contract Alignment

- **Gate 2 (`02-tech-spec.md`):** Before coding (`@architect`), document for every published or changed dataset:
  1. Contract identifier, owner, consumers, semantic version, grain, and the full column table (type, nullability, constraints, PII classification).
  2. Quality SLAs (freshness, completeness, volume, uniqueness, validity) with thresholds, severity, tooling (dbt / Soda / Great Expectations), and alert routing.
  3. Lineage-based impact analysis and the schema evolution plan (expand-contract steps, deprecation dates).
  4. PII handling per column (tokenization, masking policy, retention, erasure path) aligned with `docs/knowledge/DATA_MODELS.md`, `.agents/rules/05-security-and-secrets.md`, and `sdd-security-audit`.
- **Gate 4 (`@back-engineer` & `@qa-tester`):**
  - Implement contracts, checks, masking policies, and tokenization exactly as specified; every contracted SLA has an automated blocking check in CI and in the production pipeline.
  - Include negative tests that inject duplicates, nulls, stale timestamps, unexpected volume, and raw PII values into fixtures and prove each check fails closed.
  - Run `sdd-test-quality-audit` and `sdd-spec-compliance-audit`, and use `santa-method` for breaking schema changes. Gate 5 (`@documentator`) updates `docs/knowledge/DATA_MODELS.md` with contracts, classifications, and lineage.

## 4. Anti-Patterns & Fail-Closed Guards

| Anti-Pattern | Failure Mode | Fail-Closed Guard |
| :--- | :--- | :--- |
| Implicit contracts ("the table is the API") | Producers break consumers unknowingly. | Versioned contract file per published dataset, validated in CI. |
| Quality checks configured as `warn` only | Bad data published while alerts are ignored. | Contracted SLAs are blocking (`error`) with Write-Audit-Publish gating. |
| Filtering invalid rows silently | Undetected data loss and biased metrics (violates `sdd-silent-failure-audit`). | Quarantine table with reason codes and a blocking threshold on quarantine rate. |
| In-place column rename or retype | Dashboards and models fail or silently compute wrong values. | Expand-contract with versioned models and automated breaking-change detection. |
| `sha256(email)` presented as anonymization | Re-identification via dictionary attacks; regulatory exposure. | Keyed HMAC or vault tokenization with KMS-held keys; classification tests. |
| Raw PII in dev, CI fixtures, or logs | Data breach outside production controls. | Synthetic or tokenized datasets only; secret and PII scanning on fixtures. |
| Lineage maintained manually in wikis | Impact analysis misses consumers. | Automated OpenLineage and dbt manifest ingestion into the catalog. |
| Unclassified new columns | PII spreads without masking or retention. | CI fails when any column lacks a `meta.pii` classification. |

## 5. Deterministic Verification Commands

Use these deterministic commands during Gate 4 DoD verification (adapt data sources, paths, and selectors to `specs/STACK.md`):

```bash
# 1. Validate the data contract schema and run its quality checks against the target
datacontract lint contracts/commerce/orders.v1.yaml
datacontract test contracts/commerce/orders.v1.yaml

# 2. Detect undeclared breaking changes against the previously published contract
datacontract breaking contracts/commerce/orders.v1.prev.yaml contracts/commerce/orders.v1.yaml

# 3. Run dbt freshness and blocking data tests for the dataset and its children
dbt source freshness
dbt build --select "fct_orders+" --fail-fast

# 4. Run Soda checks (non-zero exit on any failed check)
soda scan -d warehouse -c soda/configuration.yml soda/checks/fct_orders.yml

# 5. Run the Great Expectations checkpoint for the dataset
python -m include.quality.run_checkpoint --checkpoint fct_orders_checkpoint

# 6. Fail if any model column lacks a PII classification in the dbt manifest
python -c "import json,sys; m=json.load(open('target/manifest.json')); bad=[f'{n}.{c}' for n,v in m['nodes'].items() if v['resource_type']=='model' for c,col in v['columns'].items() if 'pii' not in col.get('meta',{})]; print(*bad, sep='\n'); sys.exit(1 if bad else 0)"

# 7. List downstream impact (models and exposures) before a schema change
dbt ls --select "fct_orders+" --resource-type model exposure
```
