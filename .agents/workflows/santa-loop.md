---
description: Ejecuta doble revisión adversaria independiente (Santa Method: Checking It Twice) hasta veredicto NICE unánime.
---

# Workflow `/santa-loop` (*Santa Method*)

1. **Construir *The List*:** Extraer entregables, contratos y comandos DoD de `01-spec.md`, `02-tech-spec.md` y `03-tasks.md`.
2. **Revisor A (Contratos/Spec):** Auditar correspondencia 1:1 con `02-tech-spec.md` (`@architect` / pack reviewer).
3. **Revisor B (Adversaria/Fallos):** Buscar errores silenciados, casos límite y placeholders (`@qa-tester` / `@silent-failure-hunter` / `@gan-evaluator`).
4. **Puerta:** **`NICE + NICE`** $\rightarrow$ certificar; cualquier **`NAUGHTY`** $\rightarrow$ corregir y repetir desde Paso 2.
