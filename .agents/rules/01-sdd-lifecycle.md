# Regla 01: Ciclo de Vida SDD y Gestión del Cambio

## 1. Las 6 Puertas de Calidad (Gate 00 a Gate 5)
Todo incremento en el sistema debe atravesar secuencialmente estas puertas:

| Puerta | Nombre | Entregable Clave | Aprobador |
| :--- | :--- | :--- | :--- |
| **Gate 00** | **Stack Bootstrap** | `specs/STACK.md` firmado | Usuario Humano |
| **Gate 0** | **Backlog Intake** | Registro en `specs/BACKLOG.md` con ID único | Tech Lead / Humano |
| **Gate 1** | **Functional Spec** | `01-spec.md` con Requisitos EARS y Given-When-Then | Usuario Humano |
| **Gate 2** | **Technical Spec** | `02-tech-spec.md` con Arquitectura y Contratos tipados | Usuario Humano |
| **Gate 3** | **Task Graph (DAG)** | `03-tasks.md` con bloques paralelos y DoD determinista | Usuario Humano |
| **Gate 4** | **Verification & QA** | Tests en verde y auditorías de calidad pasadas | @qa-tester / CI |
| **Gate 5** | **Living Documentation** | Living docs 0DD actualizadas en `docs/` | @documentator |

## 2. Inmutabilidad de Features Finalizadas (`RN-SDD-IMMUTABLE-DONE`)
- Los ficheros en `specs/features/FEAT-XXX-*/` de ítems completados son **SOLO LECTURA**.
- Para evolucionar una funcionalidad existente, se crea un Change Request: `specs/changes/CR-XXX-<nombre>/`.
- Se aplica estrictamente la cardinalidad 1:1: **1 CR por cada Feature afectada**.
