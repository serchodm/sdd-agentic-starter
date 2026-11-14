---
description: Ejecuta el bucle GAN-Style Harness (gan-planner -> gan-generator -> gan-evaluator) con rúbrica >= 8.5/10.
---

# Workflow `/gan-build` (*GAN-Style Harness*)

1. **`gan-planner` (`@architect` / `@orchestrator`):** Fijar contrato del bloque y rúbrica (Spec 35%, Rigor 25%, Seguridad/Arquitectura 20%, Pruebas 20%).
2. **`gan-generator` (Constructores activos):** Implementar módulos y tests en contexto limpio según `03-tasks.md`.
3. **`gan-evaluator` (`@gan-evaluator` / `@qa-tester`):** Ejecutar comandos DoD de `specs/STACK.md`; score **$\ge 8.5/10$** $\rightarrow$ `PASS`, **$< 8.5/10$** $\rightarrow$ `ITERATE` con hallazgos `archivo:línea`.
