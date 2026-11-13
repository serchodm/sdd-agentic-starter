# Catálogo de Entidades y Modelos de Datos

## 1. Modelos Inmutables del Framework (`FWK-001`, `FWK-002` & `FWK-003`)

| Entidad / Modelo | Capa / Módulo | Propósito | Campos Clave | Relaciones / Restricciones |
| :--- | :--- | :--- | :--- | :--- |
| `StackConfig` | `scripts/sdd_pack_registry.py` (`@dataclass(frozen=True)`) | Configuración estructurada extraída del bloque `yaml sdd:stack-config` de `specs/STACK.md`. | `stack_approved: bool` (con alias `@property gate00_approved`), `preset: str`, `packs: tuple[str, ...]`, `uiux: dict[str, Any] \| None` | `preset` validado contra `DEFAULT_VALID_PRESETS`; soporte dual-accept `stack_approved`/`gate00_approved` (`FWK-004`); `uiux` validado por `_validate_uiux_config()` (`FWK-002`). |
| `PackActivation` | `scripts/sdd_pack_registry.py` (`@dataclass(frozen=True)`) | Registro de activación de un pack resuelto indicando su origen. | `name: str`, `pack_id: str`, `source: Literal["stack-config", "manual"]` | Deduplicado por `dir_name`; `"manual"` para `--packs` CLI. |
| `PackManifest` | `scripts/sdd_pack_registry.py` (`@dataclass(frozen=True)`) | Manifiesto validado de un pack cargado desde `.sdd/catalog/packs/<pack>/pack.json`. | `dir_name: str`, `pack_id: str`, `family: str`, `requires: tuple[str, ...]`, `description: str`, `rules`, `specialists`, `skills`, `workflows` (`tuple[str, ...]`), `targets: tuple[str, ...]`, `upstream: dict[str, Any] \| None` | `id` y `family` obligatorios no vacíos; `id` único en todo el catálogo; `targets` y `upstream` opcionales validados (`FWK-002`). |
| `ResolvedPackAssets` | `scripts/sdd_pack_registry.py` (`@dataclass(frozen=True)`) | Rutas físicas ya validadas dentro del directorio del pack listas para planificar. | `manifest: PackManifest`, `pack_dir: Path`, `agent_files: tuple[Path, ...]`, `skill_dirs: tuple[tuple[str, Path], ...]`, `rule_files: tuple[Path, ...]`, `workflow_files: tuple[Path, ...]` | Prohíbe rutas absolutas o `..`; toda skill exige `SKILL.md`; si `upstream.vendor_lock` existe, ejecuta `verify_vendor_lock()` antes de resolver. |
| `WorkspacePaths` | `scripts/sdd_agent_generator.py` (`@dataclass(frozen=True)`) | Mapa de rutas resueltas del workspace a partir de `repo_root`. | `root`, `agents_dir`, `overrides_dir`, `inbox_dir`, `pack_rules_dir`, `skills_dir`, `stack_path`, `lock_file`, `archetypes_dir`, `specialists_dir`, `packs_dir` (`pathlib.Path`) | `pack_rules_dir` apunta a `.agents/pack-rules` fuera de `.agents/rules/`. |
| `PlannedFile` | `scripts/sdd_agent_generator.py` (`@dataclass(frozen=True)`) | Unidad determinista planificada para prevalidación *fail-closed* y escritura. | `rel_path: str`, `content: bytes`, `sha256: str`, `owner: str`, `kind: Literal["agent", "skill", "rule", "workflow"]` | `rel_path` POSIX relativo al repo; `owner` es `"builder:<name>"`, `"specialists"` o `"pack:<dir_name>"`. |
| `PackDefinition` | `scripts/sdd_catalog_import.py` (`TypedDict`) | Definición tipada de cada pack integrado en `STACK_PACKS`. | `id`, `family`, `requires`, `description`, `rules`, `specialists`, `skills`, `workflows` | Mapea el catálogo importable desde `affaan-m/ecc` (sin incluir `capability-ui-design`). |
| `BuilderSpec` / `PresetSpec` | `scripts/sdd_agent_generator.py` (`TypedDict`) | Definición de builders y presets (`compact`, `granular`, `api-only`, `spa-only`). | `name`, `archetype`, `zone_paths`, `dod`, `forbidden` / `description`, `builders` | Compilados vía arquetipos o `.agents/overrides/<name>.md`. |
| `ValidationSeverity` | `scripts/sdd_tokens_validator.py` (`Enum(str)`) | Severidad de violaciones detectadas durante la validación de tokens. | `ERROR`, `WARNING`, `INFO` | `ERROR` invalida el resultado (`exit 1`); `WARNING` invalida solo si `strict=True` (`FWK-003`). |
| `TokenViolation` | `scripts/sdd_tokens_validator.py` (`@dataclass`) | Registro atómico de una discrepancia de tokens o literal de estilo prohibido. | `severity: ValidationSeverity`, `category: str`, `message: str`, `file_path: str`, `line_number: int`, `token_name: str`, `literal_value: str` | Trazabilidad por fichero y línea exacta en código fuente o specs (`FWK-003`). |
| `TokenValidationResult` | `scripts/sdd_tokens_validator.py` (`@dataclass`) | Resultado consolidado de la suite de validación de tokens de diseño. | `is_valid: bool`, `total_tokens_checked: int`, `total_sources_scanned: int`, `missing_in_master: list[str]`, `missing_in_json: list[str]`, `violations: list[TokenViolation]`, `skipped_reason: str \| None` | Serialización a JSON (`--format json`) o informe legible en texto plano (`FWK-003`). |

---

## 2. Esquemas Persistidos y Contratos JSON / YAML

### 2.1. Bloque `yaml sdd:stack-config` en `specs/STACK.md`
- Debe existir `0` o `1` bloque vallado ```` ```yaml sdd:stack-config ```` en `specs/STACK.md` (más de uno o bloque sin cerrar lanza `StackConfigError`).
- Campos: `stack_approved` (canónica, `true`/`false` estricto) o `gate00_approved` (legacy, `true`/`false` estricto; si ambas coexisten con valores contradictorios lanza `StackConfigError`), `preset` (clave en `DEFAULT_VALID_PRESETS`, por defecto `"compact"`), `packs` (lista de strings no vacíos), `uiux` (mapa opcional).
- La activación automática exige simultáneamente firma humana canónica `[x] Gate S0 Approved` (o legacy `[x] Gate 00 Approved`) en el documento y `stack_approved: true` (o `gate00_approved: true`). Si hay firma humana sin bloque `sdd:stack-config` → `StackConfigError`.

#### 2.1.1. Esquema Estricto de `uiux` en `sdd:stack-config` (`FWK-002`)
Cuando `uiux` está presente (si es `None` o se omite sigue siendo válido):
- **Claves permitidas (`_UIUX_ALLOWED_KEYS`):** `{"enabled", "provider", "version", "hifi_format", "brand_constraints"}`. Cualquier clave desconocida lanza `StackConfigError`.
- **`enabled` (`bool`, obligatorio):** booleano estricto (`true`/`false`). Si `enabled is True` con `preset == "api-only"` → `StackConfigError`.
- **`provider` (`str`, opcional):** string no vacío; cuando `enabled is True`, debe valer `"ui-ux-pro-max"`.
- **`version` (`str`, opcional):** string no vacío (en plantilla base `"2.15.0"`).
- **`hifi_format` (`str`, opcional):** perteneciente a `{"html", "figma", "html+figma"}`.
- **`brand_constraints` (`str | None`, opcional):** `null` (`None`) o ruta relativa segura sin prefijos absolutos POSIX/Windows, unidad de disco ni `..` / `.`.
- **Coherencia con `packs` (`resolve_active_packs`):** cuando `effective_gate00_approved` es `True`, `uiux.enabled is True` debe coincidir exactamente con la presencia de `capability-ui-design` (`capability:ui-design`) en `packs`; cualquier discordancia lanza `StackConfigError`.

### 2.2. `.agents/squad.lock.json` (`schema_version: 2`)
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `schema_version` | `int` (`2`) | Versión del esquema de bloqueo y trazabilidad por fichero. |
| `timestamp` | `str` (ISO-8601 UTC) | Marca temporal de generación; se conserva sin reescribir el fichero si el resto de la carga útil es idéntica. |
| `stack_approved` | `bool` | Estado efectivo de Gate S0 (`has_human_signoff and config.stack_approved`). |
| `gate00_approved` | `bool` | Alias retrocompatible para lectores v2 existentes (`== stack_approved`). |
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
- **Integridad de Vendor (`scripts/sdd_vendor_update.py`):** `VendorIntegrityError` (convertida en `InvalidManifestError` durante `sdd_pack_registry.resolve_pack_assets()`).

### 2.4. Esquema Extendido de `pack.json` (`targets` y `upstream`, `FWK-002`)
Además de `id`, `family`, `requires`, `description`, `rules`, `specialists`, `skills` y `workflows`:

| Campo | Tipo | Obligatoriedad | Validación / Contrato |
| :--- | :--- | :--- | :--- |
| `targets` | `list[str]` | Opcional | Si se declara, debe ser lista de strings no vacíos (p. ej. `["web"]` en `capability-ui-design`). |
| `upstream` | `dict[str, Any]` | Opcional | Objeto JSON con procedencia externa (`repo`, `package`, `license`, `version`, `copyright`, `vendor_lock`). Si incluye `vendor_lock`, debe ser string relativo seguro no vacío verificado contra traversal y symlinks. |

### 2.5. Manifiesto `VENDOR.lock.json` (`schema_version: 1`, `FWK-002`)
Ubicado en `.sdd/catalog/packs/capability-ui-design/vendor/ui-ux-pro-max/VENDOR.lock.json`:

| Campo | Tipo | Descripción / Reglas `verify_vendor_lock()` |
| :--- | :--- | :--- |
| `schema_version` | `int` (`1`) | Versión estricta del esquema del lock de vendorización (`type(...) is int` y valor `1`). |
| `package` | `str` | Paquete npm upstream fijado (`"ui-ux-pro-max-cli"`). |
| `version` | `str` | Versión semver no vacía fijada y aprobada (`"2.15.0"`). |
| `license` | `str` | Identificador SPDX de licencia (`"MIT"`). |
| `upstream_repo` | `str` | Repositorio fuente (`"nextlevelbuilder/ui-ux-pro-max-skill"`). |
| `updated_at` | `str` | Marca temporal ISO-8601 UTC de generación del lock. |
| `vendor_subdir` | `str` | Subruta relativa del proveedor (`"vendor/ui-ux-pro-max"`). |
| `files` | `dict[str, {"sha256": str, "bytes": int}]` | Mapa no vacío (`46` entradas en `2.15.0`: `LICENSE` + `45` ficheros runtime). Toda clave debe ser ruta relativa POSIX segura (sin `/`, `\`, `..`, unidad ni `VENDOR.lock.json`), coincidir 1:1 con disco (ignorando `__pycache__/` y `*.pyc`, rechazando symlinks) en tamaño exacto `bytes` y digest `sha256` (64 hex). |

### 2.6. Esquema Normativo de `docs/design-system/` (Proyectos con UI Activa, `FWK-002`)
> **Nota:** El repositorio starter vacío **no** incluye `docs/design-system/`. Esta estructura nace en el proyecto usuario durante la feature fundacional `Design System Foundation`.

| Artefacto | Propósito | Campos / Secciones Normativas |
| :--- | :--- | :--- |
| `docs/design-system/MASTER.md` | Fuente normativa visual global (neutra de idioma) | Cabecera YAML (`design_system_version`, `owner_feature`, `provider`, `hifi_format`, `brand_constraints`), paleta semántica con ratios WCAG, tipografía, espaciado, radios, sombras, motion, breakpoints, componentes y antipatrones. Prohibido `--force` sobre `MASTER.md` existente. |
| `docs/design-system/design-tokens.json` | Tokens estructurados sincronizados 1:1 con `MASTER.md` | Claves raíz obligatorias: `version`, `meta` (`owner_feature`, `provider`, `hifi_format`, `brand_constraints`), `colors`, `typography`, `spacing`, `radii`, `shadows`, `motion`, `breakpoints`. |
| `docs/design-system/CHANGELOG.md` | Historial semver trazado a `FEAT-XXX` / `CR-XXX` | `MAJOR` (`X.0.0`, incompatible, lista obligatoria de `SCR-###` afectados), `MINOR` (`0.X.0`, adiciones retrocompatibles), `PATCH` (`0.0.X`, ajuste de valor sin ruptura). |
| `docs/design-system/pages/SCR-XXX.md` | Overrides específicos por pantalla (`SCR-XXX`) | Cabecera (`screen_id`, `owner_feature`, `design_system: MASTER@<rango>`), referencia exclusiva a tokens de `design-tokens.json` (cero literales `#hex`/`px` sin token). |

### 2.7. Estructura Canónica DTCG de `design-tokens.json` y Convención de Escape (`FWK-003`)

El validador `scripts/sdd_tokens_validator.py` valida la jerarquía normalizada de tokens basada en el estándar W3C DTCG (*Design Tokens Community Group*):

```json
{
  "$schema": "https://design-tokens.github.io/community-group/format/",
  "version": "1.0.0",
  "color": {
    "brand": {
      "primary": { "value": "#2563eb", "type": "color", "description": "Color principal de marca" },
      "secondary": { "value": "#475569", "type": "color" }
    },
    "feedback": {
      "error": { "value": "#dc2626", "type": "color" },
      "success": { "value": "#16a34a", "type": "color" },
      "warning": { "value": "#f59e0b", "type": "color" }
    },
    "background": {
      "default": { "value": "#ffffff", "type": "color" },
      "subtle": { "value": "#f8fafc", "type": "color" }
    },
    "text": {
      "primary": { "value": "#0f172a", "type": "color" },
      "muted": { "value": "#64748b", "type": "color" }
    }
  },
  "typography": {
    "fontFamily": {
      "base": { "value": "Inter, sans-serif", "type": "fontFamily" },
      "heading": { "value": "Inter, sans-serif", "type": "fontFamily" }
    },
    "fontSize": {
      "sm": { "value": "0.875rem", "type": "dimension" },
      "base": { "value": "1rem", "type": "dimension" },
      "lg": { "value": "1.125rem", "type": "dimension" },
      "xl": { "value": "1.25rem", "type": "dimension" }
    }
  },
  "spacing": {
    "1": { "value": "0.25rem", "type": "dimension" },
    "2": { "value": "0.5rem", "type": "dimension" },
    "4": { "value": "1rem", "type": "dimension" },
    "6": { "value": "1.5rem", "type": "dimension" },
    "8": { "value": "2rem", "type": "dimension" }
  }
}
```

- **Aplanamiento a Dot-Notation**: Las hojas del árbol que contienen `value` o `$value` se aplanan a notación de puntos (p. ej. `color.brand.primary` con valor `#2563eb`, `spacing.4` con `1rem`). Los metadatos (`$schema`, `version`, `meta`) son excluidos automáticamente del aplanamiento.
- **Convención de Escape de Literales en Ficheros Fuente**: Cuando sea estrictamente necesario emplear un literal de estilo sin token (casos de borde o estilos de depuración aislados), se admiten comentarios de escape en la misma línea:
  - En TypeScript / TSX / JavaScript / JSX: `// sdd-token-ignore`
  - En CSS / SCSS / SASS / Less / HTML / Vue / Svelte: `/* sdd-token-ignore */`
  El escáner `--check-sources` ignora cualquier línea que contenga estos marcadores, evitando falsos positivos sin relajar las restricciones globales.

---

## 3. Entidades de Negocio de la Aplicación *(Pendiente de Gate 00)*

| Entidad / Tabla | Capa | Propósito | Campos Clave | Relaciones |
| :--- | :--- | :--- | :--- | :--- |
| *(Inicialmente vacío hasta aprobación de `specs/STACK.md`)* | - | - | - | - |
