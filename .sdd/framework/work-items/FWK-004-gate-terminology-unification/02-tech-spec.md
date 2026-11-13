# Especificación Técnica: Unificación de Terminología de Gates, Estados y Ejecución DAG (`FWK-004`)

- **ID del Work Item:** `FWK-004-gate-terminology-unification`
- **Estado:** `Done` (Gate 5 completado — 2026-11-13)
- **Especificación Funcional Asociada:** [`01-spec.md`](01-spec.md) (Gate 1 Approved)
- **RFC Base:** [`RFC-002`](../../rfcs/RFC-002-gate-terminology-unification.md) (`Aceptado`)
- **Tech Lead / Arquitecto:** `@orchestrator`
- **Fecha de Creación:** 2026-11-13
- **Última Actualización:** 2026-11-13

---

## 0. Inventario *Research-First* y Restricciones Verificadas

- **Módulos y contratos existentes inspeccionados:**
  - `scripts/sdd_pack_registry.py` (`494` líneas — techo obligatorio `<= 500` verificado por `test_sdd_pack_materialization.py` y `test_sdd_ui_design.py`).
  - `scripts/sdd_agent_generator.py` (`materialize_squad()` genera `.agents/agents/*` y `.agents/squad.lock.json` v2 con SHA-256).
  - `scripts/sdd_instincts.py` (`seed_core_instincts()` siembra `.agents/instincts.json`).
  - `.agents/scripts/sdd_stack_gate_guard.py`, `.agents/scripts/sdd_code_gate_guard.py`, `.agents/scripts/sdd_immutable_feature_guard.py`, `.agents/scripts/sdd_healthcheck.py`.
  - `tests/test_sdd_pack_materialization.py` (verifica `lock["gate00_approved"]` y `cfg.gate00_approved`) y `tests/test_sdd_ui_design.py` (`test_group6_contractual_assertions_on_real_artefacts`).
- **Frontera Productora Única:**
  - `scripts/sdd_pack_registry.py` es el único parser normativo de `specs/STACK.md` y del bloque `yaml sdd:stack-config`.
  - `.agents/scripts/sdd_stack_gate_guard.py` importa/replica exclusivamente la verificación de marcador humano en `specs/STACK.md` para hooks pre-tool.
- **Líneas Base Inmutables (`RN-SDD-IMMUTABLE-DONE`):**
  - No se modifican `.sdd/framework/work-items/FWK-001*`, `FWK-002*`, `FWK-003*`, `RFC-001*`, ni `vendor/`.

---

## 1. Contratos Técnicos Ejecutables (`scripts/` y `.agents/scripts/`)

### 1.1. `scripts/sdd_pack_registry.py` (Dual-Accept `Gate S0` / `Gate 00`, techo `<= 500` líneas)

1. **Marcadores Humanos aceptados en `specs/STACK.md`:**
   - Canónicos: `"[x] Gate S0 Approved"`, `"[X] Gate S0 Approved"`
   - Alias legacy: `"[x] Gate 00 Approved"`, `"[X] Gate 00 Approved"`
   - `_HUMAN_SIGNOFF_MARKERS` contendrá las 4 variantes.
2. **Claves YAML aceptadas en `sdd:stack-config`:**
   - Clave canónica: `stack_approved` (bool estricto).
   - Alias legacy: `gate00_approved` (bool estricto).
   - **Regla *Fail-Closed* (`RF-005`):**
     - Si ninguna de las dos claves está presente (o la presente no es `bool`), lanzar `StackConfigError`.
     - Si **ambas** están presentes y `stack_approved != gate00_approved`, lanzar `StackConfigError("Conflicting 'stack_approved' and legacy 'gate00_approved' in sdd:stack-config.")`.
     - En otro caso, `approved = stack_val if "stack_approved" in data else gate00_val`.
3. **Compatibilidad de interfaz en `StackConfig`:**
   - `StackConfig` mantiene el campo/propiedad de compatibilidad `gate00_approved` junto a `stack_approved` (ej. atributo `stack_approved: bool` + `@property def gate00_approved(self) -> bool: return self.stack_approved`, o viceversa con `gate00_approved` como alias de lectura) para no romper llamadores existentes (`test_sdd_pack_materialization.py`, `test_sdd_ui_design.py`).
   - *Nota de tamaño:* refactorizar/compactar líneas auxiliares si es necesario para garantizar `<= 500` líneas totales en `scripts/sdd_pack_registry.py`.

### 1.2. `scripts/sdd_agent_generator.py` y `.agents/squad.lock.json`

- En `materialize_squad()`, el manifiesto `squad.lock.json` (`schema_version: 2`) emitirá:
  - `"stack_approved": effective_gate_s0` (campo canónico)
  - `"gate00_approved": effective_gate_s0` (alias retrocompatible para lectores v2 existentes)
- Mensaje de salida: actualiza etiqueta informativa a `gate_s0: {effective_gate_s0}` (manteniendo claridad sin romper contratos).
- Tras modificar `.sdd/catalog/archetypes/*` o `.agents/agents/*`, ejecutar `uv run python scripts/sdd_agent_generator.py --materialize` para sincronizar todos los hashes SHA-256 de `.agents/squad.lock.json`.

### 1.3. `.agents/scripts/sdd_stack_gate_guard.py` y `sdd_code_gate_guard.py`

- `check_stack_gate()` acepta los 4 marcadores: `[x] Gate S0 Approved`, `[X] Gate S0 Approved`, `[x] Gate 00 Approved`, `[X] Gate 00 Approved`.
- Mensajes de error emitidos en español/inglés usan `Gate S0` como término canónico (mencionando `Gate S0 Approved`).
- `sdd_code_gate_guard.py` actualiza comentarios/docstrings de `Gate 00` a `Gate S0` manteniendo intacta la lógica de `validate_active_work_item()`.

### 1.4. `.agents/scripts/sdd_immutable_feature_guard.py` y `.agents/scripts/sdd_healthcheck.py`

- `get_done_features()` mantiene la regex dual-accept `(Done|Completado|Completed)`.
- `sdd_healthcheck.py` en `check_spec_triads()` amplía la detección de expedientes iniciales en Gate 1 para aceptar `draft`, `proposed`, `propuesto` o `gate 1` (siempre excluyendo `done`/`completado`).

### 1.5. `scripts/sdd_instincts.py` y `.agents/instincts.json`

- Actualiza el trigger `inst-anti-rubber-stamp` a `"Al auditar o validar Gate S0, Gate 1, Gate 2 o Gate 3"` y actualiza `.agents/instincts.json` en coherencia.

---

## 2. Normalización Documental y Plantillas (4 Ámbitos)

### 2.1. Tabla Canónica Única y Fuente de Verdad

| ID | Ámbito | EN | ES | Sign-off / Criterio |
|---|---|---|---|---|
| `Gate S0` | Proyecto | Stack Lock | Bloqueo de Stack | `[x] Gate S0 Approved (Human Sign-off)` / `stack_approved: true` |
| `Gate 0` | Work Item | Backlog Intake | Registro en Backlog | ID único en `specs/BACKLOG.md` + carpeta spec |
| `Gate 1` | Work Item | Functional Spec | Especificación Funcional | `[x] Gate 1 Approved (Human Sign-off)` |
| `Gate 2` | Work Item | Technical Spec | Especificación Técnica | `[x] Gate 2 Approved (Human Sign-off)` |
| *Sub-Gate 2V* | Work Item (`SCR-###` / `N/A`) | Visual Sign-off | Validación Visual | `[x] Gate 2 Visual Sign-off (Human)` |
| `Gate 3` | Work Item | Task Graph (DAG) | Plan de Tareas (DAG) | `[x] Gate 3 Approved (Human Sign-off)` |
| `Gate 4` | Work Item | Implementation & QA | Implementación y QA | Tests + 4 auditorías QA + CI en verde |
| `Gate 5` | Work Item | Living Docs (0DD) & Closure | Documentación Viva (0DD) y Cierre | `docs/es/`, `docs/en/`, `docs/knowledge/`, `TRACEABILITY-MATRIX.md`, `git push` |

### 2.2. Ámbitos de Actualización

1. **Gobernanza y Agentes:**
   - `AGENTS.md`: actualizar `RN-SDD-GATE00-STACK-LOCK` → `RN-SDD-GATE-S0-STACK-LOCK` (documentando `Gate 00` como alias legacy), reemplazar `Fase` en Phase Splitting por `Session Phase (Sesión A: Gates 0–3 / Sesión B: Gates 4–5)`, y consolidar tabla de carga perezosa con `Gate S0`, `Gate 0..5`.
   - `.agents/rules/00-stack-lock.md`, `01-sdd-lifecycle.md`, `02-change-management.md`, `03-ears-requirements.md`, `04-multiagent-dag.md`, `06-functional-doc-0dd.md`, `07-engineering-baseline.md`.
   - `.agents/agents/*.md`, `.agents/skills/*/SKILL.md` (los propios SDD: `sdd-bootstrap`, `sdd-change-gate`, `sdd-spec-compliance-audit`, `sdd-test-quality-audit`, `sdd-silent-failure-audit`, `pipeline-run`, `strategic-compact`, `gan-style-harness`, `santa-method`), `.agents/workflows/*.md` (`continue.md`, `gate5.md`, `gan-build.md`, `santa-loop.md`), `.agents/contexts/*.md`.
2. **Specs, Plantillas y Catálogo SDD:**
   - `specs/SDD_FRAMEWORK.md`: alinear diagrama Mermaid y Sección 4 con `Gate S0` + `Gate 0..5` (`Gate 4 = Implementation & QA`, `Gate 5 = Living Docs (0DD) & Closure`), reemplazar `Fase 1..5` por `Gate 1..5`, y unificar estados a `Candidate`/`Backlog`/`In Progress`/`In Review`/`Done`.
   - `specs/BACKLOG.md` y `.sdd/framework/BACKLOG.md`: alinear leyendas (`Candidate` -> `Backlog` -> `In Progress` -> `In Review` -> `Done`) y encabezados de tabla (`Gate 0..5`).
   - `specs/STACK.md` y `specs/templates/00-stack.template.md`: emitir `[ ] Gate S0 Approved (Human Sign-off)` y `stack_approved: false` en `yaml sdd:stack-config` (manteniendo nota del alias legacy `Gate 00` / `gate00_approved`).
   - `specs/templates/01-functional-spec.template.md`, `02-technical-spec.template.md`, `03-tasks.template.md`: unificar estados (`[Draft | In Review | Approved | Done]`), corregir enlace roto `08-ears-requirements-standard.md` → `03-ears-requirements.md` y placeholder `Project` → `[Sistema]`, y estandarizar sign-offs (`[ ] Gate 1 Approved (Human Sign-off)`, `[ ] Gate 2 Approved (Human Sign-off)`, `[ ] Gate 2 Visual Sign-off (Human)`, `[ ] Gate 3 Approved (Human Sign-off)`).
   - **Consolidación de plantillas CR:** fusionar los contenidos útiles de `04-change-spec.template.md` dentro de [`04-change-request-spec.template.md`](../../../../specs/templates/04-change-request-spec.template.md) y eliminar el duplicado `specs/templates/04-change-spec.template.md`.
   - `.sdd/catalog/archetypes/*.archetype.md` y `.sdd/catalog/packs/capability-ui-design/` + `capability-web-frontend/agents/a11y-architect.md`: alinear referencias a `Gate S0`, `Gate 1..5`, `Gate 2 Visual Sign-off (Human)` y `Block` / `Session Phase`.
3. **Documentación Viva y Estándares:**
   - `docs/standards/MULTIAGENT_ORCHESTRATION_STANDARD.md`, `docs/standards/EARS_REQUIREMENTS_STANDARD.md`, `docs/standards/FUNCTIONAL_DOCUMENTATION_STANDARD.md`.
   - `docs/es/`, `docs/en/` (`README.md`, `00-governance/DOCUMENTATION-INDEX.md`, `02-functional/modules/MOD-001/`, `MOD-002/`), `docs/knowledge/` (`SYSTEM_TOPOLOGY.md`, `DATA_MODELS.md`, `API_CATALOG.md`, `ADRS.md` — añadiendo `ADR-005` en Gate 5 sin alterar decisiones históricas previas) y `docs/traceability/TRACEABILITY-MATRIX.md`.

---

## 3. Estrategia de Tests y Verificación (`tests/`)

1. **Tests existentes a preservar / adaptar:**
   - `tests/test_sdd_pack_materialization.py`: sigue pasando con `cfg.gate00_approved` y `lock["gate00_approved"]` intactos; verificar `<= 500` líneas.
   - `tests/test_sdd_ui_design.py`: actualizar las aserciones de `test_group6_contractual_assertions_on_real_artefacts` para reflejar los nuevos literales canónicos (`Gate 2 Visual Sign-off (Human)`, `Gate 0 (Backlog Intake)`).
2. **Nuevo archivo `tests/test_sdd_terminology_unification.py`:**
   - Prueba unitaria de aceptación dual en `parse_stack_config()` (`Gate S0 Approved` + `stack_approved: true`, `Gate 00 Approved` + `gate00_approved: true`, y combinación mixta coherente).
   - Prueba unitaria *fail-closed* ante conflicto (`stack_approved: true` y `gate00_approved: false` -> `StackConfigError`).
   - Prueba unitaria de `check_stack_gate()` con ambos marcadores y rechazo si falta.
   - Prueba unitaria de `get_done_features()` y `check_spec_triads()` con estados canónicos (`Done`, `Draft`) y legacy (`Completado`, `Propuesto`).
   - Prueba contractual de que `04-change-spec.template.md` fue consolidado y no quedan enlaces rotos a `08-ears-requirements-standard.md`.

---

## 4. Aprobación Formal Gate 2 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)

- [x] **Gate 2 Approved (Human Sign-off):** Los contratos dual-accept, el mapa de normalización en los 4 ámbitos y la estrategia de tests de `FWK-004` han sido validados por el usuario.
- **Sub-Gate 2V (Visual Sign-off):** `N/A` *(item de marco/gobernanza sin pantallas `SCR-###`)*.
