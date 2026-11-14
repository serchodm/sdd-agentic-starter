---
name: strategic-compact
description: Compactación estratégica de contexto en fronteras de Gate y Bloque DAG (affaan-m/ECC + RN-SDD-CONTEXT-SEMAPHORE) para preservar precisión cognitiva.
---

# Skill: `strategic-compact`

Sincronizada con `RN-SDD-CONTEXT-SEMAPHORE & AUTO-HANDOFF`: consolida estado solo en fronteras lógicas (nunca a mitad de un fichero):

1. **Fronteras de Handoff:** Fin de Gate 3 $\rightarrow$ Gate 4 (Sesión B), fin de cada `BLOCK_X` DAG, o al alcanzar umbral Semáforo Amarillo (`Turn >= 11` / `Blocks == 2`) o Rojo (`Turn >= 15`).
2. **Persistir en `.agents/ACTIVE_STATE.md`:** Work Item activo, Gate actual, tareas `[x]` vs `[ ]`, archivos modificados, comandos DoD verificados y `Mandatory Context Files` (máx. 4).
3. **Descartar del Hilo:** Trazas largas resueltas, exploraciones previas y diffs antiguos.
