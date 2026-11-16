# Spec Funcional: Motor CI-Agnóstico (`FWK-013`)

- **ID:** `FWK-013-ci-agnostic-verify`
- **RFC:** [`RFC-007`](../../rfcs/RFC-007-release-ops-ci-agnostic.md) (`Aceptado`)
- **Estado:** `Approved`
- **Gate 1 Sign-off:** `[x] Gate 1 Approved (Authorized by PO on 2026-11-16T18:13:32+01:00)`

## 1. Resumen y Alcance
Extraer la lógica de verificación embebida hoy en `.github/workflows/ci.yml` hacia un motor CI-agnóstico y portable (`scripts/sdd_ci.py`, invocable como `./sdd ci-verify`), capaz de ejecutarse de forma idéntica en local y en cualquier proveedor CI (GitHub Actions, GitLab CI, Bitbucket Pipelines o shell estándar), diferenciando automáticamente entre el repositorio starter/framework y un proyecto derivado con `Gate S0` aprobado.

- **In-Scope:**
  - `scripts/sdd_ci.py` con ejecución unificada de invariantes SDD (`hooks.json` sin BOM ni escapes, `sdd_healthcheck`, cumplimiento 0DD bilingüe + trazabilidad, `verify_architecture_boundaries`, `sdd_agent_generator --list/--verify`, `sdd_dag --verify`, `sdd_gate_seal --verify`, `sdd_git status`, `sdd_instincts list`, `sdd_tokens_validator --allow-missing`) y pruebas de framework o de stack según el modo (`auto|framework|project`).
  - Integración del subcomando `ci-verify` en `scripts/sdd_cli.py` con soporte de `--mode`, `--run-stack`, `--min-tests` y `--format text|json`.
  - Ejecución segura (`shell=False`) de los comandos declarados en `specs/STACK.md §2.5` (`yaml sdd:verification-commands`) únicamente cuando `--run-stack` esté activo y `Gate S0` esté aprobado.
  - Simplificación de `.github/workflows/ci.yml` para delegar en `scripts/sdd_cli.py ci-verify` y creación de plantillas portables en `specs/templates/ci/` (GitLab CI, Bitbucket Pipelines y script POSIX/PowerShell).
- **Out-of-Scope:**
  - Formalización de `Gate 6`, plantilla `08-release-readiness.template.md`, `scripts/sdd_release.py`, `CHANGELOG.md` y preflight en `release-start`/`release-finish` (diferidos a `FWK-014`).
  - Onboarding brownfield `/onboard` (`v1.3.0`) y métricas FinOps (`v1.4.0`).

## 2. Requisitos (EARS)
- `RF-1301` (**Motor CI unificado y portable `sdd ci-verify`**): El sistema deberá proveer `scripts/sdd_ci.py` (expuesto vía `scripts/sdd_cli.py ci-verify`) para ejecutar de forma determinista y sin dependencias externas todas las comprobaciones de gobernanza SDD actualmente dispersas en `.github/workflows/ci.yml`, devolviendo código `0` solo cuando todos los checks requeridos superen la verificación y emitiendo reporte estructurado en `--format text` o `--format json`.
- `RF-1302` (**Detección automática de contexto `framework` vs `project`**): CUANDO `ci-verify` se ejecute con `--mode auto`, deberá resolver `framework` únicamente si `Gate S0` no está aprobado y existen los artefactos internos del starter (`.sdd/framework/BACKLOG.md`, `.sdd/framework/work-items/` y `tests/test_sdd_governance.py`), exigiendo entonces la suite completa del starter con umbral mínimo de regresión (`>= 120` tests por defecto o `--min-tests`); en cualquier proyecto derivado (`Gate S0` aprobado o sin `tests/test_sdd_governance.py`), deberá resolver `project` sin imponer el umbral `>= 120` de tests del starter.
- `RF-1303` (**Ejecución segura y opt-in de comandos `STACK.md §2.5`**): CUANDO se invoque `ci-verify --run-stack`, el sistema deberá leer exclusivamente el bloque estructurado `yaml sdd:verification-commands` de `specs/STACK.md` mediante `parse_verification_commands`; si `Gate S0` no está aprobado o algún comando contiene metacaracteres de shell inseguros (`;`, `|`, `` ` ``, `$(`, `>`, `<`, saltos de línea o `&` simple) o falta la clave requerida, deberá abortar en *fail-closed* antes de lanzar subprocesos, ejecutando los comandos permitidos (`lint`, `unit_test`, `integration_test` opcional, `build`, `infra`) con `shell=False`. Sin `--run-stack`, los comandos de stack se reportarán como `SKIPPED_OPT_IN` sin ejecutarse.
- `RF-1304` (**Desacoplo de `.github/workflows/ci.yml` y plantillas Multi-CI**): `.github/workflows/ci.yml` deberá reemplazar los scripts Python inline por invocaciones a `uv run python scripts/sdd_cli.py ci-verify` (activando `--run-stack` solo si `specs/STACK.md` está aprobado), y `specs/templates/ci/` deberá incorporar plantillas equivalentes y sincronizables (`gitlab-ci.yml`, `bitbucket-pipelines.yml`, `ci-verify.sh`) con cero impacto en el presupuesto de `.agents/`.

## 3. Criterios de Aceptación (BDD / Given-When-Then)
1. **Escenario `CA-1301` (`ci-verify` en modo `framework` con salida JSON):**
   - **Dado** el repositorio `sdd-agentic-starter` con `Gate S0` sin aprobar y todas las invariantes SDD íntegras
   - **Cuando** se ejecuta `uv run python scripts/sdd_cli.py ci-verify --mode framework --format json`
   - **Entonces** el comando retorna código `0` y el JSON incluye `mode: "framework"`, `overall_status: "PASS"` y el resultado individual de cada check (`hooks`, `healthcheck`, `odd_compliance`, `boundaries`, `catalog_verify`, `dag_verify`, `gate_seals`, `tokens`, `framework_tests` con `tests_run >= 120`).
2. **Escenario `CA-1302` (Proyecto derivado con `--mode auto` sin falsos fallos por `>= 120` tests):**
   - **Dado** un workspace temporal de proyecto derivado con `specs/STACK.md` (`Gate S0` aprobado), `docs/knowledge/`, `docs/es/` y `docs/en/` válidos y solo `2` tests propios (sin `tests/test_sdd_governance.py`)
   - **Cuando** se ejecuta `ci-verify --mode auto`
   - **Entonces** detecta `mode: "project"`, omite el umbral `>= 120` del starter, valida gobernanza SDD + `0DD` + `DAGs` y retorna código `0` reportando los comandos de stack como `SKIPPED_OPT_IN` al no pasarse `--run-stack`.
3. **Escenario `CA-1303` (Validación *fail-closed* de `--run-stack` y rechazo de metacaracteres):**
   - **Dado** un proyecto derivado con `Gate S0` aprobado y `yaml sdd:verification-commands` conteniendo `lint: "python -V && python -c pass"` o bien un comando malicioso `lint: "python -V; rm -rf /"`
   - **Cuando** se ejecuta `ci-verify --mode project --run-stack`
   - **Entonces** con `&&` válido ejecuta ambos segmentos con `shell=False` y retorna `0`, mientras que con `;`, `|`, `$(` o `Gate S0` sin aprobar aborta inmediatamente en *fail-closed* con código distinto de `0`.
4. **Escenario `CA-1304` (Detección de regresión 0DD / BOM en `hooks.json`):**
   - **Dado** un workspace donde `.agents/hooks.json` tiene BOM UTF-8 o una feature `Done` en `specs/BACKLOG.md` carece de entrada en `TRACEABILITY-MATRIX.md`
   - **Cuando** se ejecuta `ci-verify`
   - **Entonces** retorna código `1` identificando el check fallido en el reporte.

<!-- sdd:gate-seal gate=1 sha256=5610a87d3440cc7316975b97151e33eadd3ef29e1cd421a6254d0484f208b564 -->
