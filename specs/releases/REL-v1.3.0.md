# Release Readiness (Gate 6): `REL-v1.3.0`

> **Uso obligatorio:** Generar en `specs/releases/REL-v1.3.0.md` mediante `./sdd release prepare --version 1.3.0` conforme a `specs/SDD_FRAMEWORK.md §4 (Gate 6)`. Debe permanecer no vacío, con plan de despliegue/rollback completo y sin autoaprobación para superar `./sdd release verify --version 1.3.0 --stage finish` y `.agents/scripts/sdd_healthcheck.py`.

- **ID:** `REL-v1.3.0`
- **Versión SemVer:** `v1.3.0`
- **Tag previo:** `v1.2.0`
- **Fecha objetivo:** `2026-11-20`
- **Rama de release:** `release/v1.3.0` (PR hacia `main` y backport a `develop` según `RN-SDD-BRANCH-SYNC`)
- **Estado del Documento:** `Approved`

---

## 1. Alcance y Work Items `Done`
- **Resumen ejecutivo de la release:** Entrega completa de `RFC-008` (`v1.3.0`), incorporando el motor offline de adopción brownfield (`./sdd adopt` en `scripts/sdd_brownfield.py`) junto con el workflow `/brownfield-adopt` y `@spec-miner` (`FWK-015`), así como el detector determinista de *Spec Drift* (`./sdd drift` en `scripts/sdd_drift.py`), zonas *Strangler Fig* (`governed` vs `legacy-readonly`) en `sdd:ownership-map` / `sdd_code_gate_guard.py` y soporte de *Baseline Retroactiva Ligera* (`origin: brownfield-mined`) en `sdd_healthcheck.py`, `sdd_gate_seal.py` y `sdd_ci.py` (`FWK-016`).
- **Work Items incluidos (estado `Done` en `BACKLOG.md`):**
- `FWK-015` (framework, `done`): Motor de Adopción Brownfield (`sdd adopt`), Descubrimiento Determinista y Workflow `@spec-miner`
- `FWK-016` (framework, `done`): Detector de *Spec Drift* (`sdd drift`), Zonas *Strangler Fig* y Baseline Retroactiva Ligera
- **CHANGELOG sincronizado:** Sección `## [v1.3.0] - 2026-11-20` generada y verificada en `CHANGELOG.md`.

---

## 2. Checklist Automático de Calidad y Seguridad
- [x] Cero work items abiertos (`In Progress`, `In Review`, `Blocked` en backlog o `.agents/active_work_item.json` distinto de `IDLE`/`REL-v1.3.0`).
- [x] `./sdd ci-verify` ejecutado en verde (`PASS`).
- [x] `.agents/scripts/sdd_healthcheck.py` y `verify_architecture_boundaries.py` ejecutados en verde.
- [x] `CHANGELOG.md` actualizado de forma determinista con la versión `v1.3.0`.
- [x] Cero secretos expuestos, árbol de trabajo limpio y sin commits directos a `main`.

---

## 3. Riesgos, Breaking Changes y Migraciones
- **Breaking changes y deprecaciones:** Ninguno. Se mantiene compatibilidad retroactiva total en `./sdd`, `specs/STACK.md`, bloques `sdd:ownership-map` sin sección `zones` (asumidos como `governed`), hooks `PreToolUse` y flujos *greenfield* existentes.
- **Migraciones de datos / configuración / entorno:** N/A para datos persistentes. En proyectos derivados que adopten `v1.3.0` mediante `sdd_sync.py` o adopten repositorios brownfield: (a) usar `./sdd adopt --dry-run` antes de `--apply` para generar el borrador de `specs/STACK.md` sin autoaprobar `Gate S0`, (b) declarar opcionalmente `zones` (`governed` / `legacy-readonly`) en `sdd:ownership-map` para habilitar adopción incremental *Strangler Fig*, y (c) marcar las features minadas con `origin: brownfield-mined` en `01-spec.md` tras revisión humana explícita.
- **Matriz de riesgos y mitigación:**

| Riesgo | Impacto / Probabilidad | Mitigación preventiva |
| :--- | :--- | :--- |
| Bloqueo de `release-finish` por ficheros temporales `.lock` o artefactos sin seguimiento en el árbol Git | Bajo / Medio | Verificación previa de `git status --porcelain` y limpieza/resolución de archivos no trackeados antes de `sdd release verify --stage finish`. |
| Falsos positivos o cobertura incompleta en `sdd drift` por citas `SRC-###` desactualizadas o sin cabecera `brownfield-mined` | Bajo / Medio | Modo advisory por defecto (`--fail-on-drift` opcional) y validación explícita de citas `path::symbol` en el cierre de Gate 5 / `ci-verify`. |
| Desincronización entre `main` y `develop` tras el merge de la PR de release | Medio / Bajo | Flujo PR-first hacia `main` seguido de etiquetado `v1.3.0` y back-merge / sincronización a `develop` (`RN-SDD-BRANCH-SYNC`). |

---

## 4. Plan de Despliegue y Rollback
- **Secuencia de despliegue:**
  1. Verificar rama `release/v1.3.0` actualizada y checks CI/CD en verde (`./sdd release verify --version 1.3.0 --stage finish`).
  2. Ejecutar `./sdd git release-finish --version 1.3.0` para abrir Pull Request hacia `main` (`RN-SDD-BRANCH-SYNC`).
  3. Tras aprobación y merge de la PR en `main`, etiquetar `v1.3.0` y sincronizar `develop` con los artefactos de release (`REL-v1.3.0.md` y `CHANGELOG.md`).
- **Verificación post-despliegue (Smoke Test):**
  - Ejecutar `uv run python scripts/sdd_cli.py ci-verify --mode auto --format text` en `main` tras el merge y confirmar `PASS` junto con `./sdd adopt --dry-run`, `./sdd drift`, el tag `v1.3.0` y la sección `## [v1.3.0] - 2026-11-20` en `CHANGELOG.md`.
- **Plan de Rollback (Reversión Determinista):**
  - **Criterio de activación:** Fallo crítico S1 en validación post-despliegue, degradación grave o regresión de seguridad.
  - **Procedimiento de reversión:**
    1. Detener la promoción del artefacto y revertir el commit de merge en `main` mediante Pull Request de reversión (`git revert -m 1 MERGE_SHA`) o redesplegar inmediatamente el tag estable previo (`v1.2.0`).
    2. Ejecutar rollback `Down` de migraciones de configuración/esquema si aplicara y verificar restauración del servicio.
    3. Abrir expediente `HOTFIX-XXX` según `specs/SDD_FRAMEWORK.md §8.5` para causa raíz y regresión.

---

## 5. Aprobación Formal Gate 6 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
> ⚠️ **Exclusivo para el Stakeholder Humano** (Los agentes de IA y comandos CLI tienen prohibido marcar esta casilla por su cuenta):
- [x] **Gate 6 Approved (Human Sign-off):** Alcance de la release, checklist CI/CD, análisis de riesgos, migraciones y plan de despliegue/rollback revisados y aprobados para integrar en main (Authorized by PO in chat on 2026-11-20T10:26:05+01:00).
