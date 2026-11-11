# SDD Starter — Active Session Pointer (Managed by @orchestrator)
- **Timestamp:** 2026-11-11 16:30
- **Active Work Item:** `None` (`FWK-002` completado y marcado `Done` en Gate 5; listo para nuevo hilo limpio según `RN-SDD-SESSION-LIFECYCLE`)
- **Active Branch:** `feat/fwk-002-capability-ui-design` (sincronizada con `origin` tras cierre de `FWK-002`; lista para PR hacia `develop`)
- **Spec Folder Path:** `.sdd/framework/work-items/FWK-002-capability-ui-design` (Línea base cerrada en `Done`)
- **Current Gate:** Gate 5 Completado y Certificado (`FWK-002` `Done`: `T_A1`–`T_A3`, `T_B1`, `T_C1`, `T_D1` `[x]`)
- **Recommended Model Tier:** High-Reasoning (Opus/Pro/Sonnet) si se inicia Gate 1 de `FWK-003` en un nuevo hilo limpio
- **Last Completed Milestone:** Bloque D (`T_D1` `@documentator` + cierre Gate 5) completado: `ADR-003` registrado en `docs/knowledge/ADRS.md`, actualizados `docs/knowledge/{SYSTEM_TOPOLOGY,DATA_MODELS,API_CATALOG}.md`, `docs/traceability/TRACEABILITY-MATRIX.md`, documentación bilingüe `docs/{es,en}/` (`MOD-002`, `README.md`, `DOCUMENTATION-INDEX.md`), `FWK-002` marcado `Done` en `.sdd/framework/BACKLOG.md`, `37` tests offline en verde y sincronización en `feat/fwk-002-capability-ui-design`.
- **Next Execution Target:** Abrir hilo nuevo y limpio para PR `feat/fwk-002-capability-ui-design` -> `develop` o iniciar Gate 1 de `FWK-003` (*Quality gates visuales condicionales*) previa aprobación humana.
- **Mandatory Context Files (MAX 4 FILES):**
  1. `AGENTS.md`
  2. `.sdd/framework/BACKLOG.md`
  3. `.sdd/framework/rfcs/RFC-001-ui-ux-pro-max.md`
  4. `docs/knowledge/ADRS.md`
- **Critical Technical Decisions / Snapshot:**
  - `FWK-002` (`capability-ui-design` + `ui-ux-pro-max-cli@2.15.0` MIT) cerrado en `Done` (`Gate 1..5 [x]`); rama `feat/fwk-002-capability-ui-design` creada desde `develop` (sin tocar `src/` ni `specs/BACKLOG.md`, y sin `docs/design-system/` en el starter).
  - Contratos implementados y verificados: `scripts/sdd_vendor_update.py` (`485` líneas), `scripts/sdd_pack_registry.py` (`494` líneas), `scripts/sdd_agent_generator.py` (`471` líneas), `tests/test_sdd_pack_materialization.py` (`497` líneas), `tests/test_sdd_ui_design.py` (`479` líneas); `45` ficheros runtime + `LICENSE` = `46` entradas en `VENDOR.lock.json`.
  - `.gitattributes` fija `text eol=lf` para `.sdd/catalog/packs/capability-ui-design/**` y `.agents/**`.
