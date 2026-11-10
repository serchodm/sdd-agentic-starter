# SDD Starter — Active Session Pointer (Managed by @orchestrator)
- **Timestamp:** 2026-11-10 20:44
- **Active Work Item:** `IDLE` (`FWK-001` Done — Gate 5 cerrado)
- **Active Branch:** `feat/fwk-001-pack-materialization`
- **Spec Folder Path:** `.sdd/framework/work-items/FWK-001-pack-materialization`
- **Current Gate:** Gate 5 Completo (`FWK-001` Done; listo para nuevo Work Item o Gate 00 en sesión limpia)
- **Recommended Model Tier:** Reasoning (Opus/Sonnet) for Gates 00-3 (`FWK-002`)
- **Last Completed Milestone:** `FWK-001` completado end-to-end (Gates 1–5): registro YAML `sdd:stack-config` + Gate 00 fail-closed (`scripts/sdd_pack_registry.py`), materializador atómico + lock v2 (`scripts/sdd_agent_generator.py`), importador con workflows + sync (`scripts/sdd_catalog_import.py`, `scripts/sdd_sync.py`), 30/30 tests offline (`tests/test_sdd_pack_materialization.py`), 3 auditorías Gate 4 PASS y documentación viva 0DD (`ADR-002`, `docs/knowledge/`, `TRACEABILITY-MATRIX.md`, `docs/es/` y `docs/en/`).
- **Next Execution Target:** Abrir hilo nuevo para iniciar `FWK-002` (`capability-ui-design` / UI UX Pro Max en `.sdd/framework/BACKLOG.md`) o ejecutar Gate 00 en `specs/STACK.md`.
- **Mandatory Context Files (MAX 4 FILES):**
  1. `AGENTS.md`
  2. `.sdd/framework/BACKLOG.md`
  3. `.sdd/framework/rfcs/RFC-001-ui-ux-pro-max.md`
  4. `specs/STACK.md`
- **Critical Technical Decisions / Snapshot:**
  - `FWK-001` validado y cerrado en `.sdd/framework/BACKLOG.md` (no tocar `specs/features/` ni `src/`).
  - Plantilla base saneada con `gate00_approved: false`, `active_packs: []` y `.agents/squad.lock.json` `schema_version: 2`.
  - Reglas de pack aisladas en `.agents/pack-rules/<pack>/` (`ADR-002`, `RN-SDD-SELECTIVE-CONTEXT`).
  - Rama `feat/fwk-001-pack-materialization` sincronizada con `origin` tras cierre Gate 5.
