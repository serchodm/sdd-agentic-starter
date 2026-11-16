# Plan de Tareas (DAG): `FWK-012` Alineación de Coherencia v1.1.1

- **ID:** `FWK-012-coherence-alignment`
- **Estado:** `Done`
- **Gate 3 Sign-off:** `[x] Gate 3 Approved (Authorized by PO on 2026-11-16T11:46:29+01:00)`

## Grafo DAG por Bloques de Ejecución

### Bloque A: CLI, Plantillas, `spec-miner` SDD y `release-finish` [PARALLEL: BLOCK_A]

- [x] `T12.1` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Implementar subcomando `work-item` (`show`, `set`) en `scripts/sdd_cli.py` sin autoaprobar Gates 1..3 y corregir referencias CLI en `README.md` y `.agents/workflows/bug-fast-track.md`.
  - *Archivos exactos*: `scripts/sdd_cli.py`, `README.md`, `.agents/workflows/bug-fast-track.md`
  - *Contrato de referencia*: `02-tech-spec.md` §1.1 (`RF-1201`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py --help`

- [x] `T12.2` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Habilitar soporte `HOTFIX-*` en `sdd_code_gate_guard.py`, `sdd_immutable_feature_guard.py`, `sdd_gate_seal.py` y validar `HOTFIX-*` / `SPIKE-*` en `sdd_healthcheck.py` (`<= 500L`).
  - *Archivos exactos*: `.agents/scripts/sdd_code_gate_guard.py`, `.agents/scripts/sdd_immutable_feature_guard.py`, `scripts/sdd_gate_seal.py`, `.agents/scripts/sdd_healthcheck.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.2 (`RF-1202`)
  - *Comando de verificación DoD*: `uv run python .agents/scripts/sdd_healthcheck.py`

- [x] `T12.3` [`@documentator`] `[PARALLEL: BLOCK_A]`: Crear `specs/templates/06-spike-report.template.md` y `specs/templates/07-hotfix-fast-track.template.md`, y limpiar rutas legacy de `specs/SDD_FRAMEWORK.md §3`.
  - *Archivos exactos*: `specs/templates/06-spike-report.template.md`, `specs/templates/07-hotfix-fast-track.template.md`, `specs/SDD_FRAMEWORK.md`
  - *Contrato de referencia*: `02-tech-spec.md` §1.2 (`RF-1202`)
  - *Comando de verificación DoD*: `uv run python .agents/scripts/sdd_healthcheck.py`

- [x] `T12.4` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Adaptar `.sdd/catalog/specialists-optin/spec-miner.md` al formato SDD (`specs/features/` + `domains/`) y proteger `SDD_CUSTOMIZED_SPECIALISTS` en `scripts/sdd_catalog_import.py`.
  - *Archivos exactos*: `.sdd/catalog/specialists-optin/spec-miner.md`, `scripts/sdd_catalog_import.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.3 (`RF-1203`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_agent_generator.py --list`

- [x] `T12.5` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Actualizar `cmd_release_finish` y `cmd_hotfix_finish` en `scripts/sdd_git.py` a flujo PR-first por defecto con flag explícito `--local-merge`.
  - *Archivos exactos*: `scripts/sdd_git.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.4 (`RF-1204`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_git.py status`

### Bloque B: Batería de Tests y Auditorías Gate 4 [SEQUENTIAL: AFTER BLOCK_A]

- [x] `T12.6` [`@qa-tester`] `[SEQUENTIAL: AFTER BLOCK_A]`: Añadir pruebas deterministas para `work-item`, `spec-miner` preservado, `HOTFIX-*` / `SPIKE-*` y `release-finish` PR-first, manteniendo todos los `.py` en `<= 500L` y ejecutando la suite completa + auditorías.
  - *Archivos exactos*: `tests/test_sdd_governance.py`, `tests/test_sdd_security_guards.py`, `tests/test_sdd_git_concurrency.py`
  - *Contrato de referencia*: `02-tech-spec.md` §2
  - *Comando de verificación DoD*: `uv run python -m unittest discover -s tests -q`

### Bloque C: Cierre 0DD Gate 5 y Preparación Release v1.1.1 [SEQUENTIAL: AFTER T12.6]

- [x] `T12.7` [`@documentator`] `[SEQUENTIAL: AFTER T12.6]`: Actualizar documentación funcional (`docs/es/`, `docs/en/`), `docs/knowledge/{API_CATALOG,SYSTEM_TOPOLOGY,ADRS}.md`, `docs/traceability/TRACEABILITY-MATRIX.md`, cerrar `FWK-012` / `RFC-006` en `Done` y sincronizar la rama `feat/fwk-012-coherence-alignment` hacia PR en `develop` (y posterior `release/v1.1.1` hacia `main`).
  - *Archivos exactos*: `docs/traceability/TRACEABILITY-MATRIX.md`, `docs/knowledge/API_CATALOG.md`, `docs/knowledge/SYSTEM_TOPOLOGY.md`, `docs/knowledge/ADRS.md`, `.sdd/framework/BACKLOG.md`, `.sdd/framework/rfcs/RFC-006-coherence-and-catalog-alignment.md`
  - *Contrato de referencia*: `AGENTS.md` (`RN-SDD-0DD`, `RN-SDD-BRANCH-SYNC`)
  - *Comando de verificación DoD*: `uv run python .agents/scripts/sdd_healthcheck.py`

<!-- sdd:gate-seal gate=3 sha256=aa9dede25ef5a02c0b13a654eabc81be3bb9fe475b43631970257edf08d0f6bc -->
