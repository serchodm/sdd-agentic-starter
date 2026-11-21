# RFC-009: Portfolio / Épicas, FinOps Agéntico y Contratos Multi-Servicio (`v1.4.0`)

- **ID:** `RFC-009`
- **Versión objetivo:** `v1.4.0`
- **Estado:** `Aceptado` *(Autorización explícita PO: `2026-11-21T01:14:44+01:00` — "Quiero los 3 bloques completos" / "Si")*
- **Rama base:** `develop`
- **Antecedentes:** [`RFC-006`](RFC-006-coherence-and-catalog-alignment.md), [`RFC-007`](RFC-007-release-ops-ci-agnostic.md), [`RFC-008`](RFC-008-brownfield-adoption-and-spec-drift.md), [`ADR-010`](../../../docs/knowledge/ADRS.md)

## 1. Motivación y Análisis Crítico

La hoja de ruta acordada tras `v1.1.0` (`RFC-006` / `ADR-010`) establece **`v1.4.0`** como el hito de **Capa de Producto, FinOps y Escala**. Completados `v1.1.1` (Coherencia), `v1.2.0` (`Gate 6` CI-agnóstico) y `v1.3.0` (*Brownfield* & *Spec Drift*), el análisis del repositorio detecta tres carencias estructurales que deben resolverse en tres entregas consecutivas:

1. **Salto Pre-Gate-0 sin Épicas, Roadmap ni Dependencias entre Features (`FWK-017`):**
   - `specs/SDD_FRAMEWORK.md §2.1` define conceptualmente la *Épica (`Epic`)*, pero `specs/BACKLOG.md` sigue siendo una tabla plana de `FEAT-XXX` sin agrupación por `EPIC-XXX`, sin priorización estructurada (*MoSCoW / RICE*), sin grafo de dependencias entre features y sin cálculo determinista de progreso ni ruta crítica de portfolio.
   - Se requiere `scripts/sdd_portfolio.py` (`./sdd portfolio`), plantilla `specs/templates/09-epic-roadmap.template.md` (`0` bytes en `.agents/`) y soporte retrocompatible para proyectos con o sin Épicas declaradas.
2. **Telemetría de Sesión sin Contabilidad FinOps por Work Item ni Épica (`FWK-018`):**
   - `.agents/scripts/sdd_token_usage.py` (`405L`) mide únicamente la salud de contexto de la sesión actual (`Turn X/15`, tokens `In/Out/Cache`), sin acumular consumo histórico por `FEAT`/`CR`/`BUG`/`HOTFIX`/`FWK` ni permitir presupuestos o estimación de coste por tier/modelo.
   - Se requiere `scripts/sdd_finops.py` (`./sdd finops`) para imputar sesiones en `.agents/active_work_item.json` y un ledger histórico por work item/épica con alertas de presupuesto configurables 100% offline.
3. **Modelo Single-App sin Gobierno Multi-Servicio / Monorepo ni Contratos Compartidos (`FWK-019`):**
   - `specs/STACK.md` y `.agents/scripts/verify_architecture_boundaries.py` (`422L`) asumen por defecto un único backend/frontend/BBDD, sin modelar relaciones productor–consumidor entre servicios/paquetes (`packages/`, `services/`) ni detectar *breaking changes* en contratos compartidos (OpenAPI, JSON Schema, eventos) antes de Gate 2/4.
   - Se requiere `scripts/sdd_contracts.py` (`./sdd contracts`), extensión retrocompatible de `sdd:ownership-map` / `00-stack.template.md` e integración *opt-in / fail-closed* en `verify_architecture_boundaries.py` y `sdd_ci.py`.

## 2. Descomposición en Work Items

| ID | Título | Prioridad | Depende de | Alcance |
| :--- | :--- | :---: | :---: | :--- |
| **`FWK-017`** | Portfolio, Épicas (`EPIC-XXX`), Roadmap y Dependencias entre Features (`sdd portfolio`) | P0 | — | `specs/templates/09-epic-roadmap.template.md`, `scripts/sdd_portfolio.py`, subcomando `portfolio` en `scripts/sdd_cli.py`, integración no intrusiva en `scripts/sdd_ci.py` y `tests/test_sdd_portfolio.py`. |
| **`FWK-018`** | FinOps Agéntico: Imputación Acumulada, Coste por Work Item/Épica y Presupuestos (`sdd finops`) | P1 | `FWK-017` | `scripts/sdd_finops.py`, subcomando `finops` en `scripts/sdd_cli.py`, integración de rollup por `EPIC-XXX` / Work Item, tabla de tarifas offline y alertas de presupuesto, y `tests/test_sdd_finops.py`. |
| **`FWK-019`** | Multi-Servicio / Monorepo y Verificador de Contratos Compartidos (`sdd contracts`) | P1 | `FWK-017` | Extensión retrocompatible de `specs/templates/00-stack.template.md` y `scripts/sdd_ownership.py`, `scripts/sdd_contracts.py`, subcomando `contracts` en `scripts/sdd_cli.py`, integración en `verify_architecture_boundaries.py` / `sdd_ci.py` y `tests/test_sdd_contracts.py`. |

## 3. Restricciones Transversales

- **Stdlib-only & Modularidad (`<= 500L`):** Python `>= 3.12` sin dependencias externas (`pyproject.toml`); todo módulo nuevo o modificado bajo `scripts/`, `.agents/scripts/` y `tests/` debe mantenerse estrictamente en `<= 500` líneas (dado que `sdd_ownership.py`, `sdd_healthcheck.py` y `sdd_ci.py` rozan actualmente `497–499L`, la nueva lógica debe aislarse en módulos dedicados).
- **Seguridad *Fail-Closed* (`shell=False`):** prohibido `shell=True`; validación estricta contra symlinks/junctions, prefijos `\\?\` y *path traversal* (`resolve_repo_relative_path`, `is_link_or_junction`).
- **Presupuesto de Contexto (`< 25k`):** todas las nuevas plantillas residen bajo `specs/templates/` (`0` bytes en `.agents/`) manteniendo el presupuesto Markdown activo de `.agents/` por debajo de `25k` tokens estimados.
- **Compatibilidad Retroactiva:** proyectos *greenfield* o *brownfield* sin Épicas, sin ledger FinOps o con topología *single-app* deben seguir pasando `sdd_healthcheck.py` y `sdd ci-verify` sin fricción (`SKIPPED_NO_APPLICABLE` cuando no aplique).
- **Autoridad Humana (`RN-SDD-HUMAN-GATE-OWNERSHIP`):** ninguna herramienta puede autoaprobar `Gate S0`, `Gate 1..3` ni `Gate 6`.
