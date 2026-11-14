---
description: Guarda el estado de sesión en .agents/ACTIVE_STATE.md para handoff a un hilo limpio.
---
Protocolo `RN-SDD-AUTO-CHECKPOINT`:
1. Detén ejecuciones o despachos en curso.
2. Sobrescribe `.agents/ACTIVE_STATE.md` (máx. 25 líneas) con Work Item, Gate actual, siguiente tarea pendiente en `03-tasks.md`, modelo recomendado y máx. 4 rutas en `Mandatory Context Files`.
3. Sin lecturas adicionales, responde:
   "✅ **Handoff listo en `.agents/ACTIVE_STATE.md`**. Siguiente objetivo: [Target] | Modelo: [Tier]. Abre sesión nueva con `/continue` (o `/gate5`)."
