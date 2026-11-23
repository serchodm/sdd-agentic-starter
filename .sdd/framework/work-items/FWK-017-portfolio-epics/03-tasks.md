# Plan de Tareas (DAG): `FWK-017` Portfolio, Épicas (`EPIC-XXX`), Roadmap y Dependencias entre Features

- **ID:** `FWK-017-portfolio-epics`
- **Estado:** `Approved`
- **Gate 3 Sign-off:** `[x] Gate 3 Approved (Authorized by PO on 2026-11-21T01:17:55+01:00 — "Perfecto")`

## Grafo DAG por Bloques de Ejecución

### Bloque A: Plantilla, Motor Portfolio y CLI [PARALLEL: BLOCK_A]

- [ ] `T17.1` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Crear la plantilla `specs/templates/09-epic-roadmap.template.md` (`0` bytes en `.agents/`), actualizar `specs/SDD_FRAMEWORK.md §3` con `specs/epics/` y `09-epic-roadmap.template.md`, e implementar `scripts/sdd_portfolio.py` (`<= 500L`, stdlib-only) con `init`, `status`, `graph`, `validate`, cálculo *MoSCoW*/*RICE*, DAG de dependencias, detección de ciclos, ruta crítica y `run_portfolio_ci_check`.
  - *Archivos exactos*: `specs/templates/09-epic-roadmap.template.md`, `specs/SDD_FRAMEWORK.md`, `scripts/sdd_portfolio.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.1, §1.2 (`RF-1701`, `RF-1702`, `RF-1703`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_portfolio.py --help`

- [ ] `T17.2` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Registrar `portfolio` en `DISPATCH_MAP` y `print_help()` de `scripts/sdd_cli.py` (`<= 500L`).
  - *Archivos exactos*: `scripts/sdd_cli.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.3 (`RF-1704`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py --help`

### Bloque B: Integración CI y Pruebas Offline [SEQUENTIAL: AFTER BLOCK_A]

- [ ] `T17.3` [`@back-engineer`] `[SEQUENTIAL: AFTER BLOCK_A]`: Integrar `check_portfolio` (`run_portfolio_ci_check`) en `scripts/sdd_ci.py` respetando estrictamente el límite modular `<= 500L` y devolviendo `SKIPPED_NO_APPLICABLE` cuando no existan Épicas ni dependencias.
  - *Archivos exactos*: `scripts/sdd_ci.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.4 (`RF-1704`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py ci-verify --mode framework --skip-tests --format text`

- [ ] `T17.4` [`@qa-tester`] `[SEQUENTIAL: AFTER T17.3]`: Crear `tests/test_sdd_portfolio.py` (`<= 500L`) cubriendo `CA-1701..CA-1704`, verificar presupuesto `< 25k` tokens en `.agents/` y límite `<= 500L` en todos los `.py`, y ejecutar la suite completa offline + `sdd ci-verify --mode framework`.
  - *Archivos exactos*: `tests/test_sdd_portfolio.py`
  - *Contrato de referencia*: `02-tech-spec.md` §2 (`CA-1701`..`CA-1704`)
  - *Comando de verificación DoD*: `uv run python -m unittest discover -s tests -q`

### Bloque C: Documentación Viva 0DD y Cierre Gate 5 [SEQUENTIAL: AFTER T17.4]

- [ ] `T17.5` [`@documentator`] `[SEQUENTIAL: AFTER T17.4]`: Actualizar `docs/es/`, `docs/en/`, `docs/knowledge/{API_CATALOG,DATA_MODELS,SYSTEM_TOPOLOGY,ADRS}.md` (`ADR-015`) y `docs/traceability/TRACEABILITY-MATRIX.md`, marcar `FWK-017` como `Done` en `.sdd/framework/BACKLOG.md` y sincronizar la rama `feat/fwk-017-portfolio-epics` hacia `develop` (`RN-SDD-0DD`, `RN-SDD-BRANCH-SYNC`).
  - *Archivos exactos*: `docs/es/README.md`, `docs/en/README.md`, `docs/knowledge/API_CATALOG.md`, `docs/knowledge/DATA_MODELS.md`, `docs/knowledge/SYSTEM_TOPOLOGY.md`, `docs/knowledge/ADRS.md`, `docs/traceability/TRACEABILITY-MATRIX.md`, `.sdd/framework/BACKLOG.md`
  - *Contrato de referencia*: `AGENTS.md` (`RN-SDD-0DD`, `RN-SDD-BRANCH-SYNC`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py ci-verify --mode framework`

- [x] **Gate 3 Approved (Human Sign-off):** Revisado y validado por Stakeholder Humano (`2026-11-21T01:17:55+01:00`).

<!-- sdd:gate-seal gate=3 sha256=92d63a2d73b43d1d9e0fec315a9f324af9f563523e22f2429f8b29a2e604b50b -->
