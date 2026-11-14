# SDD Starter — Active Session Pointer (Managed by @orchestrator)
- **Timestamp:** 2026-11-14 22:38
- **Active Work Item:** `IDLE (No Active Work Item)`
- **Active Branch:** `develop`
- **Spec Folder Path:** `N/A`
- **Current Gate:** `IDLE`
- **Active Worktrees:** None
- **Recommended Model Tier:** Fast / Balanced Execution
- **Last Completed Milestone:** `RFC-003` (`FWK-005`..`FWK-009`) completado al 100% en `develop` (Gates 1–5 cerrados en `Done`, `115/115` tests en verde a través de `10` módulos `<= 500` líneas, `sdd_healthcheck.py` y `verify_architecture_boundaries.py` sin errores, contexto Markdown en `.agents/` reducido a `71.9 KB` / `~18.0k` tokens `< 25k` budget, y Living Docs 0DD + `TRACEABILITY-MATRIX.md` + `ADR-006`..`ADR-008` sincronizados).
- **Next Execution Target:** `IDLE` — Esperando asignación de nuevo Work Item o inicio de bootstrap de stack (`Gate S0` en `specs/STACK.md`).
- **Mandatory Context Files (MAX 4 FILES):**
  1. `AGENTS.md`
  2. `specs/STACK.md`
  3. `specs/BACKLOG.md`
  4. `.agents/ACTIVE_STATE.md`
- **Critical Technical Decisions / Snapshot:**
  - `RFC-001`, `RFC-002` y `RFC-003` implementados; `FWK-001`..`FWK-009` en estado `Done`.
  - Seguridad P0 *fail-closed* (`FWK-005`): `.agents/hooks.json` sin BOM UTF-8, guardias pre-tool y Git hooks *fail-closed*, `sdd_trim_exec.py` con `shell=False`, contención estricta de `WorktreeManager.remove` bajo `worktrees_root` y eliminación de `SDD_FORCE_MAIN_PUSH`.
  - Compilador declarativo y DAG (`FWK-006`): `sdd:ownership-map` (`scripts/sdd_ownership.py`) + enforcement AST de `forbid_imports`, generador transaccional (`scripts/sdd_generator_tx.py`) con `content_digest` y `--verify`, y planificador/validador `scripts/sdd_dag.py` (`--verify`/`--plan`).
  - Slimming `< 25k` tokens y DX (`FWK-007`): `9` agentes base activos en `.agents/agents/`, `19` especialistas opt-in en `.sdd/catalog/specialists-optin/`, `12` arquetipos canónicos únicos en `.sdd/catalog/archetypes/`, eliminación de `.agents/archetypes/`, workflow `/bug-fast-track` (`BUG-XXX`) y directorio `domains/` bajo demanda (excluyendo el acoplamiento rígido de `AUD-020`).
  - Concurrencia multi-worktree y modularidad (`FWK-008` & `FWK-009`): estado aislado en `.agents/worktree_states/`, reserva atómica de puertos en `ports_registry.json`, `sdd_sync.py` transaccional con `--dry-run`/`--force`, `pyproject.toml` PEP 621 y techo estricto `<= 500` líneas en todos los módulos Python (`115/115` tests en verde).
