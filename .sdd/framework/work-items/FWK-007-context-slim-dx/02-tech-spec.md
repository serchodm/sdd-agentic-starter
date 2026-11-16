# Tech Spec: Slimming de Contexto y Adopción DX `sdd-starter` (`FWK-007`)

- **ID:** `FWK-007-context-slim-dx`
- **Gate 2 Sign-off:** `[x] Gate 2 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Arquitectura y Límites
1. **Agentes Base (`~9`) vs Opt-In:** Mantener en `.agents/agents/` base los `6` `CORE_AGENTS` (`orchestrator`, `functional-analyst`, `architect`, `qa-tester`, `documentator`, `devops`), los `builders` del preset activo (`compact`: `back-engineer`, `front-engineer` = 2) y especialistas esenciales opt-in por defecto (p.ej. `security-reviewer` = 1; total `9` agentes activos). Mover el resto de especialistas al catálogo opt-in (`.sdd/catalog/specialists-optin/` o pack dedicado en `.sdd/catalog/packs/capability-specialists-extra/`) y actualizar `sdd_catalog_import.py` si aplica. *(Nota de frontera DAG: la rematerialización final de `.agents/agents/`, `.agent-inbox/` y `squad.lock.json` ocurre en Wave 3 tras integrar `FWK-006` + `FWK-007`).*
2. **Deduplicación & Limpieza:** Borrar `.agents/archetypes/` (8 ficheros legacy); eliminar copias duplicadas por SHA y referencias residuales `PACO`/`JARVIS` en `.agents/`, `.sdd/catalog/` y `specs/`; reducir `sdd-bootstrap/SKILL.md` extrayendo plantillas extensas a referencias on-demand bajo `.agents/skills/sdd-bootstrap/references/`.
3. **DX `sdd-starter`:** Añadir `.agents/workflows/bug-fast-track.md`, plantilla `specs/templates/05-bug-fast-track.template.md` y `domains/README.md` + `domains/_template/{overview,decisions}.md`.
