---
description: Guarda el estado actual de la sesión en ACTIVE_STATE.md para hacer handoff a un hilo limpio.
---
Ejecuta el protocolo RN-SDD-AUTO-CHECKPOINT:
1. Detén cualquier ejecución de código o despacho de subagentes en curso.
2. Sobrescribe `.agents/ACTIVE_STATE.md` (máximo 25 líneas) reflejando el Work Item actual, el Gate exacto, la siguiente tarea pendiente en `03-tasks.md`, el nivel de modelo recomendado para el siguiente paso y la lista cerrada de máximo 4 archivos en `Mandatory Context Files`.
3. No leas ni explores archivos adicionales para hacer este resumen.
4. Responde únicamente:
   "✅ **Handoff listo en `.agents/ACTIVE_STATE.md`**.
   - **Siguiente objetivo:** [Next Execution Target]
   - **Modelo recomendado:** [Recommended Model Tier]
   👉 Abre una sesión nueva y escribe `/continue` (o `/gate5` si corresponde cierre documental)."
