# Especificación Funcional: Unificación de Terminología de Gates, Estados y Ejecución DAG (`FWK-004`)

- **ID del Work Item:** `FWK-004-gate-terminology-unification`
- **RFC de Origen:** [`RFC-002`](../../rfcs/RFC-002-gate-terminology-unification.md) (`Aceptado`)
- **Estado:** `Done` (Gate 5 completado — 2026-11-13)
- **Responsable:** `@orchestrator`
- **Fecha de Creación:** 2026-11-13
- **Última Actualización:** 2026-11-13

---

## 1. Resumen y Contexto

`FWK-004` elimina las contradicciones normativas, colisiones numéricas (`Gate 00` vs `Gate 0`), divergencias bilingües de estados (`Done`/`Completado`, `Candidato`/`Backlog`) y mezclas conceptuales (`Gate` vs `Block` vs `Session Phase`) detectadas en `AGENTS.md`, `.agents/`, `specs/`, `.sdd/catalog/`, `docs/` y `scripts/`, aplicando la nomenclatura canónica aprobada en `RFC-002` bajo una estrategia **cero ruptura (`Zero-Breaking Dual-Accept`)**.

### Fuentes Registradas (`SRC-###`)

| ID | Origen | Fecha | Descripción |
|---|---|---|---|
| `SRC-001` | Chat / Usuario (PO) | 2026-11-13 | Aprobación del alcance (4 problemas y 4 ámbitos) y aceptación explícita de `RFC-002`. |
| `SRC-002` | Auditoría del repositorio | 2026-11-13 | Evidencias en `AGENTS.md`, `01-sdd-lifecycle.md`, `SDD_FRAMEWORK.md`, `BACKLOG.md`, `templates/`, `scripts/`. |

---

## 2. Historias de Usuario

### HU-01: Desambiguación `Gate S0` vs `Gate 0..5` y Tabla Canónica Única
> **Como** mantenedor o agente SDD,  
> **Quiero** que exista una única tabla canónica bilingüe (`Gate S0` para Stack Lock a nivel de proyecto y `Gate 0..5` para Work Items, incluyendo `Gate 2 Visual Sign-off`),  
> **Para que** no haya contradicciones entre `AGENTS.md`, `.agents/rules/`, `specs/SDD_FRAMEWORK.md`, `specs/BACKLOG.md` y las plantillas.

### HU-02: Vocabulario Canónico de Estados y Consolidación de Plantillas CR
> **Como** `@orchestrator` o `@qa-tester`,  
> **Quiero** un vocabulario unívoco de estados para Work Items (`Candidate` → `Backlog` → `In Progress` → `In Review` → `Done` / `Blocked`), Specs (`Draft` → `In Review` → `Approved` → `Done` / `Superseded`) y RFCs (`Proposed` → `Accepted` / `Rejected`), más una única plantilla de Change Request,  
> **Para que** los tableros, plantillas y guardias automáticos operen sin ambigüedad.

### HU-03: Separación Ortogonal `Gate` vs `Block` vs `Session Phase`
> **Como** agente planificador o ejecutor de DAG,  
> **Quiero** que `Gate` designe exclusivamente las compuertas (`Gate S0`, `Gate 0..5`), `Block` (`Bloque DAG`) las oleadas de `03-tasks.md`, y `Session Phase` la división de contexto (`Sesión A` / `Sesión B`),  
> **Para que** desaparezcan referencias ambiguas como `Fase 1..5` en lugar de `Gate 1..5`.

### HU-04: Compatibilidad Sin Ruptura (`Dual-Accept` Fail-Closed) en Scripts y Guardias
> **Como** usuario con proyectos o specs existentes basados en `Gate 00` / `Completado` / `Propuesto`,  
> **Quiero** que los scripts y guardias acepten tanto la nomenclatura canónica nueva como los literales heredados (fallando en *fail-closed* si coexisten valores contradictorios),  
> **Para que** la actualización del starter nunca rompa repositorios previos.

---

## 3. Alcance (`In-Scope` vs `Out-of-Scope`)

### ✅ Dentro del Alcance (`In-Scope`)
1. **Gobernanza y Agentes:** `AGENTS.md`, `.agents/rules/`, `.agents/agents/`, `.agents/skills/`, `.agents/workflows/`, `.agents/instincts.json`.
2. **Specs, Plantillas y Catálogo SDD:** `specs/SDD_FRAMEWORK.md`, `specs/BACKLOG.md`, `specs/STACK.md`, `specs/templates/` (consolidando `04-change-request-spec.template.md` y `04-change-spec.template.md` en una única plantilla canónica), `.sdd/framework/BACKLOG.md`, `.sdd/catalog/archetypes/` y packs SDD propios (`capability-ui-design`, `capability-web-frontend/agents/a11y-architect.md`).
3. **Documentación Viva y Estándares:** `docs/es/`, `docs/en/`, `docs/knowledge/`, `docs/standards/`, `docs/traceability/`.
4. **Scripts y Tests:** `scripts/sdd_pack_registry.py`, `scripts/sdd_agent_generator.py`, `scripts/sdd_instincts.py`, `.agents/scripts/sdd_stack_gate_guard.py`, `.agents/scripts/sdd_code_gate_guard.py`, `.agents/scripts/sdd_immutable_feature_guard.py`, `.agents/scripts/sdd_healthcheck.py` y suite de tests unitarios.

### 🚫 Fuera del Alcance (`Out-of-Scope`)
- Alterar expedientes históricos cerrados (`Done`) bajo `.sdd/framework/work-items/FWK-001*..FWK-003*` o `RFC-001*` (`RN-SDD-IMMUTABLE-DONE`).
- Modificar ficheros upstream vendorizados en `.sdd/catalog/packs/capability-ui-design/vendor/` ni terminología genérica interna de algoritmos de skills ECC externas que usen `Phase 1/2` fuera del ciclo de Gates SDD.
- Crear o modificar código de producto en `src/`.

---

## 4. Requisitos Funcionales (EARS)

| ID | Patrón EARS | Cláusula EARS | Componente |
|---|---|---|---|
| `RF-001` | `Ubiquitous` | El framework SDD deberá usar la tabla canónica única de `RFC-002` (`Gate S0` para Stack Lock de proyecto; `Gate 0..5` para Work Items; `Gate 2 Visual Sign-off` como sub-gate condicional) en toda regla, agente, plantilla y estándar. | Gobernanza / Docs / Templates |
| `RF-002` | `Ubiquitous` | El framework SDD deberá distinguir de forma estricta `Gate` (compuerta), `Block` / `Bloque DAG` (oleada de tareas en `03-tasks.md`) y `Session Phase` (partición de contexto Sesión A/B), eliminando `Fase 1..5` como sinónimo de `Gate 1..5`. | Gobernanza / `SDD_FRAMEWORK.md` / DAG |
| `RF-003` | `Ubiquitous` | Las plantillas y tableros deberán emitir el vocabulario canónico de estados (`Candidate`/`Backlog`/`In Progress`/`In Review`/`Done`/`Blocked` para Work Items; `Draft`/`In Review`/`Approved`/`Done` para Specs; `Proposed`/`Accepted`/`Rejected` para RFCs) y consolidar una única plantilla para Change Requests. | `specs/` / `templates/` |
| `RF-004` | `Event-driven` | CUANDO `sdd_pack_registry.py` o `sdd_stack_gate_guard.py` evalúen `specs/STACK.md`, el sistema deberá aceptar tanto `[x] Gate S0 Approved` / `stack_approved: true` (canónico) como `[x] Gate 00 Approved` / `gate00_approved: true` (alias legacy). | `scripts/` / `.agents/scripts/` |
| `RF-005` | `Unwanted` | SI en el bloque `yaml sdd:stack-config` coexisten `stack_approved` y `gate00_approved` con valores booleanos distintos, ENTONCES `sdd_pack_registry.py` deberá abortar en *fail-closed* lanzando `StackConfigError`. | `scripts/sdd_pack_registry.py` |
| `RF-006` | `Event-driven` | CUANDO `sdd_immutable_feature_guard.py` o `sdd_healthcheck.py` analicen `specs/BACKLOG.md`, el sistema deberá reconocer tanto los estados canónicos (`Done`, `Draft`, `In Review`, `Gate 1`) como los alias históricos (`Completado`, `Completed`, `Propuesto`). | `.agents/scripts/` |
| `RF-007` | `Ubiquitous` | La plantilla [`01-functional-spec.template.md`](../../../../specs/templates/01-functional-spec.template.md) deberá corregir enlaces rotos o placeholders heredados (como la referencia inexistente `08-ears-requirements-standard.md` hacia `03-ears-requirements.md` y menciones literales a `Project` donde corresponda nombre genérico). | `specs/templates/` |

---

## 5. Criterios de Aceptación BDD (`Given-When-Then`)

### Escenario 1: Aceptación dual de `Gate S0` y alias legacy `Gate 00`
- **Dado que** existe un `specs/STACK.md` válido con `[x] Gate S0 Approved (Human Sign-off)` y `stack_approved: true` (o bien con el alias legacy `[x] Gate 00 Approved` y `gate00_approved: true`),
- **Cuando** se ejecutan `parse_stack_config()` y `check_stack_gate()`,
- **Entonces** ambos validadores aprueban la puerta de Stack Lock con éxito sin romper compatibilidad.

### Escenario 2: Rechazo *fail-closed* ante contradicción `stack_approved` vs `gate00_approved`
- **Dado que** el bloque `yaml sdd:stack-config` de `specs/STACK.md` declara simultáneamente `stack_approved: true` y `gate00_approved: false` (o viceversa),
- **Cuando** `sdd_pack_registry.py` parsea la configuración,
- **Entonces** lanza `StackConfigError` explícito y bloquea cualquier materialización.

### Escenario 3: Reconocimiento de estados canónicos y legacy en guardias de backlog
- **Dado que** `specs/BACKLOG.md` contiene filas con estado `Done` y filas legacy con estado `Completado` o `Propuesto`,
- **Cuando** se ejecutan `sdd_immutable_feature_guard.py` y `sdd_healthcheck.py`,
- **Entonces** las features `Done`/`Completado` quedan protegidas como inmutables y las fichas `Propuesto`/`Draft`/`Gate 1` se detectan correctamente sin falsos positivos.

### Escenario 4: Consistencia documental y cero regresión en suite offline
- **Dado que** se han normalizado los 4 ámbitos de `FWK-004` y preservado `FWK-001`..`FWK-003` intactos,
- **Cuando** se ejecutan la suite completa `pytest` y los checks de integridad (`sdd_healthcheck.py`, `sdd_tokens_validator.py`),
- **Entonces** el 100% de los tests pasan en verde y no quedan referencias normativas contradictorias (`Gate 4` ≠ QA, `Fase 1..5` = Gate, plantilla CR duplicada).

---

## 6. Aprobación Formal Gate 1 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)

- [x] **Gate 1 Approved (Human Sign-off):** El alcance, requisitos EARS y criterios Given-When-Then de `FWK-004` han sido revisados y validados por el usuario.
