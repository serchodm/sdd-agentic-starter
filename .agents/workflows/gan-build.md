---
description: Ejecuta el bucle Generador-Evaluador del GAN-Style Harness (gan-planner -> gan-generator -> gan-evaluator) con rúbrica ponderada >= 8.5/10.
---

# Workflow `/gan-build` — Construcción y Evaluación Adversaria (*GAN-Style Harness*)

Implementa el ciclo completo de tres agentes inspirado en la arquitectura GAN de Anthropic y `affaan-m/ECC`.

## Pasos de Ejecución

1. **Fase 1: `gan-planner` (`@code-architect` / `@orchestrator`)**:
   - Definir el contrato exacto del bloque a construir y la rúbrica de evaluación en 4 ejes: Fidelidad de Especificación (35%), Rigor Cognitivo/Funcional (25%), Solidez Arquitectónica/Seguridad (20%) y Evidencia de Pruebas (20%).
2. **Fase 2: `gan-generator` (Subagentes Especialistas `@back-*` / `@front-*`)**:
   - Implementar los módulos y sus suites de test en contextos limpios siguiendo `03-tasks.md`.
3. **Fase 3: `gan-evaluator` (`@gan-evaluator`)**:
   - Ejecutar los comandos deterministas de verificación DoD (`pytest`, `tsc --noEmit`, `vitest`) e inspeccionar los archivos generados.
   - Emitir puntuación numérica desglosada sobre 10:
     - Si **Puntuación $\ge 8.5/10$** $\rightarrow$ Aprobar bloque (`PASS`).
     - Si **Puntuación $< 8.5/10$** $\rightarrow$ Devolver feedback quirúrgico (`ITERATE`) al generador y repetir Fase 2.
