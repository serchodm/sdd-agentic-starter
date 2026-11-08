---
description: Audita la salud, integridad y completitud del arnés de agentes (.agents/ y backend/agents/) verificando anatomía OpenClaw, skills ECC y fronteras arquitectónicas.
---

# Workflow `/harness-audit` — Auditoría Integral del Arnés de Agentes y Anatomía Cognitiva

Ejecuta este workflow para verificar que tanto el **Anillo 1** (`backend/agents/` — los 9 agentes del Consejo y sus skills ECC) como el **Anillo 2** (`.agents/` — los 20 agentes ultra-especialistas, meta-skills, workflows, contextos y reglas) están completos y sincronizados.

## Pasos de Ejecución

1. **Verificar Anatomía OpenClaw de 8 Ficheros + Skills en `backend/agents/`**:
   - Comprobar que cada uno de los 9 agentes (`paco`, `dario`, `cora`, `clara`, `cervantes`, `rita`, `tara`, `vega`, `maia`) posee `IDENTITY.md`, `SOUL.md`, `USER.md`, `AGENTS.md`, `TOOLS.md`, `BOOT.md`, `HEARTBEAT.md`, `MEMORY.md`, `agent.yaml` y su carpeta `skills/` con las skills de `affaan-m/ECC`.
   - Comprobar que `backend/agents/_shared/skills/` contiene las 5 skills transversales compartidas.
2. **Verificar Integridad del Arnés `.agents/`**:
   - Confirmar presencia de los 20 agentes ultra-especialistas en `.agents/agents/`, las 8 meta-skills en `.agents/skills/`, los 6 workflows en `.agents/workflows/` y los 3 contextos en `.agents/contexts/`.
3. **Ejecutar Verificadores Deterministas**:
   - `uv run --project backend python .agents/scripts/verify_architecture_boundaries.py`
   - `uv run python scripts/sdd_sync.py --status`
