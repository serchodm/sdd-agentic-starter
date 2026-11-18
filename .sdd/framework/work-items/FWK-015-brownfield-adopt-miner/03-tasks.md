# Plan de Tareas (DAG): `FWK-015` Adopción Brownfield y Workflow `@spec-miner`

- **ID:** `FWK-015-brownfield-adopt-miner`
- **Estado:** `Approved`
- **Gate 3 Sign-off:** `[x] Gate 3 Approved (Authorized by PO on 2026-11-17T17:25:03+01:00 — "Aprobados")`

## Grafo DAG por Bloques de Ejecución

### Bloque A: Motor Brownfield, CLI y Workflow [PARALLEL: BLOCK_A]

- [ ] `T15.1` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Implementar `scripts/sdd_brownfield.py` (`<= 500L`, stdlib-only) con descubrimiento determinista offline (`discover_brownfield_repo`), sanitización *fail-closed* de rutas y comandos (`split_safe_chained_command`), planificación `--dry-run` por defecto y aplicación `--apply` no destructiva de `specs/STACK.md` (`stack_approved: false`), `docs/knowledge/BROWNFIELD_INVENTORY.md` y `specs/BACKLOG.md`.
  - *Archivos exactos*: `scripts/sdd_brownfield.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.1 (`RF-1501`, `RF-1502`, `RF-1503`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_brownfield.py --help`

- [ ] `T15.2` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Registrar `adopt` en `DISPATCH_MAP` y `print_help()` de `scripts/sdd_cli.py` (`<= 500L`).
  - *Archivos exactos*: `scripts/sdd_cli.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.2 (`RF-1504`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py --help`

- [ ] `T15.3` [`@orchestrator`] `[PARALLEL: BLOCK_A]`: Crear el workflow compacto `.agents/workflows/brownfield-adopt.md` (`<= 25L`) enlazando `sdd adopt` -> `Gate S0` -> `sdd generate --materialize` -> `sdd repo-map` -> `@spec-miner`.
  - *Archivos exactos*: `.agents/workflows/brownfield-adopt.md`
  - *Contrato de referencia*: `02-tech-spec.md` §1.3 (`RF-1504`)
  - *Comando de verificación DoD*: `uv run python .agents/scripts/sdd_healthcheck.py`

### Bloque B: Pruebas Offline y Verificación Integral [SEQUENTIAL: AFTER BLOCK_A]

- [ ] `T15.4` [`@qa-tester`] `[SEQUENTIAL: AFTER BLOCK_A]`: Crear `tests/test_sdd_brownfield.py` (`<= 500L`) cubriendo `CA-1501..CA-1504`, verificar compatibilidad de los bloques generados con `sdd_pack_registry.py` y `sdd_ownership.py`, comprobar presupuesto `< 25k` tokens en `.agents/` y ejecutar la suite completa + `sdd ci-verify --mode framework`.
  - *Archivos exactos*: `tests/test_sdd_brownfield.py`
  - *Contrato de referencia*: `02-tech-spec.md` §2 (`CA-1501`..`CA-1504`)
  - *Comando de verificación DoD*: `uv run python -m unittest discover -s tests -q`

### Bloque C: Documentación Viva 0DD y Cierre Gate 5 [SEQUENTIAL: AFTER T15.4]

- [ ] `T15.5` [`@documentator`] `[SEQUENTIAL: AFTER T15.4]`: Actualizar `docs/es/`, `docs/en/`, `docs/knowledge/{API_CATALOG,SYSTEM_TOPOLOGY,ADRS}.md` (`ADR-013`) y `docs/traceability/TRACEABILITY-MATRIX.md`, marcar `FWK-015` como `Done` en `.sdd/framework/BACKLOG.md` y sincronizar la rama `feat/fwk-015-brownfield-adopt-miner` hacia `develop` (`RN-SDD-0DD`, `RN-SDD-BRANCH-SYNC`).
  - *Archivos exactos*: `docs/es/README.md`, `docs/en/README.md`, `docs/knowledge/API_CATALOG.md`, `docs/knowledge/SYSTEM_TOPOLOGY.md`, `docs/knowledge/ADRS.md`, `docs/traceability/TRACEABILITY-MATRIX.md`, `.sdd/framework/BACKLOG.md`
  - *Contrato de referencia*: `AGENTS.md` (`RN-SDD-0DD`, `RN-SDD-BRANCH-SYNC`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py ci-verify --mode framework`

<!-- sdd:gate-seal gate=3 sha256=ad3bf8f6cc27c87af69f696f3dda156b49b9a57978b0de58cf345f3988166326 -->
