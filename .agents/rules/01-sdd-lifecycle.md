# Regla 01: Ciclo de Vida SDD y Gestión del Cambio

## 1. Puertas de Calidad Canónicas (Gate S0, Gate 0–5)
| Puerta | Ámbito | Sign-off / Criterio | Aprobador |
| :--- | :--- | :--- | :--- |
| **Gate S0** | Proyecto | `[x] Gate S0 Approved` / `stack_approved: true` (legacy: `Gate 00`) | Humano |
| **Gate 0** | Work Item | ID único en `specs/BACKLOG.md` + carpeta spec | Tech Lead / Humano |
| **Gate 1** | Work Item | `[x] Gate 1 Approved (Human Sign-off)` (EARS + Given-When-Then) | Humano |
| **Gate 2** | Work Item | `[x] Gate 2 Approved (Human Sign-off)` (Arquitectura y contratos) | Humano |
| ***Sub-Gate 2V*** | Work Item | `[x] Gate 2 Visual Sign-off (Human)` (pantallas `SCR-###` o `N/A`) | Humano |
| **Gate 3** | Work Item | `[x] Gate 3 Approved (Human Sign-off)` (DAG `Block` + DoD) | Humano |
| **Gate 4** | Work Item | Tests + auditorías QA + CI verde | @qa-tester / CI |
| **Gate 5** | Work Item | `docs/es/`, `docs/en/`, `docs/knowledge/`, `TRACEABILITY-MATRIX.md`, `git push` | @documentator |

## 2. Inmutabilidad (`RN-SDD-IMMUTABLE-DONE`) y `RN-SDD-1-TO-1-CR`
- Carpetas `specs/features/FEAT-XXX-*/` en estado `Done` son **SOLO LECTURA**.
- Todo cambio posterior requiere **1 Change Request por Feature afectada**: `specs/changes/CR-XXX-<nombre>/`.
