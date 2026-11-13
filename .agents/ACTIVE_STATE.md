# SDD Starter — Active Session Pointer (Managed by @orchestrator)
- **Timestamp:** 2026-11-13 12:55
- **Active Work Item:** `FWK-003-conditional-visual-gates` (Completado / Done)
- **Active Branch:** `feat/fwk-003-conditional-visual-gates`
- **Spec Folder Path:** `.sdd/framework/work-items/FWK-003-conditional-visual-gates`
- **Current Gate:** Gate 5 Completado (Work Item Done — Documentación Viva 0DD, Trazabilidad & Cierre)
- **Recommended Model Tier:** Fast Execution (Sonnet / Flash / GPT-4o) para Gate 5
- **Last Completed Milestone:** Gate 5 completado con éxito: Tarea C.1 ejecutada por `@documentator`. ADR-004 registrado, base de conocimiento y matriz de trazabilidad sincronizadas, docs bilingües actualizados y backlog cerrado en `Done`.
- **Next Execution Target:** Commit final en `feat/fwk-003-conditional-visual-gates`, push y Pull Request hacia `develop`.
- **Mandatory Context Files (MAX 4 FILES):**
  1. `AGENTS.md`
  2. `.agents/rules/06-functional-doc-0dd.md`
  3. `.sdd/framework/work-items/FWK-003-conditional-visual-gates/02-tech-spec.md`
  4. `.sdd/framework/work-items/FWK-003-conditional-visual-gates/03-tasks.md`
- **Critical Technical Decisions / Snapshot:**
  - `scripts/sdd_tokens_validator.py` (474 líneas, stdlib Python 3.12, DTCG parser, cotejo bidireccional JSON ↔ `MASTER.md`, escaneo estático `--check-sources`).
  - 4ª Auditoría formalizada en `.agents/agents/qa-tester.md` y soporte en `.sdd/catalog/packs/capability-web-frontend/agents/a11y-architect.md`.
  - `front-test.archetype.md`, plantillas `02-technical-spec` / `03-tasks` y `.github/workflows/ci.yml` sincronizados.
  - `tests/test_sdd_visual_gates.py` (337 líneas, 8 tests deterministas offline; 45/45 tests pasando en verde).
  - Despacho estricto por subagentes conforme a `RN-SDD-ORCHESTRATOR-SUBAGENTS`.
