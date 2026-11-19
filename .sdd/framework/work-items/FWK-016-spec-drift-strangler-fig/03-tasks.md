# Plan de Tareas (DAG): `FWK-016` Detector de *Spec Drift*, Zonas *Strangler Fig* y Baseline Retroactiva Ligera

- **ID:** `FWK-016-spec-drift-strangler-fig`
- **Estado:** `Approved`
- **Gate 3 Sign-off:** `[x] Gate 3 Approved (Human Sign-off)` *(Aprobado explícitamente por el usuario en chat)*

## Grafo DAG por Bloques de Ejecución

### Bloque A: Ownership *Strangler Fig*, Sellos Baseline y CLI [PARALLEL: BLOCK_A]

- [ ] `T16.1` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Extender `scripts/sdd_ownership.py` (`<= 500L`) con `governance` (`governed` | `legacy-readonly`), `resolve_path_zone`, `derive_candidate_roots` y soporte de raíces personalizadas en `validate_repo_coverage`.
  - *Archivos exactos*: `scripts/sdd_ownership.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.1 (`RF-1601`)
  - *Comando de verificación DoD*: `uv run python -m unittest tests.test_sdd_ownership_dag -q`

- [ ] `T16.2` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Añadir detección y validación de `Origin: brownfield-mined` (`is_brownfield_mined_baseline`, `validate_brownfield_baseline_docs`) y sellado/verificación Gates 1..2 sin `03-tasks.md` en `scripts/sdd_gate_seal.py` (`<= 500L`).
  - *Archivos exactos*: `scripts/sdd_gate_seal.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.3 (`RF-1602`)
  - *Comando de verificación DoD*: `uv run python -m unittest tests.test_sdd_l5_perfection -q`

- [ ] `T16.3` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Registrar el subcomando `drift` en `DISPATCH_MAP` y `print_help()` de `scripts/sdd_cli.py` (`<= 500L`).
  - *Archivos exactos*: `scripts/sdd_cli.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.5 (`RF-1604`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py --help`

### Bloque B: Motor `sdd_drift.py` y Guardias Fail-Closed [PARALLEL: BLOCK_B]

- [ ] `T16.4` [`@back-engineer`] `[PARALLEL: BLOCK_B]` `[After: T16.1, T16.2, T16.3]`: Implementar `scripts/sdd_drift.py` (`<= 500L`, stdlib-only) con cruce determinista offline de `SRC-###` y `TRACEABILITY-MATRIX.md` contra `sdd_repo_map.py`, `sdd_ownership.py` y `git diff`/`status`, flags `--repo-root`, `--base-ref`, `--strict`, `--format text|json`.
  - *Archivos exactos*: `scripts/sdd_drift.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.4 (`RF-1603`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_drift.py --help`

- [ ] `T16.5` [`@back-engineer`] `[PARALLEL: BLOCK_B]` `[After: T16.1, T16.2, T16.3]`: Actualizar `.agents/scripts/sdd_code_gate_guard.py` (`<= 500L`) para proteger raíces brownfield/personalizadas de `sdd:ownership-map` y denegar *fail-closed* ediciones sobre zonas `legacy-readonly`.
  - *Archivos exactos*: `.agents/scripts/sdd_code_gate_guard.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.2 (`RF-1601`)
  - *Comando de verificación DoD*: `uv run python -m unittest tests.test_sdd_security_guards -q`

- [ ] `T16.6` [`@back-engineer`] `[PARALLEL: BLOCK_B]` `[After: T16.1, T16.2, T16.3]`: Actualizar `.agents/scripts/sdd_healthcheck.py` (`<= 500L`) para validar baselines `brownfield-mined` (`01-spec.md` + `02-tech-spec.md` con Gate 1 y Gate 2 firmados) sin eximir features normales ni sign-offs humanos.
  - *Archivos exactos*: `.agents/scripts/sdd_healthcheck.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.3 (`RF-1602`)
  - *Comando de verificación DoD*: `uv run python .agents/scripts/sdd_healthcheck.py`

### Bloque C: Integración CI y Pruebas Offline [SEQUENTIAL: AFTER BLOCK_B]

- [ ] `T16.7` [`@back-engineer`] `[SEQUENTIAL: AFTER T16.4, T16.5, T16.6]`: Integrar `check_spec_drift` en `run_ci_verify` dentro de `scripts/sdd_ci.py` (`<= 500L`), retornando `SKIPPED_NO_APPLICABLE` en modo `framework`.
  - *Archivos exactos*: `scripts/sdd_ci.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.5 (`RF-1604`)
  - *Comando de verificación DoD*: `uv run python -m unittest tests.test_sdd_ci -q`

- [ ] `T16.8` [`@qa-tester`] `[SEQUENTIAL: AFTER T16.7]`: Crear `tests/test_sdd_drift.py` (`<= 500L`) cubriendo `CA-1601..CA-1604`, verificar presupuesto `< 25k` tokens en `.agents/` y techo `<= 500L` en todos los `.py`, y ejecutar la suite completa + `sdd ci-verify --mode framework`.
  - *Archivos exactos*: `tests/test_sdd_drift.py`
  - *Contrato de referencia*: `02-tech-spec.md` §2 (`CA-1601`..`CA-1604`)
  - *Comando de verificación DoD*: `uv run python -m unittest discover -s tests -q`

### Bloque D: Documentación Viva 0DD y Cierre Gate 5 [SEQUENTIAL: AFTER T16.8]

- [ ] `T16.9` [`@documentator`] `[SEQUENTIAL: AFTER T16.8]`: Actualizar `docs/es/README.md`, `docs/en/README.md`, `docs/knowledge/{API_CATALOG,DATA_MODELS,SYSTEM_TOPOLOGY,ADRS}.md` (`ADR-014`), `docs/traceability/TRACEABILITY-MATRIX.md`, marcar `FWK-016` como `Done` y `RFC-008` como `Implementado / Done` en `.sdd/framework/BACKLOG.md`, y sincronizar la rama `feat/fwk-016-spec-drift-strangler-fig` hacia `develop` (`RN-SDD-0DD`, `RN-SDD-BRANCH-SYNC`).
  - *Archivos exactos*: `docs/es/README.md`, `docs/en/README.md`, `docs/knowledge/API_CATALOG.md`, `docs/knowledge/DATA_MODELS.md`, `docs/knowledge/SYSTEM_TOPOLOGY.md`, `docs/knowledge/ADRS.md`, `docs/traceability/TRACEABILITY-MATRIX.md`, `.sdd/framework/BACKLOG.md`
  - *Contrato de referencia*: `AGENTS.md` (`RN-SDD-0DD`, `RN-SDD-BRANCH-SYNC`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py ci-verify --mode framework`
