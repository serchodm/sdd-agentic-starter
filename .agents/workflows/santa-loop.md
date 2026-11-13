---
description: Ejecuta el bucle de doble revisión adversaria independiente (Santa Method: Checking It Twice) hasta lograr veredicto NICE unánime.
---

# Workflow `/santa-loop` — Doble Verificación Adversaria Independiente (*Santa Method*)

Activa este workflow antes de declarar completado un bloque crítico (`Block`) o antes de pasar a Gate 5 para garantizar calidad cero defectos mediante dos revisores independientes.

## Pasos de Ejecución

1. **Construir *The List* (Lista de Verificación Explícita)**:
   - Extraer todos los entregables físicos, contratos espejo y criterios de aceptación de `01-spec.md`, `02-tech-spec.md` y `03-tasks.md`.
2. **Despachar Revisor Independiente A (Lente de Contratos y Especificación)**:
   - Invocar a `@type-design-analyzer` / `@fastapi-reviewer` / `@react-reviewer` para auditar correspondencia 1:1 con `02-tech-spec.md`.
3. **Despachar Revisor Independiente B (Lente Adversaria y Fallos Silenciosos)**:
   - Invocar en paralelo a `@gan-evaluator` / `@silent-failure-hunter` para buscar errores tragados, casos límite no cubiertos o texto genérico.
4. **Evaluar Puerta *NICE* vs *NAUGHTY***:
   - Si ambos revisores reportan **`NICE`** (0 defectos bloqueantes y todos los comandos DoD en verde) $\rightarrow$ Certificar entrega.
   - Si cualquiera reporta **`NAUGHTY`** $\rightarrow$ Corregir todos los hallazgos señalados y repetir la doble revisión desde el Paso 2.
