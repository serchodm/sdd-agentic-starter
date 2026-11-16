# Plan de Tareas (DAG): `FWK-007` Context Slimming & DX

- **ID:** `FWK-007-context-slim-dx`
- **Gate 3 Sign-off:** `[x] Gate 3 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Grafo DAG
- `T7.1` `[PARALLEL: BLOCK_C1]`: Eliminar `.agents/archetypes/`, deduplicar catálogo, erradicar refs `PACO`/`JARVIS` y alinear `README.md`.
  - *DoD:* búsqueda de `PACO|JARVIS` en `.agents/` retorna 0 coincidencias normativas y `.agents/archetypes/` no existe.
- `T7.2` `[PARALLEL: BLOCK_C1]`: Adelgazar `.agents/skills/sdd-bootstrap/SKILL.md` (`<=8KB` inline + `references/`) y reorganizar `.sdd/catalog/specialists/` + `specialists-optin/` / `scripts/sdd_catalog_import.py`.
  - *DoD:* suma estimada de bytes en `.agents/` (`rules+skills+workflows+contexts+core_agents`) < 100 KB (`<25k` est. tokens).
- `T7.3` `[PARALLEL: BLOCK_C1]`: Añadir fast-track `BUG-XXX` (`.agents/workflows/bug-fast-track.md`, `specs/templates/05-bug-fast-track.template.md`) y `domains/`.
  - *DoD:* comprobar existencia y legibilidad Markdown sin rutas rotas.
