---
description: Extrae instintos atómicos (continuous-learning-v2) de la sesión actual y los persiste en .agents/instincts.json o skills.
---

# Workflow `/learn` (`continuous-learning-v2`)

1. **Inspeccionar Señales:** Identificar preferencias de flujo (`user_preference`), correcciones técnicas (`self_lesson`), invariantes (`project`) o mejoras de skill.
2. **Formular Instinto:** Definir `trigger`, `action`, `confidence` (`0.30–0.95`) y `scope` (`agent`/`project`/`global`).
3. **Persistir Atómicamente:** Registrar con `uv run python scripts/sdd_instincts.py` en `.agents/instincts.json` (o actualizar `.agents/skills/<slug>/SKILL.md` si procede).
4. **Verificar:** Confirmar integridad JSON/Markdown con `uv run python scripts/sdd_instincts.py list`.
