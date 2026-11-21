<p align="right">
  <a href="../../../../en/02-functional/modules/MOD-003/gate-terminology-unification.md">🇬🇧 English (EN-GB)</a> | <strong>🇪🇸 Español (ES-ES)</strong>
</p>

# `MOD-003`: Unificación de Terminología de Gates, Estados y Grafo DAG

- **Identificador de Módulo:** `MOD-003`
- **Work Item / RFC de Origen:** `FWK-004`..`FWK-016` ([`RFC-002`](../../../../../.sdd/framework/rfcs/RFC-002-gate-terminology-unification.md) .. [`RFC-008`](../../../../../.sdd/framework/rfcs/RFC-008-brownfield-adoption-and-spec-drift.md))
- **Estado Funcional:** `Verified` (Confirmado y verificado por 160 tests unitarios offline en 15 suites)
- **Índice Maestro:** [DOCUMENTATION-INDEX.md](../../../00-governance/DOCUMENTATION-INDEX.md)

---

## 1. Propósito y Alcance

### 1.1. Propósito (Confirmado)
Este módulo elimina las ambigüedades normativas, colisiones numéricas (`Gate 00` vs `Gate 0`), divergencias bilingües de estados (`Done`/`Completado`) y mezclas conceptuales (`Gate` vs `Block` vs `Session Phase`) a lo largo de todo el starter, consolidando el ciclo completo de gobernanza desde `Gate S0` hasta `Gate 6` (`v1.3.0`).

Asegura que desarrolladores humanos y agentes de IA compartan un modelo mental inequívoco con soporte retrocompatible estricto (*zero-breaking dual-accept*) y validación de fallos cerrada (*fail-closed*).

### 1.2. Alcance Incluido (Confirmado)
- **Tabla Canónica Única de Gates:** `Gate S0` para Stack Lock de proyecto (`specs/STACK.md`), `Gate 0..5` para Work Items (incluyendo el condicional `Sub-Gate 2V` para validación visual de pantallas `SCR-###`) y `Gate 6` para *Release Readiness* (`specs/releases/REL-vX.Y.Z.md`).
- **Separación Ortogonal Conceptual:**
  - `Gate`: Compuertas de calidad y gobierno SDD (`Gate S0`, `Gate 0..6`).
  - `Block` / `Bloque DAG`: Agrupaciones de tareas concurrentes o secuenciales en `03-tasks.md`.
  - `Session Phase`: Particiones del contexto conversacional (`Sesión A: Gates 0 a 3` / `Sesión B: Gates 4 y 5`).
- **Soporte Dual-Accept Fail-Closed:**
  - `scripts/sdd_pack_registry.py` y `.agents/scripts/sdd_stack_gate_guard.py` aceptan canónicos (`[x] Gate S0 Approved`, `stack_approved`) y legacy (`[x] Gate 00 Approved`, `gate00_approved`).
  - Detección de incoherencia booleana entre `stack_approved` y `gate00_approved` abortando con `StackConfigError`.
  - `StackConfig` y `squad.lock.json` preservan compatibilidad v2 con alias retrocompatibles.
- **Normalización de Estados y Consolidación de Plantillas CR:**
  - Work Items: `Candidate` → `Backlog` → `In Progress` → `In Review` → `Done` (o `Blocked`).
  - Specs: `Draft` → `In Review` → `Approved` → `Done`.
  - Consolidación de plantillas de Change Request en [`specs/templates/04-change-request-spec.template.md`](../../../../../specs/templates/04-change-request-spec.template.md) y eliminación de `04-change-spec.template.md`.
  - Corrección de enlaces rotos heredados hacia `03-ears-requirements.md`.

### 1.3. Excluido Explícitamente (Fuera de Alcance)
- Alterar expedientes históricos finalizados (`FWK-001`, `FWK-002`, `FWK-003`, `RFC-001`) protegidos por `RN-SDD-IMMUTABLE-DONE`.
- Ficheros upstream vendorizados en `.sdd/catalog/packs/capability-ui-design/vendor/`.
- Código de producción de aplicación en `src/`.

---

## 2. Actores y Autoridad

| Actor | Responsabilidad | Restricción Principal |
| :--- | :--- | :--- |
| **Usuario Humano / Tech Lead** | Autoriza compuertas formales mediante sign-off humano explícito (`[x] Gate S0 Approved`, `[x] Gate 1 Approved`, `[x] Gate 2 Approved`, `[x] Gate 2 Visual Sign-off`, `[x] Gate 3 Approved`, `[x] Gate 6 Approved`). | Los agentes de IA nunca autoaprueban gates (`RN-SDD-HUMAN-GATE-OWNERSHIP`). |
| **`@orchestrator`** | Estructura el grafo de tareas DAG (`03-tasks.md`) en bloques paralelos y secuenciales (`Block`), despacha tareas a subagentes y vigila los límites de sesión. | No programa código de producción en el hilo principal (`RN-SDD-ORCHESTRATOR-SUBAGENTS`). |
| **`@back-engineer` / `@qa-tester`** | Implementan contratos ejecutables y suites de prueba manteniendo modularidad ($\le 500$ líneas por fichero). | Deben ejecutar comandos de verificación DoD deterministas sin exploración ciega. |
| **`@documentator`** | Custodia la documentación viva bilingüe (0DD) y actualiza catálogos y matrices de trazabilidad en Gate 5. | No puede cerrar Gate 5 sin certificar consistencia bilingüe 1:1. |

---

## 3. Matriz Canónica de Gates y Estados

| ID | Ámbito | Término EN | Término ES | Criterio de Sign-off |
| :--- | :--- | :--- | :--- | :--- |
| `Gate S0` | Proyecto | Stack Lock | Bloqueo de Stack | `[x] Gate S0 Approved (Human Sign-off)` / `stack_approved: true` |
| `Gate 0` | Work Item | Backlog Intake | Registro en Backlog | ID único en `specs/BACKLOG.md` + expediente en `specs/` |
| `Gate 1` | Work Item | Functional Spec | Especificación Funcional | `[x] Gate 1 Approved (Human Sign-off)` |
| `Gate 2` | Work Item | Technical Spec | Especificación Técnica | `[x] Gate 2 Approved (Human Sign-off)` |
| *Sub-Gate 2V* | Work Item (`SCR-###`) | Visual Sign-off | Validación Visual | `[x] Gate 2 Visual Sign-off (Human)` |
| `Gate 3` | Work Item | Task Graph (DAG) | Plan de Tareas (DAG) | `[x] Gate 3 Approved (Human Sign-off)` *(exento solo bajo `Origin: brownfield-mined`)* |
| `Gate 4` | Work Item | Implementation & QA | Implementación y QA | Tests + 4 auditorías de calidad en verde |
| `Gate 5` | Work Item | Living Docs (0DD) & Closure | Documentación Viva (0DD) y Cierre | `docs/`, `TRACEABILITY-MATRIX.md`, `git push` |
| `Gate 6` | Release | Release Readiness | Preparación de Release | `[x] Gate 6 Approved (Human Sign-off)` en `REL-vX.Y.Z.md` + `CHANGELOG.md` + PR a `main` |

---

## 4. Endurecimiento `RFC-003`..`RFC-008`, Motor CI-Agnóstico, `Gate 6` (`v1.2.0`) y Brownfield / *Spec Drift* (`v1.3.0`) (`FWK-005`..`FWK-016`)

- **Seguridad Fail-Closed P0 (`FWK-005`):** `.agents/hooks.json` (UTF-8 sin BOM) invoca `sdd_immutable_feature_guard.py` y `sdd_code_gate_guard.py`, exigiendo `Gate S0` aprobado y marcadores `[x] Gate 1/2/3 Approved` reales en `01..03.md` antes de editar `src/`, `tests/`, `.agents/` o `specs/STACK.md`. `sdd_trim_exec.py` ejecuta comandos con `shell=False` y `sdd_hooks.py` elimina `SDD_FORCE_MAIN_PUSH`.
- **Compilador `sdd:ownership-map`, Transaccionalidad y Motor DAG (`FWK-006`):** `scripts/sdd_ownership.py` compila zonas y valida `forbid_imports` por AST en `verify_architecture_boundaries.py`; `scripts/sdd_generator_tx.py` materializa con backup/rollback y `content_digest` (`--verify`, `--strict-agents`, `--drain-inboxes`); `scripts/sdd_dag.py` (`--verify`, `--plan`) valida aciclicidad en `03-tasks.md` y gobierna transiciones en `.agent-inbox/`.
- **Slimming `< 25k` Tokens, `/bug-fast-track` y `domains/` (`FWK-007`):** El starter mantiene **9 agentes base activos** en `.agents/agents/`, **19 especialistas opt-in** en `.sdd/catalog/specialists-optin/` y **12 arquetipos canónicos únicos** en `.sdd/catalog/archetypes/`. Los defectos acotados utilizan `/bug-fast-track` (`specs/bugs/BUG-XXX-<slug>/{01-bug-report,02-fix-spec,03-tasks}.md` desde `05-bug-fast-track.template.md` preservando `Gate S0` y `[x] Gate 1/2/3 Approved`), y el conocimiento de dominio se carga bajo demanda desde `domains/<domain-slug>/` (`_template/{overview,decisions}.md`).
- **Concurrencia Multi-Worktree y Sync Seguro `<= 500L` (`FWK-008` & `FWK-009`):** `sdd_git_state.py` y `sdd_git_worktree.py` aíslan estado (`.agents/worktree_states/<wt_id>.json`) y puertos (`ports_registry.json`), sincronizando `.agents/ACTIVE_STATE.md`. `sdd_sync.py` opera sin rutas hardcodeadas con `--dry-run`, `--force` y rollback sobre `.agents/.sdd-sync-state.json`. Todos los módulos Python del repositorio cumplen `<= 500` líneas.
- **Endurecimiento Nivel L5: Sellos Criptográficos SHA-256 de Gates, Fronteras Políglotas, Write-Set DAG y Auditoría CI (`FWK-010` / `RFC-004`):** `scripts/sdd_gate_seal.py` (`sdd approve-gate`, `sdd verify-gates`) registra hashes SHA-256 en `.agents/active_work_item.json` (`gate_seals`) y comentarios inline `<!-- sdd:gate-seal ... -->`, bloqueando cualquier alteración post-aprobación en `.agents/scripts/sdd_code_gate_guard.py`; `.agents/scripts/verify_architecture_boundaries.py` extiende `forbid_imports` con `check_polyglot_imports` a `.ts/.tsx/.js/.jsx/.cs/.go/.rs/.java/.kt` ignorando comentarios; `scripts/sdd_dag.py` detecta solapamientos de rutas/globs en olas paralelas (`DagWriteSetCollisionError`, `--auto-split`); y CI valida todos los `03-tasks.md` con `sdd_dag.py --verify` exigiendo `>= 120` tests deterministas.
- **Portabilidad POSIX y Determinismo Temporal en CI (`FWK-011` / `RFC-005`):** `.agents/scripts/sdd_immutable_feature_guard.py` rechaza en modo *fail-closed* rutas con unidad Windows/UNC en entornos POSIX (`^[A-Za-z]:` / `\\?\C:\...`) y `tests/test_sdd_governance.py` ancla el decaimiento temporal de instintos a desplazamientos relativos respecto a `datetime.now(timezone.utc)`.
- **Alineación de Coherencia `v1.1.1` (`FWK-012` / `RFC-006`):** `scripts/sdd_cli.py` incorpora `work-item show/set` en modo `PENDING_APPROVAL` (sin autoaprobar Gates 1..3); los guardias, sellos SHA-256 y `sdd_healthcheck.py` soportan `HOTFIX-*` (triada en `specs/bugs/HOTFIX-*/`) y auditan `specs/spikes/SPIKE-*/SPIKE_REPORT.md` junto a las plantillas `06-spike-report.template.md` y `07-hotfix-fast-track.template.md`; `.sdd/catalog/specialists-optin/spec-miner.md` genera especificaciones SDD (`specs/features/` y `domains/`) protegido por `SDD_CUSTOMIZED_SPECIALISTS` en `scripts/sdd_catalog_import.py`; y `release-finish` / `hotfix-finish` en `scripts/sdd_git.py` operan en flujo PR-first por defecto (`--local-merge` opt-in sin push directo a `main`).
- **Motor CI-Agnóstico Portable (`FWK-013` / `RFC-007`):** `scripts/sdd_ci.py` (invocable como `scripts/sdd_cli.py ci-verify` / `./sdd ci-verify`) unifica todas las verificaciones de gobernanza SDD (`hooks.json` sin BOM ni escapes, `sdd_healthcheck`, cumplimiento 0DD, fronteras AST políglotas, catálogo y `squad.lock.json`, `sdd_dag --verify`, sellos SHA-256, `sdd_git`/`sdd_instincts` y `sdd_tokens_validator --allow-missing`) con salida `text|json`, detección automática `framework` (umbral `>= 120` tests) vs `project` según `Gate S0`, y ejecución opt-in *fail-closed* (`shell=False`) de `specs/STACK.md §2.5` vía `--run-stack` / `--run-stack-if-approved`; `.github/workflows/ci.yml` delega en `ci-verify` y `specs/templates/ci/` ofrece plantillas equivalentes para GitLab CI, Bitbucket Pipelines y shell POSIX.
- **`Gate 6` de Release Readiness y `CHANGELOG.md` Determinista (`FWK-014` / `RFC-007`, `v1.2.0`):** `scripts/sdd_release.py` (`./sdd release prepare|changelog|verify`) instancia `specs/releases/REL-vX.Y.Z.md` desde `specs/templates/08-release-readiness.template.md` sin autoaprobar `Gate 6`, genera bloques idempotentes en `CHANGELOG.md` desde `<prev_tag>..HEAD` cruzados con `BACKLOG.md` y `01-*.md`, e integra preflight *fail-closed* `_run_release_preflight` en `scripts/sdd_git.py` (`release-start` / `release-finish`) junto con `.agents/workflows/gate6-release.md` y la exención `REL-*` en `sdd_ci.py` (`check_gate_seals`).
- **Adopción Brownfield No Destructiva (`FWK-015` / `RFC-008`, `v1.3.0`):** `scripts/sdd_brownfield.py` (`./sdd adopt --dry-run|--apply`, `--with-repo-map`) ejecuta descubrimiento 100% offline de manifiestos, ecosistemas, zonas candidatas y *bounded contexts* (`MAX_SCAN_DEPTH = 3`), filtra scripts inseguros vía `split_safe_chained_command`, crea borradores no destructivos (`specs/STACK.md` con `Gate S0` bloqueado `stack_approved: false`, `docs/knowledge/BROWNFIELD_INVENTORY.md` y `specs/BACKLOG.md`), y enlaza con `.agents/workflows/brownfield-adopt.md`, `./sdd repo-map` y `@spec-miner`.
- **Detector Offline de *Spec Drift*, Zonas *Strangler Fig* y Baseline Retroactiva Ligera (`FWK-016` / `RFC-008`, `v1.3.0`):** `scripts/sdd_drift.py` (`./sdd drift`) detecta offline `UNCOVERED_FILE`, `MISSING_SOURCE_FILE`, `MISSING_SYMBOL` y `UNLINKED_CODE_DRIFT` en zonas `governed`, citas `SRC-###` y ciclos `CR-XXX` cerrados sin mutar features `Done`; `scripts/sdd_ownership.py` y `.agents/scripts/sdd_code_gate_guard.py` aplican `governance: governed | legacy-readonly` (bloqueo *Strangler Fig*); `sdd_healthcheck.py` y `sdd_gate_seal.py` soportan baselines `Origin: brownfield-mined` (eximiendo `03-tasks.md` únicamente si existen firmas humanas reales `[x] Gate 1 Approved` y `[x] Gate 2 Approved`); y `sdd_ci.py` integra `check_spec_drift` (`160/160` tests en verde en `15` suites).
