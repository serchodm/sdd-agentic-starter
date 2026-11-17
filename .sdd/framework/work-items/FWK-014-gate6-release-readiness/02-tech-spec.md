# Tech Spec: `Gate 6` (`REL-vX.Y.Z`), Motor de Release Readiness (`sdd_release.py`) y `CHANGELOG.md` Determinista (`FWK-014`)

- **ID:** `FWK-014-gate6-release-readiness`
- **Estado:** `Approved`
- **Especificación Funcional:** [`01-spec.md`](01-spec.md)
- **Gate 2 Sign-off:** `- [x] **Gate 2 Approved (Human Sign-off):** Arquitectura modular (<= 500L), contratos CLI/API, seguridad fail-closed y estrategia de pruebas aprobados (Authorized by PO on 2026-11-17T11:01:37+01:00).`
- **Gate 2 Visual Sign-off:** `- [x] **Gate 2 Visual Sign-off (Human):** N/A (entregable CLI, gobernanza y documentación sin pantallas SCR-###).`

## 1. Arquitectura Modular (`<= 500` líneas por `.py`, stdlib-only)

### 1.1. `scripts/sdd_release.py` (nuevo módulo, objetivo `<= 460L`, stdlib-only)
Motor determinista de Release Readiness (`Gate 6`), auditoría de preflight y generación de `CHANGELOG.md`, reutilizando piezas existentes sin duplicación (`sdd_ci.run_ci_verify`, `sdd_healthcheck._parse_backlog_entries`, `sdd_stack_gate_guard.strip_non_normative_markdown`, `sdd_gate_seal.extract_inline_gate_seal` / `compute_gate_doc_sha256`, `sdd_git_state.atomic_write_text` / `is_link_or_junction`).

- **Dataclasses y contratos:**
  - `ReleaseItem(item_id: str, category: str, title: str, status: str, rfc: str = "")` con `category in {"features", "changes", "fixes", "framework", "other"}`.
  - `ReleaseCheck(name: str, status: str, detail: str, data: dict[str, Any] = ...)` con `status in {"PASS", "FAIL", "SKIPPED_STAGE"}`.
  - `ReleaseReadinessReport(version: str, tag: str, release_id: str, stage: str, overall_status: str, checks: tuple[ReleaseCheck, ...], repo_root: str)`.
- **Normalización y rutas seguras:**
  - `normalize_release_version(raw: str) -> tuple[str, str, str]`: valida SemVer estricto `^\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:\.[0-9A-Za-z]+)*)?$` (aceptando prefijo opcional `v`), devolviendo `(semver, f"v{semver}", f"REL-v{semver}")`; lanza `ValueError` ante entradas inválidas o inseguras.
  - `resolve_release_spec_path(repo_root: Path, version: str) -> Path`: resuelve `repo_root / "specs" / "releases" / f"REL-v{semver}.md"` validando ausencia de symlinks/junctions (`is_link_or_junction`) en `specs/`, `specs/releases/` y el fichero destino, y comprobando `is_relative_to(repo_root.resolve())`.
- **Resolución de artefactos en rama/worktree de release (para `release-finish` ejecutado desde `develop`):**
  - `_resolve_release_source_reader(repo_root: Path, tag: str, release_branch: str | None) -> tuple[Path, Callable[[str], str | None]]`:
    1. Si existe un worktree montado para `release_branch` (`GitRunner.get_worktrees(cwd=repo_root)`), lee desde ese worktree (siempre que esté limpio y no sea symlink/junction).
    2. Si la rama actual es `release_branch` o `release_branch` no existe todavía, lee desde `repo_root`.
    3. Si `release_branch` existe y el repo está posicionado en otra rama (p. ej. `develop`), lee `specs/releases/REL-v{semver}.md` y `CHANGELOG.md` directamente desde `git show <release_branch>:<rel_path>` (`shell=False`) si el fichero no está en el árbol actual, evitando falsos negativos al invocar `release-finish` desde `develop`.
- **Verificación de `Gate 6` (`parse_gate6_approval(text: str) -> tuple[bool, list[str]]`):**
  - Aplica `strip_non_normative_markdown(text)` para eliminar comentarios HTML y bloques de código vallados (anti-*spoofing* idéntico a `sdd_code_gate_guard.py`).
  - Exige marcador `\[[xX]\]\s*(?:\*\*)?Gate\s+6\s+Approved(?:\*\*)?` fuera de comentarios/fences.
  - Exige contenido sustantivo no vacío (incluyendo sección de rollback sin marcadores `<...>` sin rellenar en la línea del sign-off ni sección de rollback vacía).
  - Si `extract_inline_gate_seal(text, gate_num=6)` devuelve un hash o `"INVALID"`, verifica coincidencia exacta con `compute_gate_doc_sha256(text)`; ante `"INVALID"` o discrepancia falla en *fail-closed*.
- **Auditoría de Work Items abiertos (`check_open_work_items(repo_root: Path, *, allow_release_id: str) -> list[str]`):**
  - Revisa `.agents/active_work_item.json` (rechazando symlinks/junctions y JSON malformado): falla si `active_work_item_id` no está vacío, no es `"IDLE"` ni coincide con `allow_release_id` o `REL-{semver}`.
  - Parsea `specs/BACKLOG.md` mediante `_parse_backlog_entries` y, cuando `detect_ci_mode(repo_root) == "framework"` (o exista `.sdd/framework/BACKLOG.md` en modo framework), también `.sdd/framework/BACKLOG.md`: cualquier item en estado `in progress`, `in review`, `en progreso`, `en revision`, `en revisión`, `blocked` o `bloqueado` bloquea el release (`FAIL`).
- **Motor de `CHANGELOG.md` (`collect_release_items`, `render_changelog_section`, `update_changelog`, `verify_changelog_version`):**
  - `find_previous_tag(repo_root: Path, current_tag: str) -> str | None`: ejecuta `git tag -l --sort=-v:refname` (`shell=False`), excluye `current_tag` y devuelve el primer tag SemVer válido alcanzable (`git merge-base --is-ancestor <tag> HEAD`) o el más reciente en historial.
  - `collect_release_items(repo_root: Path, *, since_tag: str | None = None, current_tag: str | None = None) -> tuple[str | None, list[ReleaseItem]]`:
    - Lee commits del rango `<since_tag>..HEAD` (o `HEAD` si no hay tag previo) con `git log --no-merges --format=%H%x1f%s`.
    - Extrae IDs `FEAT-\d{3,4}`, `CR-\d{3,4}`, `BUG-\d{3,4}`, `HOTFIX-\d{3,4}`, `FWK-\d{3,4}` de los asuntos; consulta `specs/BACKLOG.md` y `.sdd/framework/BACKLOG.md` para título/RFC/estado, y enriquece título desde la cabecera `# ...` del `01-spec.md`/`01-bug-report.md` si falta en backlog.
    - Descarta ruido (`Merge ...`, `chore(release): ...`, `chore:`, `ci:`, `style:`). Si ningún commit referencia un ID SDD, conserva únicamente commits Conventional Commits sustantivos (`feat`, `fix`, `perf`, `refactor`) ordenados determinísticamente.
  - `render_changelog_section(version: str, items: Sequence[ReleaseItem], *, release_date: str) -> str`: genera `## [v{semver}] - {release_date}` agrupado por `### Features`, `### Changes`, `### Fixes & Hotfixes`, `### Framework` y `### Other Changes`.
  - `update_changelog(repo_root: Path, version: str, *, since_tag: str | None = None, release_date: str | None = None, dry_run: bool = False) -> tuple[pathlib.Path, str, bool]`: inserta o reemplaza de forma idempotente exclusivamente el bloque `## [v{semver}]` (desde su encabezado hasta el siguiente `## [` o EOF), conservando intactas el resto de secciones y escribiendo atómicamente con `atomic_write_text` (sin alterar si `dry_run=True`).
- **Flujos `prepare_release` y `run_release_preflight`:**
  - `prepare_release(repo_root: Path, version: str, *, since_tag: str | None = None, release_date: str | None = None, force: bool = False, update_changelog_file: bool = True) -> dict[str, Any]`: genera `specs/releases/REL-v{semver}.md` desde `specs/templates/08-release-readiness.template.md` (con fallback mínimo si la plantilla no existe en un repo temporal) manteniendo `[ ] **Gate 6 Approved (Human Sign-off):**` **sin marcar** (`RN-SDD-HUMAN-GATE-OWNERSHIP`). Falla si el fichero ya existe y `force=False`.
  - `run_release_preflight(repo_root: Path, version: str, *, stage: str = "finish", run_ci: bool = True, run_stack: bool = False, skip_tests: bool = False, release_branch: str | None = None) -> ReleaseReadinessReport`:
    - `stage == "start"`: valida SemVer, verifica que el tag `v{semver}` no exista aún, verifica `check_open_work_items`, y si `run_ci=True` ejecuta `run_ci_verify(repo_root, mode="auto", run_stack_if_approved=run_stack, skip_tests=skip_tests)`.
    - `stage == "finish"`: valida SemVer, limpieza del árbol si estamos en el repo raíz o worktree, `check_open_work_items`, existencia + `parse_gate6_approval` de `REL-v{semver}.md`, presencia de `v{semver}` en `CHANGELOG.md`, y `run_ci_verify(...) == "PASS"`.
- **CLI (`main(argv)`):** subcomandos `prepare`, `changelog`, `verify` (`--version`, `--stage start|finish`, `--since-tag`, `--date`, `--force`, `--stdout`, `--run-stack-if-approved`, `--skip-tests`, `--format text|json`, `--repo-root`).

### 1.2. `scripts/sdd_cli.py` (actual `251L`, objetivo `<= 270L`)
- Añadir `"release": ROOT_DIR / "scripts" / "sdd_release.py"` en `DISPATCH_MAP`.
- Documentar `release` en `print_help()` (`prepare`, `changelog`, `verify`).

### 1.3. `scripts/sdd_git.py` (actual `454L`, techo estricto `<= 500L`, objetivo `<= 478L`)
- Añadir un helper compacto `_run_release_preflight(version: str, stage: str, branch: str | None = None) -> bool` que importa `run_release_preflight` desde `scripts.sdd_release` y reporta checks fallidos devolviendo `False` (*fail-closed*).
- Invocar `_run_release_preflight(version, "start")` al inicio de `cmd_release_start` (tras validar SemVer y comprobar si la rama ya existe).
- Invocar `_run_release_preflight(version, "finish", branch=branch)` en `cmd_release_finish` (tras validar rama y limpieza del árbol, antes de `_finish_branch_flow` o `_pr_finish_flow`).
- **Compatibilidad de tests unitarios existentes:** las pruebas en `tests/test_sdd_git_concurrency.py` que ejercitan mecánicas puras de worktrees/PR en repos sintéticos mínimos sin `REL-v*` ni `BACKLOG.md` aislarán `_run_release_preflight` mediante `mock.patch.object`, mientras que `tests/test_sdd_release.py` probará la integración real sin mocks de `cmd_release_start` y `cmd_release_finish` *fail-closed*.

### 1.4. Normativa, Plantilla y Workflow (`Gate 6`)
- **`specs/SDD_FRAMEWORK.md`:** actualizar §3 (añadir `specs/templates/08-release-readiness.template.md`, `specs/templates/ci/` y `specs/releases/REL-vX.Y.Z.md`) y §4 (añadir subsección normativa `### Gate 6: Release Readiness y Rollback (REL-vX.Y.Z)` con ámbito Release, criterios de salida y prohibición de autoaprobación).
- **`specs/templates/08-release-readiness.template.md`:** plantilla oficial fuera de `.agents/` (`0` tokens de presupuesto activo) con secciones de alcance/work items `Done`, checklist automático, riesgos/migraciones, plan de despliegue/rollback y firma humana `[ ] Gate 6 Approved (Human Sign-off)`.
- **`.agents/workflows/gate6-release.md`:** workflow compacto (`<= 25L`, `< 1.5 KB`) orquestando `release-start` -> `sdd release prepare` -> `sdd ci-verify` -> firma humana en `REL-vX.Y.Z.md` -> `sdd release verify` -> `release-finish` (PR-first a `main`).

## 2. Pruebas Automatizadas (`tests/test_sdd_release.py`, objetivo `<= 460L`)
Suite 100% offline con repos Git temporales en `tempfile.TemporaryDirectory()`:
1. `prepare_release`: genera `REL-v1.2.0.md` sin autoaprobar `[x] Gate 6 Approved`, pobla work items `Done`, actualiza `CHANGELOG.md` y rechaza sobrescritura sin `--force` (`CA-1401`).
2. `update_changelog` / `collect_release_items`: cruza `<prev_tag>..HEAD` con `BACKLOG.md` y cabeceras `01-spec.md`, descarta ruido `chore:`/`Merge`, mantiene versiones anteriores intactas y resulta idempotente en ejecuciones repetidas (`CA-1402`).
3. `parse_gate6_approval` y `run_release_preflight`: rechaza *fail-closed* sign-off falsificado dentro de comentarios HTML o bloques vallados, sellos SHA-256 corruptos, work items en `In Progress`/`In Review` o `active_work_item.json` activo, y ausencia de sección en `CHANGELOG.md` (`CA-1403`).
4. Integración real `cmd_release_start` y `cmd_release_finish` en `sdd_git.py` (incluyendo ejecución desde `develop` cuando `REL-vX.Y.Z.md` y `CHANGELOG.md` viven en la rama `release/vX.Y.Z`): bloquea sin preflight válido y permite abrir PR hacia `main` cuando `Gate 6` y `ci-verify` están en verde (`CA-1404`).
5. Verificación CLI `sdd_cli.py release verify --format json` y aserción de presupuesto `.agents/` (`< 25k` tokens) y techo `<= 500` líneas en todos los `.py` modificados/creados.

<!-- sdd:gate-seal gate=2 sha256=ff3c4df7ec075257f8c2d19f3c0a0934a7fafae48b093713d68f11658d6b56b4 -->
