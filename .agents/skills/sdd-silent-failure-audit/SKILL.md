---
name: sdd-silent-failure-audit
description: Hunts swallowed exceptions, empty catch blocks, silent fallback defaults, and unpropagated errors in Python and TypeScript code (affaan-m/ecc silent-failure-hunter & morluto/rea Fail-Closed).
---

# Skill: `sdd-silent-failure-audit`

Run before Gate 5 closure to enforce **Fail-Closed Engineering** across all files touched by the active work item.

> **Reference (load on demand):** [references/polyglot-silent-failures.md](references/polyglot-silent-failures.md) (Python, TS/JS, Go, Rust, Java/Kotlin, SQL transactions, async queues/DLQs).

1. **Swallowed Exceptions (Python):** Flag `except Exception: pass`, bare `except:`, or broad `contextlib.suppress(...)` without structured logging or typed re-raise; reject returning `None` / `{}` on unexpected failures unless modeled in `02-tech-spec.md`.
2. **Swallowed Rejections (TypeScript/JS):** Flag `.catch(() => {})`, empty `catch (err) {}`, floating promises, or silent early `return;` on malformed payloads without error state or logs.
3. **Polyglot, SQL & Async Queues:** Load [references/polyglot-silent-failures.md](references/polyglot-silent-failures.md) for Go (`_ = err`), Rust (`let _ =`, `unwrap_or_default()` on I/O), Java/Kotlin (empty `catch`), SQL missing `ROLLBACK`, and consumers calling `ack` without DLQ.
4. **Unauthorized Fallbacks (`morluto/rea` Fail-Closed):** Failing dependencies, storage, auth, or render contexts must transition to an explicit observable error state from `01-spec.md`.
