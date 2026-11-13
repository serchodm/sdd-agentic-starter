# Regla 01: Ciclo de Vida SDD y Gestión del Cambio

## 1. Las Puertas de Calidad Canónicas (Gate S0, Gate 0 a Gate 5)
Todo incremento en el sistema debe atravesar secuencialmente estas puertas de calidad:

| Puerta | Ámbito | Nombre (EN) | Nombre (ES) | Sign-off / Criterio de Superación | Aprobador |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Gate S0** | Proyecto | Stack Lock | Bloqueo de Stack | `[x] Gate S0 Approved` / `stack_approved: true` (legacy: `Gate 00`) | Usuario Humano |
| **Gate 0** | Work Item | Backlog Intake | Registro en Backlog | ID único en `specs/BACKLOG.md` + carpeta spec | Tech Lead / Humano |
| **Gate 1** | Work Item | Functional Spec | Especificación Funcional | `[x] Gate 1 Approved (Human Sign-off)` (EARS + Given-When-Then) | Usuario Humano |
| **Gate 2** | Work Item | Technical Spec | Especificación Técnica | `[x] Gate 2 Approved (Human Sign-off)` (Arquitectura y contratos) | Usuario Humano |
| ***Sub-Gate 2V*** | Work Item | Visual Sign-off | Validación Visual | `[x] Gate 2 Visual Sign-off (Human)` (pantallas `SCR-###` o `N/A`) | Usuario Humano |
| **Gate 3** | Work Item | Task Graph (DAG) | Plan de Tareas (DAG) | `[x] Gate 3 Approved (Human Sign-off)` (Bloques `Block` y DoD) | Usuario Humano |
| **Gate 4** | Work Item | Implementation & QA | Implementación y QA | Tests + 4 auditorías QA + CI en verde | @qa-tester / CI |
| **Gate 5** | Work Item | Living Docs (0DD) & Closure | Documentación Viva (0DD) y Cierre | `docs/es/`, `docs/en/`, `docs/knowledge/`, `TRACEABILITY-MATRIX.md`, `git push` | @documentator |

## 2. Inmutabilidad de Features Finalizadas (`RN-SDD-IMMUTABLE-DONE`)
- Los ficheros en `specs/features/FEAT-XXX-*/` de ítems completados (`Done`) son **SOLO LECTURA (LÍNEA BASE HISTÓRICA INMUTABLE)**.
- Para evolucionar una funcionalidad existente, se crea un Change Request: `specs/changes/CR-XXX-<nombre>/`.
- Se aplica estrictamente la cardinalidad 1:1: **1 CR por cada Feature afectada** (`RN-SDD-1-TO-1-CR`).
