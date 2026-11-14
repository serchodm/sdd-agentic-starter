---
name: continuous-learning-v2
description: Motor de aprendizaje continuo basado en Instintos Atómicos (affaan-m/ECC) con puntuación de confianza (0.3-0.95), alcance (agent/project/global) y evolución hacia skills/reglas.
---

# Skill: `continuous-learning-v2` (Instintos Atómicos de `affaan-m/ECC`)

Convierte correcciones del usuario, preferencias descubiertas y lecciones operativas del arnés (`.agents/`) en **Instintos Atómicos** reutilizables gestionados con `scripts/sdd_instincts.py` y `.agents/instincts.json`.

## 1. Modelo de Instinto (`Instinct`)
- **`trigger`**: Condición exacta de activación (ej. *"al validar contratos espejo en `02-tech-spec.md`"*).
- **`action`**: Comportamiento concreto esperado.
- **`confidence`** (`0.30` – `0.95`): `0.30–0.50` tentativo, `0.70` fuerte (corrección explícita), `0.85–0.95` consolidado.
- **`scope`**: `agent` (privado del rol), `project` (repositorio actual en `.agents/instincts.json`) o `global` (transversal).

## 2. Ciclo de Vida (`/learn` $\rightarrow$ `/evolve`)
1. **Captura (`/learn`):** Registrar nuevos instintos vía `uv run python scripts/sdd_instincts.py` en `.agents/instincts.json`.
2. **Decaimiento y Similitud:** Los instintos antiguos decaen hasta `0.30` si no se refuerzan y evitan duplicados por similitud semántica.
3. **Promoción (`/evolve`):** Cuando $\ge 3$ instintos convergen con confianza $\ge 0.75$ (evaluables por `@conversation-analyzer`), se consolidan en `.agents/skills/<slug>/SKILL.md` o en `.agents/rules/`.
