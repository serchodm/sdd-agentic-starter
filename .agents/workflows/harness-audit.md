---
description: Audita la salud, integridad y sincronización del arnés SDD (.agents/, .sdd/catalog/ y scripts de gobernanza).
---

# Workflow `/harness-audit` — Auditoría del Arnés SDD

1. **Verificar Catálogo y Materialización:**
   - `uv run python scripts/sdd_agent_generator.py --list`
   - Comprobar coherencia entre `.agents/squad.lock.json`, `.agents/agents/` y `.agent-inbox/`.
2. **Verificar Reglas, Skills y Hooks:**
   - Confirmar ausencia de colisiones entre `.agents/skills/` y `.sdd/catalog/packs/*/skills/`, y presencia de `.agents/rules/`, `.agents/workflows/` y `.agents/contexts/`.
3. **Ejecutar Verificadores Deterministas:**
   - `uv run python .agents/scripts/sdd_healthcheck.py`
   - `uv run python .agents/scripts/verify_architecture_boundaries.py`
   - `uv run python -m unittest discover -s tests -v`
