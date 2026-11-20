# RFC-008: Adopción Brownfield Incremental (*Strangler Fig*), `sdd adopt` y Detección de *Spec Drift* (`v1.3.0`)

- **ID:** `RFC-008`
- **Versión objetivo:** `v1.3.0`
- **Estado:** `Aceptado` *(Autorización explícita PO: `2026-11-17T13:29:20+01:00` — "OK Continua")*
- **Rama base:** `develop`
- **Antecedentes:** [`RFC-006`](RFC-006-coherence-and-catalog-alignment.md), [`RFC-007`](RFC-007-release-ops-ci-agnostic.md), [`ADR-010`](../../../docs/knowledge/ADRS.md), [`ADR-011`](../../../docs/knowledge/ADRS.md), [`ADR-012`](../../../docs/knowledge/ADRS.md)

## 1. Motivación y Análisis Crítico

La hoja de ruta definida en `RFC-006` / `ADR-010` fija `v1.3.0` como el hito de **Brownfield & Spec Drift**. Tras completar `v1.2.0` (`Gate 6` y motor CI-agnóstico), el análisis del repositorio detecta cuatro carencias estructurales que impiden adoptar proyectos con código preexistente de forma segura, incremental y sin desperdicio de tokens:

1. **Ausencia de onboarding determinista para repositorios existentes (`sdd adopt`):**
   - `sdd-bootstrap` (`SKILL.md`) asume un repositorio *greenfield* sin código previo, y `scripts/sdd_sync.py` únicamente sincroniza rutas del framework sin inspeccionar el proyecto anfitrión.
   - Falta un motor offline en stdlib (`scripts/sdd_brownfield.py`) que detecte manifiestos (`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `pom.xml`, `*.csproj`, etc.), herramientas de test/lint/build, configuraciones CI y raíces de código para proponer `packs`, `yaml sdd:verification-commands` y `yaml sdd:ownership-map` en modo **`--dry-run` por defecto** y **`--apply` explícito no destructivo**, generando un borrador de `specs/STACK.md` estrictamente sin aprobar (`[ ] Gate S0 Approved`, `stack_approved: false`) y sin sobrescribir ficheros existentes.
2. **Desconexión operativa de `@spec-miner` y `sdd_repo_map.py`:**
   - `.sdd/catalog/specialists-optin/spec-miner.md` ya emite especificaciones nativas SDD (`specs/features/FEAT-XXX-<slug>/01-spec.md`, `SRC-###`, `AMB-###`, EARS y `domains/<slug>/`), pero no existe un workflow específico en `.agents/workflows/` que lo orqueste junto al mapa AST de `.agents/scripts/sdd_repo_map.py` para evitar lecturas masivas ciegas (`RN-SDD-SELECTIVE-CONTEXT`).
3. **Rigidez de raíces y tríadas frente a adopción incremental (*Strangler Fig*):**
   - `scripts/sdd_ownership.py` (`DEFAULT_CANDIDATE_ROOTS = ("src", "backend", "frontend", "DDBB")`) y `.agents/scripts/sdd_code_gate_guard.py` (`_PROTECTED_PREFIX_RE`) asumen convenciones *greenfield* y no contemplan raíces habituales en proyectos legacy (`app/`, `lib/`, `cmd/`, `internal/`, `packages/`, `services/`, `api/`, `web/`).
   - Además, `.agents/scripts/sdd_healthcheck.py` exige la tríada completa (`01-spec.md`, `02-tech-spec.md`, `03-tasks.md`) para cualquier `FEAT-XXX` fuera de `Draft`/`Gate 1`. Para adoptar código existente sin tareas artificiales, se requiere una **Baseline Retroactiva Ligera** (`origin: brownfield-mined`: `01-spec.md` + `02-tech-spec.md` *as-built*), validable tras firma humana explícita, junto con zonas *Strangler Fig* en `sdd:ownership-map` (`governed` vs `legacy-readonly`) que mantengan `RN-SDD-GATE2-CODE-LOCK` estrictamente *fail-closed* ante cualquier edición de código protegido.
4. **Falta de detector determinista de *Spec Drift* y cobertura (`sdd drift`):**
   - Hoy no existe una herramienta offline que cruce las citas `SRC-###` (`path::symbol` + `<sha>`) de `01-spec.md` y `docs/traceability/TRACEABILITY-MATRIX.md` frente al mapa de símbolos de `sdd_repo_map.py` y `git diff` / `git log` para detectar: (a) zonas/ficheros sin cobertura `FEAT-XXX`, (b) símbolos `SRC-###` desaparecidos o renombrados sin `CR-XXX`, y (c) modificaciones sobre ficheros de features `Done` / baseline sin `CR-XXX`, `BUG-XXX` o `HOTFIX-XXX` vinculados.

## 2. Decisiones de Diseño Acordadas

1. **Adopción no destructiva (`--dry-run` por defecto, `--apply` explícito):** `sdd adopt` nunca pisa código fuente, `README.md`, workflows CI ni configuraciones previas, y jamás marca `[x] Gate S0 Approved` ni `stack_approved: true`.
2. **Modelo *Strangler Fig* *fail-closed* por zonas:** `sdd:ownership-map` admite raíces personalizadas y clasificación de zonas (`governed` vs `legacy-readonly`), preservando intacto el bloqueo `RN-SDD-GATE2-CODE-LOCK` para toda modificación de código protegido.
3. **Baseline Retroactiva Ligera (`origin: brownfield-mined`):** Las features minadas desde código existente requieren `01-spec.md` (`SRC-###`, EARS, `Given-When-Then`, `AMB-###`) + `02-tech-spec.md` *as-built*, eximiendo `03-tasks.md` únicamente cuando el marcador estructurado acredite origen *brownfield* y cuente con aprobación humana explícita.

## 3. Descomposición en Work Items

| ID | Título | Prioridad | Depende de | Alcance |
| :--- | :--- | :---: | :---: | :--- |
| **`FWK-015`** | Motor de Adopción Brownfield (`sdd adopt`), Descubrimiento Determinista y Workflow `@spec-miner` | P0 | — | `scripts/sdd_brownfield.py`, subcomando `adopt` en `scripts/sdd_cli.py`, detección offline de stack/comandos/raíces, borrador no destructivo de `specs/STACK.md` + `docs/knowledge/BROWNFIELD_INVENTORY.md`, `.agents/workflows/brownfield-adopt.md` y `tests/test_sdd_brownfield.py`. |
| **`FWK-016`** | Detector de *Spec Drift* (`sdd drift`), Zonas *Strangler Fig* y Baseline Retroactiva Ligera | P1 | `FWK-015` | `scripts/sdd_drift.py`, subcomando `drift` en `scripts/sdd_cli.py`, soporte de raíces/zonas *Strangler Fig* en `scripts/sdd_ownership.py` y `.agents/scripts/sdd_code_gate_guard.py`, soporte `brownfield-mined` en `.agents/scripts/sdd_healthcheck.py` y `scripts/sdd_gate_seal.py`, integración en `scripts/sdd_ci.py` y `tests/test_sdd_drift.py`. |

## 4. Restricciones Transversales

- **Stdlib-only & Modularidad:** Python `>= 3.12` sin dependencias externas (`pyproject.toml`), `<= 500` líneas por cada `.py` bajo `scripts/`, `.agents/scripts/` y `tests/`.
- **Seguridad *Fail-Closed* (`shell=False`):** prohibido `shell=True`; validación estricta contra symlinks/junctions y *path traversal* (`resolve_repo_relative_path`, `is_link_or_junction`).
- **Autoridad Humana (`RN-SDD-HUMAN-GATE-OWNERSHIP`):** ninguna herramienta puede autoaprobar `Gate S0` ni `Gate 1..3`.
- **Presupuesto de Contexto (`< 25k`):** `@spec-miner` continúa en `.sdd/catalog/specialists-optin/` y los artefactos bajo `.agents/` deben mantener el presupuesto activo `< 25k` tokens.
