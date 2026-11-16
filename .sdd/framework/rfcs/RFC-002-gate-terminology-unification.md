# RFC-002 — Unificación de Terminología de Gates, Estados y Ejecución DAG

| Campo | Valor |
|---|---|
| **Estado** | `Aceptado` — aprobado e implementado en `FWK-004` (2026-11-13) |
| **Versión** | v1 (2026-11-13) |
| **Ámbito** | Framework (`feat/fwk-004-gate-terminology-unification`); no afecta a `src/` |
| **Work item derivado** | `FWK-004` (P3) — ver [BACKLOG del framework](../BACKLOG.md) |

---

## 1. Problema y Hallazgos Verificados en el Repositorio

Una auditoría transversal de `AGENTS.md`, `.agents/`, `specs/`, `.sdd/`, `docs/` y `scripts/` ha verificado cuatro focos de deriva terminológica y contradicciones normativas:

| # | Problema | Evidencia verificada | Impacto |
|---|---|---|---|
| P1 | **Colisión visual y semántica `Gate 00` vs `Gate 0`** | `.agents/rules/01-sdd-lifecycle.md` (L8–9) y `.agents/agents/orchestrator.md` (L32–39) definen `Gate 00` (Stack Lock) y `Gate 0` (Backlog Intake). En contraste, `specs/SDD_FRAMEWORK.md` (L123–141) y `specs/BACKLOG.md` (L7–9) omiten `Gate 00` por completo y arrancan en `Gate 0`. `.agents/ACTIVE_STATE.md` llegó a mezclar `Gate 0 / Preparación`. | Confusión entre la puerta única de proyecto (Stack Lock) y la puerta por Work Item (Backlog Intake). |
| P2 | **Nombres divergentes de Gates y Sign-offs** | `01-sdd-lifecycle.md` (L13–14) define `Gate 4 = Verification & QA` y `Gate 5 = Living Documentation`. Sin embargo, `specs/SDD_FRAMEWORK.md` (L174–181) llama `Gate 4` a *"Implementación Guiada por Tareas"* y `Gate 5` a *"Verificación Integral y DoD"*, omitiendo la documentación viva `0DD`. Los sign-offs también varían (`[x] Gate 00 Approved (Human Sign-off)`, `[x] Visual Sign-off (Human)`, `[ ] Gate 2 Aprobado por el Usuario`). | Contradicción directa entre el estándar maestro y las reglas operativas de los agentes. |
| P3 | **Estados inconsistentes y plantillas CR duplicadas** | `specs/BACKLOG.md` usa `Backlog -> In Progress -> In Review -> Done`; `.sdd/framework/BACKLOG.md` añade `Candidato`; `SDD_FRAMEWORK.md` (L216, L296) mezcla `Pending` y `Completado`; `01`/`02` templates usan `[Borrador \| En Revisión \| Aprobado \| En Implementación \| Completado]`; existen dos plantillas de CR distintas (`04-change-request-spec.template.md` y `04-change-spec.template.md`) con estados dispares. | Riesgo de falsos negativos o fricción en guardias (`sdd_immutable_feature_guard.py`, `sdd_healthcheck.py`) y confusión en tableros. |
| P4 | **Uso indistinto de `Gate`, `Bloque` y `Fase`** | `SDD_FRAMEWORK.md` (L123–133, L256) numera los tramos como `Fase 1..5`; `orchestrator.md` (L23, L30) habla de *"Ciclo de Vida por Fases"* y *"avanza de fase"*; `AGENTS.md` (L37, L44) usa `Phase Splitting` y `Blocks: Y/2`; `03-tasks.template.md` usa `Bloque A..D`. | Ambigüedad al coordinar DAG (`Blocks`), partición de contexto (`Session Phase`) y compuertas (`Gates`). |

---

## 2. Propuesta de Nomenclatura Canónica (Fuente Única de Verdad)

### 2.1. Desambiguación `Gate S0` vs `Gate 0..5` y Tabla Canónica Bilingüe

Se separa explícitamente el **ámbito de repositorio** (`Gate S0`) del **ámbito de Work Item** (`Gate 0` a `Gate 5`), fijando una única tabla normativa ES/EN y un formato homogéneo de sign-offs:

| ID | Ámbito | Nombre Canónico (EN) | Nombre Canónico (ES) | Entregable / Verificación Clave | Sign-off Humano Canónico |
|---|---|---|---|---|---|
| **`Gate S0`** | Proyecto (1 vez / cambios de stack) | **Stack Lock** | **Bloqueo de Stack** | `specs/STACK.md` + `sdd:stack-config` | `[x] Gate S0 Approved (Human Sign-off)` / `stack_approved: true` |
| **`Gate 0`** | Work Item | **Backlog Intake** | **Registro en Backlog** | Entrada registrada en `specs/BACKLOG.md` + carpeta spec | N/A (Tech Lead / Humano) |
| **`Gate 1`** | Work Item | **Functional Spec** | **Especificación Funcional** | `01-spec.md` (EARS + BDD) / `01-bug-report.md` | `[x] Gate 1 Approved (Human Sign-off)` |
| **`Gate 2`** | Work Item | **Technical Spec** | **Especificación Técnica** | `02-tech-spec.md` / `02-fix-spec.md` (+ ADRs) | `[x] Gate 2 Approved (Human Sign-off)` |
| *Sub-Gate 2V* | Work Item (`SCR-###` o `N/A`) | **Visual Sign-off** | **Validación Visual** | Prototipo hi-fi + `MASTER@x.y.z` + `@a11y-architect` | `[x] Gate 2 Visual Sign-off (Human)` |
| **`Gate 3`** | Work Item | **Task Graph (DAG)** | **Plan de Tareas (DAG)** | `03-tasks.md` con bloques y DoD determinista | `[x] Gate 3 Approved (Human Sign-off)` |
| **`Gate 4`** | Work Item | **Implementation & QA** | **Implementación y QA** | Código, tests, 4 auditorías QA y CI verde | `@qa-tester` + CI (+ revisión humana ante `INCONCLUSIVE`) |
| **`Gate 5`** | Work Item | **Living Docs (0DD) & Closure** | **Documentación Viva (0DD) y Cierre** | `docs/es/`, `docs/en/`, `docs/knowledge/`, `TRACEABILITY-MATRIX.md`, `git push` | `@documentator` + `@orchestrator` |

### 2.2. Vocabulario Canónico de Estados

Para evitar mezclas bilingües en tablas, metadatos y parsers, los estados normativos pasan a ser unívocos en inglés (con equivalentes descriptivos en prosa cuando aplique):

1. **Work Items (`FEAT-XXX`, `CR-XXX`, `BUG-XXX`, `FWK-XXX`)**:
   `Candidate` → `Backlog` → `In Progress` → `In Review` → `Done` *(y `Blocked` ante impedimento externo)*.
2. **Documentos de Especificación (`01-*`, `02-*`, `03-*`)**:
   `Draft` → `In Review` → `Approved` → `Done` *(o `Superseded`)*.
3. **RFCs del Framework (`.sdd/framework/rfcs/`)**:
   `Proposed` → `Accepted` / `Rejected` *(nota: en `.sdd/framework/` los RFCs existentes conservan `Aceptado` como alias histórico válido)*.

### 2.3. Separación Ortogonal: `Gate` vs `Block` vs `Session Phase`

- **`Gate` (`Gate S0`, `Gate 0..5`)**: exclusivamente las compuertas de calidad del ciclo SDD. Queda prohibido usar *"Fase 1..5"* como sinónimo de *"Gate 1..5"*.
- **`Block` / `Bloque DAG` (`Block_A..D`)**: exclusivamente las oleadas de ejecución dentro de `03-tasks.md` (`Gate 3` / `Gate 4`, reflejadas en `Blocks: Y/2` del semáforo).
- **`Session Phase` (`Sesión A` / `Sesión B`)**: exclusivamente la división de contexto entre sesiones (*Phase Splitting*: Sesión A = Gates 0–3, Sesión B = Gates 4–5).

---

## 3. Estrategia de Compatibilidad Sin Ruptura (`Zero-Breaking Dual-Accept`)

Para no romper proyectos existentes, historiales `Done` ni guardias actuales:

1. **Guardias y Registro de Packs (`scripts/sdd_pack_registry.py`, `.agents/scripts/sdd_stack_gate_guard.py`)**:
   - Aceptan como válidos tanto los literales canónicos nuevos (`[x] Gate S0 Approved` / `stack_approved: true`) como los literales heredados (`[x] Gate 00 Approved` / `gate00_approved: true`).
   - **Regla fail-closed ante conflicto**: si en el mismo `yaml sdd:stack-config` aparecen simultáneamente `stack_approved` y `gate00_approved` con valores booleanos distintos, el parser aborta con `StackConfigError`.
   - `specs/templates/00-stack.template.md`, `specs/STACK.md` y la skill `sdd-bootstrap` pasan a **emitir** la forma canónica (`Gate S0` / `stack_approved`), manteniendo documentado el alias legacy.
2. **Guardias de Inmutabilidad y Healthcheck (`.agents/scripts/sdd_immutable_feature_guard.py`, `.agents/scripts/sdd_healthcheck.py`)**:
   - Reconocen los estados canónicos (`Done`, `Draft`, `In Review`, `Gate 1`) y conservan los alias históricos (`Completado`, `Completed`, `Propuesto`) para no romper tableros existentes.
3. **Inmutabilidad de Líneas Base Históricas (`RN-SDD-IMMUTABLE-DONE`)**:
   - No se modifican expedientes ya cerrados bajo `.sdd/framework/work-items/FWK-001*..FWK-003*` ni `RFC-001*`.
   - Tampoco se alteran ficheros upstream `vendor/` ni vocabulario genérico interno de skills externas (p. ej. algoritmos iterativos de ECC que usen `Phase 1/2` fuera del ciclo de Gates SDD).

---

## 4. Alcance Previsto para `FWK-004`

Si se acepta este RFC, `FWK-004` normalizará los cuatro ámbitos acordados:

1. **Gobernanza y Agentes**: `AGENTS.md`, `.agents/rules/`, `.agents/agents/`, `.agents/skills/`, `.agents/workflows/`, `.agents/instincts.json` (regeneración controlada).
2. **Specs, Plantillas y Catálogo SDD**: `specs/SDD_FRAMEWORK.md`, `specs/BACKLOG.md`, `specs/STACK.md`, `specs/templates/` (consolidando las plantillas duplicadas de Change Request en una sola fuente canónica), `.sdd/framework/BACKLOG.md`, `.sdd/catalog/archetypes/` y packs SDD propios (`.sdd/catalog/packs/capability-ui-design/`, `capability-web-frontend/agents/a11y-architect.md`).
3. **Documentación Viva y Estándares**: `docs/es/`, `docs/en/`, `docs/knowledge/`, `docs/standards/`, `docs/traceability/`.
4. **Scripts y Tests**: `scripts/sdd_pack_registry.py`, `scripts/sdd_agent_generator.py`, `scripts/sdd_instincts.py`, `.agents/scripts/sdd_stack_gate_guard.py`, `.agents/scripts/sdd_code_gate_guard.py`, `.agents/scripts/sdd_immutable_feature_guard.py`, `.agents/scripts/sdd_healthcheck.py`, más tests unitarios de compatibilidad dual y detección de conflictos.

---

## 5. Decisión del Mantenedor (`RN-SDD-HUMAN-GATE-OWNERSHIP`)

- [ ] **RFC-002 Aceptado por el Usuario** *(habilita la apertura de Gate 1 de `FWK-004-gate-terminology-unification`)*.
