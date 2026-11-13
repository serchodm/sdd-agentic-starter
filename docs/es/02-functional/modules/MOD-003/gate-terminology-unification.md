<p align="right">
  <a href="../../../../en/02-functional/modules/MOD-003/gate-terminology-unification.md">🇬🇧 English (EN-GB)</a> | <strong>🇪🇸 Español (ES-ES)</strong>
</p>

# `MOD-003`: Unificación de Terminología de Gates, Estados y Grafo DAG

- **Identificador de Módulo:** `MOD-003`
- **Work Item / RFC de Origen:** `FWK-004-gate-terminology-unification` ([`RFC-002`](../../../../../.sdd/framework/rfcs/RFC-002-gate-terminology-unification.md))
- **Estado Funcional:** `Verified` (Confirmado y verificado por 67 tests unitarios offline)
- **Índice Maestro:** [DOCUMENTATION-INDEX.md](../../../00-governance/DOCUMENTATION-INDEX.md)

---

## 1. Propósito y Alcance

### 1.1. Propósito (Confirmado)
Este módulo elimina las ambigüedades normativas, colisiones numéricas (`Gate 00` vs `Gate 0`), divergencias bilingües de estados (`Done`/`Completado`) y mezclas conceptuales (`Gate` vs `Block` vs `Session Phase`) a lo largo de todo el starter.

Asegura que desarrolladores humanos y agentes de IA compartan un modelo mental inequívoco con soporte retrocompatible estricto (*zero-breaking dual-accept*) y validación de fallos cerrada (*fail-closed*).

### 1.2. Alcance Incluido (Confirmado)
- **Tabla Canónica Única de Gates:** `Gate S0` para Stack Lock de proyecto (`specs/STACK.md`) y `Gate 0..5` para Work Items (incluyendo el condicional `Sub-Gate 2V` para validación visual de pantallas `SCR-###`).
- **Separación Ortogonal Conceptual:**
  - `Gate`: Compuertas de calidad y gobierno SDD (`Gate S0`, `Gate 0..5`).
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
| **Usuario Humano / Tech Lead** | Autoriza compuertas formales mediante sign-off humano explícito (`[x] Gate S0 Approved`, `[x] Gate 1 Approved`, `[x] Gate 2 Approved`, `[x] Gate 2 Visual Sign-off`, `[x] Gate 3 Approved`). | Los agentes de IA nunca autoaprueban gates (`RN-SDD-HUMAN-GATE-OWNERSHIP`). |
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
| `Gate 3` | Work Item | Task Graph (DAG) | Plan de Tareas (DAG) | `[x] Gate 3 Approved (Human Sign-off)` |
| `Gate 4` | Work Item | Implementation & QA | Implementación y QA | Tests + 4 auditorías de calidad en verde |
| `Gate 5` | Work Item | Living Docs (0DD) & Closure | Documentación Viva (0DD) y Cierre | `docs/`, `TRACEABILITY-MATRIX.md`, `git push` |
