# SDD Starter — Active Session Pointer (Managed by @orchestrator)
- **Timestamp:** 2026-11-13 19:37
- **Active Work Item:** `IDLE (No Active Work Item)`
- **Active Branch:** `feat/fwk-004-gate-terminology-unification`
- **Spec Folder Path:** `N/A`
- **Current Gate:** `IDLE`
- **Recommended Model Tier:** Fast / Balanced Execution
- **Last Completed Milestone:** `FWK-004-gate-terminology-unification` completado al 100% (Gates 1–5 superados, 67/67 tests passing, Healthcheck en verde, Living Docs 0DD cerrados con ADR-005, MOD-003 y TRACEABILITY-MATRIX actualizada).
- **Next Execution Target:** `IDLE` — Esperando asignación de nuevo Work Item o inicio de bootstrap de stack (Gate S0 en `specs/STACK.md`).
- **Mandatory Context Files (MAX 4 FILES):**
  1. `AGENTS.md`
  2. `specs/STACK.md`
  3. `specs/BACKLOG.md`
  4. `.agents/ACTIVE_STATE.md`
- **Critical Technical Decisions / Snapshot:**
  - `RFC-002` aceptado y `FWK-004` en estado `Done`.
  - Nomenclatura unificada: `Gate S0` (Stack Lock) y `Gate 0..5` (Work Items) con `Sub-Gate 2V` para validación visual.
  - Dual-accept obligatorio (`Gate S0`/`Gate 00`, `stack_approved`/`gate00_approved`, `Done`/`Completado`) con fail-closed ante contradicciones.
  - Techo de modularidad `<= 500` líneas respetado en todos los componentes del framework.
  - Suite de regresión offline: 67/67 tests en verde (`uv run python -m unittest discover -s tests -q`).
