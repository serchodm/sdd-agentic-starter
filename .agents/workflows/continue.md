---
description: Retoma el trabajo activo en una sesión limpia (Session Phase B o continuación de Gate/Block) leyendo únicamente ACTIVE_STATE.md y los archivos acotados.
---
Actúa como `@orchestrator` bajo las reglas de `AGENTS.md` iniciando una sesión limpia (`Turno 1/15 | Bloques 0/2`):
1. Lee `.agents/ACTIVE_STATE.md`.
2. PROHIBIDO hacer búsquedas globales en el repositorio o cargar todas las reglas de `.agents/rules/`. Lee ÚNICAMENTE los archivos enumerados bajo `Mandatory Context Files` en `.agents/ACTIVE_STATE.md`.
3. Confirma en un bloque de 3 líneas: Work Item activo, Gate actual y tarea inmediata a ejecutar.
4. Ejecuta directamente el siguiente paso o despacha el bloque (`Block`) de subagentes correspondiente sin pedir confirmación redundante si el Gate ya estaba aprobado.
5. Al finalizar el bloque o Gate, actualiza `.agents/ACTIVE_STATE.md` e incluye el semáforo de salud de contexto en el pie de tu respuesta.
