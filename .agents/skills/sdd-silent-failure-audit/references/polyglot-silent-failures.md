# Reference `sdd-silent-failure-audit`: Polyglot Silent Failures & Fail-Closed Remediation

Load during **Gate 4** (`@qa-tester`, `@back-engineer`, `@front-engineer`, `@security-reviewer`) when auditing error handling across languages, SQL persistence, or async consumers. Unmodeled failures must fail closed with observable state and causal context (`01-spec.md`, `02-tech-spec.md`).

## 1. Forbidden Language Patterns & Fail-Closed Remediation

### Python
- **Forbidden:** `except: pass`, `except Exception: return None` / `{}`, or broad `contextlib.suppress(Exception, OSError)` masking corruption or permission errors.
- **Remediation:** Catch narrow exceptions (`ValueError`, `FileNotFoundError`), log structured context (zero secrets/PII), and `raise DomainError(...) from exc`. Restrict `contextlib.suppress` to idempotent cleanup of a single expected error documented in `02-tech-spec.md`.

### TypeScript / JavaScript
- **Forbidden:** `.catch(() => {})`, empty `catch (err) {}`, floating promises (`asyncFn()` without `await` or handler), or `try { return JSON.parse(x) } catch { return {} }`.
- **Remediation:** Enforce `@typescript-eslint/no-floating-promises`, `await` every promise, normalize external payloads at the producing boundary, and return a typed `Result<T, E>` or rethrow `new DomainError("...", { cause: err })`.

### Go
- **Forbidden:** `_ = repo.Save(ctx, v)`, ignoring `rows.Err()` after iteration, `defer f.Close()` on writable files/streams, or returning `nil, nil` on lookup/IO failure.
- **Remediation:** Check every `err != nil`, wrap with `fmt.Errorf("save %s: %w", id, err)`, inspect `rows.Err()`, capture writable `Close()` errors via named returns, and run `errcheck`.

### Rust
- **Forbidden:** `let _ = fs::write(...)`, `.ok()` discarding IO/DB `Result`, or `.unwrap_or_default()` / `.unwrap_or_else(|_| vec![])` masking storage/deserialization failures as empty state.
- **Remediation:** Propagate with `?` and `thiserror` / `anyhow::Context`. Match `ErrorKind::NotFound` explicitly only when `02-tech-spec.md` models absence; deny `clippy::let_underscore_must_use`.

### Java / Kotlin
- **Forbidden:** Empty `catch (Exception e) {}`, catching `InterruptedException` without `Thread.currentThread().interrupt()`, or Kotlin `runCatching { ... }.getOrNull()` / `.getOrDefault(...)` swallowing `CancellationException`.
- **Remediation:** Rethrow `CancellationException` immediately, restore interrupt status on `InterruptedException`, and wrap infrastructure exceptions into typed domain errors preserving `cause`.

## 2. Code Contrast (Forbidden vs. Fail-Closed)

```python
# FORBIDDEN: swallows permission/disk corruption as "empty config"
with contextlib.suppress(Exception):
    return json.loads(config_path.read_text(encoding="utf-8"))
return {}

# FAIL-CLOSED: separates modeled absence from IO/parse failure
try:
    return parse_config(json.loads(config_path.read_text(encoding="utf-8")))
except FileNotFoundError:
    if allow_missing_default:
        return Config.default()
    raise ConfigMissingError(str(config_path)) from None
except (OSError, json.JSONDecodeError) as exc:
    raise ConfigCorruptedError(f"Invalid config: {config_path}") from exc
```

```rust
// FORBIDDEN: IO or UTF-8 failure masquerades as empty allowlist
let rules = std::fs::read_to_string(path).unwrap_or_default();

// FAIL-CLOSED: propagates typed IO error with path context
let rules = std::fs::read_to_string(path)
    .map_err(|source| PolicyError::Io { path: path.to_path_buf(), source })?;
```

## 3. SQL Transactions & Optimistic Concurrency

1. **Implicit Autocommit / Missing `ROLLBACK`:** Execute multi-step writes inside an explicit transaction (`BEGIN ... COMMIT`) via a unit-of-work / context manager that guarantees `ROLLBACK` on any exception before re-raising.
2. **Unchecked `COMMIT`:** Deferred constraints (`DEFERRABLE INITIALLY DEFERRED`) and serialization failures surface at `COMMIT`; never ignore `COMMIT` errors.
3. **Zero-Row Silent No-Ops:** `UPDATE` / `DELETE` statements with `WHERE id = $1 AND tenant_id = $2 AND version = $3` succeed syntactically when `0` rows match. Assert `affected_rows == 1` and raise `ConcurrencyConflictError` or `NotFoundError` when `0`.

## 4. Async Messaging & Dead-Letter Queues (DLQ)

In Kafka, RabbitMQ, SQS, NATS, or Redis Streams, acknowledging a failed message destroys data silently:
- **Ban `catch -> ack`:** Never call `ack()`, `commitOffsets()`, or `deleteMessage()` inside `catch` without durable DLQ persistence.
- **Transient vs. Terminal Routing:**
  - *Transient* (DB timeout, `503`, lock contention): `nack` / skip commit; apply bounded exponential backoff + jitter.
  - *Poison pill* (invalid schema, invariant breach, retries exhausted): publish raw payload, `correlation_id`, source topic/offset, and error metadata to `<stream>.dlq` **first**, confirm broker `ack` on the DLQ write, and only then commit/`ack` the source message.
- **Idempotency:** Record processed `event_id` in an Inbox table inside the same DB transaction as domain mutations.

## 5. Gate 4 Audit Checklist

- [ ] Zero `except: pass`, `.catch(() => {})`, `_ = err` on I/O, or `let _ =` on `Result`.
- [ ] Zero `unwrap_or_default()` / `getOrNull()` / `return None` hiding I/O, parse, auth, or network errors.
- [ ] Multi-write SQL guarantees `ROLLBACK` on error and asserts `rowcount` on versioned/tenant mutations.
- [ ] Async consumers verify DLQ persistence before acknowledging failed messages.
- [ ] Error payloads match `01-spec.md` without leaking secrets or PII (`.agents/rules/05-security-and-secrets.md`).
