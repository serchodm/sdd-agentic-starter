# SDD Starter — Active Session Pointer (Managed by @orchestrator)
- **Timestamp:** 2026-11-13 12:57
- **Active Work Item:** `FWK-003-conditional-visual-gates` (Gate 5 Finalizado / Work Item Done / Pusheado)
- **Active Branch:** `feat/fwk-003-conditional-visual-gates`
- **Spec Folder Path:** `.sdd/framework/work-items/FWK-003-conditional-visual-gates`
- **Current Gate:** Gate 5 Completado (Work Item Done & Pushed — Listo para PR hacia develop)
- **Recommended Model Tier:** High Reasoning (Opus / Pro / GPT-5) para Gate 0/1/2 del siguiente Work Item
- **Last Completed Milestone:** FWK-003 completado al 100%: Gate 5 (0DD) cerrado por `@documentator`, 45/45 tests en verde, comiteado (`ae2f80f`) y pusheado con pre-push hook aprobado a `origin/feat/fwk-003-conditional-visual-gates`.
- **Next Execution Target:** Crear Pull Request hacia `develop`, fusionar y abrir nueva sesión para el siguiente Work Item del backlog (`FWK-004-gate-terminology-unification`).
- **Mandatory Context Files (MAX 4 FILES):**
  1. `AGENTS.md`
  2. `.sdd/framework/BACKLOG.md`
  3. `docs/knowledge/ADRS.md`
  4. `.agents/ACTIVE_STATE.md`
- **Critical Technical Decisions / Snapshot:**
  - `scripts/sdd_tokens_validator.py` (474 líneas, stdlib Python 3.12, DTCG parser, cotejo bidireccional JSON ↔ `MASTER.md`, escaneo estático `--check-sources`).
  - 4ª Auditoría formalizada en `.agents/agents/qa-tester.md` y soporte en `.sdd/catalog/packs/capability-web-frontend/agents/a11y-architect.md`.
  - `front-test.archetype.md`, plantillas `02-technical-spec` / `03-tasks` y `.github/workflows/ci.yml` sincronizados.
  - `tests/test_sdd_visual_gates.py` (337 líneas, 8 tests deterministas offline; 45/45 tests pasando en verde).
  - `ADR-004` registrado, base de conocimiento y matriz de trazabilidad 100% sincronizadas sin deuda documental (0DD).
