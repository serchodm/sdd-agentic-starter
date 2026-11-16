# Change Request (CR): [Título del Cambio]

- **ID del Change Request**: [Ej. CR-004-avatar-engine-dual-representation]
- **Feature Base Afectada (Cardinalidad 1:1 — `RN-SDD-1-TO-1-CR`)**: [`FEAT-XXX`](../features/FEAT-XXX-slug/01-spec.md)
- **Estado**: [Draft | In Review | Approved | Done]
- **Responsables**: `@ai-architect` & `@orchestrator`
- **Fecha**: YYYY-MM-DD

> 🔒 **Recordatorio `RN-SDD-IMMUTABLE-DONE`:** La carpeta de la Feature original (`specs/features/FEAT-XXX-*/`) permanece **inmutable en modo lectura (Read-Only)**. Todo el alcance funcional, técnico y de tareas de esta evolución se gobierna desde este expediente `CR-XXX`.

---

## 1. Motivo del Cambio y Resumen Ejecutivo
[Explicación de por qué evoluciona la Feature base (ej. sustitución de librería, nuevo contrato de eventos, rediseño visual) y qué valor aporta.]

---

## 2. Alcance Delta (Delta Scope)

### 🔄 Modificaciones Directas
- [Elemento que se modifica o rediseña respecto a la especificación base]

### ➕ Nuevos Elementos Incorporados
- [Nuevas capacidades, contratos o comportamientos que se agregan]

### 🚫 Elementos Obsoletos / Retirados (Zero Zombie Code)
- [Elementos, archivos o tipos que se deprecian o eliminan de la implementación anterior]

### 🔒 Invariantes que se Mantienen Intactas
- [Capacidades base que no deben verse alteradas ni sufrir regresiones]

---

## 3. Matriz Comparativa del Delta (`Antes en FEAT-XXX` vs. `Después en CR-XXX`)

| Dimensión / Contrato | Estado Original en `FEAT-XXX` (Baseline Inmutable) | Nuevo Estado en `CR-XXX` (Delta Propuesto) |
| :--- | :--- | :--- |
| **Motor / Librería** | [Ej. Shaders GLSL propios en `frontend/src/...`] | [Ej. Paquete cerrado `@paco/avatar-engine` V18.6.0] |
| **Contratos / Eventos** | [Ej. Estado interno en store] | [Ej. Adaptador hacia `avatar.*`] |
| **Código Obsoleto a Eliminar** | [Archivos antiguos en uso] | [Archivos antiguos eliminados al 100% en esta entrega] |

---

## 4. Historias de Usuario Delta y Criterios BDD (`Given-When-Then`)

### Historia Delta 1: [Título]
> **Como** [actor],  
> **Quiero** [nueva capacidad o comportamiento modificado],  
> **Para** [beneficio medible].

#### Escenario 1: [Nombre del Escenario]
- **Dado que** [precondición]
- **Cuando** [acción]
- **Entonces** [resultado verificable]

---

## 5. Aprobación Formal del Stakeholder (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
- [ ] **Gate 1 Approved (Human Sign-off):** El alcance delta funcional y criterios BDD han sido validados.
- [ ] **Gate 2 Approved (Human Sign-off):** La arquitectura técnica delta y contratos han sido validados.
- [ ] **Gate 3 Approved (Human Sign-off):** El plan de tareas DAG y DoR han sido validados.
