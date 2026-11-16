# Plan de Tareas (DAG): `FWK-013` Motor CI-Agnóstico

- **ID:** `FWK-013-ci-agnostic-verify`
- **Estado:** `Approved`
- **Gate 3 Sign-off:** `[x] Gate 3 Approved (Authorized by PO on 2026-11-16T18:13:32+01:00)`

## Grafo DAG por Bloques de Ejecución

### Bloque A: Motor CI, Dispatcher CLI y Plantillas Multi-CI [PARALLEL: BLOCK_A]

- [ ] `T13.1` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Implementar `scripts/sdd_ci.py` (`<= 500L`, stdlib-only) con `detect_ci_mode`, checks unificados (`hooks.json`, `healthcheck`, `0DD`, `boundaries`, `catalog/lock`, `dags`, `gate_seals`, `git/instincts`, `tokens`), runner de tests framework (`--min-tests`) y ejecutor seguro `shell=False` de `STACK.md §2.5` (`--run-stack` / `--run-stack-if-approved`), con salida `text|json`.
  - *Archivos exactos*: `scripts/sdd_ci.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.1 (`RF-1301`, `RF-1302`, `RF-1303`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_ci.py --help`

- [ ] `T13.2` [`@back-engineer`] `[PARALLEL: BLOCK_A]`: Registrar `ci-verify` en `DISPATCH_MAP` y en `print_help()` de `scripts/sdd_cli.py` (`<= 500L`).
  - *Archivos exactos*: `scripts/sdd_cli.py`
  - *Contrato de referencia*: `02-tech-spec.md` §1.2 (`RF-1301`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py --help`

- [ ] `T13.3` [`@devops`] `[PARALLEL: BLOCK_A]`: Simplificar `.github/workflows/ci.yml` eliminando bloques Python inline para delegar en `scripts/sdd_cli.py ci-verify --mode auto --run-stack-if-approved` y crear las plantillas CI-agnósticas en `specs/templates/ci/` (`README.md`, `gitlab-ci.yml`, `bitbucket-pipelines.yml`, `ci-verify.sh`).
  - *Archivos exactos*: `.github/workflows/ci.yml`, `specs/templates/ci/README.md`, `specs/templates/ci/gitlab-ci.yml`, `specs/templates/ci/bitbucket-pipelines.yml`, `specs/templates/ci/ci-verify.sh`
  - *Contrato de referencia*: `02-tech-spec.md` §1.3 (`RF-1304`)
  - *Comando de verificación DoD*: `uv run python .agents/scripts/sdd_healthcheck.py`

### Bloque B: Pruebas Offline y Validación Integral [SEQUENTIAL: AFTER BLOCK_A]

- [ ] `T13.4` [`@qa-tester`] `[SEQUENTIAL: AFTER BLOCK_A]`: Crear `tests/test_sdd_ci.py` (`<= 500L`) cubriendo `CA-1301..CA-1304`, validar `sdd_cli.py ci-verify --mode framework --format json`, comprobar el techo modular `<= 500L` y ejecutar toda la suite determinista (`>= 128` tests en verde).
  - *Archivos exactos*: `tests/test_sdd_ci.py`
  - *Contrato de referencia*: `02-tech-spec.md` §2 (`CA-1301`..`CA-1304`)
  - *Comando de verificación DoD*: `uv run python -m unittest discover -s tests -q`

### Bloque C: Documentación Viva 0DD y Cierre Gate 5 [SEQUENTIAL: AFTER T13.4]

- [ ] `T13.5` [`@documentator`] `[SEQUENTIAL: AFTER T13.4]`: Actualizar `docs/es/`, `docs/en/`, `docs/knowledge/{API_CATALOG,SYSTEM_TOPOLOGY,ADRS}.md` (`ADR-011`) y `docs/traceability/TRACEABILITY-MATRIX.md`, marcar `FWK-013` como `Done` en `.sdd/framework/BACKLOG.md` y sincronizar la rama `feat/fwk-013-ci-agnostic-verify` hacia `develop` (`RN-SDD-0DD`, `RN-SDD-BRANCH-SYNC`).
  - *Archivos exactos*: `docs/es/README.md`, `docs/en/README.md`, `docs/knowledge/API_CATALOG.md`, `docs/knowledge/SYSTEM_TOPOLOGY.md`, `docs/knowledge/ADRS.md`, `docs/traceability/TRACEABILITY-MATRIX.md`, `.sdd/framework/BACKLOG.md`
  - *Contrato de referencia*: `AGENTS.md` (`RN-SDD-0DD`, `RN-SDD-BRANCH-SYNC`)
  - *Comando de verificación DoD*: `uv run python scripts/sdd_cli.py ci-verify --mode framework`

<!-- sdd:gate-seal gate=3 sha256=b8c0eff0cae43b88bd45fae9827bf0d46fc4d813115bf6078a6e128c79132285 -->
