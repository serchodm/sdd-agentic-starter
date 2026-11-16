---
name: gan-style-harness
description: Arquitectura Generador-Evaluador (GAN-Style Harness de Anthropic y affaan-m/ECC: gan-planner, gan-generator, gan-evaluator) para evitar sesgo de autocomplacencia en entregas complejas.
---

# Skill: `gan-style-harness` (Bucle Planificador-Generador-Evaluador)

Resuelve la degradación de contexto y el sesgo de autocomplacencia separando generación y evaluación:

1. **`gan-planner`** (`@architect` / `@orchestrator`): Define el contrato del bloque y la rúbrica ponderada.
2. **`gan-generator`** (constructores del stack): Implementa código y tests unitarios limpios.
3. **`gan-evaluator`** (`@gan-evaluator` opt-in o `@qa-tester`): Audita en frío contra la rúbrica y ejecuta los comandos DoD.

## Rúbrica de Evaluación (Sobre 10)
1. **Fidelidad de Especificación y Contratos (35%):** Correspondencia 1:1 con DTOs, esquemas e interfaces de `02-tech-spec.md`.
2. **Rigor Funcional (25%):** Cero plantillas placeholder; comportamiento completo extremo a extremo cubriendo casos límite.
3. **Arquitectura y Seguridad (20%):** Respeto de capas, cero fallos silenciosos (`except: pass`) y validación fail-closed.
4. **Verificación Empírica (20%):** Ejecución real en verde de las suites y build DoD definidas en `specs/STACK.md`.

- **Regla de Decisión:** Score **$\ge 8.5 / 10$** (y cada eje $\ge 7.0$) $\rightarrow$ `PASS`; **$< 8.5 / 10$** $\rightarrow$ `ITERATE` con hallazgos `archivo:línea`.
