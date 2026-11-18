---
description: Adopción segura de repositorios brownfield con sdd adopt y @spec-miner (Gate S0 -> Gate 1)
---

# Workflow: Adopción Brownfield (`sdd adopt` + `@spec-miner`)

Flujo no destructivo y *fail-closed* para incorporar proyectos existentes al ciclo SDD (`RN-SDD-SELECTIVE-CONTEXT`):

1. **Descubrimiento en modo solo lectura (`--dry-run`):**
   Ejecutar `uv run python scripts/sdd_cli.py adopt --format text` para inspeccionar manifiestos, ecosistemas, zonas candidatas y comandos seguros filtrados. Revisar el plan y ejecutar `uv run python scripts/sdd_cli.py adopt --apply` (añadir `--with-repo-map` si se desea extracto AST en `docs/knowledge/BROWNFIELD_INVENTORY.md`).
2. **Aprobación humana de `Gate S0` y materialización:**
   Completar/ajustar `specs/STACK.md`, obtener firma humana explícita de `Gate S0` (`RN-SDD-HUMAN-GATE-OWNERSHIP`; jamás autoaprobar) y materializar el escuadrón con `uv run python scripts/sdd_cli.py generate --materialize`.
3. **Extracción AST por bounded context:**
   Elegir un bounded context de `docs/knowledge/BROWNFIELD_INVENTORY.md` y generar su esqueleto simbólico con `uv run python scripts/sdd_cli.py repo-map <ruta-contexto>`.
4. **Minado inverso de especificación con `@spec-miner`:**
   Invocar a `@spec-miner` (`.sdd/catalog/specialists-optin/spec-miner.md`) pasando el `repo-map` del contexto para redactar el borrador `specs/features/FEAT-XXX-<slug>/01-spec.md` (`SRC-###`, `AMB-###`, requisitos EARS, criterios `Given-When-Then`) y `domains/<slug>/{overview,decisions}.md`, sin modificar `src/` ni autoaprobar `Gate 1`.
