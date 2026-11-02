---
description: Ejecuta el cierre documental bilingüe de Gate 5 (@documentator) y git sync en una sesión aislada de bajo coste.
---
Actúa como `@documentator` siguiendo `AGENTS.md`:
1. Lee `.agents/ACTIVE_STATE.md` para identificar la carpeta `specs/` del Work Item activo.
2. Lee únicamente `.agents/rules/03-functional-doc-0dd.md` y los archivos `01-spec.md`, `02-tech-spec.md` y `03-tasks.md` del ítem activo.
3. Actualiza la documentación funcional en `docs/es/` y `docs/en/`, actualiza `TRACEABILITY-MATRIX.md` y consolida `docs/knowledge/*` (`API_CATALOG.md`, `DATA_MODELS.md`, `ADRS.md`, `SYSTEM_TOPOLOGY.md`) utilizando lecturas y ediciones parciales focalizadas (nunca leas archivos históricos enteros si superan 200 líneas).
4. Marca el Gate 5 como completado en las specs y `specs/BACKLOG.md`, deja `.agents/ACTIVE_STATE.md` en estado `IDLE (No Active Work Item)` y ejecuta el commit/push según `RN-SDD-GIT-SYNC`.
