---
name: sdd-silent-failure-audit
description: Hunts swallowed exceptions, empty catch blocks, silent fallback defaults, and unpropagated errors in Python and TypeScript code. Inspired by affaan-m/ecc (silent-failure-hunter) and morluto/rea (Fail-Closed Engineering).
---

# Skill: `sdd-silent-failure-audit`

Activate this skill before Gate 5 closure to ensure the implementation adheres to **Fail-Closed Engineering** and never masks runtime or contract failures silently.

## 1. Automated & Manual Anti-Pattern Scan
Inspect all files created or modified by the current `FEAT-XXX`, `CR-XXX`, or `BUG-XXX` for:

1. **Swallowed Exceptions in Python (`backend/src/`):**
   - `except Exception: pass` or bare `except:` without structured logging (`structlog`/`logging`) or domain error re-raising.
   - Returning `None` or `{}` inside an `except` block when the contract does not explicitly model an optional/fallback state in `02-tech-spec.md`.
2. **Swallowed Rejections & Silent Catches in TypeScript (`frontend/src/`):**
   - `.catch(() => {})` or `catch (err) { /* ignore */ }` without updating error state or emitting a diagnostic telemetry event.
   - Silent early `return;` when receiving malformed WebSocket/SSE or Event Bus payloads without recording a warning or error counter.
3. **Unauthorized Fallback Masquerading (`morluto/rea` Fail-Closed Rule):**
   - Verify that if a required dependency, WebGL2 context, OIDC provider, or database connection fails, the system transitions to an explicit, observable degraded/error state defined in `01-spec.md` rather than pretending the operation succeeded.
