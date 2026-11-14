---
description: Retoma el trabajo activo en una sesión limpia leyendo únicamente ACTIVE_STATE.md y Mandatory Context Files.
---
Actúa como `@orchestrator` (`Turno 1/15 | Bloques 0/2`):
1. Lee `.agents/ACTIVE_STATE.md`.
2. Prohibido explorar el repo o cargar `.agents/rules/` completo; lee SOLO los archivos bajo `Mandatory Context Files`.
3. Resume en 3 líneas Work Item, Gate y tarea inmediata, ejecuta el siguiente paso/bloque (sin reconfirmar Gates ya aprobados) y actualiza `.agents/ACTIVE_STATE.md` + semáforo al cerrar.
