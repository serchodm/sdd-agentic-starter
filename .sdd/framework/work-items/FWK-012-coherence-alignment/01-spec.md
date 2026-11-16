# Spec Funcional: Alineación de Coherencia v1.1.1 (`FWK-012`)

- **ID:** `FWK-012-coherence-alignment`
- **RFC:** [`RFC-006`](../../rfcs/RFC-006-coherence-and-catalog-alignment.md) (`Aceptado`)
- **Estado:** `Done`
- **Gate 1 Sign-off:** `[x] Gate 1 Approved (Authorized by PO on 2026-11-16T11:46:29+01:00)`

## 1. Resumen y Alcance
Resolver los desajustes detectados en la auditoría de `main` (`712648c`) para dejar el starter 100% consistente antes de iniciar las entregas funcionales `v1.2.0` (`Gate 6` CI-agnóstico), `v1.3.0` (Brownfield & Spec Drift) y `v1.4.0` (Portfolio/FinOps).

- **In-Scope:** CLI `work-item` + rutas documentadas en `README.md`/`bug-fast-track.md`; soporte `HOTFIX-*` y `SPIKE-*` en guardias, sellos, healthcheck y plantillas; limpieza §3 de `SDD_FRAMEWORK.md`; adaptación SDD de `.sdd/catalog/specialists-optin/spec-miner.md` con protección en `sdd_catalog_import.py`; modo PR por defecto en `release-finish` / `hotfix-finish`.
- **Out-of-Scope:** Implementación de `Gate 6` (`v1.2.0`), onboarding brownfield completo `/onboard` (`v1.3.0`) o métricas FinOps/Épicas (`v1.4.0`).

## 2. Requisitos (EARS)
- `RF-1201` (**Coherencia CLI `sdd_cli.py` y documentación**): El sistema deberá implementar el subcomando `work-item` (`show` y `set <ID>`) en `scripts/sdd_cli.py` para consultar o seleccionar un work item (`FEAT`, `CR`, `BUG`, `HOTFIX`, `FWK`) en `.agents/active_work_item.json` y `.agents/ACTIVE_STATE.md` en estado `PENDING_APPROVAL` (sin autoaprobar `gate_1_approved`..`gate_3_approved` ni `approved_by_human`, cumpliendo `RN-SDD-HUMAN-GATE-OWNERSHIP`), y corregir las referencias erróneas `.agents/scripts/sdd_cli.py` en `README.md` y `.agents/workflows/bug-fast-track.md`.
- `RF-1202` (**Soporte integral `HOTFIX-*`, `SPIKE-*` y limpieza de `SDD_FRAMEWORK.md §3`**): CUANDO un expediente sea `HOTFIX-XXX` bajo `specs/bugs/HOTFIX-XXX-<slug>/`, `.agents/scripts/sdd_code_gate_guard.py`, `.agents/scripts/sdd_immutable_feature_guard.py`, `.agents/scripts/sdd_healthcheck.py` y `scripts/sdd_gate_seal.py` deberán aceptarlo y validarlo con la misma triada (`01-bug-report.md`, `02-fix-spec.md`, `03-tasks.md`) y sellos SHA-256 que `BUG-XXX`; además, `specs/templates/` incorporará `06-spike-report.template.md` y `07-hotfix-fast-track.template.md`, `sdd_healthcheck.py` auditará `specs/spikes/SPIKE-*/SPIKE_REPORT.md` cuando exista, y `specs/SDD_FRAMEWORK.md §3` eliminará referencias a rutas inexistentes.
- `RF-1203` (**Alineación SDD de `spec-miner.md` y protección contra sobreescritura**): `.sdd/catalog/specialists-optin/spec-miner.md` deberá especificar la extracción de requisitos EARS, escenarios `Given-When-Then` y contexto de dominio directamente hacia `specs/features/FEAT-XXX-<slug>/01-spec.md`, `domains/<slug>/` y `docs/knowledge/` (eliminando rutas `openspec/specs/` y formato `#### Scenario:`), y `scripts/sdd_catalog_import.py` deberá preservar especialistas adaptados a SDD (`SDD_CUSTOMIZED_SPECIALISTS`) salvo flag explícito `--overwrite-sdd-custom`.
- `RF-1204` (**Flujo PR seguro en `release-finish` y `hotfix-finish`**): CUANDO el usuario ejecute `sdd git release-finish` o `sdd git hotfix-finish` sin `--local-merge`, `scripts/sdd_git.py` deberá validar limpieza/rama, crear o preparar la Pull Request hacia `main` vía `GitProviderAdapter.create_pr` y actualizar `.agents/ACTIVE_STATE.md` sin ejecutar `git merge` directo sobre `main` (preservando `--local-merge` como opción explícita local que nunca hace `push` directo a `main`, cumpliendo `RN-SDD-BRANCH-SYNC`).

## 3. Criterios de Aceptación (BDD / Given-When-Then)
1. **Escenario `CA-1201` (`sdd work-item set` *fail-closed*):**
   - **Dado** un expediente `specs/bugs/BUG-001-demo/` existente
   - **Cuando** se ejecuta `uv run python scripts/sdd_cli.py work-item set BUG-001`
   - **Entonces** `.agents/active_work_item.json` actualiza `active_work_item_id`, `spec_dir` y `status: "PENDING_APPROVAL"` manteniendo `approved_by_human: false` y `gate_1_approved..3: false`, y falla con código `1` si el ID no existe o escapa del repo.
2. **Escenario `CA-1202` (`HOTFIX-*` permitido tras Gate 1–3 y `SPIKE` auditado):**
   - **Dado** `specs/bugs/HOTFIX-001-auth-bypass/` con triada aprobada y sellada y `specs/STACK.md` aprobado
   - **Cuando** `sdd_code_gate_guard.py` evalúa una escritura en `src/` y `sdd_healthcheck.py` audita `specs/`
   - **Entonces** el guard permite la escritura y `sdd_healthcheck.py` pasa en verde (fallando si falta algún archivo de la triada o si `SPIKE_REPORT.md` contiene directivas de *prompt injection*).
3. **Escenario `CA-1203` (`spec-miner` SDD preservado):**
   - **Dado** `.sdd/catalog/specialists-optin/spec-miner.md` adaptado a SDD
   - **Cuando** se ejecuta `import_specialists` con un fetcher simulado sin `--overwrite-sdd-custom`
   - **Entonces** `spec-miner.md` conserva la versión SDD intacta sin volver a `openspec/specs/`.
4. **Escenario `CA-1204` (`release-finish` PR-first):**
   - **Dado** una rama `release/v1.1.1` limpia
   - **Cuando** se ejecuta `cmd_release_finish` por defecto (sin `--local-merge`)
   - **Entonces** invoca `GitProviderAdapter.create_pr` hacia `main` sin mutar ni pushear directamente la rama `main` local.

<!-- sdd:gate-seal gate=1 sha256=1da8fa7f5f05c2ebf7d533dcc2db85a7893dcac36f0b65d50f454701c22d62e5 -->
