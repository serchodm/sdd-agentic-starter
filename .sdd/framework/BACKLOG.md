# Backlog del Framework SDD

## RFCs

| ID | Título | Versión | Estado | Fecha |
| :--- | :--- | :--- | :--- | :--- |
| [`RFC-001`](./rfcs/RFC-001-ui-ux-pro-max.md) | Integración de UI UX Pro Max | v2 | Aceptado | 2026-11-10 |
| [`RFC-002`](./rfcs/RFC-002-gate-terminology-unification.md) | Unificación de Terminología de Gates, Estados y Ejecución DAG | v1 | Aceptado | 2026-11-13 |

## Work Items

| ID | RFC | Título | Prioridad | Depende de | Gate 1 | Gate 2 | Gate 3 | Gate 4 | Gate 5 | Estado |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `FWK-001` | RFC-001 | Materialización y activación fiables de packs | P0 | — | [x] | [x] | [x] | [x] | [x] | Done |
| `FWK-002` | RFC-001 | Pack `capability-ui-design` (UI UX Pro Max) | P1 | FWK-001 | [x] | [x] | [x] | [x] | [x] | Done |
| `FWK-003` | RFC-001 | Quality gates visuales condicionales | P2 | FWK-002 | [x] | [x] | [x] | [x] | [x] | Done |
| `FWK-004` | RFC-002 | Unificar terminología de Gates | P3 | — | [x] | [x] | [x] | [x] | [x] | Done |

*Estados: `Candidate` → `Backlog` → `In Progress` → `In Review` → `Done`. Los items de un RFC solo pasan a `In Progress` tras su aceptación.*
