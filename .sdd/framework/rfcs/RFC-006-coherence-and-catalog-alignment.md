# RFC-006: Alineación de Coherencia v1.1.1 (CLI, `HOTFIX`/`SPIKE`, `spec-miner` SDD y `release-finish`)

- **ID:** `RFC-006`
- **Versión objetivo:** `v1.1.1`
- **Estado:** `Implementado / Done` *(Autorización explícita PO: `2026-11-16T11:46:29+01:00` — "Revisados y aprobados. Ejecuta")*
- **Rama base:** `develop` (trabajo en `feat/fwk-012-coherence-alignment`)
- **Alcance origen:** Auditoría integral sobre `main` (`712648c`, `2026-11-16`).

## 1. Motivación y Pilares (`FWK-012`)

Antes de construir nuevas capacidades mayores (`v1.2.0` Release/Ops CI-agnóstico, `v1.3.0` Brownfield & Spec Drift, `v1.4.0` Portfolio/FinOps), se resuelven las 4 inconsistencias detectadas entre documentación, catálogo opt-in y herramientas deterministas:

1. **Coherencia CLI ↔ Documentación (`RF-1201`):**
   - `README.md` y `.agents/workflows/bug-fast-track.md` referencian `.agents/scripts/sdd_cli.py` y el subcomando `work-item`, mientras el despachador real reside en `scripts/sdd_cli.py` y carece de `work-item`.
   - Se corrigen todas las referencias a `scripts/sdd_cli.py` y se implementa el subcomando `work-item` (`show`, `set <ID>`) con actualización segura en estado `PENDING_APPROVAL` (sin autoaprobar Gates `1..3`).

2. **Soporte End-to-End de `HOTFIX-*` y `SPIKE-*` (`RF-1202`):**
   - `specs/SDD_FRAMEWORK.md §8.5` define `specs/bugs/HOTFIX-<ID>-<nombre>/`, pero `sdd_code_gate_guard.py`, `sdd_immutable_feature_guard.py` y `sdd_gate_seal.py` solo aceptan `FEAT|CR|BUG|FWK`.
   - Se habilita `HOTFIX-\d{3,4}` en los guardias y sellos, se añaden plantillas oficiales (`06-spike-report.template.md`, `07-hotfix-fast-track.template.md`), se valida `specs/spikes/SPIKE-*/SPIKE_REPORT.md` en `sdd_healthcheck.py` y se depuran las rutas legacy inexistentes de `specs/SDD_FRAMEWORK.md §3`.

3. **Alineación de `spec-miner.md` al Estándar SDD (`RF-1203`):**
   - `.sdd/catalog/specialists-optin/spec-miner.md` conserva formato OpenSpec (`openspec/specs/<capability>/spec.md`, `#### Scenario:`), incompatible con `specs/features/FEAT-XXX/`, EARS, `domains/` y `sdd_healthcheck.py`.
   - Se adapta `spec-miner.md` al esquema SDD nativo (`specs/features/FEAT-XXX/01-spec.md` + `domains/<slug>/`) y se protege en `scripts/sdd_catalog_import.py` frente a sobreescrituras accidentales en futuras importaciones *upstream*.

4. **Alineación de `release-finish` / `hotfix-finish` con `RN-SDD-BRANCH-SYNC` (`RF-1204`):**
   - `cmd_release_finish` y `cmd_hotfix_finish` en `scripts/sdd_git.py` ejecutan fusión local directa a `main`, lo que entra en tensión con `RN-SDD-BRANCH-SYNC` y el bloqueo `pre-push` de `scripts/sdd_hooks.py`.
   - Por defecto pasan a crear/preparar la PR hacia `main` vía `GitProviderAdapter.create_pr` (reservando la fusión local únicamente bajo flag explícito `--local-merge` sin push directo a `main`).
