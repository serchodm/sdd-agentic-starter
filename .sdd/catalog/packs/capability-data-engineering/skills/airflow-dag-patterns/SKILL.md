---
name: airflow-dag-patterns
description: Production Apache Airflow orchestration using the TaskFlow API (@dag and @task decorators), zero I/O at top-level DAG parse time, idempotent backfill-safe tasks keyed on logical_date and the data interval, deferrable sensors and triggers, secure Connections and Variables handling, and cycle-free DAG import tests. Use when designing, implementing, or reviewing Airflow DAGs, operators, sensors, or deployments under SDD Gate 2 and Gate 4.
---

# Airflow DAG Patterns

Production-grade Apache Airflow engineering playbook for fast-parsing, idempotent, backfill-safe, and credential-free DAGs that recover deterministically from retries and reruns.

## 1. When to Activate

Activate this skill whenever a Work Item (`FEAT-XXX`, `CR-XXX`, or `BUG-XXX`) involves any of the following:

- Creating or refactoring Airflow DAGs (Airflow 2.7+ or Airflow 3.x, including Astronomer, Google Cloud Composer, and Amazon MWAA).
- Orchestrating dbt, Spark, warehouse SQL, ingestion jobs, or ML pipelines with TaskFlow tasks, provider operators, or Cosmos task groups.
- Designing schedules, catchup and backfill behavior, asset/dataset-driven scheduling, or cross-DAG dependencies.
- Adding sensors that wait on files, partitions, external jobs, or APIs.
- Handling Connections, Variables, secrets backends, or service-account credentials.
- Investigating slow scheduler parsing, DAG import errors, duplicated loads after retries, zombie tasks, or exhausted worker slots.

## 2. Production Architecture & Patterns

### 2.1. TaskFlow API as the Default Authoring Style

Use the `@dag` and `@task` decorators for Python logic so XCom passing, dependencies, and typing stay explicit. Use classic provider operators only when they add real value (deferrable sensors, managed transfers).

```python
# dags/orders_daily.py
from __future__ import annotations

import pendulum
from airflow.sdk import dag, task  # Airflow 2.x: from airflow.decorators import dag, task

DEFAULT_ARGS = {
    "owner": "data-platform",
    "retries": 3,
    "retry_delay": pendulum.duration(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": pendulum.duration(minutes=30),
    "execution_timeout": pendulum.duration(minutes=45),
}


@dag(
    dag_id="orders_daily",
    schedule="0 3 * * *",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["domain:commerce", "layer:ingestion"],
    doc_md=__doc__,
)
def orders_daily():
    @task
    def extract(data_interval_start=None, data_interval_end=None) -> str:
        from include.orders.extract import export_orders_window  # heavy import inside task

        return export_orders_window(
            start=data_interval_start.isoformat(),
            end=data_interval_end.isoformat(),
        )

    @task
    def load(staged_uri: str, data_interval_start=None) -> int:
        from include.orders.load import replace_partition

        return replace_partition(
            staged_uri=staged_uri,
            partition_date=data_interval_start.date().isoformat(),
        )

    load(extract())


orders_daily()
```

- **Small XComs Only:** Pass URIs, partition keys, and row counts between tasks; never return DataFrames or files through XCom. Persist payloads to object storage with deterministic, interval-scoped paths.
- **Business Logic Outside `dags/`:** Keep transformation code in an importable package (`include/` or a versioned wheel) with its own unit tests; the DAG file only wires tasks together.
- **Explicit Concurrency Limits:** Set `max_active_runs`, `max_active_tis_per_dag`, and `pool` / `pool_slots` for tasks hitting shared warehouses or rate-limited APIs.

### 2.2. Zero I/O at Top-Level DAG Parse Time

The DAG processor re-imports every DAG file continuously (every `min_file_process_interval` seconds). Any top-level side effect multiplies across parses, slows scheduling, and leaks load onto metadata databases and external systems.

- **Forbidden at Module Level:** database queries, HTTP calls, `Variable.get()`, `BaseHook.get_connection()`, cloud SDK client creation, reading large files, `datetime.now()` in `start_date`, and heavy imports (`pandas`, `tensorflow`, `pyspark`).
- **Allowed at Module Level:** constants, pendulum literals, lightweight imports, DAG / task definitions, and Jinja templates such as `{{ var.value.orders_bucket }}` or `{{ conn.warehouse.host }}` (resolved at runtime, not parse time).
- **Dynamic DAGs:** Generate DAGs from a version-controlled YAML/JSON file shipped with the code, never from a live database or API listing. For runtime fan-out, use dynamic task mapping (`.expand()` / `.expand_kwargs()`) with a bounded `max_map_length`.
- **Parse Budget:** Each DAG file must import in under `2` seconds locally (`dagbag_import_timeout` defaults to `30`); treat anything above budget as a defect.

### 2.3. Idempotent, Backfill-Safe Tasks

Every task must produce the same final state whether it runs once, is retried, or is re-run months later during a backfill.

| Concern | Required Pattern | Forbidden Pattern |
| :--- | :--- | :--- |
| Time window | `data_interval_start` / `data_interval_end` (or `logical_date`) from the task context. | `datetime.now()`, `date.today()`, `CURRENT_DATE` in SQL. |
| Writes | Replace a partition (`DELETE ... WHERE ds = '{{ ds }}'` + insert in one transaction, `MERGE` on a business key, `INSERT OVERWRITE PARTITION`). | Blind `INSERT` / append that duplicates rows on retry. |
| Files | Deterministic paths such as `s3://bucket/orders/ds={{ ds }}/part-000.parquet`, overwritten on retry. | Timestamped or random file names per attempt. |
| External side effects | Idempotency key derived from `dag_id`, `task_id`, and `logical_date`; check-before-act. | Sending emails, payments, or webhooks without dedupe keys. |
| Backfill | `airflow backfill create` (Airflow 3) or `airflow dags backfill` (Airflow 2) with `max_active_runs` bounded. | Ad hoc manual reruns that skip data intervals. |

- **Catchup Policy:** Default to `catchup=False` and run historical loads as explicit, reviewed backfills. Set `depends_on_past=True` only when interval N strictly requires interval N-1, and document it in Gate 2.
- **Asset-Aware Scheduling:** Prefer `schedule=[Asset("s3://.../orders")]` (Airflow 3) or `Dataset` (Airflow 2.4+) over brittle cross-DAG `ExternalTaskSensor` chains.

### 2.4. Deferrable Sensors & Triggers

Classic sensors in `poke` mode hold a worker slot for the entire wait. Use deferrable operators so the wait moves to the async triggerer process.

```python
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

wait_for_export = S3KeySensor(
    task_id="wait_for_export",
    bucket_key="s3://partner-drop/orders/ds={{ ds }}/_SUCCESS",
    aws_conn_id="aws_partner_drop",
    deferrable=True,
    poke_interval=300,
    timeout=6 * 60 * 60,
    soft_fail=False,
)
```

- **Always Bound the Wait:** Every sensor sets `timeout`; default `soft_fail=False` so a missing upstream fails loudly instead of skipping downstream loads silently.
- **Run a Triggerer:** Deferrable tasks require at least one `airflow triggerer` process per environment (two for high availability). Verify it in the deployment manifest.
- **Fallback Mode:** If no deferrable variant exists, use `mode="reschedule"` with a long `poke_interval`, never `poke` for waits longer than a few minutes.

### 2.5. Secure Connections, Variables & Secrets Backends

- **Zero Hardcoded Credentials:** No passwords, tokens, keys, or connection URIs in DAG files, `default_args`, Docker images, or Git. Reference credentials only by `conn_id`.
- **Secrets Backend in Production:** Configure HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager, or Azure Key Vault as `[secrets] backend`; use `AIRFLOW_CONN_<CONN_ID>` environment variables only for local and CI environments.
- **Masking:** Mark sensitive Variables with names containing `secret`, `password`, `token`, or `api_key` (or extend `sensitive_var_conn_names`) so logs and the UI mask them; never `print()` connection objects.
- **Least Privilege:** Use one connection per system and purpose with scoped service accounts (read-only for extraction, write only to target schemas). Prefer workload identity / IRSA over static keys.

## 3. SDD Gate 2 & Gate 4 Contract Alignment

- **Gate 2 (`02-tech-spec.md`):** Before coding (`@architect`), document for every DAG:
  1. `dag_id`, owner, schedule or asset triggers, `start_date`, `catchup`, `max_active_runs`, and SLA / deadline expectations.
  2. Task graph with idempotency strategy per task (partition replace, `MERGE` key, deterministic path) and retry budget (`retries`, backoff, `execution_timeout`).
  3. Sensors with deferrable mode, `timeout`, and failure semantics.
  4. Required Connections and Variables by `conn_id` / key only, with the secrets backend and least-privilege scopes aligned with `.agents/rules/05-security-and-secrets.md` and `sdd-security-audit`.
  5. Upstream and downstream data assets registered in `docs/knowledge/DATA_MODELS.md` and orchestration topology in `docs/knowledge/SYSTEM_TOPOLOGY.md`.
- **Gate 4 (`@back-engineer` & `@qa-tester`):**
  - Implement DAGs strictly matching the Gate 2 task graph; business logic ships with unit tests independent of the Airflow runtime.
  - Provide a DagBag import test (zero import errors, zero cycles, required tags and owners present, retries configured) and a `dag.test()` run for one fixed `logical_date` against local or containerized dependencies.
  - Prove idempotency by executing the same data interval twice and asserting identical target row counts and key uniqueness. Apply `sdd-test-quality-audit` and `sdd-spec-compliance-audit` before Gate 5 (`@documentator`).

```python
# tests/dags/test_dag_integrity.py
import pytest
from airflow.models import DagBag


@pytest.fixture(scope="session")
def dagbag() -> DagBag:
    return DagBag(dag_folder="dags", include_examples=False)


def test_no_import_errors_or_cycles(dagbag: DagBag) -> None:
    # Cycles raise during import and surface here as import errors.
    assert dagbag.import_errors == {}, dagbag.import_errors


def test_dag_governance(dagbag: DagBag) -> None:
    for dag_id, dag in dagbag.dags.items():
        assert dag.tags, f"{dag_id} has no tags"
        assert dag.max_active_runs is not None, f"{dag_id} lacks max_active_runs"
        for t in dag.tasks:
            assert t.retries >= 1, f"{dag_id}.{t.task_id} has no retries"
            assert t.owner != "airflow", f"{dag_id}.{t.task_id} uses default owner"
```

## 4. Anti-Patterns & Fail-Closed Guards

| Anti-Pattern | Failure Mode | Fail-Closed Guard |
| :--- | :--- | :--- |
| `Variable.get()` or DB/API calls at module level | Scheduler slowdown, metadata DB load, import timeouts. | Jinja templates or in-task lookups; CI parse-time budget check per DAG file. |
| `datetime.now()` inside task logic or `start_date` | Non-reproducible results; backfills load the wrong window. | Use `data_interval_start` / `data_interval_end`; static timezone-aware `start_date`. |
| Append-only `INSERT` without partition replace or key | Duplicated rows on every retry or rerun. | Partition overwrite or `MERGE` on a business key; idempotency test in CI. |
| Sensors in `poke` mode without `timeout` | Worker slots exhausted; DAGs wait forever. | `deferrable=True`, explicit `timeout`, `soft_fail=False`. |
| Credentials in DAG code, `default_args`, or images | Secret leakage via Git, logs, or UI. | Secrets backend + `conn_id` references; secret scanning in CI. |
| `try/except Exception: pass` inside tasks | Task succeeds while data is missing (violates `sdd-silent-failure-audit`). | Let exceptions propagate so retries and alerts fire; use `on_failure_callback`. |
| Large objects passed through XCom | Metadata DB bloat and serialization failures. | Pass URIs and keys only; persist payloads to object storage. |
| Live DB or API listing to generate DAGs dynamically | Flapping DAGs and parse storms when the source is slow. | Version-controlled config files or dynamic task mapping with bounded fan-out. |

## 5. Deterministic Verification Commands

Use these deterministic commands during Gate 4 DoD verification (adapt paths, DAG IDs, and dates to `specs/STACK.md`):

```bash
# 1. Fail on any DAG import error (includes cycle detection)
airflow dags list-import-errors --output json | python -c "import json,sys; e=json.load(sys.stdin); sys.exit(1 if e else 0)"

# 2. Run the DAG integrity test suite (import, cycles, owners, retries, tags)
pytest tests/dags -q

# 3. Enforce the parse-time budget for a single DAG file (< 2 seconds)
timeout 2 python dags/orders_daily.py

# 4. Execute one deterministic data interval end-to-end without the scheduler
airflow dags test orders_daily 2025-01-15

# 5. Re-run the same interval to prove idempotency, then compare target counts
airflow dags test orders_daily 2025-01-15

# 6. Lint DAG code, including Airflow-specific deprecation and top-level-code rules
ruff check dags/ include/ --select E,F,AIR

# 7. Scan DAGs and includes for hardcoded secrets
gitleaks detect --no-banner --source . --redact
```
