# Plan de Tareas (DAG): `FWK-011` Portabilidad POSIX y Determinismo Temporal CI

- **ID:** `FWK-011-ci-posix-time-determinism`
- **Gate 3 Sign-off:** `[x] Gate 3 Approved (Authorized by PO on 2026-11-16T00:56:38+01:00)`

## Grafo DAG
- [x] `T11.1` [`@back-engineer`] `[PARALLEL: BLOCK_F1]`: Rechazar rutas con unidad Windows en entorno POSIX dentro de `resolve_repo_relative_path` y `resolve_target_context` en `.agents/scripts/sdd_immutable_feature_guard.py`.
  - *Archivos exactos*: `.agents/scripts/sdd_immutable_feature_guard.py`
  - *Comando de verificación DoD*: `uv run python -m unittest tests.test_sdd_security_guards -q`
- [x] `T11.2` [`@qa-tester`] `[PARALLEL: BLOCK_F1]`: Hacer relativos a `now` los timestamps de `test_sdd_instincts_temporal_decay` en `tests/test_sdd_governance.py`.
  - *Archivos exactos*: `tests/test_sdd_governance.py`
  - *Comando de verificación DoD*: `uv run python -m unittest tests.test_sdd_governance -q`
- [x] `T11.3` [`@qa-tester`] `[SEQUENTIAL: AFTER BLOCK_F1]`: Añadir verificación de regresión POSIX en `tests/test_sdd_security_guards.py` (`<= 500L`) y ejecutar la suite completa (`>= 120` tests) + `sdd_healthcheck.py` + `verify_architecture_boundaries.py`.
  - *Archivos exactos*: `tests/test_sdd_security_guards.py`
  - *Comando de verificación DoD*: `uv run python -m unittest discover -s tests -q`
- [x] `T11.4` [`@documentator`] `[SEQUENTIAL: AFTER T11.3]`: Actualizar documentación 0DD (`docs/traceability/TRACEABILITY-MATRIX.md`, `docs/es/`, `docs/en/` si aplica), cerrar `FWK-011` / `RFC-005` en `Done` y sincronizar en `develop`.
  - *Archivos exactos*: `docs/traceability/TRACEABILITY-MATRIX.md`, `.sdd/framework/BACKLOG.md`, `.sdd/framework/rfcs/RFC-005-ci-posix-time-determinism.md`
  - *Comando de verificación DoD*: `uv run python .agents/scripts/sdd_healthcheck.py`

<!-- sdd:gate-seal gate=3 sha256=ab5ef919c934cef16aedf7f7e0d7414122f959040597633cf9c7be7ee3b27dcd -->
