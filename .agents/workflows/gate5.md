---
description: Ejecuta Gate 5 (Living Docs 0DD con @documentator) y git sync en sesión aislada.
---
Actúa como `@documentator` (`AGENTS.md`):
1. Lee `.agents/ACTIVE_STATE.md`, `.agents/rules/06-functional-doc-0dd.md` y `01-spec.md`/`02-tech-spec.md`/`03-tasks.md` del Work Item activo.
2. Con lecturas/ediciones parciales, actualiza `docs/es/`, `docs/en/`, `docs/traceability/TRACEABILITY-MATRIX.md` y `docs/knowledge/{API_CATALOG,DATA_MODELS,ADRS,SYSTEM_TOPOLOGY}.md`.
3. Marca `Done` en `specs/BACKLOG.md`, reinicia `.agents/ACTIVE_STATE.md` a `IDLE` y ejecuta commit/push (`RN-SDD-BRANCH-SYNC`; nunca a `main`).
