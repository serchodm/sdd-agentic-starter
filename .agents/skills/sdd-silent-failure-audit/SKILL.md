---
name: sdd-silent-failure-audit
description: Hunts swallowed exceptions, empty catch blocks, silent fallback defaults, and unpropagated errors in Python and TypeScript code (affaan-m/ecc silent-failure-hunter & morluto/rea Fail-Closed).
---

# Skill: `sdd-silent-failure-audit`

Run before Gate 5 closure to enforce **Fail-Closed Engineering** across all files touched by the active work item:

1. **Swallowed Exceptions (Python):** Flag `except Exception: pass` or bare `except:` without structured logging or typed re-raise; reject returning `None` / `{}` on unexpected failures unless explicitly modeled in `02-tech-spec.md`.
2. **Swallowed Rejections (TypeScript/JS):** Flag `.catch(() => {})`, empty `catch (err) {}`, or silent early `return;` on malformed payloads without error state or diagnostic logs.
3. **Unauthorized Fallbacks (`morluto/rea` Fail-Closed):** Verify failing dependencies, storage, auth, or render contexts transition to an explicit observable error state from `01-spec.md` instead of masquerading success.
