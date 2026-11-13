---
name: strategic-compact
description: Protocolo de compactación estratégica de contexto en fronteras lógicas de Gate y Bloque DAG (affaan-m/ECC + RN-SDD-CONTEXT-SEMAPHORE) para preservar precisión cognitiva.
---

# Skill: `strategic-compact` (Compactación Estratégica de Contexto en Fronteras de Gate y Bloque)

Adaptada de `strategic-compact` de `affaan-m/ECC` y sincronizada con la regla `RN-SDD-CONTEXT-SEMAPHORE & AUTO-HANDOFF` de Project, esta meta-skill evita que la degradación por ventana de contexto afecte la precisión en tareas multi-bloque.

## 1. Cuándo Compactar y Hacer Handoff (Fronteras Lógicas)

Nunca compactes a mitad de la implementación de un archivo. Ejecuta la consolidación de estado exactamente en estas fronteras naturales:

1. **Transición de Especificación a Implementación (Fin de Gate 3 $\rightarrow$ Inicio de Gate 4 / Sesión B)**:
   - Una vez sellados `01-spec.md`, `02-tech-spec.md` y `03-tasks.md`, el historial de debate de diseño ya no es necesario para los subagentes constructores.
2. **Transición entre Bloques del Grafo DAG (Fin de `BLOCK_1` $\rightarrow$ Inicio de `BLOCK_2`)**:
   - Registrar en `.agents/ACTIVE_STATE.md` los archivos completados y los comandos DoD superados.
3. **Umbral Semáforo Amarillo (`Turn >= 11` o `Blocks == 2`) / Rojo (`Turn >= 15`)**:
   - Actualizar `.agents/ACTIVE_STATE.md` con el resumen ejecutivo de progreso, decisiones técnicas tomadas y la siguiente tarea exacta pendiente.

## 2. Qué Debe Persistir y Qué Debe Descartarse
- **Persistir en `.agents/ACTIVE_STATE.md`**: ID del Work Item activo, Gate actual, tabla de tareas completadas (`[x]`) vs pendientes (`[ ]`), rutas de archivos modificados y comandos DoD verificados.
- **Descartar del Hilo Activo**: Trazas largas de consola ya resueltas, lecturas exploratorias intermedias y diffs obsoletos.
