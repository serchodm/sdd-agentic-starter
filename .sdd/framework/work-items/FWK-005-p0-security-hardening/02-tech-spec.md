# Especificación Técnica: Stop-the-Line P0 Seguridad (`FWK-005`)

- **ID:** `FWK-005-p0-security-hardening`
- **Gate 2 Sign-off:** `[x] Gate 2 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Contratos por Zona Disjunta (`<= 500` líneas por módulo Python)

1. **`W1.1` Hooks & Guards** (`.agents/hooks.json`, `.agents/scripts/{sdd_code_gate_guard,sdd_immutable_feature_guard,sdd_stack_gate_guard,sdd_trim_exec}.py`):
   - `.agents/hooks.json`: codificación UTF-8 sin BOM, rutas `uv run python .agents/scripts/...`.
   - `sdd_immutable_feature_guard.py` & `sdd_code_gate_guard.py`: retornar `{"decision": "deny", "reason": ...}` (código `0` + deny JSON o error fail-closed según contrato hook Claude/AGY existente: mantener esquema `{"decision": "deny", "reason": ...}`) ante JSON inválido, stdin vacío inesperado, error al leer `STACK.md` / `BACKLOG.md` / `active_work_item.json`, o fallo de contención. Normalizar `\\?\` / `\\?\UNC\` antes de `resolve(strict=False)` y comprobar `is_relative_to(repo_root.resolve())` contra path traversal y symlinks/junctions saliendo del repo.
   - Proteger rutas críticas `tests/`, `.agents/`, `specs/STACK.md`, `scripts/` cuando el código/reglas de gate apliquen: `sdd_code_gate_guard.py` protege `src|backend|frontend|DDBB|docker-compose*` + `tests/` + `.agents/hooks.json` + `.agents/scripts/` + `specs/STACK.md` (sin bloquear `.agents/active_work_item.json` ni `ACTIVE_STATE.md` si corresponde, pero sí impidiendo tampering de guardias/tests sin work item aprobado, mientras `sdd_immutable_feature_guard.py` bloquea `specs/features/FEAT-XXX/` si `Done` y comprueba path resuelto dentro del repo). *Nota:* asegurar compatibilidad con tests existentes en `tests/`.
   - `validate_active_work_item(repo_root)`: además de `active_work_item.json` con `gates: {1..3: true}`, localizar la carpeta `specs/<bucket>/<ID>*`, exigir existencia de `01-spec.md`/`01-bug-report.md`, `02-tech-spec.md`/`02-fix-spec.md`, `03-tasks.md` con contenido sustantivo y marcadores humanos `[x] Gate 1 Approved`, `[x] Gate 2 Approved`, `[x] Gate 3 Approved` reales (no dentro de comentarios HTML / bloques de código).
   - `sdd_trim_exec.py`: prohibir `shell=True`. Parsear comando CLI con `shlex.split` (POSIX / `posix=(os.name != 'nt')` según argumento) o aceptar lista `--` argv y pasar `list[str]` a `subprocess.run(..., shell=False)`. Rechazar operadores de encadenamiento si llega un único string ambiguo sin lista.
2. **`W1.2` Healthcheck & Baseline** (`.agents/scripts/sdd_healthcheck.py`, `specs/BACKLOG.md`):
   - `check_spec_triads()`: parsear filas Markdown separando por `|` y revisando estrictamente la columna de estado (última o penúltima columna según cabecera `Estado`/`Status`), nunca toda la línea.
   - Añadir verificación de commits que muten features `Done` (`git log` / `git diff` contra último tag o rango base `develop..HEAD` / commits recientes sobre `specs/features/FEAT-XXX` marcados `Done` si no existe `CR-XXX` vinculado, o comprobar árbol + commits respecto a `origin/develop`/`develop`).
   - Revisar en `specs/BACKLOG.md`: limpiar fila `FEAT-001` placeholder `In Progress` dejando la tabla ejemplo limpia/comentada sin expedientes fantasmas activos que rompan la coherencia inicial.
3. **`W1.3` Git Hooks, CLI & Worktree Containment** (`scripts/sdd_hooks.py`, `.githooks/*`, `sdd.cmd`, `scripts/sdd_git.py`):
   - `scripts/sdd_hooks.py`: eliminar `SDD_FORCE_MAIN_PUSH` (A4: fail-closed estricto en `pre-push` hacia `main`), fallar cerrado si `git diff` o lectura de ficheros falla en `pre-commit` / `pre-push`.
   - `sdd.cmd`: pasar `%*` directo o validar el primer argumento sin `echo %FIRST_ARG% | findstr` (evitar ejecución de metacaracteres `& | > <`).
   - `scripts/sdd_git.py` (`WorktreeManager.remove`): resolver `target = wt_path.resolve(strict=False)` y `root = self.worktrees_root.resolve(strict=False)`; rechazar si `target == root` o `not target.is_relative_to(root)`.
4. **`W1.4` Pack Skill Contamination** (`.agents/skills/`):
   - Eliminar `.agents/skills/{fastapi-patterns,postgres-patterns,react-performance-and-patterns}/` (permanecen en `.sdd/catalog/packs/`).
5. **`W1.5` Suite Adversarial P0** (`tests/test_sdd_security_guards.py`, `<= 500` líneas).
