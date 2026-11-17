# Tech Spec: Motor CI-Agnóstico (`FWK-013`)

- **ID:** `FWK-013-ci-agnostic-verify`
- **Estado:** `Approved`
- **Especificación Funcional:** [`01-spec.md`](01-spec.md)
- **Gate 2 Sign-off:** `[x] Gate 2 Approved (Authorized by PO on 2026-11-16T18:13:32+01:00)`

## 1. Arquitectura Modular (`<= 500` líneas por `.py`)

### 1.1. `scripts/sdd_ci.py` (nuevo módulo, objetivo `<= 450L`, stdlib-only)
Módulo determinista sin dependencias externas que encapsula todas las verificaciones de CI del framework y de proyectos derivados:
- **Dataclasses y contratos:**
  - `CheckResult(name: str, status: str, detail: str, duration_ms: int, data: dict[str, Any] = ...)` con `status in {"PASS", "FAIL", "SKIPPED_OPT_IN", "SKIPPED_NO_APPLICABLE"}`.
  - `CiVerifyReport(mode: str, overall_status: str, checks: tuple[CheckResult, ...], repo_root: str)`.
- **Detección de modo `detect_ci_mode(repo_root: Path, requested: str = "auto") -> str`:**
  - Valida `requested in {"auto", "framework", "project"}`.
  - En `auto`: invoca `parse_stack_config(repo_root / "specs" / "STACK.md")`; si `stack_approved` es `True`, devuelve `"project"`. Si no está aprobado y existen `.sdd/framework/BACKLOG.md`, `.sdd/framework/work-items/` y `tests/test_sdd_governance.py`, devuelve `"framework"`. En caso contrario devuelve `"project"`.
- **Checks de gobernanza compartidos (`framework` y `project`):**
  1. `check_hooks_json(repo_root)`: valida existencia de `.agents/hooks.json`, ausencia de BOM UTF-8 (`\xef\xbb\xbf`), JSON válido, lista de comandos con al menos un script `.py/.sh/.ps1/.cmd` que resuelva dentro de `repo_root` sin escapes ni symlinks/junctions saliendo del repo.
  2. `check_healthcheck(repo_root)`: ejecuta `.agents/scripts/sdd_healthcheck.py` (subproceso Python con `--repo-root` o `cwd=repo_root` según soporte; nota: `sdd_healthcheck.py` admite invocación en `cwd=repo_root`).
  3. `check_odd_compliance(repo_root)`: reutiliza `parse_done_features_from_text` de `.agents/scripts/sdd_healthcheck.py`; exige no vacíos `docs/knowledge/{ADRS,API_CATALOG,DATA_MODELS,SYSTEM_TOPOLOGY}.md`, `docs/traceability/TRACEABILITY-MATRIX.md`, presencia de `*.md` no vacíos en `docs/es/` y `docs/en/`, y trazabilidad de cada `Done` en `specs/BACKLOG.md` dentro de `TRACEABILITY-MATRIX.md`.
  4. `check_architecture_boundaries(repo_root)`: invoca `.agents/scripts/verify_architecture_boundaries.py`.
  5. `check_catalog_and_squad_lock(repo_root)`: invoca `scripts/sdd_agent_generator.py --list` y `--verify`.
  6. `check_dags(repo_root)`: localiza todos los `03-tasks.md` bajo `.sdd/framework/work-items/*/` y `specs/*/*/`; en modo `framework` exige al menos 1 fichero DAG; en modo `project` si no hay ninguno devuelve `SKIPPED_NO_APPLICABLE`, y para cada fichero encontrado ejecuta `scripts/sdd_dag.py --verify <path>`.
  7. `check_gate_seals(repo_root)`: invoca `scripts/sdd_gate_seal.py --verify` (si `.agents/active_work_item.json` tiene `active_work_item_id`, lo valida; si está en `IDLE`/vacío retorna `PASS` limpio).
  8. `check_git_and_instincts(repo_root)`: invoca `scripts/sdd_git.py status` y `scripts/sdd_instincts.py list`.
  9. `check_design_tokens(repo_root)`: invoca `scripts/sdd_tokens_validator.py --allow-missing`.
- **Checks específicos de modo:**
  - **Modo `framework`:** `check_framework_unittest(repo_root, min_tests=120)` ejecuta `unittest` discover sobre `tests/` en subproceso limpio con `cwd=repo_root` y verifica `wasSuccessful()` y `testsRun >= min_tests` (evitando recursión infinita si `tests/test_sdd_ci.py` se autoinvoca mediante variable de guardia `SDD_CI_NESTED_TEST=1` cuando se ejecute desde dentro de un test o `tests_dir` configurable para pruebas unitarias).
  - **Modo `project` con `--run-stack`:**
    - Exige `stack_approved == True`; si no, falla en *fail-closed*.
    - Lee `VerificationCommands` con `parse_verification_commands(repo_root / "specs" / "STACK.md")` (`scripts/sdd_generator_tx.py`).
    - Slots ejecutados en orden determinista: `("lint", "unit_test", "build", "infra")` (y `integration_test` / `full_suite` si `--include-integration` o si se pasa `--stack-slots`).
    - **Parser seguro `split_safe_chained_command(cmd: str) -> list[list[str]]`:**
      - Rechaza metacaracteres peligrosos fuera o dentro de la cadena (`;`, `|`, `` ` ``, `$(`, `>`, `<`, `\n`, `\r`, y `&` aislado distinto de `&&`).
      - Divide en segmentos `&&` respetando comillas y tokeniza cada segmento con `shlex.split(seg, posix=True)` rechazando segmentos vacíos.
      - Ejecuta cada segmento con `subprocess.run(argv, cwd=str(repo_root), shell=False)`.
- **CLI de `scripts/sdd_ci.py`:**
  - `main(argv: list[str] | None = None) -> int` con `--repo-root`, `--mode auto|framework|project`, `--run-stack`, `--include-integration`, `--min-tests 120`, `--skip-tests` (útil dentro de tests unitarios), `--format text|json`.

### 1.2. `scripts/sdd_cli.py` (actual `248L`, objetivo `<= 270L`)
- Añadir `"ci-verify": ROOT_DIR / "scripts" / "sdd_ci.py"` en `DISPATCH_MAP`.
- Documentar `ci-verify` en `print_help()`.

### 1.3. `.github/workflows/ci.yml` y Plantillas Multi-CI (`specs/templates/ci/`)
- **`.github/workflows/ci.yml` (objetivo `<= 55L`):**
  - Eliminar los 3 bloques `python - <<'PY'` inline (~90L).
  - Un único paso tras `uv python install 3.12`:
    - `uv run python scripts/sdd_cli.py ci-verify --mode auto --format text` (y en proyectos derivados con `Gate S0` aprobado puede habilitarse `--run-stack` sin romper el starter donde `stack_approved: false`).
    - Verificar explícitamente que cuando `specs/STACK.md` tenga `stack_approved: true` en el propio workflow de GitHub Actions se pueda pasar un paso condicional o flag `--run-stack-if-approved`! **Decisión de diseño:** añadir `--run-stack-if-approved` a `sdd_ci.py` para que `ci.yml` y las plantillas CI puedan invocar un único comando universal (`uv run python scripts/sdd_cli.py ci-verify --mode auto --run-stack-if-approved`) que en el starter corre modo `framework` (sin stack commands porque `Gate S0` no está aprobado) y en proyectos derivados con `Gate S0` aprobado corre automáticamente `lint` + `unit_test` + `build` + `infra` de `STACK.md §2.5`, manteniendo `--run-stack` estricto (*fail-closed* si S0 no está aprobado) para uso explícito.
- **Plantillas portables bajo `specs/templates/ci/` (0 tokens en `.agents/`):**
  - `specs/templates/ci/README.md`: guía breve de activación por proveedor.
  - `specs/templates/ci/gitlab-ci.yml`: pipeline equivalente para GitLab CI invocando `uv run python scripts/sdd_cli.py ci-verify --mode auto --run-stack-if-approved`.
  - `specs/templates/ci/bitbucket-pipelines.yml`: pipeline equivalente para Bitbucket Pipelines.
  - `specs/templates/ci/ci-verify.sh`: wrapper POSIX (`#!/usr/bin/env sh`, `set -eu`) para Jenkins, Forgejo/Gitea, Woodpecker o local.

## 2. Pruebas Automatizadas (`tests/test_sdd_ci.py`, objetivo `<= 450L`)
Suite 100% offline con `tempfile.TemporaryDirectory()`:
1. Detección `detect_ci_mode`: `framework` en copia/fixture del starter vs `project` con `Gate S0` aprobado vs `project` sin `Gate S0` pero sin `tests/test_sdd_governance.py`.
2. `check_hooks_json`: éxito con JSON válido y rechazo *fail-closed* ante BOM UTF-8, ruta faltante o path escape (`../`).
3. `check_odd_compliance`: éxito con docs mínimos + trazabilidad y fallo ante `Done` sin trazar o idioma faltante.
4. `split_safe_chained_command` y `--run-stack`: ejecución real de comandos inocuos (`python -c ... && python -c ...`) con `shell=False`, rechazo *fail-closed* ante `;`, `|`, `$(`, `>`, `&` simple, y fallo si `--run-stack` se pide sin `Gate S0` aprobado.
5. `--run-stack-if-approved`: en `framework` omite stack commands (`SKIPPED_NO_APPLICABLE`) y en `project` con S0 aprobado los ejecuta.
6. CLI end-to-end `scripts/sdd_cli.py ci-verify --format json` y verificación de que todos los `.py` del repo siguen `<= 500` líneas.

<!-- sdd:gate-seal gate=2 sha256=933c0edcf50e99a4a4dc7306da7e9b0cffb930d10c2d4fcadfbd941fffbb2a73 -->
