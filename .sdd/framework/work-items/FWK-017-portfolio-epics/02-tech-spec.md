# Tech Spec: Portfolio, Épicas (`EPIC-XXX`), Roadmap y Dependencias entre Features (`FWK-017`)

- **ID:** `FWK-017-portfolio-epics`
- **Estado:** `Approved`
- **Especificación Funcional:** [`01-spec.md`](01-spec.md)
- **Gate 2 Sign-off:** `[x] Gate 2 Approved (Authorized by PO on 2026-11-21T01:17:55+01:00 — "Perfecto")`

## 1. Arquitectura Modular (`<= 500` líneas por `.py`)

### 1.1. Plantilla `specs/templates/09-epic-roadmap.template.md` y Norma `specs/SDD_FRAMEWORK.md §3`
- **`specs/templates/09-epic-roadmap.template.md`:** Plantilla oficial fuera de `.agents/` (`0` tokens en presupuesto activo) con cabecera de Épica (`ID`, `Título`, `Estado`: `Draft|Active|Completed|On Hold`, `Prioridad MoSCoW`, `RICE`) y bloque cercado `yaml sdd:epic` parseable de forma determinista:
  ```yaml
  epic_id: "EPIC-001"
  title: "[Título de la Épica]"
  status: "Draft"
  priority: "Must"
  rice:
    reach: 100
    impact: 2.0
    confidence: 0.8
    effort: 2.0
  features:
    - id: "FEAT-001"
      title: "[Slice vertical inicial]"
      priority: "Must"
      depends_on: []
  ```
- **`specs/SDD_FRAMEWORK.md §3`:** Añadir `specs/templates/09-epic-roadmap.template.md` y `specs/epics/EPIC-XXX-<slug>.md` al árbol estándar de `specs/`.

### 1.2. `scripts/sdd_portfolio.py` (nuevo módulo, objetivo `<= 480L`, stdlib-only)
Motor offline sin dependencias externas para creación, análisis, grafo y validación de Épicas y dependencias entre features:

- **Reutilización obligatoria (`search-first`):**
  - Seguridad de rutas y escritura atómica: `is_link_or_junction`, `atomic_write_text` desde `scripts/sdd_git_state.py`.
  - Normalización Win32 y validación de rutas relativas: `strip_win32_extended_prefix`, `resolve_repo_relative_path` desde `.agents/scripts/sdd_immutable_feature_guard.py`.
  - Limpieza de bloques no normativos: `strip_non_normative_markdown` desde `.agents/scripts/sdd_stack_gate_guard.py`.
  - Parsing de estado de features en `specs/BACKLOG.md`: `_parse_backlog_entries`, `_split_markdown_row`, `_clean_cell`, `_normalize_status` desde `.agents/scripts/sdd_healthcheck.py`.
- **Contratos / Dataclasses (`frozen=True`):**
  - `PortfolioError(ValueError)`: error *fail-closed* para entradas, rutas o IO inseguro.
  - `RiceScore(reach: float, impact: float, confidence: float, effort: float, score: float)`
  - `PortfolioFeature(feature_id: str, title: str, epic_id: str | None, status: str, priority: str, depends_on: tuple[str, ...], rice: RiceScore | None, ready: bool, blocked_by: tuple[str, ...])`
  - `EpicSummary(epic_id: str, title: str, status: str, priority: str, source_file: str, total_features: int, done_features: int, in_progress_features: int, blocked_features: int, progress_pct: float, feature_ids: tuple[str, ...], ready_features: tuple[str, ...], rice: RiceScore | None)`
  - `PortfolioFinding(code: str, severity: str, detail: str, subject: str | None = None)` (`severity` en `{"error", "warning"}`; códigos: `CYCLE_DETECTED`, `UNKNOWN_DEPENDENCY`, `INVALID_PRIORITY`, `INVALID_RICE`, `DUPLICATE_EPIC`, `DUPLICATE_FEATURE_EPIC`, `ORPHAN_FEATURE_REF`, `PRIORITY_INVERSION`).
  - `PortfolioReport(repo_root: str, has_portfolio_data: bool, status: str, epics: tuple[EpicSummary, ...], features: tuple[PortfolioFeature, ...], waves: tuple[tuple[str, ...], ...], critical_path: tuple[str, ...], findings: tuple[PortfolioFinding, ...])`
- **Reglas deterministas y parser:**
  1. **Validación *fail-closed* de rutas (`_validate_repo_root`):** rechaza rutas vacías, inexistentes, no directorios o symlinks/junctions (`is_link_or_junction`). Verifica igualmente que `specs/`, `specs/epics/` y cada `specs/epics/EPIC-*.md` no sean symlinks/junctions ni escapen de `repo_root`.
  2. **Extracción unificada de Épicas y Features:**
     - Lee `specs/BACKLOG.md` (si existe) para obtener estado real (`Candidate`, `Backlog`, `In Progress`, `In Review`, `Done`, `Blocked`) y columnas opcionales (`Épica`/`Epic`, `Prioridad`/`Priority`, `Depende de`/`Depends on`, `RICE`).
     - Lee `specs/epics/EPIC-*.md` parseando el bloque cercado `yaml sdd:epic` con parser YAML determinista estricto (sin `eval`, sin PyYAML).
     - Fusión determinista: `specs/BACKLOG.md` es fuente de verdad para `status` de cada `FEAT-XXX` cuando el ID figura en el backlog; si una feature declarada en `EPIC-*.md` no figura aún en `BACKLOG.md`, toma estado `Candidate` (o el declarado) y emite advertencia `ORPHAN_FEATURE_REF` solo si está referenciada como `In Progress`/`Done` sin existir en backlog.
     - Validación de prioridad *MoSCoW* (`MUST`, `SHOULD`, `COULD`, `WONT`, case-insensitive normalizado; por defecto `Should` si se omite, y `INVALID_PRIORITY` si tiene un valor desconocido) y *RICE* (`effort <= 0` o campos negativos -> `INVALID_RICE`).
  3. **Grafo DAG entre Features (`build_feature_graph`):**
     - Algoritmo de Kahn determinista (ordenado lexicográficamente por ID en cada ola para garantizar estabilidad 100% reproducible) produciendo `waves` y detectando ciclos (`CYCLE_DETECTED` con nodos implicados).
     - Cálculo de `critical_path`: camino más largo sobre features cuyo `status != "Done"` en el subgrafo acíclico.
     - Verificación de inversiones de prioridad (`PRIORITY_INVERSION` *warning* cuando `weight(feature.priority) > weight(dep.priority)` con umbral `Must` -> `Could`/`Wont`).
  4. **Comando `init` (`init_epic_doc`):**
     - Valida `--id` contra `^EPIC-\d{3,4}$`, normaliza slug kebab-case seguro, carga `specs/templates/09-epic-roadmap.template.md` (con fallback a plantilla mínima idéntica si se ejecuta sobre repo externo sin plantilla local), sustituye `EPIC-001` / título y escribe `specs/epics/<EPIC-ID>-<slug>.md` mediante `atomic_write_text` rechazando sobrescritura salvo `--force`.
  5. **Integración CI (`run_portfolio_ci_check(repo_root: Path) -> tuple[str, str, dict[str, Any]]`):**
     - Retorna `("SKIPPED_NO_APPLICABLE", ...)` si `not report.has_portfolio_data`.
     - Retorna `("PASS", ...)` si `status == "PASS"` (sin findings `severity == "error"`).
     - Retorna `("FAIL", ...)` si hay ciclos, dependencias rotas, errores de esquema o symlinks.

### 1.3. `scripts/sdd_cli.py` (actual `262L`, objetivo `<= 270L`)
- Añadir `"portfolio": ROOT_DIR / "scripts" / "sdd_portfolio.py"` en `DISPATCH_MAP`.
- Documentar `portfolio` (`init|status|graph|validate`) en `print_help()`.

### 1.4. `scripts/sdd_ci.py` (actual `497L`, límite `<= 500L`)
- Añadir import de `run_portfolio_ci_check` desde `sdd_portfolio` y registrar `check_portfolio(repo_root)` dentro de `run_ci_verify` manteniendo el fichero estrictamente `<= 500` líneas (reorganizando/compactando imports o tupla de checks si fuera necesario para dejar margen >= 3 líneas bajo `500L`).

## 2. Pruebas Automatizadas (`tests/test_sdd_portfolio.py`, objetivo `<= 450L`)

Suite 100% offline con `tempfile.TemporaryDirectory()`:
1. `CA-1701`: `portfolio init` crea `specs/epics/EPIC-001-core-billing.md` válido, rechaza segunda ejecución sin `--force`, permite `--force`, y rechaza IDs inválidos o symlinks en `--repo-root` / `specs/epics`.
2. `CA-1702`: Cálculo de *rollup* por Épica (`progress_pct`, `done_features`, `ready_features`), prioridad *MoSCoW* y cálculo *RICE* (`40.0`) cruzando `specs/epics/EPIC-*.md` con `specs/BACKLOG.md`.
3. `CA-1703`: Detección *fail-closed* de ciclos (`CYCLE_DETECTED`), dependencias inexistentes (`UNKNOWN_DEPENDENCY`), `effort <= 0` (`INVALID_RICE`) e inversión de prioridad `Must -> Wont` (`PRIORITY_INVERSION`).
4. `CA-1704`: Subcomando CLI `scripts/sdd_cli.py portfolio graph --format json` (`waves` y `critical_path`), comprobación `check_portfolio` en `sdd_ci.py` (`SKIPPED_NO_APPLICABLE` sin Épicas vs `PASS`/`FAIL` con Épicas), presupuesto `.agents/` `< 25k` tokens y techo `<= 500` líneas en todos los `.py`.

- [x] **Gate 2 Approved (Human Sign-off):** Revisado y validado por Stakeholder Humano (`2026-11-21T01:17:55+01:00`).

<!-- sdd:gate-seal gate=2 sha256=f4a4f0610c4a5cc0c092a2a4775316556f076f3a8b7bf9172d022269794378a4 -->
