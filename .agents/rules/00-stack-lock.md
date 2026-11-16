# Regla 00: Stack Lock, Ownership Map y Bootstrap (Gate S0 / Legacy Gate 00)

> **FAIL-CLOSED:** Código de producción y tests están **BLOQUEADOS** hasta aprobar `specs/STACK.md` (`[x] Gate S0 Approved` o alias legacy `[x] Gate 00 Approved`).

## 1. Disparo de `sdd-bootstrap`
1. **Detección Automática:** Si `specs/STACK.md` tiene `[ ] Gate S0 Approved (Human Sign-off)` (o `[ ] Gate 00 Approved`), `@orchestrator` bloquea tareas de código/backlog y activa `.agents/skills/sdd-bootstrap/SKILL.md`.
2. **Ejecución:** Cuestionario bilingüe con poda dinámica (Cloud, Docker, PaaS/Vercel, Air-Gapped) que congela §2.5 (**Comandos Deterministas DoD**: lint, unit <1s, integración, build), §3.2 (**Ownership Map** sin solapes) y §3.3 (`sdd:stack-config`), y materializa el escuadrón con `uv run python scripts/sdd_agent_generator.py --materialize`.

## 2. Criterios de Aprobación y Guardia
- `specs/STACK.md` requiere: topología/hosting, stack Backend/Frontend/BD (o `N/A`), comandos DoD §2.5, Ownership Map §3.2, Golden Samples (Do/Don't) y casilla `[x] Gate S0 Approved (Human Sign-off)` marcada solo tras confirmación humana expresa.
- `.agents/scripts/sdd_code_gate_guard.py` deniega cualquier edición en `src/` o `tests/` si Gate S0 o Gate 2 no están aprobados.
