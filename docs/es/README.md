<p align="right">
  <a href="../en/README.md">🇬🇧 English (EN-GB)</a> | <strong>🇪🇸 Español (ES-ES)</strong>
</p>

# Documentación Funcional Viva (`docs/es/`)

Bienvenido a la documentación funcional viva del repositorio **`sdd-agentic-starter`**, mantenida bajo el estándar **Zero Document Debt (0DD)** en equivalencia **1:1** entre español (ES-ES) e inglés británico (EN-GB).

---

## Baseline Activa (`v1.5.0`)

- **Work Items de Framework Completados / Verificados:**
  - `FWK-001` — *Materialización y Activación Fiables de Packs* (`RFC-001` v2, estado `Verified` / `Done`).
  - `FWK-002` — *Pack `capability-ui-design` (UI UX Pro Max)* (`RFC-001` v2, estado `Verified` / `Done`).
  - `FWK-003` — *Quality Gates Visuales Condicionales y Anti-Deriva de Tokens* (`RFC-001` v2, estado `Verified` / `Done`).
  - `FWK-004` — *Unificación de Terminología de Gates, Estados y Ejecución DAG* (`RFC-002`, estado `Verified` / `Done`).
  - `FWK-005`..`FWK-009` — *Endurecimiento Integral Post-Auditoría: Seguridad Fail-Closed P0, Compilador `sdd:ownership-map` & Motor DAG, Slimming `< 25k` Tokens + `/bug-fast-track` + `domains/`, Concurrencia Multi-Worktree y Sync Transaccional / Modularidad `<= 500L`* (`RFC-003`, estado `Verified` / `Done`).
  - `FWK-010` — *Endurecimiento Nivel L5 (10/10): Sello Criptográfico SHA-256 de Gates (`sdd_gate_seal.py` / `approve-gate` / `verify-gates`), Fronteras Arquitectónicas Políglotas, Detección de Colisiones `Write-Set` en Olas Paralelas DAG y Auditoría CI (`>= 120` tests)* (`RFC-004`, estado `Verified` / `Done`).
  - `FWK-011`..`FWK-012` — *Portabilidad POSIX / Determinismo CI y Alineación de Coherencia `v1.1.1`: `sdd work-item`, `HOTFIX`/`SPIKE`, `spec-miner` SDD y `release-finish` PR-First* (`RFC-005` & `RFC-006`, estado `Verified` / `Done`).
  - `FWK-013` — *Motor CI-Agnóstico Portable (`sdd ci-verify`), Detección `framework` vs `project`, Ejecución Segura `STACK.md §2.5` y Plantillas Multi-CI* (`RFC-007`, estado `Verified` / `Done`).
  - `FWK-014` — *`Gate 6` (`REL-vX.Y.Z`), Motor de Release Readiness (`./sdd release prepare|changelog|verify` en `scripts/sdd_release.py`), `CHANGELOG.md` Determinista, Preflight Fail-Closed en `sdd_git.py`, Plantilla `08-release-readiness.template.md` y Workflow `gate6-release.md`* (`RFC-007`, estado `Verified` / `Done`).
  - `FWK-015` — *Motor de Adopción Brownfield (`./sdd adopt --dry-run|--apply` en `scripts/sdd_brownfield.py`), Descubrimiento Determinista Offline, Sanitización Fail-Closed y Workflow `/brownfield-adopt` (`@spec-miner`)* (`RFC-008`, estado `Verified` / `Done`).
  - `FWK-016` — *Detector Determinista Offline de Spec Drift (`./sdd drift` en `scripts/sdd_drift.py`), Zonas Strangler Fig (`governance: governed | legacy-readonly` en `sdd_ownership.py` y `sdd_code_gate_guard.py`), Baseline Retroactiva Ligera (`Origin: brownfield-mined` con Gates 1 y 2 obligatorios en `sdd_healthcheck.py` y `sdd_gate_seal.py`) e Integración CI (`check_spec_drift` en `sdd_ci.py`)* (`RFC-008`, estado `Verified` / `Done`, `160/160` tests offline en `15` suites).
  - `FWK-017` — *Motor Determinista Offline de Portfolio, Épicas (`EPIC-XXX`), Priorización MoSCoW/RICE y Grafo DAG entre Features (`./sdd portfolio init|status|graph|validate` en `scripts/sdd_portfolio.py`, `476L`), Plantilla `specs/templates/09-epic-roadmap.template.md` (`38L`, `0` bytes en `.agents/`), Normativa `specs/SDD_FRAMEWORK.md §3` e Integración CI (`check_portfolio` en `sdd_ci.py`)* (`RFC-009`, estado `Verified` / `Done`, `174/174` tests offline en `16` suites).
  - `FWK-020` — *Gobernanza Core `L4/L5` (`sdd-security-audit` STRIDE/OWASP ASVS + `references/` bajo demanda en 4 skills Core = `15` skills Core activas), Saneamiento ECC (`R0`–`R4`) y Expansión Enterprise Opt-In (`25` packs / `86` skills de catálogo = `101` skills totales; `capability-event-driven`, `capability-api-governance`, `capability-iac-cloud`, `framework-nextjs`, `framework-nestjs`, `capability-data-engineering`, ampliaciones en `capability-devops` y `capability-database`, poda `api-only`/`spa-only` y preservación fail-closed en `sdd_catalog_import.py`)* (`RFC-010`, estado `Verified` / `Done`, `182/182` tests offline en `17` módulos, `OVER_500=0`).
- **Aplicación de Proyecto:** Pendiente de definición tecnológica y firma humana en **Gate S0** (`specs/STACK.md`, con soporte legacy para `Gate 00`). Hasta entonces, esta documentación cubre la funcionalidad operativa del motor de materialización, activación de packs, vendorización UI/UX offline, sincronización del catálogo, gobernanza agéntica unificada, *Release Readiness* en `Gate 6`, herramientas brownfield / *Spec Drift* y gestión de Portfolio/Épicas del starter.

---

## Mapa de Lectura

| Bloque / Recurso | Contenido | Enlace |
| :--- | :--- | :--- |
| **Índice Maestro (`00-governance`)** | Punto de entrada normativo, estado de artefactos y alcance documental vigente. | [DOCUMENTATION-INDEX.md](./00-governance/DOCUMENTATION-INDEX.md) |
| **Módulo `MOD-001` (`02-functional`)** | Guía funcional y operativa de materialización de packs (`sdd:stack-config`, Gate S0 / Gate 00, carga perezosa, limpieza *fail-closed* e importación de catálogo). | [pack-materialization.md](./02-functional/modules/MOD-001/pack-materialization.md) |
| **Módulo `MOD-002` (`02-functional`)** | Guía funcional del pack `capability-ui-design` (vendorización offline `ui-ux-pro-max@2.15.0` con `VENDOR.lock.json`, poda `uiux` en `sdd-bootstrap`, flujo Gate 2 con `@ui-ux-designer` + `@a11y-architect`, ciclo semver de `docs/design-system/`, validador `sdd_tokens_validator.py` y quality gates visuales bi-nivel en Gate 4). | [capability-ui-design.md](./02-functional/modules/MOD-002/capability-ui-design.md) |
| **Módulo `MOD-003` (`02-functional`)** | Unificación de terminología de Gates (`Gate S0`, `Gate 0..6`), estados (`Candidate`..`Done`), bloques DAG (`Block`), fases de sesión, soporte dual-accept fail-closed, motor CI-agnóstico (`sdd ci-verify`), `Gate 6` (`sdd release`), brownfield (`sdd adopt`), *Spec Drift* (`sdd drift`), Portfolio/Épicas (`sdd portfolio`) y endurecimiento (`FWK-004`..`FWK-020`). | [gate-terminology-unification.md](./02-functional/modules/MOD-003/gate-terminology-unification.md) |
| **Base de Conocimiento (`docs/knowledge/`)** | Decisiones de arquitectura (`ADR-001`..`ADR-015`), topología, modelos de datos y catálogo CLI/APIs (`./sdd release prepare|changelog|verify`, `./sdd adopt --dry-run|--apply`, `./sdd drift`, `./sdd portfolio init|status|graph|validate`). | [ADRS.md](../knowledge/ADRS.md) · [SYSTEM_TOPOLOGY.md](../knowledge/SYSTEM_TOPOLOGY.md) · [DATA_MODELS.md](../knowledge/DATA_MODELS.md) · [API_CATALOG.md](../knowledge/API_CATALOG.md) |
| **Matriz de Trazabilidad (0DD)** | Trazabilidad bidireccional de `FWK-001` a `FWK-020` desde requisitos EARS, reglas de negocio y NFRs hasta código, pruebas offline y documentación. | [TRACEABILITY-MATRIX.md](../traceability/TRACEABILITY-MATRIX.md) |

## Ciclo Operativo `Gate 6` (`REL-vX.Y.Z`)

1. **Preflight e inicio de rama:** `./sdd git release-start --version X.Y.Z` valida SemVer, ausencia del tag, cero work items abiertos y `ci-verify` en verde antes de crear `release/vX.Y.Z`.
2. **Expediente y `CHANGELOG.md` determinista:** `./sdd release prepare --version X.Y.Z` instancia `specs/releases/REL-vX.Y.Z.md` desde `specs/templates/08-release-readiness.template.md` (manteniendo `[ ] Gate 6 Approved` sin marcar) y actualiza `CHANGELOG.md` de forma idempotente (también invocable de forma aislada vía `./sdd release changelog --version X.Y.Z`).
3. **Firma humana y cierre PR-First:** Siguiendo `.agents/workflows/gate6-release.md`, tras la firma humana en `REL-vX.Y.Z.md`, `./sdd release verify --version X.Y.Z --stage finish` y `./sdd git release-finish --version X.Y.Z` validan en modo *fail-closed* y abren la PR hacia `main` (`RN-SDD-BRANCH-SYNC`).

## Ciclo de Adopción Brownfield (`sdd adopt` + `@spec-miner`)

1. **Descubrimiento solo lectura (`--dry-run`) y scaffolding no destructivo:** `./sdd adopt --format text` inspecciona de forma determinista y offline manifiestos, ecosistemas, zonas candidatas y comandos DoD seguros (filtrando metacaracteres inseguros). Tras revisar el plan, `./sdd adopt --apply` (opcionalmente `--with-repo-map`) crea únicamente los borradores ausentes: `specs/STACK.md` (`[ ] Gate S0 Approved`, `stack_approved: false`), `docs/knowledge/BROWNFIELD_INVENTORY.md` y `specs/BACKLOG.md`, sin sobrescribir artefactos existentes.
2. **Aprobación humana de `Gate S0` y materialización:** Ajustar `specs/STACK.md`, recabar firma humana explícita en `Gate S0` (`RN-SDD-HUMAN-GATE-OWNERSHIP`) y ejecutar `./sdd generate --materialize`.
3. **Extracción AST y minado inverso con `@spec-miner`:** Siguiendo `.agents/workflows/brownfield-adopt.md` (`/brownfield-adopt`), elegir un *bounded context* de `docs/knowledge/BROWNFIELD_INVENTORY.md`, extraer su mapa simbólico con `./sdd repo-map <ruta-contexto>` e invocar a `@spec-miner` (`.sdd/catalog/specialists-optin/spec-miner.md`) para redactar `specs/features/FEAT-XXX-<slug>/01-spec.md` (`SRC-###`, `AMB-###`, requisitos EARS, `Given-When-Then`) y `domains/<slug>/{overview,decisions}.md` sin editar `src/` ni autoaprobar `Gate 1`.
4. **Migración incremental *Strangler Fig*, baseline retroactiva ligera y auditoría *Spec Drift*:** En `specs/STACK.md` (`yaml sdd:ownership-map`), las zonas pueden declarar `governance: legacy-readonly` (bloqueadas a edición directa por `.agents/scripts/sdd_code_gate_guard.py`) frente a `governance: governed` (por defecto). Las features minadas del sistema existente pueden usar `Origin: brownfield-mined` en `01-spec.md` junto a `02-tech-spec.md` *as-built* —eximiendo `03-tasks.md` únicamente tras las firmas humanas `[x] Gate 1 Approved` y `[x] Gate 2 Approved`— y verificarse continuamente con `./sdd drift` (`--base-ref`, `--strict`, `--format text|json`) e integración en `./sdd ci-verify`.

## Ciclo de Portfolio, Épicas (`EPIC-XXX`) y Grafo de Features (`sdd portfolio`)

1. **Creación atómica de Épicas (`init`):** `./sdd portfolio init --id EPIC-XXX --title "<título>"` instancia `specs/epics/EPIC-XXX-<slug>.md` desde la plantilla `specs/templates/09-epic-roadmap.template.md` (`Draft`, sin marcas `[x]` de aprobación), rechazando sobrescrituras accidentales salvo `--force`, IDs inválidos o rutas con symlinks/junctions.
2. **Priorización *MoSCoW*/*RICE* y *Rollup* de progreso (`status`):** `./sdd portfolio status [--epic EPIC-XXX] [--format text|json]` fusiona `specs/epics/EPIC-*.md` (bloque `yaml sdd:epic`) con el estado real de `specs/BACKLOG.md` y sus columnas opcionales (`Épica`, `Prioridad`, `Depende de`, `RICE`), validando *MoSCoW* (`Must`, `Should`, `Could`, `Wont`), calculando `RICE = (reach * impact * confidence) / effort` (`effort > 0`) y reportando `total_features`, `done_features`, `in_progress_features`, `blocked_features`, `progress_pct` y `ready_features`.
3. **Grafo DAG, ruta crítica y validación *fail-closed* (`graph` / `validate`):** `./sdd portfolio graph` y `./sdd portfolio validate` construyen el DAG determinista de dependencias entre `FEAT-XXX`, calculan las olas topológicas (Kahn) y la ruta crítica pendiente (`critical_path`), bloquean en modo *fail-closed* ciclos (`CYCLE_DETECTED`) o dependencias inexistentes (`UNKNOWN_DEPENDENCY`), advierten sobre inversiones de prioridad (`PRIORITY_INVERSION`, `Must` -> `Could`/`Wont`), y se ejecutan en `./sdd ci-verify` (`check_portfolio`, retornando `SKIPPED_NO_APPLICABLE` cuando el repo no declara Épicas ni dependencias).
