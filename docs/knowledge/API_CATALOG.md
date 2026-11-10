# Catálogo Unificado de APIs e Interfaces

Este catálogo se actualiza en el Gate 5 de cada Feature, Change Request o Work Item del Framework.

## 1. Interfaces CLI y Módulos del Framework (`FWK-001`)

| Endpoint / Interfaz | Método / Tipo | Descripción | Contrato Entrada | Contrato Salida | Introducido en |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `scripts/sdd_agent_generator.py` | CLI (`uv run python ...`) | Lista catálogo o materializa atómicamente builders, especialistas universales y packs activos en `.agents/` y `.agent-inbox/`. | Flags: `--materialize`, `--mode {compact,granular,api-only,spa-only}`, `--packs [PACK ...]`, `--list` | Código `0` (éxito, actualiza `.agents/squad.lock.json` v2 si hay cambios); código `1` (`[ERROR SDD] ...` ante `SddGeneratorError`) | `FWK-001` |
| `sdd_agent_generator.materialize_squad(...)` | Python API (`scripts/sdd_agent_generator.py`) | Orquesta parseo de `STACK.md`, resolución de packs, prevalidación *fail-closed*, limpieza y escritura atómica. | `preset_name: str \| None = None`, `requested_packs: list[str] \| None = None`, `repo_root: Path \| None = None` | `dict[str, Any]` (carga útil completa de `squad.lock.json` v2) o lanza subclase de `SddGeneratorError` | `FWK-001` |
| `sdd_pack_registry.parse_stack_config(...)` | Python API (`scripts/sdd_pack_registry.py`) | Extrae el bloque único ```` ```yaml sdd:stack-config ```` y calcula la aprobación efectiva de Gate 00. | `stack_path: Path`, `valid_presets: Collection[str] = DEFAULT_VALID_PRESETS` | `tuple[StackConfig, bool]` (`effective_gate00_approved`); lanza `StackConfigError` si es inválido o falta bloque con firma humana | `FWK-001` |
| `sdd_pack_registry.resolve_active_packs(...)` | Python API (`scripts/sdd_pack_registry.py`) | Deduplica packs (`stack-config` + `manual`), valida `requires` y resuelve activos verificando traversal. | `config: StackConfig`, `effective_gate00_approved: bool`, `cli_packs: Sequence[str] \| None`, `packs_dir: Path`, `registry: Mapping[str, PackManifest] \| None = None` | `tuple[tuple[PackActivation, ...], tuple[ResolvedPackAssets, ...]]`; lanza `InvalidManifestError` o `PackDependencyError` | `FWK-001` |
| `sdd_pack_registry.load_catalog_registry(...)` | Python API (`scripts/sdd_pack_registry.py`) | Carga y valida todos los `pack.json` bajo `.sdd/catalog/packs/`, rechazando `id` duplicados. | `packs_dir: Path` | `dict[str, PackManifest]` indexado por `dir_name` | `FWK-001` |
| `scripts/sdd_catalog_import.py` | CLI / Python API (`import_specialists`, `import_packs`) | Descarga especialistas universales y `STACK_PACKS` (incluyendo `workflows`) preservando packs externos ajenos a `STACK_PACKS`. | `fetcher: TextFetcher = fetch_text`, `specialists_dir: Path`, `packs_dir: Path` | `list[str]` con advertencias `[WARN]` si falla alguna descarga; escribe en `.sdd/catalog/` sin tocar packs externos | `FWK-001` |
| `scripts/sdd_sync.py` | CLI / Python API (`is_syncable_framework_file`, `load_managed_lock_paths`) | Sincronización bidireccional proyecto ↔ plantilla protegiendo archivos generados o listados en `squad.lock.json["files"]`. | Flags: `--status`, `--push-to-template PATH`, `--pull-from-template PATH`, `--template-dir PATH` | Informe de divergencia o copia selectiva excluyendo rutas en `squad.lock.json` y archivos con marcador `GENERATED` | `FWK-001` |

---

## 2. Endpoints de la Aplicación del Proyecto *(Pendiente de Gate 00)*

| Endpoint / Interfaz | Método / Tipo | Descripción | Contrato Entrada | Contrato Salida | Introducido en |
| :--- | :--- | :--- | :--- | :--- | :--- |
| *(Inicialmente vacío hasta implementar features del proyecto)* | - | - | - | - | - |
