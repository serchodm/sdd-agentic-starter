---
name: santa-method
description: Protocolo de doble verificación independiente convergente (Santa Method de affaan-m/ECC) que exige veredicto NICE unánime de dos revisores aislados antes de certificar un entregable.
---

# Skill: `santa-method` (*Checking It Twice*)

Elimina puntos ciegos mediante dos revisores independientes sin contexto compartido frente a una lista cerrada (*The List*):

1. **Construir *The List*:** Extraer entregables físicos, invariantes de contrato y comandos DoD de `01-spec.md`, `02-tech-spec.md` y `03-tasks.md`.
2. **Ejecución:** Constructores implementan tareas y pasan tests locales.
3. **Doble Revisión Aislada:**
   - **Revisor A (Contratos y Spec):** Verifica 1:1 ficheros, DTOs y requisitos EARS (`@architect` / `@type-design-analyzer` / pack reviewer).
   - **Revisor B (Adversaria y Fallos Silenciosos):** Busca errores tragados, regresiones, casos límite o placeholders (`@qa-tester` / `@silent-failure-hunter` / `@gan-evaluator`).
4. **Decisión:** **`NICE + NICE`** (0 defectos) $\rightarrow$ Certificar; cualquier **`NAUGHTY`** $\rightarrow$ consolidar defectos, corregir y repetir Paso 3 (máx. 3 rondas antes de escalar al usuario).
