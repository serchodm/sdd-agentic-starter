# Change Request (CR): [Título del Cambio]

- **ID del Change Request**: [Ej. CR-004-avatar-engine-dual-representation]
- **Feature Base Afectada (Cardinalidad 1:1 — `RN-SDD-1-TO-1-CR`)**: [`FEAT-XXX`](../features/FEAT-XXX-slug/01-spec.md)
- **Estado**: [Propuesto | Aprobado Gate 1-3 | En Implementación | Completado]
- **Responsables**: `@ai-architect` & `@jarvis`
- **Fecha**: YYYY-MM-DD

> 🔒 **Recordatorio `RN-SDD-IMMUTABLE-DONE`:** La carpeta de la Feature original (`specs/features/FEAT-XXX-*/`) permanece **inmutable en modo lectura (Read-Only)**. Todo el alcance funcional, técnico y de tareas de esta evolución se gobierna desde este expediente `CR-XXX`.

---

## 1. Motivo del Cambio y Resumen Ejecutivo
[Explicación de por qué evoluciona la Feature base (ej. sustitución de librería, nuevo contrato de eventos, rediseño visual) y qué valor aporta.]

---

## 2. Matriz Comparativa del Delta (`Antes en FEAT-XXX` vs. `Después en CR-XXX`)

| Dimensión / Contrato | Estado Original en `FEAT-XXX` (Baseline Inmutable) | Nuevo Estado en `CR-XXX` (Delta Propuesto) |
| :--- | :--- | :--- |
| **Motor / Librería** | [Ej. Shaders GLSL propios en `frontend/src/...`] | [Ej. Paquete cerrado `@paco/avatar-engine` V18.6.0] |
| **Contratos / Eventos** | [Ej. Estado interno en store] | [Ej. Adaptador hacia `avatar.*`] |
| **Código Obsoleto a Eliminar** | [Archivos antiguos en uso] | [Archivos antiguos eliminados al 100% en esta entrega] |

---

## 3. Historias de Usuario Delta y Criterios BDD (`Given-When-Then`)

### Historia Delta 1: [Título]
> **Como** [actor],
> **Quiero** [nueva capacidad o comportamiento modificado],
> **Para** [beneficio medible].

#### Escenario 1: [Nombre del Escenario]
- **Dado que** [precondición]
- **Cuando** [acción]
- **Entonces** [resultado verificable]

---

## 4. Aprobación Formal del Stakeholder (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
- [ ] **Gate 1 (Funcional) Aprobado por el Usuario**
- [ ] **Gate 2 (Técnico) Aprobado por el Usuario**
- [ ] **Gate 3 (Tareas / DoR) Aprobado por el Usuario**
