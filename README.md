<div align="center">

# 🛡️ Spec-Driven Development (SDD) — Agentic Engineering Framework

**Governance-First, Multi-Agent, Stack-Agnostic Software Delivery Architecture**

[![Governance](https://img.shields.io/badge/Governance-Gate_S0_to_Gate_5-blue)](#sdd-lifecycle-en)
[![Base Agents](https://img.shields.io/badge/Base_Agents-9_Active_+_19_Opt--In-purple)](#agent-squad-en)
[![Stack Packs](https://img.shields.io/badge/Stack_Packs-19_Packs_(30_Specialists)-emerald)](#stack-packs-en)
[![Skills & Workflows](https://img.shields.io/badge/Skills_%26_Workflows-13_Base_Skills_%7C_13_Workflows-orange)](#skills-workflows-en)
[![Security](https://img.shields.io/badge/Hooks-Fail--Closed_PreToolUse-red)](#rfc003-hardening-en)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](#credits-en)

[**🇬🇧 English (EN-GB)**](#en-gb) &nbsp;|&nbsp; [**🇪🇸 Español (ES-ES)**](#es-es)

</div>

---

<a id="en-gb"></a>

## 🇬🇧 English Documentation (EN-GB)

### Table of Contents
- [1. Overview & Philosophy](#overview-en)
- [2. The Golden SDD Lifecycle (Gate S0 -> Gate 5)](#sdd-lifecycle-en)
- [3. RFC-003 Hardening, Ownership & Multi-Worktree Runtime](#rfc003-hardening-en)
- [4. Multi-Agent Squad & Opt-In Catalog](#agent-squad-en)
- [5. Stack Packs & Layer Archetypes](#stack-packs-en)
- [6. Base Skills, Workflows & Fast-Track Bugs](#skills-workflows-en)
- [7. On-Demand Domain Context (`domains/`)](#domains-en)
- [8. Quick Start & CLI Reference](#quickstart-en)
- [9. Repository Architecture](#repo-arch-en)
- [10. Credits & Attribution](#credits-en)

---

<a id="overview-en"></a>

### 1. Overview & Philosophy

**SDD Agentic Starter** transforms AI-assisted development from ad-hoc prompting into a deterministic, auditable, **Spec-Driven Development (SDD)** pipeline. Production code under `src/` cannot be edited until the technology stack (`Gate S0`), functional requirements (`Gate 1`), technical contracts (`Gate 2` + optional visual `Sub-Gate 2V`), and atomic DAG task plan (`Gate 3`) receive explicit human approval.

Key principles:
1. **Zero Code Without Approved Specs (`RN-SDD-GATE-S0-STACK-LOCK` & `RN-SDD-GATE2-CODE-LOCK`):** Production edits fail closed when `specs/STACK.md` or the active work item's `Gate 1/2/3` sign-offs are missing.
2. **Immutable Done History (`RN-SDD-IMMUTABLE-DONE`):** Once a feature reaches `Done`, `specs/features/FEAT-XXX-*/` becomes read-only; evolutions require a `1:1` Change Request (`specs/changes/CR-XXX-*/`).
3. **Zero Documentation Debt (`RN-SDD-0DD`):** No work item reaches `Done` until `@documentator` synchronizes `docs/es/`, `docs/en/`, `docs/knowledge/`, `domains/`, and `docs/traceability/TRACEABILITY-MATRIX.md`.
4. **Compact Starter Context:** Only **9 active base agents**, **8 governance rules**, and **13 core skills** load by default; stack packs and `domains/` cards materialize strictly on demand.

---

<a id="sdd-lifecycle-en"></a>

### 2. The Golden SDD Lifecycle (`Gate S0` -> `Gate 5`)

Canonical backlog states across `specs/BACKLOG.md`: **`Candidate` -> `Backlog` -> `In Progress` -> `In Review` -> `Done`** (plus **`Blocked`**).
Canonical document states: **`Draft` -> `In Review` -> `Approved` -> `Done`**.

```mermaid
flowchart LR
    GS0["Gate S0: Stack Lock\n(specs/STACK.md)"] --> G0["Gate 0: Backlog Triage\n(Candidate / Backlog)"]
    G0 --> G1["Gate 1: Functional Spec\n(EARS / Bug Report)"]
    G1 --> G2["Gate 2: Tech Spec\n(+ Sub-Gate 2V UI)"]
    G2 --> G3["Gate 3: Atomic DAG\n(03-tasks.md)"]
    G3 --> G4["Gate 4: Code Execution\n(Worktrees & Guards)"]
    G4 --> G5["Gate 5: 0DD Closure\n(Docs, Domains & Push)"]
```

| Gate | Artefact / Action | Human Sign-off Marker | Blocking Rule |
| :--- | :--- | :--- | :--- |
| **Gate S0** | `specs/STACK.md` (`sdd-bootstrap`) | `[x] Gate S0 Approved` *(legacy alias: `Gate 00`)* | `RN-SDD-GATE-S0-STACK-LOCK` |
| **Gate 0** | Register `FEAT-XXX`, `CR-XXX`, or `BUG-XXX` in `specs/BACKLOG.md` | Backlog prioritization | Single SSOT for IDs & status |
| **Gate 1** | `01-spec.md` (EARS + Given-When-Then) or `01-bug-report.md` | `[x] Gate 1 Approved` | Fail-closed ambiguity check |
| **Gate 2** | `02-tech-spec.md` or `02-fix-spec.md` (`+ Sub-Gate 2V` if UI) | `[x] Gate 2 Approved` *(+ `Gate 2 Visual Sign-off`)* | Typed contracts before code |
| **Gate 3** | `03-tasks.md` with DAG dependencies, `ALLOWED_FILES` & DoD commands | `[x] Gate 3 Approved` | `RN-SDD-GATE2-CODE-LOCK` |
| **Gate 4** | Isolated implementation (`opsx-delegate` / `opsx-pickup`) + TDD & audits | Gate 4 verification passes | `sdd_code_gate_guard.py` |
| **Gate 5** | Bilingual docs, `docs/knowledge/`, `domains/`, traceability & `git push` | `Done` sign-off | `RN-SDD-0DD` & branch sync |

---

<a id="rfc003-hardening-en"></a>

### 3. RFC-003 Hardening, Ownership & Multi-Worktree Runtime

The framework enforces engineering discipline through verifiable Python tooling under `.agents/scripts/`:

- **Fail-Closed `PreToolUse` & Git Hooks:**
  - `sdd_code_gate_guard.py` & `sdd_gate_seal.py` (`sdd approve-gate`, `sdd verify-gates`): Blocks writes to `src/` unless `Gate S0` is approved, `specs/BACKLOG.md` tracks an active `In Progress` work item, and `01..03` documents carry valid `[x] Gate 1/2/3 Approved` markers and intact SHA-256 cryptographic gate seals (`gate_seals`).
  - `sdd_immutable_feature_guard.py`: Enforces `RN-SDD-IMMUTABLE-DONE` against edits to `Done` feature specs.
  - `sdd_trim_exec.py`: Runs test/lint subcommands with `shell=False`, allowlisted executables, and path containment.
  - `sdd_healthcheck.py`: Validates directory structure, spec triads (`features`, `changes`, `bugs`), prompt-injection hygiene, and catalog integrity.
- **Declarative `sdd:ownership-map` & Transactional Squad Compiler:** `sdd_agent_generator.py` and `sdd_pack_registry.py` materialize stack specialists and update `.agents/squad.lock.json` transactionally with SHA-256 verification and automatic rollback on error.
- **Executable DAG Scheduler (`sdd_dag.py`):** Parses `03-tasks.md`, detects dependency cycles and parallel-wave `Write-Set` overlaps (`DagWriteSetCollisionError`, `--auto-split`), validates `ALLOWED_FILES`, and computes parallel execution batches for `/opsx-delegate`.
- **Multi-Worktree Isolation (`sdd_git.py` & `sdd_dev.py`):** Allocates isolated worktrees and deterministic per-worktree dev ports for parallel task execution without cross-contamination.
- **Modularity, Polyglot Boundaries & AST Context:** `verify_architecture_boundaries.py` enforces polyglot `forbid_imports` across Python, TS/JS, C#, Go, Rust, Java, and Kotlin, plus **`<= 800` lines hard ceiling / `<= 500` warning** in `src/`, and **`<= 500` lines** across framework scripts and tests. `sdd_repo_map.py` builds compressed structural maps across **20+ languages**.

---

<a id="agent-squad-en"></a>

### 4. Multi-Agent Squad & Opt-In Catalog

The starter keeps **9 active base agents** loaded by default (`1` default universal reviewer `@security-reviewer` from `.sdd/catalog/specialists/`) and stores **19 opt-in universal specialists** in `.sdd/catalog/specialists-optin/` (`20` universal specialists total across the catalog, plus `30` stack-specific specialists in `.sdd/catalog/packs/`).

| Group | Agents | Mode |
| :--- | :--- | :--- |
| **Core Governance (6)** | `@orchestrator`, `@functional-analyst`, `@architect`, `@qa-tester`, `@documentator`, `@devops` | Always active in `.agents/agents/` |
| **Compact Builders (2)** | `@back-engineer`, `@front-engineer` | Starter `compact` templates compiled/replaced from `specs/STACK.md` (`sdd:ownership-map`) |
| **Default Security Reviewer (1)** | `@security-reviewer` | Active universal reviewer from `.sdd/catalog/specialists/` |
| **Opt-In Universal Specialists (19)** | `build-error-resolver`, `code-architect`, `code-explorer`, `code-simplifier`, `comment-analyzer`, `conversation-analyzer`, `docs-lookup`, `e2e-runner`, `gan-evaluator`, `gan-generator`, `gan-planner`, `opensource-sanitizer`, `performance-optimizer`, `pr-test-analyzer`, `refactor-cleaner`, `silent-failure-hunter`, `spec-miner`, `tdd-guide`, `type-design-analyzer` | Stored in `.sdd/catalog/specialists-optin/`; activated on demand |

---

<a id="stack-packs-en"></a>

### 5. Stack Packs & Layer Archetypes

`specs/STACK.md` declares active technologies from **19 Stack Packs** (`.sdd/catalog/packs/`), which materialize **30 dynamic specialists** and **70 specialized pack skills (`SKILL.md`)** along with **12 unique canonical layer archetypes** in `.sdd/catalog/archetypes/` (`cli-tool`, `front-logic`, `front-test`, `front-ui`, `layer-api`, `layer-db`, `layer-domain`, `layer-infra`, `layer-test`, `mobile-app`, `tier-backend`, `tier-frontend`).

- **Languages (`lang-*`):** Python, TypeScript, Go, Rust, Java, C#.
- **Frameworks (`framework-*`):** FastAPI, Django, Next.js, React, Spring Boot, Angular, Vue, NestJS, Astro, Flutter, React Native.
- **Capabilities (`capability-*`):** UI Design (Stitch MCP & Sub-Gate 2V), DevOps CI/CD & Containers.

---

<a id="skills-workflows-en"></a>

### 6. Base Skills, Workflows & Fast-Track Bugs

#### 13 Base Starter Skills (`.agents/skills/`)
1. `sdd-bootstrap` — Guided Gate S0 stack & ownership configuration (`specs/STACK.md`).
2. `sdd-change-gate` — Enforces `RN-SDD-IMMUTABLE-DONE` and 1:1 `CR-XXX` creation.
3. `pipeline-run` — Autonomous DAG lifecycle execution (`Gate 0` -> `Gate 5`).
4. `opsx-delegate` — Dispatches isolated task tickets with `ALLOWED_FILES` to `.agent-inbox/`.
5. `opsx-pickup` — Picks up inbox tickets, checks DoR, and verifies DoD.
6. `search-first` — Consults `docs/knowledge/` and `domains/` before authoring code.
7. `strategic-compact` — Context hygiene and `/continue` handoff at gate boundaries.
8. `sdd-silent-failure-audit` — Hunts swallowed exceptions and silent fallback defaults.
9. `sdd-spec-compliance-audit` — Verifies 1:1 contract parity against `02-tech-spec.md`.
10. `sdd-test-quality-audit` — Audits tests for assertion quality and tautological mocks.
11. `santa-method` — Independent dual-reviewer convergence protocol.
12. `gan-style-harness` — Generator-evaluator harness for high-complexity deliverables.
13. `continuous-learning-v2` — Instincts capture and reusable workflow evolution.

#### 13 Slash Command Workflows (`.agents/workflows/`)
`/pipeline-run` · `/opsx-delegate` · `/opsx-pickup` · `/bug-fast-track` · `/build-fix` · `/checkpoint` · `/continue` · `/gate5` · `/harness-audit` · `/santa-loop` · `/gan-build` · `/learn` · `/evolve`

#### Fast-Track Bug Workflow (`/bug-fast-track`)
Scoped defects and regressions use `specs/bugs/BUG-XXX-<slug>/` generated from `specs/templates/05-bug-fast-track.template.md` (`01-bug-report.md`, `02-fix-spec.md`, `03-tasks.md`). It trims multi-domain feature ceremony while strictly preserving:
- `Gate S0` stack lock and `specs/BACKLOG.md` as the sole status SSOT (`Historial de Bugs (BUG)`).
- Full triad completeness verified by `sdd_healthcheck.py`.
- Explicit `[x] Gate 1/2/3 Approved` human markers verified by `sdd_code_gate_guard.py`.
- Test-First (`Red -> Fix -> Green`) verification and automatic escalation to `FEAT-XXX` or `CR-XXX` if contracts change.

---

<a id="domains-en"></a>

### 7. On-Demand Domain Context (`domains/`)

To prevent bloating always-on `.agents/rules/` (`8` rules total), domain knowledge lives in **`domains/<domain-slug>/`** using two concise templates (`domains/_template/overview.md` and `domains/_template/decisions.md`):
- **Loaded on demand** during `Gate 1/2` and `/bug-fast-track` strictly for the `Affected Domains`.
- **Synchronized at Gate 5** by `@documentator` without duplicating `docs/knowledge/DATA_MODELS.md` or `API_CATALOG.md`.

---

<a id="quickstart-en"></a>

### 8. Quick Start & CLI Reference

```bash
# 1. Verify framework integrity, spec triads & hooks
uv run python .agents/scripts/sdd_healthcheck.py

# 2. Validate active DAG dependencies & architecture boundaries
uv run python .agents/scripts/verify_architecture_boundaries.py

# 3. Inspect CLI subcommands (materialize, verify, work-item, worktree)
uv run python .agents/scripts/sdd_cli.py --help

# 4. Run the framework self-test suite
uv run python -m unittest discover -s tests -v
```

Inside your AI coding session:
1. Run **`sdd-bootstrap`** to complete `specs/STACK.md` and sign off **`[x] Gate S0 Approved`**.
2. Use **`/pipeline-run`** for features/changes (`FEAT-XXX` / `CR-XXX`) or **`/bug-fast-track`** for scoped defects (`BUG-XXX`).
3. Keep sessions bounded with **`/checkpoint`**, **`/continue`**, and **`/gate5`**.

---

<a id="repo-arch-en"></a>

### 9. Repository Architecture

```text
├── AGENTS.md                       # Global mandatory SDD governance directives
├── .agents/
│   ├── agents/                     # 9 active base agents (compiled via STACK.md)
│   ├── rules/                      # 8 always-on governance rules (00..07)
│   ├── skills/                     # 13 base starter skills (SKILL.md)
│   ├── workflows/                  # 13 slash command workflows (incl. /bug-fast-track)
│   ├── scripts/                    # CLI, guards, DAG scheduler, git worktrees, healthcheck
│   ├── hooks.json                  # PreToolUse & git hook configuration
│   └── squad.lock.json             # SHA-256 lockfile for materialized packs/specialists
├── .sdd/catalog/                   # Opt-in catalog: 19 universal specialists, 19 packs, 12 canonical archetypes
├── domains/                        # On-demand bounded-context docs & _template/
├── specs/
│   ├── STACK.md                    # Gate S0 technology & ownership contract
│   ├── BACKLOG.md                  # Sole SSOT for FEAT, CR, and BUG state
│   ├── templates/                  # Canonical SDD templates (00..05 incl. 05-bug-fast-track)
│   ├── features/                   # FEAT-XXX-* triads (immutable once Done)
│   ├── changes/                    # CR-XXX-* triads (1:1 per affected Done feature)
│   └── bugs/                       # BUG-XXX-* fast-track triads
├── docs/                           # Bilingual guides (es/, en/), knowledge/, traceability/
└── tests/                          # Framework regression, security & materialization test suite
```

---

<a id="credits-en"></a>

### 10. Credits & Attribution

Released under the **MIT License**. Built with curated governance, verification, and workflow patterns credited in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

---

<a id="es-es"></a>

## 🇪🇸 Documentación en Español (ES-ES)

### Tabla de Contenidos
- [1. Visión General y Filosofía](#overview-es)
- [2. Ciclo de Vida SDD (`Gate S0` -> `Gate 5`)](#sdd-lifecycle-es)
- [3. Endurecimiento `RFC-003`, Ownership y Multi-Worktree](#rfc003-hardening-es)
- [4. Escuadrón Base y Catálogo Opt-In](#agent-squad-es)
- [5. Stack Packs y Arquetipos de Capa](#stack-packs-es)
- [6. Skills Base, Workflows y Bugs Fast-Track](#skills-workflows-es)
- [7. Contexto de Dominio Bajo Demanda (`domains/`)](#domains-es)
- [8. Inicio Rápido y Referencia CLI](#quickstart-es)
- [9. Arquitectura del Repositorio](#repo-arch-es)
- [10. Créditos y Atribuciones](#credits-es)

---

<a id="overview-es"></a>

### 1. Visión General y Filosofía

**SDD Agentic Starter** convierte el desarrollo asistido por IA en un flujo determinista y auditable de **Spec-Driven Development (SDD)**. El código en `src/` permanece bloqueado hasta que el stack (`Gate S0`), los requisitos funcionales (`Gate 1`), el diseño técnico (`Gate 2` y `Sub-Gate 2V` si hay UI) y el plan DAG atómico (`Gate 3`) cuentan con aprobación humana expresa.

Pilares clave:
1. **Cero Código sin Especificación Aprobada (`RN-SDD-GATE-S0-STACK-LOCK` y `RN-SDD-GATE2-CODE-LOCK`):** Los hooks bloquean ediciones en `src/` si falta `Gate S0` o las firmas `Gate 1/2/3` del work item activo.
2. **Inmutabilidad de Features Completadas (`RN-SDD-IMMUTABLE-DONE`):** Al pasar a `Done`, `specs/features/FEAT-XXX-*/` es de solo lectura; cualquier evolución exige un `CR-XXX` independiente (`1:1`).
3. **Deuda Cero de Documentación (`RN-SDD-0DD`):** Ningún work item cierra en `Done` sin que `@documentator` actualice `docs/es/`, `docs/en/`, `docs/knowledge/`, `domains/` y `docs/traceability/TRACEABILITY-MATRIX.md`.
4. **Contexto Base Compacto:** Por defecto solo se activan **9 agentes base**, **8 reglas de gobernanza** y **13 skills base**; los packs y fichas en `domains/` se cargan estrictamente bajo demanda.

---

<a id="sdd-lifecycle-es"></a>

### 2. Ciclo de Vida SDD (`Gate S0` -> `Gate 5`)

Estados canónicos en `specs/BACKLOG.md`: **`Candidate` -> `Backlog` -> `In Progress` -> `In Review` -> `Done`** (más **`Blocked`**).
Estados documentales: **`Draft` -> `In Review` -> `Approved` -> `Done`**.

| Gate | Artefacto / Acción | Marcador Humano | Regla de Bloqueo |
| :--- | :--- | :--- | :--- |
| **Gate S0** | `specs/STACK.md` (`sdd-bootstrap`) | `[x] Gate S0 Approved` *(alias legacy: `Gate 00`)* | `RN-SDD-GATE-S0-STACK-LOCK` |
| **Gate 0** | Alta en `specs/BACKLOG.md` (`FEAT-XXX`, `CR-XXX`, `BUG-XXX`) | Priorización en Backlog | SSOT único de IDs y estados |
| **Gate 1** | `01-spec.md` (EARS + Given-When-Then) o `01-bug-report.md` | `[x] Gate 1 Approved` | Parada *fail-closed* ante ambigüedad |
| **Gate 2** | `02-tech-spec.md` o `02-fix-spec.md` (`+ Sub-Gate 2V` si hay UI) | `[x] Gate 2 Approved` *(+ `Gate 2 Visual Sign-off`)* | Contratos tipados antes de codificar |
| **Gate 3** | `03-tasks.md` con grafo DAG, `ALLOWED_FILES` y comandos DoD | `[x] Gate 3 Approved` | `RN-SDD-GATE2-CODE-LOCK` |
| **Gate 4** | Ejecución aislada (`opsx-delegate` / `opsx-pickup`) + TDD y auditorías | Verificación Gate 4 | `sdd_code_gate_guard.py` |
| **Gate 5** | Docs bilingües, `docs/knowledge/`, `domains/`, trazabilidad y `git push` | Cierre `Done` | `RN-SDD-0DD` y sincronización Git |

---

<a id="rfc003-hardening-es"></a>

### 3. Endurecimiento `RFC-003`, Ownership y Multi-Worktree

El framework verifica el cumplimiento mediante herramientas Python deterministas en `.agents/scripts/`:

- **Hooks `PreToolUse` y Guardias *Fail-Closed*:**
  - `sdd_code_gate_guard.py` y `sdd_gate_seal.py` (`sdd approve-gate`, `sdd verify-gates`): Impiden modificar `src/` sin `Gate S0` aprobado, work item `In Progress` en `specs/BACKLOG.md`, marcadores `[x] Gate 1/2/3 Approved` y sellos criptográficos SHA-256 intactos (`gate_seals`).
  - `sdd_immutable_feature_guard.py`: Protege especificaciones de features `Done` frente a mutaciones directas.
  - `sdd_trim_exec.py`: Ejecuta subcomandos permitidos con `shell=False` y contención estricta al workspace.
  - `sdd_healthcheck.py`: Audita estructura, triadas documentales (`features`, `changes`, `bugs`), riesgos de *prompt injection* y consistencia del catálogo.
- **Compilador Declarativo `sdd:ownership-map`:** `sdd_agent_generator.py` y `sdd_pack_registry.py` materializan especialistas desde `specs/STACK.md` de forma transaccional con validación SHA-256 en `.agents/squad.lock.json` y rollback automático ante errores.
- **Planificador DAG (`sdd_dag.py`):** Valida dependencias, ciclos y colisiones de escritura en olas paralelas (`DagWriteSetCollisionError`, `--auto-split`) en `03-tasks.md` para despachar bloques paralelos sin colisiones de `ALLOWED_FILES`.
- **Aislamiento Multi-Worktree (`sdd_git.py` y `sdd_dev.py`):** Worktrees Git contenidos en el workspace con aislamiento determinista de puertos de desarrollo.
- **Techo de Modularidad, Fronteras Políglotas y Mapa AST:** `verify_architecture_boundaries.py` valida `forbid_imports` en Python, TS/JS, C#, Go, Rust, Java y Kotlin junto al límite duro de **`<= 800` líneas (`<= 500` aviso)** en `src/` y **`<= 500` líneas** en scripts/tests del framework. `sdd_repo_map.py` indexa símbolos en **más de 20 lenguajes**.

---

<a id="agent-squad-es"></a>

### 4. Escuadrón Base y Catálogo Opt-In

El starter arranca con **9 agentes base activos** (`1` revisor universal por defecto `@security-reviewer` en `.sdd/catalog/specialists/`) y mantiene **19 especialistas universales opt-in** en `.sdd/catalog/specialists-optin/` (**20** especialistas universales en total, además de **30** especialistas de stack en `.sdd/catalog/packs/`):

- **Núcleo de Gobernanza (6):** `@orchestrator`, `@functional-analyst`, `@architect`, `@qa-tester`, `@documentator`, `@devops`.
- **Constructores Compactos (2):** `@back-engineer`, `@front-engineer` (compilados/reemplazados mediante `sdd:ownership-map` en `specs/STACK.md`).
- **Revisor de Seguridad por Defecto (1):** `@security-reviewer`.
- **Especialistas Universales Opt-In (19 en `.sdd/catalog/specialists-optin/`):** `build-error-resolver`, `code-architect`, `code-explorer`, `code-simplifier`, `comment-analyzer`, `conversation-analyzer`, `docs-lookup`, `e2e-runner`, `gan-evaluator`, `gan-generator`, `gan-planner`, `opensource-sanitizer`, `performance-optimizer`, `pr-test-analyzer`, `refactor-cleaner`, `silent-failure-hunter`, `spec-miner`, `tdd-guide`, `type-design-analyzer`.

---

<a id="stack-packs-es"></a>

### 5. Stack Packs y Arquetipos de Capa

Al completar `specs/STACK.md`, el motor materializa bajo demanda desde **19 Stack Packs** (`.sdd/catalog/packs/`):
- **30 especialistas dinámicos de stack** (Python, TypeScript, Go, Rust, Java, C#, FastAPI, Django, Next.js, React, Spring Boot, Angular, Vue, NestJS, Astro, Flutter, React Native, UI Design y DevOps).
- **70 skills especializadas de pack (`SKILL.md`)**.
- **12 arquetipos canónicos únicos de capa** en `.sdd/catalog/archetypes/` (`cli-tool`, `front-logic`, `front-test`, `front-ui`, `layer-api`, `layer-db`, `layer-domain`, `layer-infra`, `layer-test`, `mobile-app`, `tier-backend`, `tier-frontend`).

---

<a id="skills-workflows-es"></a>

### 6. Skills Base, Workflows y Bugs Fast-Track

- **13 Skills Base (`.agents/skills/`):** `sdd-bootstrap`, `sdd-change-gate`, `pipeline-run`, `opsx-delegate`, `opsx-pickup`, `search-first`, `strategic-compact`, `sdd-silent-failure-audit`, `sdd-spec-compliance-audit`, `sdd-test-quality-audit`, `santa-method`, `gan-style-harness` y `continuous-learning-v2`.
- **13 Slash Command Workflows (`.agents/workflows/`):** `/pipeline-run`, `/opsx-delegate`, `/opsx-pickup`, `/bug-fast-track`, `/build-fix`, `/checkpoint`, `/continue`, `/gate5`, `/harness-audit`, `/santa-loop`, `/gan-build`, `/learn`, `/evolve`.
- **Flujo `/bug-fast-track` (`BUG-XXX`):** Utiliza `specs/bugs/BUG-XXX-<slug>/` (`specs/templates/05-bug-fast-track.template.md`) con `01-bug-report.md`, `02-fix-spec.md` y `03-tasks.md` Test-First (`Red -> Fix -> Green`), reduciendo ceremonia sin omitir `Gate S0`, `specs/BACKLOG.md` como SSOT ni las firmas humanas `[x] Gate 1/2/3 Approved`.

---

<a id="domains-es"></a>

### 7. Contexto de Dominio Bajo Demanda (`domains/`)

Cada dominio activo puede documentarse en `domains/<domain-slug>/` a partir de `domains/_template/overview.md` y `domains/_template/decisions.md` (`DOM-<slug>.D-01`), cargándose bajo demanda en **Gate 1/2** o `/bug-fast-track` y sincronizándose en **Gate 5** por `@documentator`. Ver índice en [`domains/README.md`](domains/README.md).

---

<a id="quickstart-es"></a>

### 8. Inicio Rápido y Referencia CLI

```bash
# 1. Auditoría de salud, triadas e integridad del framework
uv run python .agents/scripts/sdd_healthcheck.py

# 2. Validación de límites arquitectónicos y modularidad
uv run python .agents/scripts/verify_architecture_boundaries.py

# 3. Subcomandos CLI (materialize, verify, work-item, worktree)
uv run python .agents/scripts/sdd_cli.py --help

# 4. Ejecutar la suite de tests del framework
uv run python -m unittest discover -s tests -v
```

---

<a id="repo-arch-es"></a>

### 9. Arquitectura del Repositorio

Consulta el árbol completo en la [sección inglesa](#repo-arch-en). Las reglas globales residen en [`AGENTS.md`](AGENTS.md), la especificación metodológica en [`specs/SDD_FRAMEWORK.md`](specs/SDD_FRAMEWORK.md) y la plantilla de bugs en [`specs/templates/05-bug-fast-track.template.md`](specs/templates/05-bug-fast-track.template.md).

---

<a id="credits-es"></a>

### 10. Créditos y Atribuciones

Licencia **MIT**. Consulta el detalle completo de fuentes externas y atribuciones en [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
