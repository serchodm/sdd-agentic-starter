# Tech Spec: Motor de Adopción Brownfield (`sdd adopt`) y Workflow `@spec-miner` (`FWK-015`)

- **ID:** `FWK-015-brownfield-adopt-miner`
- **Estado:** `Approved`
- **Especificación Funcional:** [`01-spec.md`](01-spec.md)
- **Gate 2 Sign-off:** `[x] Gate 2 Approved (Authorized by PO on 2026-11-17T17:25:03+01:00 — "Aprobados")`

## 1. Arquitectura Modular (`<= 500` líneas por `.py`)

### 1.1. `scripts/sdd_brownfield.py` (nuevo módulo, objetivo `<= 470L`, stdlib-only)
Módulo determinista sin dependencias externas para descubrir repositorios *brownfield* y generar el expediente inicial SDD de forma no destructiva:

- **Reutilización obligatoria (`search-first`):**
  - Seguridad de rutas y escritura atómica: `is_link_or_junction`, `atomic_write_text` desde `scripts/sdd_git_state.py`, y `strip_win32_extended_prefix` desde `.agents/scripts/sdd_immutable_feature_guard.py`.
  - Validación de comandos seguros: `split_safe_chained_command` desde `scripts/sdd_ci.py` (misma política *fail-closed* contra `;`, `|`, `` ` ``, `$(`, `>`, `<`, `\n`, `\r`, `&` aislado).
  - Mapa de extensiones e ignorados: `EXTENSION_PARSERS` e `IGNORED_DIRS` desde `.agents/scripts/sdd_repo_map.py` (y `build_repo_map_lines` cuando se pase `--with-repo-map` para adjuntar un resumen acotado en `BROWNFIELD_INVENTORY.md`).
  - Detección de `Gate S0` ya aprobado: `parse_stack_config` / `StackConfigError` desde `scripts/sdd_pack_registry.py`.
- **Contratos / Dataclasses (`frozen=True`):**
  - `CandidateZone(zone_id: str, owner: str, paths: tuple[str, ...], file_count: int, languages: tuple[str, ...], dod_slot: str)`
  - `BrownfieldDiscovery(repo_root: str, manifests: tuple[str, ...], ci_files: tuple[str, ...], ecosystems: tuple[str, ...], suggested_packs: tuple[str, ...], suggested_preset: str, verification_commands: dict[str, str], rejected_commands: tuple[str, ...], candidate_zones: tuple[CandidateZone, ...], bounded_contexts: tuple[str, ...], existing_sdd_files: tuple[str, ...], stack_s0_approved: bool, warnings: tuple[str, ...])`
  - `AdoptPlan(dry_run: bool, applied: bool, created: tuple[str, ...], skipped_existing: tuple[str, ...], discovery: BrownfieldDiscovery)`
- **Reglas de detección (`discover_brownfield_repo(repo_root: Path, preset_override: str = "auto") -> BrownfieldDiscovery`):**
  1. **Validación *fail-closed* de `repo_root`:** rechaza rutas inexistentes, no directorios o symlinks/junctions (comprobando también componentes padre directos vía `is_link_or_junction`).
  2. **Escaneo de manifiestos (profundidad acotada `<= 3` saltando `IGNORED_DIRS` y `.agents`/`.worktrees`/`.sdd`):**
     - `pyproject.toml` / `requirements*.txt` / `setup.py` -> `lang-python`; inspección textual/TOML (`tomllib` stdlib Python 3.12!) para detectar `fastapi` -> `framework-fastapi`, `django` -> `framework-django`, `sqlalchemy`/`alembic` -> `capability-database`, `ruff`/`mypy`/`pytest` para `verification_commands`.
     - `package.json` / `tsconfig.json` -> `lang-typescript`; `json.loads` para detectar `react`/`next` -> `framework-react` + `capability-web-frontend`, `vue`/`nuxt` -> `framework-vue` + `capability-web-frontend`, `prisma`/`typeorm`/`drizzle-orm` -> `capability-database`; inspección de `scripts` (`lint`, `typecheck`, `test`, `build`) filtrados por `split_safe_chained_command` (prefijando `pnpm run` / `npm run` / `bun run` según lockfile detectado).
     - `go.mod` -> `lang-go` (`go vet ./...`, `go test ./...`, `go build ./...`).
     - `Cargo.toml` -> `lang-rust` (`cargo clippy`, `cargo test`, `cargo build --release`).
     - `*.csproj` / `*.sln` -> `lang-csharp` (`dotnet test`, `dotnet build`).
     - `pom.xml` / `build.gradle` / `build.gradle.kts` -> `lang-java` / `lang-kotlin`.
     - `CMakeLists.txt` -> `lang-cpp`; `pubspec.yaml` -> `lang-dart`; `Package.swift` -> `lang-swift`.
     - `Dockerfile` / `docker-compose*.yml` / `.github/workflows/*.yml` / `.gitlab-ci.yml` / `bitbucket-pipelines.yml` -> `capability-devops`.
     - Filtrado final de `suggested_packs` contra los directorios reales presentes en `.sdd/catalog/packs/` (si existe en `repo_root` o `ROOT_DIR`) para no sugerir packs inexistentes.
  3. **Detección de zonas candidatas (`CandidateZone`):**
     - Busca directorios de código de primer nivel o bajo monorepo (`src`, `app`, `lib`, `backend`, `frontend`, `api`, `web`, `services`, `packages`, `cmd`, `internal`, `DDBB`, `tests`, más subdirectorios inmediatos de `services/`/`packages/`/`src/` si `src/` contiene `backend/` o `frontend/`) contando ficheros cuya extensión esté en `EXTENSION_PARSERS`.
     - Asigna `owner` según `suggested_preset` (`compact`: `back-engineer` / `front-engineer` / `qa-tester`; `granular`: `back-api` / `back-domain` / `front-ui` / `qa-tester`) y genera `paths` con globs exactos (`"<dir>/**"`).
     - Deriva `bounded_contexts` desde subdirectorios cohesivos de negocio o módulos de primer nivel para guiar `@spec-miner`.
  4. **Inspección del estado SDD actual:**
     - Comprueba existencia de `specs/STACK.md`, `specs/BACKLOG.md`, `docs/knowledge/BROWNFIELD_INVENTORY.md` y lee estado de `Gate S0` en `specs/STACK.md` si existe.
- **Generación de artefactos (`plan_adopt` / `apply_adopt`):**
  - `render_draft_stack_md(discovery: BrownfieldDiscovery) -> str`: genera `specs/STACK.md` manteniendo `[ ] Gate S0 Approved (Human Sign-off)` y bloques cercados válidos para los parsers existentes:
    - `yaml sdd:stack-config` con `stack_approved: false`, `gate00_approved: false`, `preset`, `packs`, `uiux: { enabled: false }`.
    - `yaml sdd:verification-commands` con los comandos seguros inferidos (y comentario `# TODO(S0)` si falta algún slot).
    - `yaml sdd:ownership-map` con `unowned_policy: fail-closed` y las `zones` descubiertas.
  - `render_brownfield_inventory_md(discovery: BrownfieldDiscovery, repo_map_excerpt: str = "") -> str`: resume ecosistemas, manifiestos, ficheros CI, comandos aceptados/rechazados, zonas candidatas, bounded contexts sugeridos para `@spec-miner` y (si `--with-repo-map`) extracto acotado de `sdd_repo_map.py`.
  - `render_initial_backlog_md() -> str`: plantilla limpia de `specs/BACKLOG.md` lista para registrar `FEAT-XXX` minadas o nuevas.
  - **Garantía no destructiva:** solo escribe un archivo si `not target.exists()` (o para `BROWNFIELD_INVENTORY.md` si `--overwrite-inventory`), verificando que `target` no sea symlink/junction ni escape de `repo_root`. Si `specs/STACK.md` ya existe, siempre pasa a `skipped_existing` y nunca se modifica.
- **CLI (`main(argv: list[str] | None = None) -> int`):**
  - Flags: `--repo-root`, `--apply` (mutuamente excluyente o prevaleciendo sobre default `dry_run=True`), `--dry-run`, `--preset auto|compact|granular`, `--with-repo-map`, `--overwrite-inventory`, `--format text|json`.

### 1.2. `scripts/sdd_cli.py` (actual `256L`, objetivo `<= 270L`)
- Añadir `"adopt": ROOT_DIR / "scripts" / "sdd_brownfield.py"` en `DISPATCH_MAP`.
- Documentar `adopt` en `print_help()` con ejemplo `./sdd adopt --dry-run` / `./sdd adopt --apply`.

### 1.3. `.agents/workflows/brownfield-adopt.md` (nuevo fichero, `<= 25` líneas)
Workflow compacto (`RN-SDD-SELECTIVE-CONTEXT`, presupuesto `.agents/` `< 25k` tokens):
1. Ejecutar `uv run python scripts/sdd_cli.py adopt --format text` (`--dry-run` por defecto) y revisar inventario antes de `uv run python scripts/sdd_cli.py adopt --apply`.
2. Completar/ajustar `specs/STACK.md` y obtener firma humana explícita de `Gate S0` (`RN-SDD-HUMAN-GATE-OWNERSHIP`), ejecutando después `uv run python scripts/sdd_cli.py generate --materialize`.
3. Seleccionar un bounded context de `docs/knowledge/BROWNFIELD_INVENTORY.md` y extraer su esqueleto AST con `uv run python scripts/sdd_cli.py repo-map <ruta-contexto>`.
4. Invocar a `@spec-miner` (`.sdd/catalog/specialists-optin/spec-miner.md`) para generar el borrador `specs/features/FEAT-XXX-<slug>/01-spec.md` (`SRC-###`, `AMB-###`, EARS, `Given-When-Then`) y `domains/<slug>/{overview,decisions}.md` sin tocar `src/` ni autoaprobar `Gate 1`.

## 2. Pruebas Automatizadas (`tests/test_sdd_brownfield.py`, objetivo `<= 450L`)
Suite 100% offline con `tempfile.TemporaryDirectory()`:
1. `CA-1501`: Descubrimiento multi-stack (Python FastAPI + React/TS `package.json`, Go `go.mod`, Rust `Cargo.toml`) validando packs sugeridos, `preset`, zonas y salida JSON.
2. `CA-1502`: Comportamiento `--dry-run` por defecto (0 ficheros creados) vs `--apply` creando `specs/STACK.md` (compatible con `parse_stack_config` y `parse_ownership_map`, `stack_approved: False`), `docs/knowledge/BROWNFIELD_INVENTORY.md` y `specs/BACKLOG.md`; re-ejecución `--apply` preserva ficheros existentes intactos.
3. `CA-1503`: Rechazo *fail-closed* de `--repo-root` symlink/inexistente y sanitización de comandos inseguros en `package.json` (`;`, `|`, `$(`) sin inyectarlos en `yaml sdd:verification-commands`.
4. `CA-1504`: Ejecución CLI `scripts/sdd_cli.py adopt --format json`, comprobación de `.agents/workflows/brownfield-adopt.md` (`<= 25` líneas), presupuesto `.agents/` `< 25k` tokens y techo `<= 500` líneas en todos los `.py`.

<!-- sdd:gate-seal gate=2 sha256=659a7aca8066e015bf0dab7d9143253310badba4206818a939fbdf234c99b585 -->
