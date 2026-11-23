# Release Readiness (Gate 6): `REL-v1.4.0`

> **Uso obligatorio:** Generar en `specs/releases/REL-v1.4.0.md` mediante `./sdd release prepare --version 1.4.0` conforme a `specs/SDD_FRAMEWORK.md §4 (Gate 6)`. Debe permanecer no vacío, con plan de despliegue/rollback completo y sin autoaprobación para superar `./sdd release verify --version 1.4.0 --stage finish` y `.agents/scripts/sdd_healthcheck.py`.

- **ID:** `REL-v1.4.0`
- **Versión SemVer:** `v1.4.0`
- **Tag previo:** `v1.3.0`
- **Fecha objetivo:** `2026-11-23`
- **Rama de release:** `release/v1.4.0` (PR hacia `main` y backport a `develop` según `RN-SDD-BRANCH-SYNC`)
- **Estado del Documento:** `Approved`

---

## 1. Alcance y Work Items `Done`
- **Resumen ejecutivo de la release:** Entrega de `FWK-017` (`RFC-009`), incorporando el motor determinista de Portfolio, Épicas (`EPIC-XXX`), Roadmap y Dependencias entre Features (`./sdd portfolio` en `scripts/sdd_portfolio.py` con plantilla `specs/templates/09-epic-roadmap.template.md`, scoring MoSCoW + RICE, detección fail-closed de ciclos, cálculo de olas/camino crítico, integración en `sdd_ci.py` y `ADR-015`), junto con la actualización modular de la skill `santa-method` (`.agents/skills/santa-method/SKILL.md` + `references/reviewer-prompt.md` + `references/sdd-rubrics.md` para `Pre-Gate 2`, `Gate 4` y `Gate 5`, sincronizada con `/santa-loop`, `gan-style-harness`, `pipeline-run`, `review.md` y `MULTIAGENT_ORCHESTRATION_STANDARD.md`).
- **Work Items incluidos (estado `Done` en `BACKLOG.md`):**
- `FWK-017` (framework, `done`): Portfolio, Épicas (`EPIC-XXX`), Roadmap y Dependencias entre Features (`sdd portfolio`)
- **Mejoras adicionales de gobernanza y skills incluidas:**
- `santa-method` (`7f436d3`): Protocolo modular *Checking It Twice* con triggers objetivos por riesgo y volumen/contaminación de contexto, rúbricas binarias por Gate (`Pre-Gate 2`, `Gate 4`, `Gate 5`), agentes frescos por ronda y frontera explícita con `gan-style-harness`.
- **CHANGELOG sincronizado:** Sección `## [v1.4.0] - 2026-11-23` generada y verificada en `CHANGELOG.md`.

---

## 2. Checklist Automático de Calidad y Seguridad
- [x] Cero work items abiertos (`In Progress`, `In Review`, `Blocked` en backlog o `.agents/active_work_item.json` distinto de `IDLE`/`REL-v1.4.0`).
- [x] `./sdd ci-verify` ejecutado en verde (`PASS`, `174/174` tests unitarios + presupuesto `.agents/` `< 25.000` tokens).
- [x] `.agents/scripts/sdd_healthcheck.py` y `verify_architecture_boundaries.py` ejecutados en verde.
- [x] `CHANGELOG.md` actualizado de forma determinista con la versión `v1.4.0`.
- [x] Cero secretos expuestos, árbol de trabajo limpio y sin commits directos a `main`.

---

## 3. Riesgos, Breaking Changes y Migraciones
- **Breaking changes y deprecaciones:** Ninguno. Compatibilidad retroactiva total en `./sdd`, `specs/BACKLOG.md`, `specs/STACK.md`, hooks `PreToolUse` y skills existentes. El chequeo `portfolio` en `sdd ci-verify` devuelve `SKIPPED_NO_APPLICABLE` cuando no existen épicas ni dependencias declaradas.
- **Migraciones de datos / configuración / entorno:** N/A para datos persistentes. En proyectos derivados que adopten `v1.4.0` mediante `sdd_sync.py`: (a) usar `./sdd portfolio init --id EPIC-001 --title "..."` para crear épicas bajo `specs/epics/`, (b) sincronizar la nueva carpeta `.agents/skills/santa-method/references/` para disponer de las plantillas JSON y rúbricas binarias de `/santa-loop`.
- **Matriz de riesgos y mitigación:**

| Riesgo | Impacto / Probabilidad | Mitigación preventiva |
| :--- | :--- | :--- |
| Bloqueo de `release verify --stage finish` por ficheros temporales `.lock` sin seguimiento en `.agents/` | Bajo / Medio | Verificación previa de `git status --porcelain` y limpieza de `.lock` residuales antes de ejecutar `--stage finish`. |
| Sobrepasar el presupuesto de tokens de `.agents/` (`< 25.000` tokens) en futuras ediciones de skills | Medio / Bajo | Test automatizado `test_python_line_ceiling_and_agents_token_budget` en `tests/test_sdd_portfolio.py` y carga progresiva en `references/`. |
| Desincronización entre `main` y `develop` tras el merge de la PR de release | Medio / Bajo | Flujo PR-first hacia `main` seguido de etiquetado `v1.4.0` y back-merge / sincronización a `develop` (`RN-SDD-BRANCH-SYNC`). |

---

## 4. Plan de Despliegue y Rollback
- **Secuencia de despliegue:**
  1. Verificar rama `release/v1.4.0` actualizada y checks CI/CD en verde (`./sdd release verify --version 1.4.0 --stage finish`).
  2. Ejecutar `./sdd git release-finish --version 1.4.0` para abrir Pull Request hacia `main` (`RN-SDD-BRANCH-SYNC`).
  3. Tras aprobación y merge de la PR en `main`, etiquetar `v1.4.0` y sincronizar `develop` con los artefactos de release (`REL-v1.4.0.md` y `CHANGELOG.md`).
- **Verificación post-despliegue (Smoke Test):**
  - Ejecutar `uv run python scripts/sdd_cli.py ci-verify --mode auto --format text` en `main` tras el merge y confirmar `PASS` junto con `uv run python scripts/sdd_cli.py portfolio validate`, el tag `v1.4.0` y la sección `## [v1.4.0] - 2026-11-23` en `CHANGELOG.md`.
- **Plan de Rollback (Reversión Determinista):**
  - **Criterio de activación:** Fallo crítico S1 en validación post-despliegue, degradación grave o regresión de seguridad.
  - **Procedimiento de reversión:**
    1. Detener la promoción del artefacto y revertir el commit de merge en `main` mediante Pull Request de reversión (`git revert -m 1 MERGE_SHA`) o redesplegar inmediatamente el tag estable previo (`v1.3.0`).
    2. Ejecutar rollback `Down` de migraciones de configuración/esquema si aplicara y verificar restauración del servicio.
    3. Abrir expediente `HOTFIX-XXX` según `specs/SDD_FRAMEWORK.md §8.5` para causa raíz y regresión.

---

## 5. Aprobación Formal Gate 6 (`RN-SDD-HUMAN-GATE-OWNERSHIP`)
> ⚠️ **Exclusivo para el Stakeholder Humano** (Los agentes de IA y comandos CLI tienen prohibido marcar esta casilla por su cuenta):
- [x] **Gate 6 Approved (Human Sign-off):** Alcance de la release, checklist CI/CD, análisis de riesgos, migraciones y plan de despliegue/rollback revisados y aprobados para integrar en main (Authorized by PO in chat on 2026-11-23T17:39:46+01:00).
