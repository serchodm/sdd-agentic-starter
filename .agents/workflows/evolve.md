---
description: Agrupa instintos relacionados de alta confianza (>= 0.75) y los evoluciona hacia nuevas skills, reglas técnicas o mejoras del arnés.
---

# Workflow `/evolve` — Consolidación de Instintos en Skills y Reglas (`continuous-learning-v2`)

Ejecuta este workflow periódicamente o al cerrar un hito para auditar los instintos acumulados en `backend/agents/*/MEMORY.md` y `USER.md` y promocionar los patrones maduros a skills o reglas formales.

## Pasos de Ejecución

1. **Inventariar Instintos Acumulados (`@conversation-analyzer`)**:
   - Leer las secciones `## Instintos y Lecciones Aprendidas` en `backend/agents/*/MEMORY.md` y `USER.md`.
2. **Detectar Clústeres de Alta Confianza**:
   - Agrupar instintos que compartan dominio o `trigger` y cuya confianza sea $\ge 0.75$.
3. **Promocionar según el Tipo de Patrón**:
   - Si el clúster define un procedimiento especializado de dominio $\rightarrow$ Actualizar o crear `backend/agents/<id>/skills/<slug>/SKILL.md` (o `.agents/skills/<slug>/SKILL.md`).
   - Si el clúster establece una invariante obligatoria de arquitectura o seguridad $\rightarrow$ Proponer su incorporación en `.agents/rules/`.
4. **Podar Duplicados**:
   - Consolidar entradas redundantes en `MEMORY.md` manteniendo un registro limpio, de alta señal y bajo consumo de tokens.
