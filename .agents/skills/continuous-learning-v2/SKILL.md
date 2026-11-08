---
name: continuous-learning-v2
description: Motor de aprendizaje continuo basado en Instintos Atómicos (Instincts v2 de affaan-m/ECC) con puntuación de confianza (0.3-0.9), alcance (agent/project/global) y evolución hacia skills/reglas.
---

# Skill: `continuous-learning-v2` (Motor de Aprendizaje por Instintos de `affaan-m/ECC`)

Esta meta-skill implementa la arquitectura **`continuous-learning-v2`** de `affaan-m/ECC` tanto para los agentes de la Sala de Consejo (`backend/agents/`) como para el arnés de ingeniería (`.agents/`). Convierte correcciones del usuario, preferencias descubiertas y lecciones operativas en **Instintos Atómicos** reutilizables.

## 1. Modelo de un Instinto Atómico (`Instinct`)

Un instinto es una regla conductual pequeña, explícita y verificable vinculada a un disparador claro:

- **`trigger`**: La situación o condición exacta en la que se activa (ej. *"al responder una consulta técnica junto a un especialista"* o *"al modificar un DTO en `backend/src/api/dtos/`"*).
- **`action`**: La acción concreta que el agente debe ejecutar (ej. *"limitar la intervención de Project a un Highlight Ejecutivo de 2-3 frases sin duplicar el listado del experto"*).
- **`confidence`**: Nivel de certeza entre `0.30` y `0.95`:
  - `0.30 - 0.50`: Tentativo (observado una sola vez).
  - `0.70`: Fuerte (preferencia o corrección explícita del usuario — valor por defecto en *motu proprio*).
  - `0.85 - 0.95`: Consolidado (validado repetidamente sin contradicciones).
- **`scope`**:
  - `agent`: Privado de la entidad (persiste en `MEMORY.md` del agente y en `MnemoConsolidationService` con `scope="agent"`).
  - `project` / `global`: Compartido con todo el Consejo o el repositorio (persiste en `USER.md` o `MnemoConsolidationService` con `scope="global"`).

## 2. Destinos de Persistencia Atómica (`AutonomousLearningService`)

| Categoría (`category`) | Archivo Físico en `backend/agents/<id>/` | Consolidación Semántica (`Mnemo`) |
| :--- | :--- | :--- |
| `user_preference` | `USER.md` (`## Preferencias y Estilo del Usuario Aprendidos`) | `scope="global"` |
| `self_lesson` | `MEMORY.md` (`## Instintos y Lecciones Aprendidas`) | `scope="agent"` |
| `council_fact` | `MEMORY.md` (`## Instintos y Lecciones Aprendidas`) | `scope="global"` |
| `skill_refinement` | `skills/<target_skill_slug>/SKILL.md` (`## Refinamientos Aprendidos en Ejecución`) | `scope="agent"` |

## 3. Ciclo de Evolución (`/learn` $\rightarrow$ `/evolve`)

1. **Captura en Caliente**: Durante cualquier turno, el agente invoca `learn_and_remember` *motu proprio* cuando detecta una preferencia, corrección o hecho relevante.
2. **Invalidación Inmediata de Caché**: `AutonomousLearningService` escribe de forma atómica (`tempfile` + `os.replace`) e invalida la caché de `AgentAnatomyHydrator` para que el siguiente turno ya opere con el nuevo instinto.
3. **Promoción (`/evolve`)**: Cuando $\ge 3$ instintos convergen en un mismo dominio con confianza $\ge 0.75$, `@conversation-analyzer` los agrupa en una nueva skill o regla permanente.
