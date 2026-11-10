# Catálogo de Entidades y Modelos de Datos

## 1. Modelos Inmutables del Framework (`FWK-001`)

| Entidad / Modelo | Capa / Módulo | Propósito | Campos Clave | Relaciones / Restricciones |
| :--- | :--- | :--- | :--- | :--- |
| `StackConfig` | `scripts/sdd_pack_registry.py` (`@dataclass(frozen=True)`) | Configuración estructurada extraída del bloque `yaml sdd:stack-config` de `specs/STACK.md`. | `gate00_approved: bool`, `preset: str`, `packs: tuple[str, ...]`, `uiux: dict[str, Any] \| None` | `preset` validado contra `PRESET_CONFIGS`; `uiux` reservado para `FWK-002`. |
| `PackActivation` | `scripts/sdd_pack_registry.py` (`@dataclass(frozen=True)`) | Registro de activación de un pack resuelto indicando su origen. | `name: str`, `pack_id: str`, `source: Literal["stack-config", "manual"]` | Deduplicado por `dir_name`; `"manual"` para `--packs` CLI. |
| `PackManifest` | `scripts/sdd_pack_registry.py` (`@dataclass(frozen=True)`) | Manifiesto validado de un pack cargado desde `.sdd/catalog/packs/<pack>/pack.json`. | `dir_name: str`, `pack_id: str`, `family: str`, `requires: tuple[str, ...]`, `description: str`, `rules`, `specialists`, `skills`, `workflows` (`tuple[str, ...]`) | `id` y `family` obligatorios no vacíos; `id` único en todo el catálogo. |
| `ResolvedPackAssets` | `scripts/sdd_pack_registry.py` (`@dataclass(frozen=True)`) | Rutas físicas ya validadas dentro del directorio del pack listas para planificar. | `manifest: PackManifest`, `pack_dir: Path`, `agent_files: tuple[Path, ...]`, `skill_dirs: tuple[tuple[str, Path], ...]`, `rule_files: tuple[Path, ...]`, `workflow_files: tuple[Path, ...]` | Prohíbe rutas absolutas o `..`; toda skill exige `SKILL.md`. |
| `WorkspacePaths` | `scripts/sdd_agent_generator.py` (`@dataclass(frozen=True)`) | Mapa de rutas resueltas del workspace a partir de `repo_root`. | `root`, `agents_dir`, `overrides_dir`, `inbox_dir`, `pack_rules_dir`, `skills_dir`, `stack_path`, `lock_file`, `archetypes_dir`, `specialists_dir`, `packs_dir` (`pathlib.Path`) | `pack_rules_dir` apunta a `.agents/pack-rules` fuera de `.agents/rules/`. |
| `PlannedFile` | `scripts/sdd_agent_generator.py` (`@dataclass(frozen=True)`) | Unidad determinista planificada para prevalidación *fail-closed* y escritura. | `rel_path: str`, `content: bytes`, `sha256: str`, `owner: str`, `kind: Literal["agent", "skill", "rule", "workflow"]` | `rel_path` POSIX relativo al repo; `owner` es `"builder:<name>"`, `"specialists"` o `"pack:<dir_name>"`. |
| `PackDefinition` | `scripts/sdd_catalog_import.py` (`TypedDict`) | Definición tipada de cada pack integrado en `STACK_PACKS`. | `id`, `family`, `requires`, `description`, `rules`, `specialists`, `skills`, `workflows` | Mapea el catálogo importable desde `affaan-m/ecc`. |
| `BuilderSpec` / `PresetSpec` | `scripts/sdd_agent_generator.py` (`TypedDict`) | Definición de builders y presets (`compact`, `granular`, `api-only`, `spa-only`). | `name`, `archetype`, `zone_paths`, `dod`, `forbidden` / `description`, `builders` | Compilados vía arquetipos o `.agents/overrides/<name>.md`. |

---

## 2. Esquemas Persistidos y Contratos JSON / YAML

### 2.1. Bloque `yaml sdd:stack-config` en `specs/STACK.md`
- Debe existir `0` o `1` bloque vallado ```` ```yaml sdd:stack-config ```` en `specs/STACK.md` (más de uno o bloque sin cerrar lanza `StackConfigError`).
- Campos: `gate00_approved` (`true`/`false` estricto), `preset` (clave en `PRESET_CONFIGS`, por defecto `"compact"`), `packs` (lista de strings no vacíos), `uiux` (mapa opcional).
- La activación automática exige simultáneamente `[x] Gate 00 Approved` (o `[X]`) en el documento y `gate00_approved: true`. Si hay firma humana sin bloque `sdd:stack-config` → `StackConfigError`.

### 2.2. `.agents/squad.lock.json` (`schema_version: 2`)
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `schema_version` | `int` (`2`) | Versión del esquema de bloqueo y trazabilidad por fichero. |
| `timestamp` | `str` (ISO-8601 UTC) | Marca temporal de generación; se conserva sin reescribir el fichero si el resto de la carga útil es idéntica. |
| `gate00_approved` | `bool` | Estado efectivo (`has_human_signoff and config.gate00_approved`). |
| `preset` | `str` | Preset efectivo aplicado (`compact`, `granular`, `api-only`, `spa-only`). |
| `tech_stack` | `str` | Etiqueta de stack (`"Multi-Stack"` por defecto). |
| `core_agents` | `list[str]` | Lista fija de los 6 agentes core (`orchestrator`, `functional-analyst`, `architect`, `qa-tester`, `documentator`, `devops`). |
| `builders` | `list[str]` | Builders materializados según el preset activo. |
| `specialists` | `list[str]` | Especialistas universales materializados desde `.sdd/catalog/specialists/`. |
| `active_packs` | `list[object]` | Lista de `{ "name": str, "id": str, "source": "stack-config" \| "manual" }`. |
| `files` | `dict[str, object]` | Diccionario por ruta POSIX relativa con `{ "sha256": str, "owner": str, "kind": "agent" \| "skill" \| "rule" \| "workflow" }`. |

### 2.3. Cabecera de Procedencia `GENERATED` y Jerarquía de Errores
- **Cabecera Markdown:** `<!-- GENERATED by sdd_agent_generator (<owner>). Do not edit directly. -->` (insertada justo tras el cierre `---` del YAML frontmatter si existe; en línea 1 si no tiene frontmatter; omitida en ficheros no Markdown como `.py`).
- **Excepciones (`SddGeneratorError`, código de salida CLI `1`):** `StackConfigError`, `InvalidManifestError`, `PackDependencyError`, `CollisionError`, `ManualModificationConflictError`.

---

## 3. Entidades de Negocio de la Aplicación *(Pendiente de Gate 00)*

| Entidad / Tabla | Capa | Propósito | Campos Clave | Relaciones |
| :--- | :--- | :--- | :--- | :--- |
| *(Inicialmente vacío hasta aprobación de `specs/STACK.md`)* | - | - | - | - |
