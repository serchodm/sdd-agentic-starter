---
description: Agrupa instintos de alta confianza (>= 0.75) en .agents/instincts.json y los promueve a skills o reglas.
---

# Workflow `/evolve` (`continuous-learning-v2`)

1. **Inventariar:** Consultar `.agents/instincts.json` vía `uv run python scripts/sdd_instincts.py list` (apoyado por `@conversation-analyzer` si está activo).
2. **Detectar Clústeres:** Agrupar instintos por dominio/`trigger` con confianza $\ge 0.75$.
3. **Promocionar:** Procedimientos $\rightarrow$ `.agents/skills/<slug>/SKILL.md`; invariantes obligatorias $\rightarrow$ `.agents/rules/`.
4. **Podar Duplicados:** Consolidar entradas redundantes manteniendo señal alta y bajo consumo de contexto.
