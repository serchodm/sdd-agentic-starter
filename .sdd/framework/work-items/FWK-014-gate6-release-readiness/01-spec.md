# Spec Funcional: `Gate 6` (`REL-vX.Y.Z`), Motor de Release Readiness (`sdd_release.py`) y `CHANGELOG.md` Determinista (`FWK-014`)

- **ID:** `FWK-014-gate6-release-readiness`
- **RFC:** [`RFC-007`](../../rfcs/RFC-007-release-ops-ci-agnostic.md) (`Aceptado`)
- **Estado:** `Approved`
- **Gate 1 Sign-off:** `- [x] **Gate 1 Approved (Human Sign-off):** Alcance, requisitos EARS (RF-1401..RF-1404) y criterios BDD (CA-1401..CA-1404) aprobados (Authorized by PO on 2026-11-17T11:01:37+01:00).`

## 1. Resumen y Alcance
Completar la segunda entrega de `RFC-007` (`v1.2.0`) formalizando **`Gate 6` (`REL-vX.Y.Z`, ámbito Release)** como compuerta simétrica a `Gate S0` (ámbito Proyecto), implementando el motor offline y determinista de Release Readiness y generación de `CHANGELOG.md` (`scripts/sdd_release.py`, expuesto vía `./sdd release`), e integrando verificaciones *fail-closed* de preflight en `scripts/sdd_git.py` (`release-start` / `release-finish`) sin superar el techo modular global (`<= 500` líneas por fichero Python) ni degradar el presupuesto de contexto activo en `.agents/` (`< 25k` tokens).

- **In-Scope:**
  - Formalización de `Gate 6` (`REL-vX.Y.Z`) en `specs/SDD_FRAMEWORK.md` (§3 y §4), nueva plantilla `specs/templates/08-release-readiness.template.md` (fuera de `.agents/`) y workflow conciso `.agents/workflows/gate6-release.md`.
  - Módulo stdlib-only `scripts/sdd_release.py` (`<= 500L`) y registro del subcomando `release` (`prepare`, `changelog`, `verify`) en `scripts/sdd_cli.py`.
  - Generador determinista, idempotente y 100% offline de `CHANGELOG.md` cruzando el rango Git `<prev_tag>..HEAD` con `specs/BACKLOG.md` / `.sdd/framework/BACKLOG.md` y cabeceras de especificaciones (`01-spec.md` / `01-bug-report.md`).
  - Integración *fail-closed* de preflight SDD en `scripts/sdd_git.py` (`cmd_release_start` y `cmd_release_finish`), preservando el flujo PR-first hacia `main` (`RN-SDD-BRANCH-SYNC`) y `<= 500L`.
  - Cobertura de pruebas offline en `tests/test_sdd_release.py` (`<= 500L`) y aislamiento de pruebas previas en `tests/test_sdd_git_concurrency.py` si procede.
- **Out-of-Scope:**
  - Publicación automática en GitHub Releases / GitLab Releases / PyPI o firma criptográfica GPG/Sigstore externa.
  - Onboarding brownfield `/onboard` (`v1.3.0`) y métricas FinOps (`v1.4.0`).
  - Autoaprobación de `Gate 6` por IA o por CLI (`RN-SDD-HUMAN-GATE-OWNERSHIP`).

## 2. Requisitos (EARS)
- `RF-1401` (**Definición normativa de `Gate 6`, plantilla `REL-vX.Y.Z` y workflow**): El sistema deberá formalizar `Gate 6` con ámbito Release (`REL-vX.Y.Z`) en `specs/SDD_FRAMEWORK.md` (§3 y §4), proveer la plantilla `specs/templates/08-release-readiness.template.md` bajo `specs/templates/` (`0` bytes en `.agents/`) y añadir `.agents/workflows/gate6-release.md` manteniendo el presupuesto total de `.agents/` por debajo de `25k` tokens (`< 100 KB`).
- `RF-1402` (**Preparación y verificación *fail-closed* de Release Readiness `sdd release`**): CUANDO se ejecute `sdd release prepare --version <X.Y.Z>`, el sistema deberá generar `specs/releases/REL-vX.Y.Z.md` a partir de la plantilla oficial con la lista de work items `Done` del rango y la casilla `- [ ] **Gate 6 Approved (Human Sign-off):** ...` estrictamente desmarcada, rechazando sobrescrituras sin `--force`. CUANDO se ejecute `sdd release verify --version <X.Y.Z> --stage finish`, el sistema deberá validar en modo *fail-closed*: (a) SemVer válido, (b) ausencia de work items abiertos (`In Progress`, `In Review`, `Blocked` en backlog o `active_work_item.json` distinto de `IDLE`/`REL-*`), (c) existencia de `specs/releases/REL-vX.Y.Z.md` con firma `[x] Gate 6 Approved` real fuera de comentarios HTML y bloques vallados (y sello SHA-256 íntegro si está presente), (d) existencia de la sección `vX.Y.Z` en `CHANGELOG.md`, y (e) resultado `PASS` de `sdd_ci.run_ci_verify`.
- `RF-1403` (**Generación determinista e idempotente de `CHANGELOG.md`**): CUANDO se ejecute `sdd release changelog --version <X.Y.Z>`, el sistema deberá operar 100% offline inspeccionando commits en `<prev_tag>..HEAD` (`shell=False`), cruzar los identificadores (`FEAT|CR|BUG|HOTFIX|FWK-XXX`) contra `BACKLOG.md` y cabeceras de especificaciones para descartar ruido de commits (`Merge ...`, `chore(release)...`, etc.), y actualizar o insertar la sección `## [vX.Y.Z] - YYYY-MM-DD` en `CHANGELOG.md` de manera idempotente sin mutar secciones de versiones previas.
- `RF-1404` (**Preflight SDD en `scripts/sdd_git.py` (`release-start` / `release-finish`)**): CUANDO se invoque `sdd git release-start` o `sdd git release-finish`, el sistema deberá ejecutar el preflight de `sdd_release.py` (`stage="start"` en `release-start`: SemVer válido, tag inexistente, sin work items abiertos y `ci-verify` en verde; `stage="finish"` en `release-finish`: `stage="start"` + `Gate 6` firmado + `CHANGELOG.md` actualizado), abortando con código `1` antes de crear ramas o abrir PRs ante cualquier incumplimiento, respetando `RN-SDD-BRANCH-SYNC` y manteniendo `scripts/sdd_git.py` en `<= 500` líneas.

## 3. Criterios de Aceptación (BDD / Given-When-Then)
1. **Escenario `CA-1401` (Preparación sin autoaprobación y protección ante sobrescritura):**
   - **Dado** un repositorio válido con `FWK-013` / `FEAT-001` en estado `Done` y sin `specs/releases/REL-v1.2.0.md`
   - **Cuando** se ejecuta `sdd release prepare --version 1.2.0 --date 2026-11-17`
   - **Entonces** crea `specs/releases/REL-v1.2.0.md` con `[ ] **Gate 6 Approved (Human Sign-off):**` sin marcar (`[ ]`), actualiza `CHANGELOG.md` con `## [v1.2.0] - 2026-11-17`, retorna código `0`, y una segunda ejecución sin `--force` falla con código `1` sin sobreescribir el expediente.
2. **Escenario `CA-1402` (`CHANGELOG.md` determinista, idempotente y sin ruido):**
   - **Dado** un repositorio Git con tag `v1.1.0`, commits posteriores que referencian `FEAT-001` (registrada `Done` en `specs/BACKLOG.md` y con título en `01-spec.md`) junto a commits de ruido `chore: format` y un `CHANGELOG.md` previo con `## [v1.1.0] - 2026-10-01`
   - **Cuando** se ejecuta dos veces consecutivas `sdd release changelog --version 1.2.0 --date 2026-11-17`
   - **Entonces** el resultado en disco tras ambas ejecuciones es byte a byte idéntico, incluye `FEAT-001` bajo `### Features`, omite el ruido `chore: format` y conserva intacta la sección `## [v1.1.0] - 2026-10-01`.
3. **Escenario `CA-1403` (`verify` *fail-closed* ante spoofing de `Gate 6`, work items abiertos o ausencia de `CHANGELOG.md`):**
   - **Dado** un expediente `specs/releases/REL-v1.2.0.md` donde `[x] Gate 6 Approved` aparece únicamente dentro de un comentario HTML `<!-- ... -->` o bloque vallado ```` ``` ````, o bien existe un work item en `In Progress` / falta `v1.2.0` en `CHANGELOG.md`
   - **Cuando** se ejecuta `sdd release verify --version 1.2.0 --stage finish --format json`
   - **Entonces** retorna código `1` con `overall_status: "FAIL"` detallando el check fallido sin permitir falsos positivos.
4. **Escenario `CA-1404` (Preflight integrado en `sdd_git.py` `release-start` y `release-finish`):**
   - **Dado** un repositorio sin `Gate 6` firmado o con `active_work_item.json` activo distinto de `IDLE`
   - **Cuando** se ejecuta `sdd git release-start --version 1.2.0` o `sdd git release-finish --version 1.2.0`
   - **Entonces** el comando aborta en *fail-closed* con código `1` sin crear la rama `release/v1.2.0` ni invocar `GitProviderAdapter.create_pr`; y tras limpiar el work item activo, aprobar `Gate 6` y actualizar `CHANGELOG.md`, `release-finish` prepara la PR hacia `main` retornando código `0`.

<!-- sdd:gate-seal gate=1 sha256=6246607ffbe868985775984e384c3aa0c5111a8de9fc9061d310465f2807c212 -->
