# Release Readiness (Gate 6): `REL-vX.Y.Z`

> **Uso obligatorio:** Generar en `specs/releases/REL-vX.Y.Z.md` mediante `./sdd release prepare --version X.Y.Z` conforme a `specs/SDD_FRAMEWORK.md §4 (Gate 6)`. Debe permanecer no vacío, con plan de despliegue/rollback completo y sin autoaprobación para superar `./sdd release verify --version X.Y.Z --stage finish` y `.agents/scripts/sdd_healthcheck.py`.

- **ID:** `REL-vX.Y.Z`
- **Versión SemVer:** `vX.Y.Z`
- **Tag previo:** `vA.B.C` (o inicial)
- **Fecha objetivo:** `YYYY-MM-DD`
- **Rama de release:** `release/vX.Y.Z` (PR hacia `main` y backport a `develop` según `RN-SDD-BRANCH-SYNC`)
- **Estado del Documento:** `Draft` | `In Review` | `Approved` | `Released`

---

## 1. Alcance y Work Items `Done`
- **Resumen ejecutivo de la release:** [Descripción concisa de las capacidades, correcciones y mejoras incluidas en `vX.Y.Z`.]
- **Work Items incluidos (estado `Done` en `BACKLOG.md`):**
{{RELEASE_ITEMS}}
- **CHANGELOG sincronizado:** Sección `## [vX.Y.Z] - YYYY-MM-DD` generada y verificada en `CHANGELOG.md`.

---

## 2. Checklist Automático de Calidad y Seguridad
- [ ] Cero work items abiertos (`In Progress`, `In Review`, `Blocked` en backlog o `.agents/active_work_item.json` distinto de `IDLE`/`REL-vX.Y.Z`).
- [ ] `./sdd ci-verify` ejecutado en verde (`PASS`).
- [ ] `.agents/scripts/sdd_healthcheck.py` y `verify_architecture_boundaries.py` ejecutados en verde.
- [ ] `CHANGELOG.md` actualizado de forma determinista con la versión `vX.Y.Z`.
- [ ] Cero secretos expuestos, árbol de trabajo limpio y sin commits directos a `main`.

---

## 3. Riesgos, Breaking Changes y Migraciones
- **Breaking changes y deprecaciones:** [Ninguno, o detallar cambios incompatibles, avisos y período de gracia según `SDD_FRAMEWORK.md §8.8`.]
- **Migraciones de datos / configuración / entorno:** [N/A, o detallar pasos `Up`/`Down`, variables de entorno nuevas y compatibilidad hacia atrás según `SDD_FRAMEWORK.md §8.3`.]
- **Matriz de riesgos y mitigación:**

| Riesgo | Impacto / Probabilidad | Mitigación preventiva |
| :--- | :--- | :--- |
| [Riesgo operativo o técnico principal] | [Bajo / Medio / Alto] | [Medida de contención y validación previa] |

---

## 4. Plan de Despliegue y Rollback
- **Secuencia de despliegue:**
  1. Verificar rama `release/vX.Y.Z` actualizada y checks CI/CD en verde (`./sdd release verify --version X.Y.Z --stage finish`).
  2. Ejecutar `./sdd git release-finish --version X.Y.Z` para abrir Pull Request hacia `main` (`RN-SDD-BRANCH-SYNC`).
  3. Tras aprobación y merge de la PR en `main`, etiquetar `vX.Y.Z` y ejecutar el pipeline de publicación/despliegue del entorno objetivo.
- **Verificación post-despliegue (Smoke Test):**
  - [Comprobación de salud del servicio/CLI tras publicar la versión `vX.Y.Z`.]
- **Plan de Rollback (Reversión Determinista):**
  - **Criterio de activación:** Fallo crítico S1 en validación post-despliegue, degradación grave o regresión de seguridad.
  - **Procedimiento de reversión:**
    1. Detener la promoción del artefacto y revertir el commit de merge en `main` mediante Pull Request de reversión (`git revert -m 1 MERGE_SHA`) o redesplegar inmediatamente el tag estable previo (`vA.B.C`).
    2. Ejecutar rollback `Down` de migraciones de configuración/esquema si aplicara y verificar restauración del servicio.
    3. Abrir expediente `HOTFIX-XXX` según `specs/SDD_FRAMEWORK.md §8.5` para causa raíz y regresión.

---

## 5. Aprobación Formal Gate 6 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
> ⚠️ **Exclusivo para el Stakeholder Humano** (Los agentes de IA y comandos CLI tienen prohibido marcar esta casilla por su cuenta):
- [ ] **Gate 6 Approved (Human Sign-off):** Alcance de la release, checklist CI/CD, análisis de riesgos, migraciones y plan de despliegue/rollback revisados y aprobados para integrar en main.
