# Tech Spec: Alineación de Coherencia v1.1.1 (`FWK-012`)

- **ID:** `FWK-012-coherence-alignment`
- **Estado:** `Done`
- **Especificación Funcional:** [`01-spec.md`](01-spec.md)
- **Gate 2 Sign-off:** `[x] Gate 2 Approved (Authorized by PO on 2026-11-16T11:46:29+01:00)`

## 1. Arquitectura Modular (`<= 500` líneas por `.py`)

### 1.1. `scripts/sdd_cli.py` (actual `133L`, objetivo `<= 230L`)
- Añadir subcomando `work-item` con acciones `show` y `set <ID> [--spec-dir <PATH>]`:
  - Resolución segura de `<ID>` (`^(?:FEAT|CR|BUG|HOTFIX|FWK)-\d{3,4}`) contra `specs/features`, `specs/changes`, `specs/bugs` y `.sdd/framework/work-items` rechazando rutas ambiguas, inexistentes o symlinks/junctions.
  - Escribir `.agents/active_work_item.json` atómicamente con `status: "PENDING_APPROVAL"`, `gate_1_approved: false`, `gate_2_approved: false`, `gate_3_approved: false`, `approved_by_human: false`, `enforce_gate_seals: true`, `gate_seals: {}`, y sincronizar `.agents/ACTIVE_STATE.md` vía `sync_active_state_md` de `scripts/sdd_git_state.py`.
- Actualizar `README.md` y `.agents/workflows/bug-fast-track.md` para invocar `scripts/sdd_cli.py` con los subcomandos reales (`work-item`, `git`, `approve-gate`, `verify-gates`, etc.).

### 1.2. Soporte `HOTFIX-*` y `SPIKE-*`
- **`.agents/scripts/sdd_immutable_feature_guard.py` (actual `357L`, objetivo `<= 365L`):**
  - Ampliar `_WORK_ITEM_ID_RE` a `^((?:FEAT|CR|BUG|HOTFIX|FWK)-\d{3,4})$`.
- **`.agents/scripts/sdd_code_gate_guard.py` (actual `491L`, objetivo `<= 495L`):**
  - Ampliar `_WORK_ITEM_ID_RE` a `^((?:FEAT|CR|BUG|HOTFIX|FWK)-\d{3,4})(?:-[A-Za-z0-9._-]+)?$` (1 línea, manteniendo `<= 500L`).
- **`scripts/sdd_gate_seal.py` (actual `309L`, objetivo `<= 315L`):**
  - Ampliar regex de ID canónico en `_resolve_spec_dir` a `^((?:FEAT|CR|BUG|HOTFIX|FWK)-\d{3,4})`.
- **`.agents/scripts/sdd_healthcheck.py` (actual `495L`, objetivo `<= 500L`):**
  - Ajustar `SPEC_CATEGORIES` / `PREFIX_TO_CATEGORY` para mapear `"HOTFIX": "bugs"` dentro de `specs/bugs/` manteniendo la triada (`01-bug-report.md`, `02-fix-spec.md`, `03-tasks.md`) sin duplicar directorios, y validar `specs/spikes/SPIKE-*/SPIKE_REPORT.md` (no vacío y libre de *prompt injection*). Si el ajuste acercara `sdd_healthcheck.py` a `> 498L`, compactar sin pérdida o extraer helper ligero sin romper importaciones existentes.
- **Plantillas y Norma:**
  - Crear `specs/templates/06-spike-report.template.md` y `specs/templates/07-hotfix-fast-track.template.md`.
  - Limpiar en `specs/SDD_FRAMEWORK.md §3` las carpetas legacy inexistentes (`specs/principles/`, `specs/architecture/`, `specs/roadmap/`).

### 1.3. Alineación SDD de `spec-miner` y `sdd_catalog_import.py`
- **`.sdd/catalog/specialists-optin/spec-miner.md`:**
  - Reescribir el contrato operativo conservando la cabecera MIT `affaan-m/ecc` y `Prompt Defense Baseline`:
    - Salida en `specs/features/FEAT-XXX-<slug>/01-spec.md` (EARS + `Given-When-Then` + `SRC-###` + `AMB-###`), `domains/<slug>/{overview,decisions}.md` y referencias a `docs/knowledge/{SYSTEM_TOPOLOGY,API_CATALOG,DATA_MODELS}.md`.
    - Guardrail `Write` restringido a `specs/features/` y `domains/` (nunca `openspec/specs/` ni `src/`).
- **`scripts/sdd_catalog_import.py` (actual `466L`, objetivo `<= 485L`):**
  - Definir `SDD_CUSTOMIZED_SPECIALISTS = frozenset({"spec-miner"})`.
  - Añadir parámetro `overwrite_sdd_custom: bool = False` (CLI `--overwrite-sdd-custom`) a `import_specialists()`: si el destino de un especialista en `SDD_CUSTOMIZED_SPECIALISTS` ya existe y `overwrite_sdd_custom=False`, preservarlo con mensaje `[SKIP-SDD]`.

### 1.4. Flujo PR-first en `scripts/sdd_git.py` (actual `418L`, objetivo `<= 455L`)
- Añadir `--local-merge` (booleano, `default=False`) a `release-finish` y `hotfix-finish` en `build_parser()`.
- Cuando `local_merge=False` (comportamiento por defecto):
  - Verificar existencia de `branch` y limpieza del árbol (`require_clean=True` en `release-finish`).
  - Invocar `GitProviderAdapter.create_pr(governance.get("provider", "github"), branch, main_branch, title, body)` para abrir/preparar PR hacia `main` sin hacer `checkout main` ni `merge` directo ni `push` a `main`.
  - Actualizar estado en `ACTIVE_STATE.md` (`PR_OPENED:<url>` o `PR_READY:<branch>->main`).
- Cuando `local_merge=True`: conservar `_finish_branch_flow` existente pero rechazar `--push` hacia `main` si `push=True` y `main` está protegido (`RN-SDD-BRANCH-SYNC`), exigiendo `PR` aprobada para producción.

## 2. Pruebas Automatizadas
- Ampliar `tests/test_sdd_governance.py` (`work-item show/set`, `spec-miner` preservación en `sdd_catalog_import.py`, `release-finish` PR-first vs `--local-merge`).
- Ampliar `tests/test_sdd_l5_perfection.py` o `tests/test_sdd_security_guards.py` (`HOTFIX-001` en `sdd_code_gate_guard.py`, `sdd_gate_seal.py` y `sdd_healthcheck.py` + `SPIKE` check).
- Verificar techo modular `<= 500` líneas en el 100% de `.py` y ejecutar `unittest` completo (`>= 120` tests en verde).

<!-- sdd:gate-seal gate=2 sha256=e5a52937a6818913708d928c4d372c8a85e18d46fe9dd964e9d7dfdaac41966d -->
