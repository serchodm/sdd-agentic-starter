# Release Readiness (Gate 6): `REL-v1.5.0`

> **Uso obligatorio:** Generar en `specs/releases/REL-v1.5.0.md` mediante `./sdd release prepare --version 1.5.0` conforme a `specs/SDD_FRAMEWORK.md §4 (Gate 6)`. Debe permanecer no vacío, con plan de despliegue/rollback completo y sin autoaprobación para superar `./sdd release verify --version 1.5.0 --stage finish` y `.agents/scripts/sdd_healthcheck.py`.

- **ID:** `REL-v1.5.0`
- **Versión SemVer:** `v1.5.0`
- **Tag previo:** `v1.4.0`
- **Fecha objetivo:** `2026-11-25`
- **Rama de release:** `release/v1.5.0` (PR hacia `main` y backport a `develop` según `RN-SDD-BRANCH-SYNC`)
- **Estado del Documento:** `Approved`

---

## 1. Alcance y Work Items `Done`
- **Resumen ejecutivo de la release:** Entrega integral de `FWK-020` (`RFC-010`), consolidando la gobernanza Core de seguridad y calidad (`sdd-security-audit` con modelado STRIDE en `Gate 2` y verificación OWASP/ASVS en `Gate 4`, además de la elevación de `L3` a `L4` con `references/` bajo demanda de `sdd-silent-failure-audit`, `sdd-test-quality-audit`, `sdd-execution-guardrails` y `search-first`), el saneamiento completo (`R0`–`R4`) de los 19 packs previos del catálogo con auditoría determinista en `tests/test_sdd_governance.py`, y la expansión a **25 packs Enterprise** (`capability:event-driven`, `capability:api-governance`, `capability:iac-cloud`, `capability:data-engineering`, `framework:nextjs`, `framework:nestjs`, más `helm-gitops-patterns` en `capability:devops` y `multi-tenant-isolation` en `capability:database`), preservación *fail-closed* de extensiones SDD en `scripts/sdd_catalog_import.py`, poda de perfiles en `scripts/sdd_pack_registry.py` y paridad 1:1 de atribuciones `MIT`/`Apache-2.0` en `.sdd/catalog/UPSTREAM.md` y `THIRD_PARTY_NOTICES.md`.
- **Work Items incluidos (estado `Done` en `BACKLOG.md`):**
- `FWK-020` (framework, `done`): Gobernanza Core (sdd-security-audit + references/ L4), Saneamiento ECC y Expansión de Packs Enterprise (v1.5.0)
- **CHANGELOG sincronizado:** Sección `## [v1.5.0] - 2026-11-25` generada y verificada en `CHANGELOG.md`.

---

## 2. Checklist Automático de Calidad y Seguridad
- [x] Cero work items abiertos (`In Progress`, `In Review`, `Blocked` en backlog o `.agents/active_work_item.json` distinto de `IDLE`/`REL-v1.5.0`).
- [x] `./sdd ci-verify` ejecutado en verde (`PASS`, `182` tests offline + `OVER_500=0` + presupuestos de tokens `.agents/` `< 25.000` y `references/` `< 15.000`).
- [x] `.agents/scripts/sdd_healthcheck.py` y `verify_architecture_boundaries.py` ejecutados en verde.
- [x] `CHANGELOG.md` actualizado de forma determinista con la versión `v1.5.0`.
- [x] Cero secretos expuestos, árbol de trabajo limpio y sin commits directos a `main`.

---

## 3. Riesgos, Breaking Changes y Migraciones
- **Breaking changes y deprecaciones:** Ninguno. Compatibilidad retroactiva total con proyectos derivados `v1.4.0`, `specs/STACK.md`, hooks `PreToolUse`, `./sdd` y los 19 packs preexistentes. Los 6 packs nuevos son opt-in durante `/sdd-bootstrap` o `./sdd generate --materialize`.
- **Migraciones de datos / configuración / entorno:** N/A para datos persistentes. En proyectos derivados que actualicen a `v1.5.0` mediante `./sdd sync`: (a) sincronizar `.agents/skills/sdd-security-audit/` y las carpetas `references/` de las 4 skills Core `L4`, (b) ejecutar `./sdd generate --materialize` si se habilitan los nuevos packs Enterprise en `specs/STACK.md`.
- **Matriz de riesgos y mitigación:**

| Riesgo | Impacto / Probabilidad | Mitigación preventiva |
| :--- | :--- | :--- |
| Reintroducción de rutas externas (`rules/ecc/`, `.claude/`) o cercas rotas al re-importar packs upstream | Medio / Bajo | Preservación *fail-closed* de extensiones SDD en `scripts/sdd_catalog_import.py` y auditoría automática `audit_catalog_pack_references` (`R0`–`R4`) en `tests/test_sdd_governance.py`. |
| Desviación de presupuesto de tokens en `.agents/` (`< 25k`) o `references/` (`< 15k`) | Medio / Bajo | Guardrails deterministas en `tests/test_sdd_{governance,release,brownfield,drift,portfolio}.py` con carga progresiva L4 bajo demanda. |
| Desincronización entre `main` y `develop` tras el merge de la PR de release | Medio / Bajo | Flujo PR-first hacia `main` con `.github/workflows/release.yml` (etiquetado `v1.5.0`, GitHub Release *Latest* y back-merge automático a `develop`). |

---

## 4. Plan de Despliegue y Rollback
- **Secuencia de despliegue:**
  1. Verificar rama `release/v1.5.0` actualizada y checks CI/CD en verde (`./sdd release verify --version 1.5.0 --stage finish`).
  2. Ejecutar `./sdd git release-finish --version 1.5.0` para abrir Pull Request hacia `main` (`RN-SDD-BRANCH-SYNC`).
  3. Tras aprobación y merge de la PR en `main`, `.github/workflows/release.yml` crea el tag `v1.5.0`, publica la GitHub Release como *Latest* e intenta el back-merge a `develop`.
- **Verificación post-despliegue (Smoke Test):**
  - Ejecutar `uv run python scripts/sdd_cli.py ci-verify --mode framework --format text` y `uv run python scripts/sdd_agent_generator.py --verify` en `main` tras el merge, confirmando `PASS`, la presencia del tag `v1.5.0`, la GitHub Release *Latest* y la sección `## [v1.5.0] - 2026-11-25` en `CHANGELOG.md`.
- **Plan de Rollback (Reversión Determinista):**
  - **Criterio de activación:** Fallo crítico S1 en validación post-despliegue, degradación grave o regresión de seguridad.
  - **Procedimiento de reversión:**
    1. Detener la promoción del artefacto y revertir el commit de merge en `main` mediante Pull Request de reversión (`git revert -m 1 MERGE_SHA`) o redesplegar inmediatamente el tag estable previo (`v1.4.0`).
    2. Ejecutar rollback `Down` de migraciones de configuración/esquema si aplicara y verificar restauración del servicio.
    3. Abrir expediente `HOTFIX-XXX` según `specs/SDD_FRAMEWORK.md §8.5` para causa raíz y regresión.

---

## 5. Aprobación Formal Gate 6 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
> ⚠️ **Exclusivo para el Stakeholder Humano** (Los agentes de IA y comandos CLI tienen prohibido marcar esta casilla por su cuenta):
- [x] **Gate 6 Approved (Human Sign-off):** Alcance de la release, checklist CI/CD, análisis de riesgos, migraciones y plan de despliegue/rollback revisados y aprobados para integrar en main (Authorized by PO in chat on 2026-11-25T20:50:07+01:00).
