# Plan de Tareas (DAG): `FWK-014` `Gate 6` (`REL-vX.Y.Z`), Motor de Release Readiness (`sdd_release.py`) y `CHANGELOG.md` Determinista

- **ID:** `FWK-014-gate6-release-readiness`
- **Estado:** `Approved`
- **Gate 3 Sign-off:** `- [x] **Gate 3 Approved (Human Sign-off):** Plan DAG por bloques, write-sets disjuntos y comandos de verificación DoD aprobados (Authorized by PO on 2026-11-17T11:01:37+01:00).`

## Grafo DAG por Bloques de Ejecución

### Bloque A: Motor Release Readiness y Normativa `Gate 6` [PARALLEL: BLOCK_A]

- [ ] `T14.1` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Implementar `scripts/sdd_release.py` (`<= 500L`, stdlib-only) con `normalize_release_version`, `prepare_release`, `collect_release_items` + `update_changelog` idempotente, `parse_gate6_approval` anti-spoofing, `check_open_work_items`, `run_release_preflight` (`start`/`finish`) y CLI `prepare|changelog|verify` (`--format text|json`).
  - *Archivos exactos*: `scripts/sdd_release.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.1 (`RF-1402`, `RF-1403`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_release.py --help`

- [ ] `T14.2` [`@devops`] `[PARALLEL: BLOCK_A]`: Formalizar `Gate 6` (`REL-vX.Y.Z`) en `specs/SDD_FRAMEWORK.md` (§3 y §4), crear `specs/templates/08-release-readiness.template.md` fuera de `.agents/` y añadir el workflow compacto `.agents/workflows/gate6-release.md`.
  - *Archivos exactos*: `specs/SDD_FRAMEWORK.md`, `specs/templates/08-release-readiness.template.md`, `.agents/workflows/gate6-release.md`
  - *Contrato de referencia*: `02-tech-spec.md` §1.4 (`RF-1401`)
  - *Comando de verificación DoD*: `uv run python .agents/scripts/sdd_healthcheck.py`

### Bloque B: Integración CLI y Preflight en `sdd_git.py` [PARALLEL: BLOCK_B] [Depende de: T14.1]

- [ ] `T14.3` [`@back-engineer`] `[PARALLEL: BLOCK_B]` `[Depende de: T14.1]`: Registrar el subcomando `release` en `DISPATCH_MAP` y `print_help()` de `scripts/sdd_cli.py` (`<= 500L`).
  - *Archivos exactos*: `scripts/sdd_cli.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.2 (`RF-1402`, `RF-1403`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py --help`

- [ ] `T14.4` [`@back-engineer`] `[PARALLEL: BLOCK_B]` `[Depende de: T14.1]`: Integrar `_run_release_preflight` *fail-closed* en `cmd_release_start` (`stage="start"`) y `cmd_release_finish` (`stage="finish"`) dentro de `scripts/sdd_git.py` manteniendo `<= 500L`.
  - *Archivos exactos*: `scripts/sdd_git.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.3 (`RF-1404`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_git.py --help`

### Bloque C: Pruebas Offline y Validación Integral [SEQUENTIAL: AFTER BLOCK_B]

- [ ] `T14.5` [`@qa-tester`] `[SEQUENTIAL: AFTER BLOCK_B]`: Crear `tests/test_sdd_release.py` (`<= 500L`) cubriendo `CA-1401..CA-1404`, aislar los tests previos de mecánica pura de worktree/PR en `tests/test_sdd_git_concurrency.py` si procede, verificar techo `<= 500L` / presupuesto `.agents/ < 25k` tokens y ejecutar la suite completa en verde (`>= 138` tests).
  - *Archivos exactos*: `tests/test_sdd_release.py`, `tests/test_sdd_git_concurrency.py`
  - *Contrato de referencia*: `02-tech-spec.md` §2 (`CA-1401`..`CA-1404`)
  - *Comando de verificación DoD*: `uv run python -m unittest discover -s tests -q`

### Bloque D: Documentación Viva 0DD y Cierre Gate 5 [SEQUENTIAL: AFTER T14.5]

- [ ] `T14.6` [`@documentator`] `[SEQUENTIAL: AFTER T14.5]`: Actualizar `docs/es/README.md`, `docs/en/README.md`, `docs/knowledge/{API_CATALOG,SYSTEM_TOPOLOGY,ADRS}.md` (`ADR-012`) y `docs/traceability/TRACEABILITY-MATRIX.md`, marcar `FWK-014` y `RFC-007` como `Done` en `.sdd/framework/BACKLOG.md`, reiniciar `.agents/ACTIVE_STATE.md` / `active_work_item.json` a `IDLE` y sincronizar la rama `feat/fwk-014-gate6-release-readiness` (`RN-SDD-0DD`, `RN-SDD-BRANCH-SYNC`).
  - *Archivos exactos*: `docs/es/README.md`, `docs/en/README.md`, `docs/knowledge/API_CATALOG.md`, `docs/knowledge/SYSTEM_TOPOLOGY.md`, `docs/knowledge/ADRS.md`, `docs/traceability/TRACEABILITY-MATRIX.md`, `.sdd/framework/BACKLOG.md`
  - *Contrato de referencia*: `AGENTS.md` (`RN-SDD-0DD`, `RN-SDD-BRANCH-SYNC`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py ci-verify --mode framework`

<!-- sdd:gate-seal gate=3 sha256=b8d1ab1b251c9506ef08bfb2b2164c10dbe1587a7bce45c5333621444334761f -->
