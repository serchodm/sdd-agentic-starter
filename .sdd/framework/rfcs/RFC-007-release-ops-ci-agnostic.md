# RFC-007: Motor CI-Agnóstico, `Gate 6` de Release Readiness y Changelog Determinista (`v1.2.0`)

- **ID:** `RFC-007`
- **Versión objetivo:** `v1.2.0`
- **Estado:** `Aceptado` *(Autorización explícita PO: `2026-11-16T18:13:32+01:00` — "confirmo")*
- **Rama base:** `develop`
- **Antecedentes:** [`RFC-006`](RFC-006-coherence-and-catalog-alignment.md), [`ADR-010`](../../../docs/knowledge/ADRS.md)

## 1. Motivación y Análisis Crítico

La hoja de ruta definida en `RFC-006` / `ADR-010` fija `v1.2.0` como el hito de **Release & Ops CI-agnóstico (`Gate 6`)**. El análisis del repositorio tras `v1.1.1` detecta cinco carencias estructurales que deben resolverse en dos entregas consecutivas:

1. **Lógica CI atrapada en GitHub Actions y acoplada al starter:** `.github/workflows/ci.yml` embebe ~90 líneas de Python inline (validación de `.agents/hooks.json` sin BOM, auditoría 0DD, bucle `sdd_dag.py --verify` y umbral `>= 120` tests). Como `scripts/sdd_sync.py` sincroniza `.github/workflows` hacia proyectos derivados, un proyecto nuevo hereda un pipeline que exige `>= 120` tests del starter y omite sus comandos de `specs/STACK.md §2.5`.
2. **Ausencia de portabilidad multi-CI:** proyectos en GitLab CI, Bitbucket Pipelines o entornos puramente locales carecen de un punto de entrada único (`./sdd ci-verify`) y de plantillas CI equivalentes que deleguen en el mismo motor determinista.
3. **Separación de ámbito para `Gate 6`:** `Gate 0..5` pertenecen al ciclo de cada Work Item; las releases (`vX.Y.Z`) agrupan *N* Work Items ya `Done` en `develop`. `Gate 6` debe definirse con **ámbito Release (`REL-vX.Y.Z`)**, simétrico a `Gate S0` (ámbito Proyecto), con plantilla de *Release Readiness & Rollback* fuera de `.agents/` para no penalizar el presupuesto `< 25k` tokens (`ADR-007`).
4. **`cmd_release_start` / `cmd_release_finish` sin preflight SDD (`scripts/sdd_git.py`):** hoy `sdd_git.py` mide `454L` (cerca del techo `<= 500L`) y abre ramas/PRs de release sin comprobar salud SDD, work items abiertos, sellos SHA-256 ni sign-off de `Gate 6`.
5. **`CHANGELOG.md` trazable:** generar notas solo desde `git log` arrastra ruido; es necesario cruzar rango `<tag>..HEAD` con `BACKLOG.md` y cabeceras de specs de forma idempotente y 100% offline.

## 2. Descomposición en Work Items

| ID | Título | Prioridad | Depende de | Alcance |
| :--- | :--- | :---: | :---: | :--- |
| **`FWK-013`** | Motor CI-Agnóstico (`sdd ci-verify`), Desacoplo de `ci.yml` y Plantillas Multi-CI | P0 | — | `scripts/sdd_ci.py`, subcomando `ci-verify` en `scripts/sdd_cli.py`, refactor ligero de `.github/workflows/ci.yml`, plantillas en `specs/templates/ci/` y tests offline. |
| **`FWK-014`** | `Gate 6` (`REL-vX.Y.Z`), Motor de Release Readiness (`sdd_release.py`) y `CHANGELOG.md` Determinista | P1 | `FWK-013` | `specs/SDD_FRAMEWORK.md` (§4 `Gate 6`), `specs/templates/08-release-readiness.template.md`, `.agents/workflows/gate6-release.md`, `scripts/sdd_release.py`, integración preflight en `scripts/sdd_git.py` y tests offline. |

## 3. Restricciones Transversales
- **Stdlib-only & Modularidad:** Python `>= 3.12` sin dependencias externas (`pyproject.toml`), `<= 500` líneas por cada `.py` bajo `scripts/`, `.agents/scripts/` y `tests/`.
- **Seguridad *Fail-Closed* (`shell=False`):** prohibido `shell=True`; los comandos de `specs/STACK.md §2.5` solo se leen del bloque estructurado `yaml sdd:verification-commands` y se ejecutan en local únicamente bajo opt-in (`--run-stack`).
- **Presupuesto de Contexto (`< 25k`):** las plantillas CI y de release residen bajo `specs/templates/` (0 tokens en `.agents/`).
- **Autoridad Humana (`RN-SDD-HUMAN-GATE-OWNERSHIP`):** ninguna herramienta puede autoaprobar `Gate 6`.
