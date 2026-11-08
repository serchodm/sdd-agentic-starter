---
description: Extrae instintos atómicos (continuous-learning-v2) de la sesión actual y los persiste en MEMORY.md, USER.md o SKILL.md de los agentes.
---

# Workflow `/learn` — Extracción y Persistencia de Instintos (`continuous-learning-v2`)

Ejecuta este workflow para destilar correcciones del usuario, preferencias descubiertas o lecciones técnicas de la sesión en curso y convertirlas en **Instintos Atómicos** permanentes.

## Pasos de Ejecución

1. **Inspeccionar Señales de Aprendizaje (`@conversation-analyzer`)**:
   - Identificar en la conversación reciente:
     - Preferencias explícitas o implícitas del usuario sobre tono, concisión o flujo de trabajo (`user_preference`).
     - Correcciones sobre cómo debe actuar un agente del Consejo o subagente técnico (`self_lesson`).
     - Acuerdos estratégicos o arquitectónicos tomados en la Sala de Consejo (`council_fact`).
     - Mejoras operativas aplicables a una skill concreta (`skill_refinement`).
2. **Formular cada Instinto con Estructura Determinista**:
   - Definir `trigger` (cuándo se activa), `action` (qué hacer exactamente), `confidence` (`0.3` a `0.95`) y `scope` (`agent` o `global`).
3. **Persistir Atómicamente**:
   - En runtime del Consejo: a través de `AutonomousLearningService.apply_learnings(...)` / herramienta `learn_and_remember`.
   - En arnés de desarrollo: actualizando la sección `## Instintos y Lecciones Aprendidas (Motu Proprio - ECC continuous-learning-v2)` en `backend/agents/<id>/MEMORY.md`, `USER.md` o `.agents/skills/`.
4. **Verificar Integridad**:
   - Comprobar que los archivos `.md` mantienen formato válido y que la caché de `AgentAnatomyHydrator` queda sincronizada.
