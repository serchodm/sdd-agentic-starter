# Release Readiness (Gate 6): `REL-v1.2.0`

> **Uso obligatorio:** Generar en `specs/releases/REL-v1.2.0.md` mediante `./sdd release prepare --version 1.2.0` conforme a `specs/SDD_FRAMEWORK.md §4 (Gate 6)`. Debe permanecer no vacío, con plan de despliegue/rollback completo y sin autoaprobación para superar `./sdd release verify --version 1.2.0 --stage finish` y `.agents/scripts/sdd_healthcheck.py`.

- **ID:** `REL-v1.2.0`
- **Versión SemVer:** `v1.2.0`
- **Tag previo:** `v1.1.1`
- **Fecha objetivo:** `2026-11-17`
- **Rama de release:** `release/v1.2.0` (PR hacia `main` y backport a `develop` según `RN-SDD-BRANCH-SYNC`)
- **Estado del Documento:** `In Review`

---

## 1. Alcance y Work Items `Done`
- **Resumen ejecutivo de la release:** Entrega completa de `RFC-007` (`v1.2.0`), incorporando el motor de verificación CI-agnóstico unificado (`./sdd ci-verify`) con plantillas multi-CI (`FWK-013`) y la formalización de `Gate 6` (`REL-vX.Y.Z`) con motor de Release Readiness (`./sdd release`), generación determinista de `CHANGELOG.md` y preflight Git *fail-closed* (`FWK-014`).
- **Work Items incluidos (estado `Done` en `BACKLOG.md`):**
- `FWK-013` (framework, `done`): Motor CI-Agnóstico (`sdd ci-verify`), Desacoplo de `ci.yml` y Plantillas Multi-CI (`RFC-007`)
- `FWK-014` (framework, `done`): `Gate 6` (`REL-vX.Y.Z`), Motor de Release Readiness (`sdd_release.py`) y `CHANGELOG.md` Determinista (`RFC-007`)
- **CHANGELOG sincronizado:** Sección `## [v1.2.0] - 2026-11-17` generada y verificada en `CHANGELOG.md`.

---

## 2. Checklist Automático de Calidad y Seguridad
- [x] Cero work items abiertos (`In Progress`, `In Review`, `Blocked` en backlog o `.agents/active_work_item.json` distinto de `IDLE`/`REL-v1.2.0`).
- [x] `./sdd ci-verify` ejecutado en verde (`PASS`).
- [x] `.agents/scripts/sdd_healthcheck.py` y `verify_architecture_boundaries.py` ejecutados en verde.
- [x] `CHANGELOG.md` actualizado de forma determinista con la versión `v1.2.0`.
- [x] Cero secretos expuestos, árbol de trabajo limpio y sin commits directos a `main`.

---

## 3. Riesgos, Breaking Changes y Migraciones
- **Breaking changes y deprecaciones:** Ninguno. Compatibilidad retroactiva preservada en `./sdd`, `specs/STACK.md`, hooks `PreToolUse` y flujos existentes (`SDD_FRAMEWORK.md §8.8`).
- **Migraciones de datos / configuración / entorno:** N/A para datos persistentes. En proyectos derivados que adopten `v1.2.0` mediante `sdd_sync.py`, copiar opcionalmente las plantillas CI de `specs/templates/ci/` y verificar que `.agents/active_work_item.json` no tenga work items abiertos antes de ejecutar `release-start` (`SDD_FRAMEWORK.md §8.3`).
- **Matriz de riesgos y mitigación:**

| Riesgo | Impacto / Probabilidad | Mitigación preventiva |
| :--- | :--- | :--- |
| Bloqueo de `release-finish` por ficheros temporales/lock sin seguimiento en el árbol Git | Bajo / Medio | Verificación explícita de árbol limpio (`git status --porcelain`) antes de `sdd release verify --stage finish` y `release-finish`. |
| Desincronización entre `main` y `develop` tras el merge de la PR de release | Medio / Bajo | Flujo PR-first hacia `main` seguido de etiquetado `v1.2.0` y back-merge / sincronización a `develop` (`RN-SDD-BRANCH-SYNC`). |

---

## 4. Plan de Despliegue y Rollback
- **Secuencia de despliegue:**
  1. Verificar rama `release/v1.2.0` actualizada y checks CI/CD en verde (`./sdd release verify --version 1.2.0 --stage finish`).
  2. Ejecutar `./sdd git release-finish --version 1.2.0` para abrir Pull Request hacia `main` (`RN-SDD-BRANCH-SYNC`).
  3. Tras aprobación y merge de la PR en `main`, etiquetar `v1.2.0` y sincronizar `develop` con los artefactos de release (`REL-v1.2.0.md` y `CHANGELOG.md`).
- **Verificación post-despliegue (Smoke Test):**
  - Ejecutar `uv run python scripts/sdd_cli.py ci-verify --mode auto --format text` en `main` tras el merge y confirmar `PASS` (`143/143` tests deterministas en verde) junto con la presencia del tag `v1.2.0` y la sección `## [v1.2.0] - 2026-11-17` en `CHANGELOG.md`.
- **Plan de Rollback (Reversión Determinista):**
  - **Criterio de activación:** Fallo crítico S1 en validación post-despliegue, degradación grave o regresión de seguridad.
  - **Procedimiento de reversión:**
    1. Detener la promoción del artefacto y revertir el commit de merge en `main` mediante Pull Request de reversión (`git revert -m 1 MERGE_SHA`) o redesplegar inmediatamente el tag estable previo (`v1.1.1`).
    2. Ejecutar rollback `Down` de migraciones de configuración/esquema si aplicara y verificar restauración del servicio.
    3. Abrir expediente `HOTFIX-XXX` según `specs/SDD_FRAMEWORK.md §8.5` para causa raíz y regresión.

---

## 5. Aprobación Formal Gate 6 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
> ⚠️ **Exclusivo para el Stakeholder Humano** (Los agentes de IA y comandos CLI tienen prohibido marcar esta casilla por su cuenta):
- [ ] **Gate 6 Approved (Human Sign-off):** Alcance de la release, checklist CI/CD, análisis de riesgos, migraciones y plan de despliegue/rollback revisados y aprobados para integrar en main.
