# Backlog del Framework SDD

## RFCs

| ID | Título | Versión | Estado | Fecha |
| :--- | :--- | :--- | :--- | :--- |
| [`RFC-001`](./rfcs/RFC-001-ui-ux-pro-max.md) | Integración de UI UX Pro Max | v2 | Aceptado | 2026-11-10 |
| [`RFC-002`](./rfcs/RFC-002-gate-terminology-unification.md) | Unificación de Terminología de Gates, Estados y Ejecución DAG | v1 | Aceptado | 2026-11-13 |
| [`RFC-003`](./rfcs/RFC-003-audit-remediation-and-hardening.md) | Endurecimiento Integral Post-Auditoría Adversarial, Ownership Compiler, Concurrencia y Slimming (`AUD-001`..`AUD-025`) | v1 | Aceptado | 2026-11-14 |

## Work Items

| ID | RFC | Título | Prioridad | Depende de | Gate 1 | Gate 2 | Gate 3 | Gate 4 | Gate 5 | Estado |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `FWK-001` | RFC-001 | Materialización y activación fiables de packs | P0 | — | [x] | [x] | [x] | [x] | [x] | Done |
| `FWK-002` | RFC-001 | Pack `capability-ui-design` (UI UX Pro Max) | P1 | FWK-001 | [x] | [x] | [x] | [x] | [x] | Done |
| `FWK-003` | RFC-001 | Quality gates visuales condicionales | P2 | FWK-002 | [x] | [x] | [x] | [x] | [x] | Done |
| `FWK-004` | RFC-002 | Unificar terminología de Gates | P3 | — | [x] | [x] | [x] | [x] | [x] | Done |
| `FWK-005` | RFC-003 | Stop-the-Line P0 Seguridad, Hooks Fail-Closed, Anti-RCE y Contención Worktrees | P0 | FWK-004 | [x] | [x] | [x] | [ ] | [ ] | In Progress |
| `FWK-006` | RFC-003 | Compilador `sdd:ownership-map`, Registry Targets, Generador Transaccional y DAG Engine | P1 | FWK-005 | [x] | [x] | [x] | [ ] | [ ] | Backlog |
| `FWK-007` | RFC-003 | Slimming de Contexto (`<25k` tokens), Limpieza PACO y Fast-Track `BUG-XXX` / `domains/` | P1 | FWK-005 | [x] | [x] | [x] | [ ] | [ ] | Backlog |
| `FWK-008` | RFC-003 | Concurrencia Multi-Worktree en `sdd_git` (`<=500L`) y Sincronía `ACTIVE_STATE` | P1 | FWK-005 | [x] | [x] | [x] | [ ] | [ ] | Backlog |
| `FWK-009` | RFC-003 | Sync Seguro (`--dry-run`), Hardening CI/0DD, `pyproject.toml` y Split Modular `<=500L` | P2 | FWK-005 | [x] | [x] | [x] | [ ] | [ ] | Backlog |

*Estados: `Candidate` → `Backlog` → `In Progress` → `In Review` → `Done`. Los items de un RFC solo pasan a `In Progress` tras su aceptación.*
