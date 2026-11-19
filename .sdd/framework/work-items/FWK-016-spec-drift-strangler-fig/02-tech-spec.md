# Tech Spec: Detector de *Spec Drift* (`sdd drift`), Zonas *Strangler Fig* y Baseline Retroactiva Ligera (`FWK-016`)

- **ID:** `FWK-016-spec-drift-strangler-fig`
- **Estado:** `Approved`
- **Especificación Funcional:** [`01-spec.md`](01-spec.md)
- **Gate 2 Sign-off:** `[x] Gate 2 Approved (Human Sign-off)` *(Aprobado explícitamente por el usuario en chat)*

## 1. Arquitectura Modular y Restricción de Techo (`<= 500` líneas por `.py`)

### 1.1. `scripts/sdd_ownership.py` (actual `477L`, techo `<= 498L`)
Extensión retrocompatible de `sdd:ownership-map` para soportar arquitectura *Strangler Fig* y raíces brownfield:
- **Constantes y dataclasses:**
  - `VALID_ZONE_GOVERNANCE: frozenset[str] = frozenset({"governed", "legacy-readonly"})`
  - Añadir `"governance"` a `_ZONE_KEYS`.
  - Añadir `governance: Literal["governed", "legacy-readonly"] = "governed"` a `OwnershipZone`.
  - `_parse_zone_entry(...)`: valida `raw.get("governance")` (default `"governed"`, case-insensitive, lanza `OwnershipError` si no pertenece a `VALID_ZONE_GOVERNANCE`).
- **Helpers públicos nuevos:**
  - `resolve_path_zone(config: OwnershipMapConfig, rel_posix_path: str) -> OwnershipZone | None`: retorna la `OwnershipZone` cuyo glob coincide con `rel_posix_path` (o `None`).
  - `derive_candidate_roots(config: OwnershipMapConfig, base_roots: Sequence[str] = DEFAULT_CANDIDATE_ROOTS) -> tuple[str, ...]`: extrae los prefijos de directorio estáticos iniciales de `zone.paths` (excluyendo wildcards en raíz) y los fusiona preservando orden con `base_roots`.
  - `validate_repo_coverage(...)`: cuando no se pasa un `candidate_roots` explícito (o usando `derive_candidate_roots(config)`), evalúa cobertura sobre `DEFAULT_CANDIDATE_ROOTS` + raíces declaradas en `config.zones`.

### 1.2. `.agents/scripts/sdd_code_gate_guard.py` (actual `491L`, techo `<= 498L`)
Refuerzo *fail-closed* para raíces brownfield y zonas *Strangler Fig*:
- **Reutilización y límite `<= 500L`:**
  - Para mantener `sdd_code_gate_guard.py` holgadamente `<= 498L` (actualmente `491L`), la lógica de inspección de `sdd:ownership-map` se encapsula en un helper importado desde `scripts/sdd_ownership.py` o `scripts/sdd_drift.py` (p. ej. `inspect_ownership_path(repo_root, rel_posix) -> tuple[bool, str | None]`, que devuelve `(matched_zone_exists, legacy_readonly_zone_id)` en modo *fail-closed* ante errores de parseo de `STACK.md`).
  - Ampliar `_APP_PREFIX_RE` / `_PROTECTED_PREFIX_RE` o complementar `is_protected_code_path` con las raíces declaradas en `sdd:ownership-map` (y raíces brownfield estándar cuando exista `specs/STACK.md` aprobado con zonas en `app/`, `lib/`, `api/`, `web/`, `services/`, `packages/`, `cmd/`, `internal/`).
  - Si `legacy_readonly_zone_id` no es `None`, `main()` deniega inmediatamente vía `_deny(...)`: `"SDD Strangler Fig Lock: Zone '<id>' is marked 'legacy-readonly'. Migrate or promote it via CR/STACK.md before editing."`.
  - Mantener las comprobaciones `RN-ECC-DOC-SPRAWL` y `MAX_SOURCE_LINES` (`800L`) aplicables a rutas `governed` de código de aplicación.

### 1.3. `scripts/sdd_gate_seal.py` (actual `309L`, objetivo `<= 365L`) & `.agents/scripts/sdd_healthcheck.py` (actual `497L`, techo `<= 499L`)
Soporte controlado de **Baseline Retroactiva Ligera (`origin: brownfield-mined`)**:
- En `scripts/sdd_gate_seal.py`:
  - `is_brownfield_mined_baseline(spec_dir: Path) -> bool`: lee `01-spec.md` (sin seguir symlinks), elimina comentarios HTML y bloques vallados con `strip_non_normative_markdown`, y detecta el marcador estructurado `^(?:[-*]\s+)?(?:\*\*)?(?:Origin|Origen)(?:\*\*)?\s*:\s*`?brownfield-mined`?\s*$` (case-insensitive).
  - `validate_brownfield_baseline_docs(spec_dir: Path, rel_dir: str) -> list[str]`: verifica que existan `01-spec.md` y `02-tech-spec.md` no vacíos y con marcadores reales `[x] Gate 1 Approved` y `[x] Gate 2 Approved` fuera de comentarios/fences (fallando *fail-closed* si falta cualquiera de los dos o si no hay contenido sustantivo).
  - Actualizar `verify_work_item_gate_seals` y `seal_work_item_gates`: si `is_brownfield_mined_baseline(spec_dir)` es `True` y `03-tasks.md` no existe (y no hay sello previo de Gate 3 en `active_work_item.json`), operar sobre `gates = (1, 2)` en lugar de `(1, 2, 3)`. Si `03-tasks.md` falta sin marcador válido, mantiene el error *fail-closed* actual.
- En `.agents/scripts/sdd_healthcheck.py` (`497L` -> `<= 499L`):
  - En `check_spec_triads(...)`: cuando `category == "features"` y `status` no está en `GATE1_INITIAL_STATES`, delegar en `validate_brownfield_baseline_docs` importado de `sdd_gate_seal.py` si `is_brownfield_mined_baseline(item_dir)` y `(item_dir / "03-tasks.md")` no existe, consumiendo `<= 3` líneas netas y preservando estrictamente `<= 500L`.

### 1.4. `scripts/sdd_drift.py` (nuevo módulo, objetivo `<= 470L`, stdlib-only)
Motor determinista 100% offline de detección de *Spec Drift* y cobertura:
- **Reutilización obligatoria (`search-first`):**
  - `validate_repo_root` desde `scripts/sdd_brownfield.py` (rechazo *fail-closed* de symlinks/junctions y rutas inválidas).
  - `is_link_or_junction` desde `scripts/sdd_git_state.py` y `resolve_repo_relative_path` desde `.agents/scripts/sdd_immutable_feature_guard.py`.
  - `parse_ownership_map`, `zone_matches_path`, `resolve_path_zone` desde `scripts/sdd_ownership.py`.
  - `collect_source_files`, `EXTENSION_PARSERS`, `IGNORED_DIRS` desde `.agents/scripts/sdd_repo_map.py`.
  - `_parse_backlog_entries`, `parse_done_features_from_text` desde `.agents/scripts/sdd_healthcheck.py`.
  - Subprocesos `git` estrictamente con `shell=False` y `timeout` acotado, validando rutas de salida dentro de `repo_root`.
- **Contratos / Dataclasses (`frozen=True`):**
  - `SrcCitation(feature_id: str, src_id: str, rel_path: str, symbol: str | None, commit_sha: str | None)`
  - `DriftFinding(kind: str, severity: str, feature_id: str, path: str, symbol: str | None, detail: str)`
    - Valores `kind`: `"UNCOVERED_FILE"`, `"MISSING_SOURCE_FILE"`, `"MISSING_SYMBOL"`, `"UNLINKED_CODE_DRIFT"`.
    - Valores `severity`: `"error"` | `"warning"`.
  - `DriftReport(repo_root: str, status: str, findings: tuple[DriftFinding, ...], governed_files: int, legacy_readonly_files: int, covered_files: int, citations_checked: int, warnings: tuple[str, ...])`
- **Lógica de Análisis (`run_drift_check(repo_root: Path | str, *, base_ref: str | None = None, strict: bool = False) -> DriftReport`):**
  1. **Recolección de citas `SRC-###`, cobertura y supersesión por `CR-XXX` (`collect_feature_citations`):**
     - Recorre `specs/features/FEAT-*/01-spec.md` (y `02-tech-spec.md` si contiene citas `SRC-###`) y `specs/changes/CR-*/01-spec.md` extrayendo referencias con patrón `path/to/file.ext` o `path/to/file.ext::SymbolName` (soportando `ClassName.method()` y hash corto opcional `(sha)` / columna SHA).
     - Complementa la cobertura por fichero leyendo `docs/traceability/TRACEABILITY-MATRIX.md` (rutas de código asociadas a cada `FEAT-XXX`).
     - Consulta `specs/BACKLOG.md` + carpetas `specs/changes/CR-*/` y `specs/bugs/{BUG,HOTFIX}-*/` para distinguir: (i) `CR-XXX` abiertos (no-`Done`) vinculados a `FEAT-XXX`, (ii) `CR-XXX` cerrados (`Done`) vinculados a `FEAT-XXX` cuyas citas `SRC-###` / commits consolidados reemplazan la línea base de `FEAT-XXX` sin mutar `specs/features/FEAT-XXX/` (`RN-SDD-IMMUTABLE-DONE`), y (iii) work items `CR`/`BUG`/`HOTFIX` activos en `.agents/active_work_item.json`.
  2. **Chequeo A — Cobertura de Zonas `governed`:**
     - Si existe `yaml sdd:ownership-map` en `specs/STACK.md`, clasifica ficheros fuente soportados (`EXTENSION_PARSERS`, excluyendo zonas `qa-tester` / `tests/` y `legacy-readonly`) en `governed_files` vs `legacy_readonly_files`. Si no hay `ownership-map`, escanea raíces candidatas de código existentes excluyendo `tests/`.
     - Todo fichero `governed` ausente del mapa de cobertura `FEAT-*` (o `CR-*` vinculado) genera `DriftFinding("UNCOVERED_FILE", "error" if strict else "warning", "-", rel_path, None, ...)`.
  3. **Chequeo B — Integridad de Símbolos `SRC-###`:**
     - Si una `FEAT-XXX` tiene un `CR-XXX` vinculado (abierto o `Done`) que actualiza ese mismo fichero (o declara citas `SRC-###` nuevas sobre `rel_path`), la verificación de símbolos/existencia sobre `rel_path` toma como vigentes las citas del `CR-XXX` más reciente en lugar de la cita histórica ya sustituida en `FEAT-XXX` (evitando falsos positivos tras cerrar `CR-XXX`).
     - Para cada cita vigente `SrcCitation`: comprueba que `rel_path` existe como fichero regular dentro de `repo_root`; si no existe y `feature_id` no tiene `CR-XXX` abierto vinculado, emite `MISSING_SOURCE_FILE` (`"error"` si la `FEAT-XXX`/`CR-XXX` es `Done` o `strict`, `"warning"` en `Draft`/`In Progress`).
     - Si `symbol` está presente y `rel_path` tiene parser en `EXTENSION_PARSERS`, ejecuta el parser AST/regex sobre `rel_path` y verifica que el identificador base del símbolo (p. ej. `ClassName.method` -> `method` o `ClassName`) aparezca en las firmas extraídas. Si falta sin `CR-XXX` abierto vinculado, emite `MISSING_SYMBOL` (`"error"` si es `Done` o `strict`, `"warning"` en `Draft`).
  4. **Chequeo C — Deriva de Código sobre `Done` / Baseline sin `CR-XXX`/`BUG-XXX`/`HOTFIX-XXX`:**
     - Inspecciona `git status --porcelain` y `git diff --name-only <base>..HEAD` (si es repositorio Git; usando `--base-ref` o `merge-base` contra `origin/develop`/`develop`/`origin/main`/`main`). Para citas `SRC-###` de una feature `Done` con `<sha>` válido: si la `FEAT-XXX` tiene un `CR-XXX` cerrado (`Done`) vinculado que ya modificó `rel_path`, sustituye `<sha>` de referencia por el `<sha>` efectivo del `CR-XXX` (o el último commit que tocó `specs/changes/CR-XXX*`) para no re-reportar cambios históricos ya aprobados en `CR-XXX`, pero **manteniendo la detección** si se vuelve a modificar `rel_path` después sin un nuevo `CR-XXX`/`BUG-XXX`/`HOTFIX-XXX`.
     - Si un fichero cubierto por una `FEAT-XXX` en estado `Done` fue modificado sin un `CR-XXX` abierto vinculado a esa `FEAT-XXX` ni un `CR-XXX`/`BUG-XXX`/`HOTFIX-XXX` no-`Done` activo en `active_work_item.json` / `BACKLOG.md`, emite `UNLINKED_CODE_DRIFT` (`severity="error"`).
  5. **Estado Final:** `status = "FAIL"` si existe algún finding con `severity == "error"` (o si `strict=True` y hay cualquier finding), `"PASS"` en caso contrario.
- **CLI (`main(argv: list[str] | None = None) -> int`):**
  - Flags: `--repo-root`, `--base-ref`, `--strict`, `--format text|json`.

### 1.5. `scripts/sdd_cli.py` (actual `260L`, objetivo `<= 268L`) & `scripts/sdd_ci.py` (actual `477L`, techo `<= 498L`)
- **`scripts/sdd_cli.py`:**
  - Registrar `"drift": ROOT_DIR / "scripts" / "sdd_drift.py"` en `DISPATCH_MAP` y documentar `drift` en `print_help()`.
- **`scripts/sdd_ci.py`:**
  - Añadir `check_spec_drift(repo_root: Path, mode: str = "project") -> CheckResult`:
    - En `mode == "framework"` retorna `CheckResult("spec_drift", "SKIPPED_NO_APPLICABLE", "Spec drift check skipped in framework mode.", ...)`.
    - En `mode == "project"`, si no existen `specs/features/FEAT-*` ni zonas `governed`, retorna `SKIPPED_NO_APPLICABLE`; en caso contrario ejecuta `run_drift_check(repo_root)` y retorna `"PASS"` o `"FAIL"` con el resumen de findings y warnings en `data`.
  - Invocar `check_spec_drift(root, mode=resolved_mode)` dentro de `run_ci_verify(...)` manteniendo `sdd_ci.py <= 498L`.

## 2. Pruebas Automatizadas (`tests/test_sdd_drift.py`, objetivo `<= 470L`)
Suite 100% offline con `tempfile.TemporaryDirectory()` y repos Git locales sintéticos:
1. `CA-1601`: Zonas *Strangler Fig* (`governed` vs `legacy-readonly`) y raíces personalizadas en `sdd_ownership.py` (`derive_candidate_roots`, `validate_repo_coverage`, `OwnershipError` ante valor `governance` inválido) y bloqueo *fail-closed* de `sdd_code_gate_guard.py` sobre `legacy-readonly` vs permiso sobre `governed`.
2. `CA-1602`: Baseline retroactiva ligera `Origin: brownfield-mined` en `sdd_healthcheck.py` y `sdd_gate_seal.py` (`01-spec.md` + `02-tech-spec.md` con Gate 1 & Gate 2 aprobados sin `03-tasks.md` -> `PASS`; ausencia de `[x] Gate 2 Approved` o ausencia de marcador `brownfield-mined` -> `FAIL` *fail-closed*).
3. `CA-1603`: Ejecución de `sdd drift` (`text` y `json`) detectando `UNCOVERED_FILE`, `MISSING_SOURCE_FILE`, `MISSING_SYMBOL` y `UNLINKED_CODE_DRIFT`, comportamiento de `--strict`, retorno `0` cuando existe `CR-XXX` vinculado (abierto o ya cerrado `Done` tras consolidar sus citas `SRC-###` sin mutar `FEAT-XXX`) y detección de nueva deriva posterior si se edita el fichero tras cerrar `CR-XXX` sin abrir un nuevo `CR-002`.
4. `CA-1604`: Integración en `sdd_ci.py` (`framework` -> `SKIPPED_NO_APPLICABLE`, `project` con drift -> `FAIL`), CLI `sdd_cli.py drift --format json`, presupuesto `< 25k` tokens en `.agents/` y techo `<= 500` líneas en todos los `.py` de `scripts/`, `.agents/scripts/` y `tests/`.
