# SDD Agentic Starter Template

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](THIRD_PARTY_NOTICES.md)
[![SDD Governance](https://img.shields.io/badge/SDD-Spec--Driven%20Development-success.svg)](#-the-sdd-lifecycle-gate-00-to-gate-5)
[![Multi-Agent Squad](https://img.shields.io/badge/Agents-49%20Specialists-indigo.svg)](#-complete-catalog-of-agents--specialists-49-specialists)
[![AST Engine](https://img.shields.io/badge/Repo--Map-20%2B%20Languages-sky.svg)](#-deterministic-tooling-zero-discovery-overhead)
[![PreToolUse Hooks](https://img.shields.io/badge/Mechanical%20Hooks-Active%20Guardrails-rose.svg)](#-the-ownership-map--zero-write-collision-parallel-execution)
[![Multi-IDE](https://img.shields.io/badge/Multi--IDE-Antigravity%20%7C%20Claude%20%7C%20Cursor%20%7C%20Windsurf%20%7C%20Codex-violet.svg)](#-system-architecture-overview)

[ 🇬🇧 English (EN-GB)](#-english-en-gb) | [ 🇪🇸 Español (ES-ES)](#-español-es-es)

---

## 🇬🇧 English (EN-GB)

Universal, production-ready software engineering starter template governed by **Spec-Driven Development (SDD)** and multi-agent orchestration. Integrates high-rigour engineering patterns from **Everything Claude Code (ECC)** under the MIT License.

---

### 🏛️ System Architecture Overview

The framework structures software development into a clean, layered architecture inspired by modern Clean/Hexagonal principles, separating high-level orchestration, bounded domain construction, specialized code auditing, and mechanical enforcement hooks.

```mermaid
flowchart TD
    %% Modern Aesthetic ProcessOn-Style Card Classes
    classDef ideCard fill:#ffffff,stroke:#64748b,stroke-width:1.5px,color:#0f172a,rx:5px,font-size:12px;
    classDef coreCard fill:#ffffff,stroke:#6366f1,stroke-width:2px,color:#1e1b4b,rx:5px,font-weight:bold,font-size:12px;
    classDef buildCard fill:#ffffff,stroke:#10b981,stroke-width:2px,color:#064e3b,rx:5px,font-weight:bold,font-size:12px;
    classDef specCard fill:#ffffff,stroke:#0d9488,stroke-width:1.5px,color:#134e4a,rx:5px,font-size:11px;
    classDef stackCard fill:#ffffff,stroke:#f59e0b,stroke-width:1.5px,color:#78350f,rx:5px,font-size:11px;
    classDef catCard fill:#ffffff,stroke:#8b5cf6,stroke-width:1.5px,color:#4c1d95,rx:5px,font-size:11px;
    classDef toolCard fill:#ffffff,stroke:#0284c7,stroke-width:1.5px,color:#0369a1,rx:5px,font-size:11px;
    classDef guardCard fill:#ffffff,stroke:#e11d48,stroke-width:2px,color:#881337,rx:5px,font-weight:bold,font-size:11px;

    subgraph SYSTEM ["SDD Universal Agentic Architecture · Layered Box Blueprint"]
        direction TB

        subgraph L0_IDE ["Client Interfaces & Multi-IDE Runtime"]
            direction LR
            IDE1["Antigravity IDE"]:::ideCard
            IDE2["Claude Code CLI"]:::ideCard
            IDE3["Cursor Editor"]:::ideCard
            IDE4["Windsurf IDE"]:::ideCard
            IDE5["OpenAI Codex"]:::ideCard
            IDE6["Roo Code / Cline"]:::ideCard
        end

        subgraph L1_CORE ["Layer 1: Core Governance Squad (Fixed & Stack-Agnostic)"]
            direction LR
            ORCH["@orchestrator<br>Tech Lead & SDD Master"]:::coreCard
            FA["@functional-analyst<br>Gate 1 EARS & BDD"]:::coreCard
            ARCH["@architect<br>Gate 2 API & ADRs"]:::coreCard
            QA["@qa-tester<br>Gate 4 Verification"]:::coreCard
            DOC["@documentator<br>Gate 5 Living Docs 0DD"]:::coreCard
            DEVOPS["@devops<br>CI/CD & Containers"]:::coreCard
        end

        subgraph L2_BUILD ["Layer 2: Builders & Ownership Map (Exclusive Write Authority)"]
            direction LR
            DOM["@back-domain<br>Domain & Use Cases"]:::buildCard
            INFRA["@back-infra<br>Adapters & I/O"]:::buildCard
            API["@back-api<br>Routers & DTOs"]:::buildCard
            DB["@db-specialist<br>DDL & Migrations"]:::buildCard
            FUI["@front-ui<br>Components & CSS"]:::buildCard
            FLOG["@front-logic<br>State & API Client"]:::buildCard
            TEST["@back-test / @front-test<br>Automated Suites"]:::buildCard
        end

        subgraph L3_SPEC ["Layer 3: Ultra-Specialists (Read-Only Reviewers & Surgical Resolvers)"]
            direction TB
            subgraph L3A_UNIV ["20 Universal Specialists (Always Available)"]
                direction LR
                SEC["@security-reviewer<br>OWASP & Zero-Secrets"]:::specCard
                FAIL["@silent-failure-hunter<br>Catch/Except Audits"]:::specCard
                TYPE["@type-design-analyzer<br>Strict Type System"]:::specCard
                TDD["@tdd-guide<br>Red-Green-Refactor"]:::specCard
                OPT["@performance-optimizer<br>Memory & Profiling"]:::specCard
                BFIX["@build-error-resolver<br>Minimal Diff Repairs"]:::specCard
                GAN["@gan-planner · @gan-evaluator<br>Adversarial Quality (>=8.5)"]:::specCard
            end

            subgraph L3B_STACK ["29 Dynamic Stack Specialists Across 18 Packs (Activated on Demand)"]
                direction LR
                PY["Python / FastAPI / Django<br>@python-reviewer<br>@fastapi-reviewer"]:::stackCard
                TS["TypeScript / React / Vue<br>@typescript-reviewer<br>@react-reviewer"]:::stackCard
                CS["C# / .NET 9<br>@csharp-reviewer"]:::stackCard
                GO["Go / Rust<br>@go-reviewer<br>@rust-reviewer"]:::stackCard
                JVM["Java / Kotlin<br>@java-reviewer<br>@kotlin-reviewer"]:::stackCard
                CAP["DB / Web / AI<br>@database-reviewer<br>@rag-pipeline-reviewer"]:::stackCard
            end
        end

        subgraph L4_CAT ["Layer 4: Inactive Catalog & Knowledge Base (.sdd/catalog/ & docs/knowledge/)"]
            direction LR
            CAT_ARC["18 Layer Archetypes<br>domain, infra, api, db, ui..."]:::catCard
            CAT_SPC["20 Universal Specialists<br>ECC Prompt-Defense Wrappers"]:::catCard
            CAT_PCK["18 Dynamic Stack Packs<br>Rules, Agents & Skills Recipes"]:::catCard
            CAT_KB["Living Knowledge Base<br>SYSTEM_TOPOLOGY & API_CATALOG"]:::catCard
        end

        subgraph L5_TOOL ["Layer 5: Deterministic Tools & AST Engine (Zero Discovery Overhead)"]
            direction LR
            AST["sdd_repo_map.py<br>AST Skeleton (20+ Langs)"]:::toolCard
            TRIM["sdd_trim_exec.py<br>Terminal Output Trimmer"]:::toolCard
            TOK["sdd_token_usage.py<br>Multi-IDE Token Telemetry"]:::toolCard
            BOUND["verify_architecture_boundaries.py<br>AST Forbidden Import Verifier"]:::toolCard
        end

        subgraph CROSS_GUARD ["Cross-Cutting SDD Governance & Mechanical Guardrails"]
            direction LR
            HOOKS["PreToolUse Mechanical Hooks<br>sdd_code_gate_guard.py<br>sdd_immutable_feature_guard.py"]:::guardCard
            LOCKS["Gate Locks (Fail-Closed)<br>RN-SDD-GATE00-STACK-LOCK<br>RN-SDD-GATE2-CODE-LOCK<br>RN-SDD-IMMUTABLE-DONE"]:::guardCard
            LIMITS["Strict Modularity Limits<br>Hard Ceiling: 800 lines/file<br>Warning: 500 lines/file"]:::guardCard
            SEMA["Context Health Semaphore<br>Max 15 Turns / 2 DAG Blocks<br>Turn & Session Telemetry"]:::guardCard
        end
    end

    %% Process Flow & Governance Links
    L0_IDE ==>|"Prompt & Context"| L1_CORE
    L1_CORE ==>|"1. Plans DAG & Dispatches Tasks"| L2_BUILD
    L2_BUILD -.->|"2. Code Review Requests"| L3_SPEC
    L3_SPEC -.->|"3. DoD Verification Commands"| L5_TOOL
    CROSS_GUARD -.-|"Mechanical Interception on Every Tool Call"| L2_BUILD
    CROSS_GUARD -.-|"Gate Enforcement"| L1_CORE
    L4_CAT -.->|"Materializes on Bootstrap"| L2_BUILD

    %% Aesthetic Layer Container Background Styles
    style SYSTEM fill:#f8fafc,stroke:#94a3b8,stroke-width:2px,color:#0f172a
    style L0_IDE fill:#f1f5f9,stroke:#cbd5e1,stroke-width:1.5px,color:#334155
    style L1_CORE fill:#eef2ff,stroke:#a5b4fc,stroke-width:2px,color:#312e81
    style L2_BUILD fill:#ecfdf5,stroke:#6ee7b7,stroke-width:2px,color:#065f46
    style L3_SPEC fill:#f0fdfa,stroke:#5eead4,stroke-width:2px,color:#115e59
    style L3A_UNIV fill:#ffffff,stroke:#99f6e4,stroke-width:1px,color:#134e4a
    style L3B_STACK fill:#ffffff,stroke:#fde68a,stroke-width:1px,color:#78350f
    style L4_CAT fill:#f5f3ff,stroke:#c4b5fd,stroke-width:2px,color:#5b21b6
    style L5_TOOL fill:#f0f9ff,stroke:#7dd3fc,stroke-width:2px,color:#075985
    style CROSS_GUARD fill:#fff1f2,stroke:#fda4af,stroke-width:2px,color:#9f1239
```

---

### 🚀 Getting Started with a New Project

#### Step 1: Clone or Use this Template
Create a new private repository on GitHub from this starter:
```bash
gh repo create my-new-project --template serchodm/sdd-agentic-starter --private
cd my-new-project
```

#### Step 2: Initial Repository Lock (`Gate 00: Stack Lock`)
To guarantee architectural consistency and prevent premature coding, **production code in `src/` is strictly locked** by rule `RN-SDD-GATE00-STACK-LOCK`. No production code or tests may be created until the technology stack, hosting topology, Ownership Map, and agent squad are formally agreed upon.

#### Step 3: Converse with `@orchestrator` in your AI Assistant
Launch your AI programming assistant (Antigravity, Cursor, Claude Code, Windsurf, or Codex) and start with:
> *"Hello @orchestrator. We are starting a new project based on `sdd-agentic-starter`. Please launch the interactive Gate 00 Bootstrap Wizard to define the system topology, architecture, technology stack, agent squad, and conventions."*

The `@orchestrator` will:
1. Run the interactive **Gate 00 Bootstrap Wizard (`sdd-bootstrap`)** with dynamic decision tree pruning:
   - **Infrastructure & Hosting**: Public Cloud (AWS/Azure/GCP), Docker Containers, or modern PaaS (**Vercel**, Netlify, Railway).
   - **Scope & Pruning**: Automatically prunes irrelevant questions (e.g. omits UI styling for API-only projects, or backend questions for client-only SPAs).
   - **Ownership Map (§3.2)**: Configures deterministic boundaries, mapping code paths to specific builder agents with forbidden imports and verification commands.
   - **Stack Pack Activation**: Dynamically activates language, framework, and capability packs from `.sdd/catalog/packs/`.
   - **Deterministic DoD Commands (§2.5)**: Freezes verified commands for linting, fast in-memory unit tests (<1s), integration tests, and production builds to eliminate agent discovery overhead.
   - **Local Environment**: Generates `docker-compose.yml` or `vercel.json` dev setup.
2. Complete **`specs/STACK.md`** and compile the squad using `python scripts/sdd_agent_generator.py --materialize`.
3. Request your explicit human sign-off: `[x] Gate 00 Approved (Human Sign-off)`.
4. Once approved, `src/` unlocks and the normal SDD development lifecycle begins (Gate 0 -> Gate 5).

---

### 🏛️ The SDD Lifecycle (Gate 00 to Gate 5)

Development follows a strict, step-by-step quality gate progression. No code is written before Gate 2 and Gate 3 approvals, and no task is considered complete without living documentation.

```mermaid
flowchart TD
    classDef gateCard fill:#ffffff,stroke:#6366f1,stroke-width:2px,color:#1e1b4b,rx:5px,font-weight:bold,font-size:12px;
    classDef humanCard fill:#ffffff,stroke:#f59e0b,stroke-width:2px,color:#78350f,rx:5px,font-weight:bold,font-size:12px;
    classDef execCard fill:#ffffff,stroke:#10b981,stroke-width:2px,color:#064e3b,rx:5px,font-weight:bold,font-size:12px;
    classDef doneCard fill:#ffffff,stroke:#e11d48,stroke-width:2px,color:#881337,rx:5px,font-weight:bold,font-size:12px;

    G00["Gate 00: Stack Lock (specs/STACK.md)<br>• Topology & Hosting Defined<br>• Ownership Map & DoD Commands Configured<br>• Stack Packs Materialized into .agents/"]:::gateCard
    H00{"Human Sign-off<br>[x] Gate 00 Approved"}:::humanCard
    G0["Gate 0: Backlog Intake<br>• Register FEAT-XXX in specs/BACKLOG.md<br>• Initialize specs/features/FEAT-XXX/ directory"]:::gateCard
    G1["Gate 1: Functional Spec (01-spec.md)<br>• Drafted by @functional-analyst<br>• Formal EARS syntax (Ubiquitous, Event, State)<br>• Given-When-Then BDD Acceptance Criteria"]:::gateCard
    H1{"Human Sign-off<br>[x] Gate 1 Approved"}:::humanCard
    G2["Gate 2: Technical Spec (02-tech-spec.md)<br>• Designed by @architect<br>• Symmetric API & DTO Schemas<br>• Architecture Decision Records (ADRs)"]:::gateCard
    H2{"Human Sign-off<br>[x] Gate 2 Approved"}:::humanCard
    G3["Gate 3: Atomic Task DAG (03-tasks.md)<br>• Structured by @orchestrator<br>• [PARALLEL] & [SEQUENTIAL] dependency graph<br>• Definition of Ready (DoR): Agent, Zone, DoD command"]:::gateCard
    H3{"Human Sign-off<br>[x] Gate 3 Approved"}:::humanCard
    G4["Gate 4: Execution & Verification<br>• Dispatched via .agent-inbox/<agent>/<br>• Builders implement code in exclusive zones<br>• ECC Specialists review code & fix build errors<br>• @qa-tester executes regression test batteries"]:::execCard
    G5["Gate 5: Zero Document Debt (0DD)<br>• Executed by @documentator<br>• Bilingual living docs updated (docs/es/ & docs/en/)<br>• API Catalog & Data Models synchronized<br>• TRACEABILITY-MATRIX.md audit completed"]:::gateCard
    DONE["DONE: Feature Baseline Invariant<br>• specs/features/FEAT-XXX/ locked as READ-ONLY<br>• RN-SDD-IMMUTABLE-DONE baseline established<br>• Branch push & PR towards develop (RN-SDD-BRANCH-SYNC)"]:::doneCard

    G00 --> H00 --> G0 --> G1 --> H1 --> G2 --> H2 --> G3 --> H3 --> G4 --> G5 --> DONE
```

---

### 📦 Inactive Catalog vs. Active Workspace Runtime (Zero Token Overhead)

To protect the model's context window from token exhaustion while retaining access to 49+ specialized roles, the framework uses an **inert catalog separation**:

```mermaid
flowchart LR
    classDef catCard fill:#ffffff,stroke:#8b5cf6,stroke-width:1.5px,color:#4c1d95,rx:5px,font-size:12px;
    classDef genCard fill:#ffffff,stroke:#f59e0b,stroke-width:2px,color:#78350f,rx:5px,font-weight:bold,font-size:12px;
    classDef liveCard fill:#ffffff,stroke:#10b981,stroke-width:2px,color:#064e3b,rx:5px,font-weight:bold,font-size:12px;

    subgraph INERT [".sdd/catalog/ (INACTIVE CATALOG · 0 TOKENS CONSUMED)"]
        direction TB
        ARQC["18 Layer Archetypes<br>(domain, infra, api, db, test, tier, mobile, cli)"]:::catCard
        SPECC["20 Universal ECC Specialists<br>(security, silent-failures, TDD, explorers, GAN)"]:::catCard
        PACKC["18 Stack Packs<br>(Python, TS, C#, Go, Rust, Java, React, Vue, DB, AI)"]:::catCard
        SKILLSC["314+ Specialized Skills<br>(fastapi, react-perf, postgres, testing...)"]:::catCard
    end

    GEN["sdd_agent_generator.py<br>--materialize<br>Ownership Map Compiler"]:::genCard

    subgraph RUNTIME [".agents/ (ACTIVE RUNTIME · DISCOVERED BY IDE)"]
        direction TB
        COREA["Layer 1: Core Squad<br>(orchestrator, functional-analyst, architect,<br>qa-tester, documentator, devops)"]:::liveCard
        BUILDA["Layer 2: Materialized Builders<br>(compiled strictly from Ownership Map zones)"]:::liveCard
        SPECA["Layer 3: Active Specialists<br>(universals + project stack reviewers)"]:::liveCard
        OVERA[".agents/overrides/<br>(project-specific domain rules & overrides)"]:::liveCard
    end

    INERT -->|"1. Reads Catalog Recipes"| GEN
    GEN -->|"2. Emits squad.lock.json & Agents"| RUNTIME

    style INERT fill:#f5f3ff,stroke:#c4b5fd,stroke-width:2px,color:#5b21b6
    style RUNTIME fill:#ecfdf5,stroke:#6ee7b7,stroke-width:2px,color:#065f46
```

1. **`.sdd/catalog/` (Inactive Catalog)**: Resides outside `.agents/`. AI assistants (Antigravity, Cursor, Claude Code) do not discover it, meaning **0 tokens** are consumed in your chat turns.
2. **`.agents/` (Active Workspace Runtime)**: Only houses the materialized squad needed for your specific project.
3. **`.agents/overrides/` (Project Customizations)**: Place custom instructions here (e.g. `.agents/overrides/back-domain.md`). The generator respects overrides without dirtying the upstream starter template.

---

### 👥 Complete Catalog of Agents & Specialists (49 Specialists)

#### 1. Core Governance Squad (6 Agents)
| Agent | Role | Authority Boundary | Consultation |
| :--- | :--- | :--- | :--- |
| **`@orchestrator`** | Tech Lead, Scrum Master & SDD Gatekeeper | Plans DAG, dispatches to `.agent-inbox/`. **Zero code in `src/`**. | `specs/BACKLOG.md`, `specs/STACK.md` |
| **`@functional-analyst`**| Product Strategist & Requirements Engineer | Redacts `01-spec.md` with formal EARS and Given-When-Then BDD. | `specs/SYSTEM_VISION.md` |
| **`@architect`** | Solution Architect & API Designer | Designs `02-tech-spec.md`, symmetric DTOs, schemas, and ADRs. | `specs/STACK.md`, `docs/knowledge/` |
| **`@qa-tester`** | QA Lead & Quality Auditor | Executes test suites, audits mutation coverage, and runs quality gates. | Gate 1 Given-When-Then |
| **`@documentator`** | 0DD Living Documentation Custodian | Maintains bilingual docs (`docs/es/`, `docs/en/`), API catalog, and traceability matrix. | `docs/`, `specs/` |
| **`@devops`** | DevOps, Containers & CI/CD Specialist | Manages Docker, Kubernetes, Vercel/PaaS configs, and deploy scripts. | `.github/`, `docker-compose.yml` |

#### 2. Universal ECC Specialists (20 Agents — Always Available)
| Agent | Lifecycle Phase | Specialization & Mission |
| :--- | :--- | :--- |
| **`@code-explorer`** | Discovery (Gate 0/1) | Read-only end-to-end execution flow tracer and surgical file discovery. |
| **`@spec-miner`** | Discovery (Gate 0/1) | Extracts latent requirements and constraints from legacy codebases. |
| **`@docs-lookup`** | Discovery (Gate 0/1) | Fast, targeted documentation search across official framework libraries. |
| **`@code-architect`** | Design (Gate 2) | Implementation blueprint designer, module boundary planner, and compilation order architect. |
| **`@type-design-analyzer`**| Design (Gate 2) | Static type system auditor; eliminates unsafe casts, `any`, and boundary leaks. |
| **`@tdd-guide`** | Execution (Gate 4) | Test-Driven Development mentor; enforces strict Red-Green-Refactor cycles. |
| **`@build-error-resolver`**| Execution (Gate 4) | Surgical build error resolver; fixes compiler/test errors with the absolute minimal diff. |
| **`@security-reviewer`** | Audit (Gate 4) | OWASP Top 10 auditor, zero-secrets enforcer, and path-traversal blocker. |
| **`@silent-failure-hunter`**| Audit (Gate 4) | Hunts swallowed exceptions (`catch {}`, `except: pass`), dangerous fallbacks, and missing telemetry. |
| **`@performance-optimizer`**| Audit (Gate 4) | Memory leak detector, async I/O profiler, and bottleneck eliminator. |
| **`@e2e-runner`** | Audit (Gate 4) | Playwright and CLI End-to-End critical path test runner; eliminates flaky tests. |
| **`@pr-test-analyzer`** | Audit (Gate 4) | Analyzes pull request test coverage and mutation resilience. |
| **`@comment-analyzer`** | Audit (Gate 4) | Detects obsolete comments, misleading documentation, and rotting TODOs. |
| **`@code-simplifier`** | Hygiene (Gate 4) | Post-implementation simplifier; eliminates dead code and reduces cyclomatic complexity. |
| **`@refactor-cleaner`** | Hygiene (Gate 4) | Cleans unused imports, unreferenced helpers, and legacy syntax constructs. |
| **`@gan-planner`** | GAN Harness | Decomposes high-complexity deliverables into adversarial generator tasks. |
| **`@gan-generator`** | GAN Harness | Produces hardened implementations under adversarial critique. |
| **`@gan-evaluator`** | GAN Harness | Evaluates deliverable quality against a weighted rubric (pass mark >= 8.5/10). |
| **`@conversation-analyzer`**| Learning | Extracts atomic instincts (`continuous-learning-v2`) from sessions for `/learn` and `/evolve`. |
| **`@opensource-sanitizer`** | Hygiene | Sanitizes proprietary names, credentials, and local paths before framework sync. |

#### 3. Dynamic Stack Specialists (29 Agents Across 18 Packs)
| Stack Pack | Agents Included | Focus & Responsibilities |
| :--- | :--- | :--- |
| **`lang-python`** | `@python-reviewer` | Python 3.12+, static typing (`mypy`), `asyncio` safety, `dataclass(frozen=True)`. |
| **`framework-fastapi`** | `@fastapi-reviewer` | FastAPI async routers, `Depends` injection, Pydantic v2 camelCase DTOs, SSE/WebSocket lifespan. |
| **`framework-django`** | `@django-reviewer`<br>`@django-build-resolver` | Django ORM N+1 prevention, CSRF/auth security, Celery async tasks, migration healing. |
| **`lang-typescript`** | `@typescript-reviewer` | TypeScript strict flags, Node/Bun runtime, interface segregation, modern `tsconfig`. |
| **`framework-react`** | `@react-reviewer`<br>`@react-build-resolver` | React 19, hook dependencies (`useCallback`/`useMemo`), 60 FPS rendering, Vite build repairs. |
| **`framework-vue`** | `@vue-reviewer` | Vue 3 Composition API, Pinia stores, Nuxt 4 SSR hydration, Vue Router guards. |
| **`lang-csharp`** | `@csharp-reviewer` | C# .NET 9, Nullable Reference Types, EF Core `AsNoTracking`, async `ValueTask`, DI scoping. |
| **`lang-go`** | `@go-reviewer`<br>`@go-build-resolver` | Idiomatic Go, table-driven tests, goroutine leak checks, `go.mod` dependency conflict resolution. |
| **`lang-rust`** | `@rust-reviewer`<br>`@rust-build-resolver` | Rust borrow checker, memory safety, `Result`/`Option` handling, `cargo` build and lifetime repairs. |
| **`lang-java`** | `@java-reviewer`<br>`@java-build-resolver` | Java 21+, Spring Boot 3, Hibernate/JPA queries, Gradle/Maven build failure resolution. |
| **`lang-kotlin`** | `@kotlin-reviewer`<br>`@kotlin-build-resolver` | Kotlin coroutines/flows, Ktor, Exposed ORM, Compose Multiplatform, Gradle Kotlin repairs. |
| **`lang-swift`** | `@swift-reviewer`<br>`@swift-build-resolver` | Swift 6+, Actor isolation, `Sendable` types, SwiftUI lifecycle, `xcodebuild` compilation repairs. |
| **`lang-dart`** | `@flutter-reviewer`<br>`@dart-build-resolver` | Flutter widget trees, reactive state (Riverpod/Bloc), 60 FPS layouts, `dart analyze` repairs. |
| **`lang-cpp`** | `@cpp-reviewer`<br>`@cpp-build-resolver` | C++20 standards, RAII, smart pointers (`std::unique_ptr`), memory leaks, CMake build repairs. |
| **`capability-database`** | `@database-reviewer` | SQL queries, HNSW/GIN/B-Tree indexing, N+1 query prevention, async connection pooling, DDL migrations. |
| **`capability-web-frontend`**| `@a11y-architect`<br>`@seo-specialist` | WCAG 2.1 AA accessibility, keyboard navigation, WAI-ARIA roles, OpenGraph, Core Web Vitals, JSON-LD. |
| **`capability-ai-llm`** | `@rag-pipeline-reviewer`<br>`@mle-reviewer`<br>`@pytorch-build-resolver` | RAG chunking/re-ranking, hallucination mitigation, ML reproducible training, PyTorch tensor repair. |

---

### 🗺️ The Ownership Map & Zero Write-Collision Parallel Execution

Configured in `specs/STACK.md §3.2`, the Ownership Map is the **single source of truth** for code permissions. It maps code directories to single builder owners, enabling parallel multi-agent task execution without write collisions:

```yaml
ownership:
  preset: granular-backend+compact-frontend
  zones:
    - id: backend-domain
      paths: ["src/backend/domain/**", "src/backend/application/**"]
      owner: back-domain
      archetype: layer-domain
      forbid_imports: ["fastapi", "sqlalchemy", "sqlmodel", "infrastructure", "api"]
      dod: { typecheck: "uv run mypy src/backend/domain", unit: "uv run pytest tests/unit/domain -q" }
    - id: backend-infra
      paths: ["src/backend/infrastructure/**"]
      owner: back-infra
      archetype: layer-infra
      dod: { integration: "uv run pytest tests/integration -q" }
    - id: backend-api
      paths: ["src/backend/api/**"]
      owner: back-api
      archetype: layer-api
      forbid_imports: ["sqlalchemy", "sqlmodel"]
      dod: { unit: "uv run pytest tests/unit/api -q" }
    - id: frontend
      paths: ["src/frontend/**"]
      owner: front-engineer
      archetype: tier-frontend
      dod: { typecheck: "npx tsc --noEmit", build: "npm run build" }
  unowned_policy: fail-closed
```

```mermaid
flowchart TD
    classDef orchCard fill:#ffffff,stroke:#6366f1,stroke-width:2px,color:#1e1b4b,rx:5px,font-weight:bold,font-size:12px;
    classDef taskCard fill:#ffffff,stroke:#0284c7,stroke-width:1.5px,color:#0369a1,rx:5px,font-size:12px;
    classDef agentCard fill:#ffffff,stroke:#10b981,stroke-width:2px,color:#064e3b,rx:5px,font-weight:bold,font-size:12px;
    classDef zoneCard fill:#ffffff,stroke:#f59e0b,stroke-width:1.5px,color:#78350f,rx:5px,font-size:12px;
    classDef guardCard fill:#ffffff,stroke:#e11d48,stroke-width:2px,color:#881337,rx:5px,font-weight:bold,font-size:12px;

    ORCH["@orchestrator<br>Parses 03-tasks.md [PARALLEL] Block"]:::orchCard

    subgraph INBOX [".agent-inbox/ Concurrency Dispatch"]
        direction LR
        T1["Task 4.1: Domain Models<br>Assigned: @back-domain"]:::taskCard
        T2["Task 4.2: DB Migrations<br>Assigned: @db-specialist"]:::taskCard
        T3["Task 4.3: UI Components<br>Assigned: @front-ui"]:::taskCard
    end

    subgraph BUILDERS ["Specialist Builders Executing Concurrently"]
        direction LR
        A1["@back-domain"]:::agentCard
        A2["@db-specialist"]:::agentCard
        A3["@front-ui"]:::agentCard
    end

    subgraph ZONES ["Exclusive Ownership Map Zones (specs/STACK.md)"]
        direction LR
        Z1["Zone: backend-domain<br>src/backend/domain/**<br>Forbid: fastapi, sqlalchemy"]:::zoneCard
        Z2["Zone: backend-db<br>src/backend/infrastructure/db/**<br>migrations/**"]:::zoneCard
        Z3["Zone: frontend-ui<br>src/frontend/components/**<br>Forbid: backend imports"]:::zoneCard
    end

    subgraph GUARD ["Mechanical PreToolUse Interception (sdd_code_gate_guard.py)"]
        direction TB
        CHK{"Agent allowed<br>in target path?"}:::guardCard
        ALLOW["✅ Tool Call Allowed<br>Edit Applied Cleanly"]:::agentCard
        DENY["🛑 Tool Call Denied (Exit 1)<br>Fail-Closed Boundary Protection"]:::guardCard
    end

    ORCH ==>|"Dispatches parallel tickets"| INBOX
    T1 --> A1
    T2 --> A2
    T3 --> A3
    A1 ==>|"Writes exclusively to"| Z1
    A2 ==>|"Writes exclusively to"| Z2
    A3 ==>|"Writes exclusively to"| Z3
    Z1 -.->|"Tool Call Event"| CHK
    Z2 -.->|"Tool Call Event"| CHK
    Z3 -.->|"Tool Call Event"| CHK
    CHK -->|"Matches Zone"| ALLOW
    CHK -->|"Out of Zone / Unowned"| DENY

    style INBOX fill:#f0f9ff,stroke:#7dd3fc,stroke-width:2px,color:#075985
    style BUILDERS fill:#ecfdf5,stroke:#6ee7b7,stroke-width:2px,color:#065f46
    style ZONES fill:#fef3c7,stroke:#fcd34d,stroke-width:2px,color:#78350f
    style GUARD fill:#fff1f2,stroke:#fda4af,stroke-width:2px,color:#9f1239
```

- **Mechanical Hook Guard**: PreToolUse hook `sdd_code_gate_guard.py` checks `.agents/active_work_item.json`. If an agent attempts to edit files outside its assigned zone, the operation is **immediately denied**.
- **Architectural Boundary Verification**: Run `python .agents/scripts/verify_architecture_boundaries.py` to audit forbidden imports across layers via AST inspection.

---

### 🧪 Dual Quality Verification Engines: Santa Method & GAN Harness

To eliminate "suspicious green tests", confirmation bias, and complacency in complex deliveries, the framework incorporates two high-rigour verification engines adapted from Everything Claude Code:

```mermaid
flowchart TD
    classDef startCard fill:#ffffff,stroke:#6366f1,stroke-width:2px,color:#1e1b4b,rx:5px,font-weight:bold,font-size:12px;
    classDef revCard fill:#ffffff,stroke:#0d9488,stroke-width:1.5px,color:#134e4a,rx:5px,font-size:12px;
    classDef checkCard fill:#ffffff,stroke:#f59e0b,stroke-width:2px,color:#78350f,rx:5px,font-weight:bold,font-size:12px;
    classDef passCard fill:#ffffff,stroke:#10b981,stroke-width:2px,color:#064e3b,rx:5px,font-weight:bold,font-size:12px;
    classDef failCard fill:#ffffff,stroke:#e11d48,stroke-width:2px,color:#881337,rx:5px,font-weight:bold,font-size:12px;

    subgraph SANTA ["Engine A: The Santa Method ('Checking It Twice' · /santa-loop)"]
        direction TB
        DELIV_A["Task Deliverable Submitted"]:::startCard
        subgraph ISOLATED ["Dual Isolated Reviewers (Independent & Parallel)"]
            direction LR
            REV1["Reviewer 1<br>(Security & Correctness)"]:::revCard
            REV2["Reviewer 2<br>(Types & Error Handling)"]:::revCard
        end
        VERDICT{"Unanimous Consensus?<br>Both Verdicts == NICE"}:::checkCard
        CERT_A["✅ Deliverable Certified<br>Gate 4 Check Passed"]:::passCard
        REWORK_A["❌ Changes Requested<br>Loop Back to Builder Specialist"]:::failCard

        DELIV_A --> ISOLATED
        REV1 --> VERDICT
        REV2 --> VERDICT
        VERDICT -->|"Both NICE"| CERT_A
        VERDICT -->|"Any Issue"| REWORK_A
        REWORK_A -.->|"Fixed Deliverable"| DELIV_A
    end

    subgraph GAN ["Engine B: GAN-Style Adversarial Harness (/gan-build)"]
        direction TB
        PLAN["@gan-planner<br>Formulates Deliverable Blueprint<br>& Weighted Evaluation Rubric"]:::startCard
        GEN["@gan-generator<br>Produces Hardened Code<br>Under Adversarial Critique"]:::revCard
        EVAL["@gan-evaluator<br>Scores Deliverable Objectively<br>Rubric: Arch, Security, DoD, Edge Cases"]:::checkCard
        SCORE{"Evaluation Score<br>>= 8.5 / 10.0?"}:::checkCard
        CERT_B["✅ Deliverable Accepted<br>High-Rigour Standard Achieved"]:::passCard
        CRITIQUE["❌ Adversarial Critique<br>Actionable Defect Feedback"]:::failCard

        PLAN --> GEN
        GEN --> EVAL
        EVAL --> SCORE
        SCORE -->|"Pass (Score >= 8.5)"| CERT_B
        SCORE -->|"Fail (Score < 8.5)"| CRITIQUE
        CRITIQUE -.->|"Refine Code"| GEN
    end

    style SANTA fill:#f0fdfa,stroke:#5eead4,stroke-width:2px,color:#115e59
    style ISOLATED fill:#ffffff,stroke:#99f6e4,stroke-width:1px,color:#134e4a
    style GAN fill:#eef2ff,stroke:#a5b4fc,stroke-width:2px,color:#312e81
```

1. **The Santa Method (`/santa-loop`)**: Inspired by the Santa Claus rhyme ("Making a list, checking it twice"). A deliverable must receive a unanimous **`NICE`** verdict from two independent, isolated reviewers before Gate 4 sign-off.
2. **GAN-Style Adversarial Harness (`/gan-build`)**: Deploys a Generator-Evaluator adversarial architecture. `@gan-planner` creates an objective rubric, `@gan-generator` produces the code, and `@gan-evaluator` scores it objectively until reaching a passing mark of **>= 8.5 / 10.0**.

---

### 🧠 Continuous Learning v2 & Instinct Evolution Engine

The framework features an autonomous learning loop based on ECC's Atomic Instincts engine (`continuous-learning-v2`), transforming developer interactions and problem-solving sessions into permanent institutional knowledge:

```mermaid
flowchart LR
    classDef sessCard fill:#ffffff,stroke:#64748b,stroke-width:1.5px,color:#0f172a,rx:5px,font-size:12px;
    classDef learnCard fill:#ffffff,stroke:#6366f1,stroke-width:2px,color:#1e1b4b,rx:5px,font-weight:bold,font-size:12px;
    classDef instCard fill:#ffffff,stroke:#f59e0b,stroke-width:1.5px,color:#78350f,rx:5px,font-size:12px;
    classDef ruleCard fill:#ffffff,stroke:#10b981,stroke-width:2px,color:#064e3b,rx:5px,font-weight:bold,font-size:12px;

    subgraph SESSION ["Engineering Session"]
        S1["Debugging, Refactoring<br>or Architecture Discovery"]:::sessCard
        S2["Reusable Pattern or<br>Framework Fix Identified"]:::sessCard
        S1 --> S2
    end

    subgraph LEARN ["/learn Trigger"]
        ANALYZER["@conversation-analyzer<br>Extracts Atomic Pattern"]:::learnCard
    end

    subgraph INSTINCTS ["Instinct Pool (continuous-learning-v2)"]
        direction TB
        I1["Instinct #1<br>Confidence: 0.3 (Candidate)"]:::instCard
        I2["Instinct #2<br>Confidence: 0.6 (Reinforced)"]:::instCard
        I3["Instinct #3<br>Confidence: 0.9 (Proven)"]:::instCard
        I1 -.->|"Repeated Success"| I2
        I2 -.->|"Cross-Session Validation"| I3
    end

    subgraph EVOLVE ["/evolve Trigger"]
        EVOLVER["Instinct Evolution Engine<br>Clusters Related High-Confidence Patterns"]:::learnCard
    end

    subgraph PERM ["Permanent Repository Assets"]
        R1[".agents/rules/*.md<br>Enforced Project Rules"]:::ruleCard
        R2[".agents/skills/*.md<br>Autonomous Reusable Skills"]:::ruleCard
    end

    S2 ==>|"Triggers /learn"| ANALYZER
    ANALYZER ==>|"Persists atomic instinct"| I1
    I3 ==>|"Confidence >= 0.75"| EVOLVER
    EVOLVER ==>|"Generates"| R1
    EVOLVER ==>|"Packages"| R2

    style SESSION fill:#f8fafc,stroke:#cbd5e1,stroke-width:1.5px,color:#334155
    style LEARN fill:#eef2ff,stroke:#a5b4fc,stroke-width:2px,color:#312e81
    style INSTINCTS fill:#fef3c7,stroke:#fcd34d,stroke-width:2px,color:#78350f
    style EVOLVE fill:#eef2ff,stroke:#a5b4fc,stroke-width:2px,color:#312e81
    style PERM fill:#ecfdf5,stroke:#6ee7b7,stroke-width:2px,color:#065f46
```

- **Confidence Scoring (`0.3` to `0.9`)**: Candidate patterns enter at confidence `0.3`. As patterns succeed across sessions, confidence increases to `0.6` and `0.9`.
- **Automatic Evolution (`/evolve`)**: When related instincts reach confidence `>= 0.75`, the engine clusters them and synthesizes permanent `.agents/rules/*.md` or modular `.agents/skills/*.md`.

---

### 🔄 The 12 Slash Command Workflows

| Category | Command | Dispatches To | Description |
| :--- | :--- | :--- | :--- |
| **Lifecycle** | `/pipeline-run` | Orchestrator & Specialists | Autonomous, end-to-end execution of an approved feature from Gate 3 to Gate 5. |
| | `/opsx-delegate` | Orchestrator | Tech Lead deposits atomic task tickets in `.agent-inbox/<agent>/` enforcing strict DoR. |
| | `/opsx-pickup` | Builder Specialist | Picks up assigned task ticket, audits DoR, implements code, and validates DoD. |
| | `/gate5` | `@documentator` | Dedicated, cost-effective closing session for bilingual living documentation and Git sync. |
| **Session** | `/checkpoint` | Session State | Snapshots pending tasks into `.agents/ACTIVE_STATE.md` and prepares clean handoff. |
| | `/continue` | Clean Session | Resumes execution in a fresh session with bounded context (max 4 files), resetting turns to `1/15`. |
| **Quality** | `/santa-loop` | Dual Independent Reviewers | Santa Method ("Checking It Twice"): loops until two isolated reviewers reach unanimous NICE verdict. |
| | `/gan-build` | `@gan-planner` → `@gan-generator` → `@gan-evaluator` | Adversarial Generator-Evaluator loop for complex deliverables with weighted scoring (>= 8.5/10). |
| | `/build-fix` | Build Error Resolvers | Repairs compiler, linter, or test failures using the minimal surgical diff. |
| | `/harness-audit` | Harness Auditor | Audits health of rules, agent definitions, inbox tickets, and architectural boundaries. |
| **Learning** | `/learn` | Continuous Learning v2 | Extracts atomic instincts from session reasoning into `skills/` or `rules/`. |
| | `/evolve` | Instinct Engine | Clusters high-confidence instincts (>= 0.75) and evolves them into permanent rules or skills. |

---

### 🚦 Context Health Semaphore & Token Telemetry (`RN-SDD-CONTEXT-SEMAPHORE`)

To prevent hallucination loops and context degradation in long-running tasks, the `@orchestrator` monitors turn depth and tokens on every turn:

```text
---
🟢/🟡/🔴 Context Health: Turn X/15 | Blocks: Y/2 | Gate: Z
    ↳ Tokens (Last Turn): In X.Xk · Out X.Xk · Cache X.Xk
    ↳ Tokens (Session Total): In X.Xk · Out X.Xk · Cache X.Xk (Hit: XX.X%)
```

- 🟢 **Green (`Turn 1-10` | `Blocks 0-1`)**: Optimal execution window.
- 🟡 **Yellow (`Turn 11-14` | `Blocks 2`)**: Warning threshold. The agent prepares for handoff.
- 🔴 **Red (`Turn 15+` | `Blocks 3+`)**: **Strict Stop-the-Line**. The agent halts subagent dispatch and triggers `/checkpoint` to force a clean `/continue` handoff.

Inspect token usage across Antigravity, Claude Code, Cursor, Codex, Windsurf, or Roo Code at any time:
```bash
python .agents/scripts/sdd_token_usage.py
```

---

### ⚡ Deterministic Tooling (Zero Discovery Overhead)

1. **Universal Multi-Language AST Repo-Map (`sdd_repo_map.py`)**:
   Extracts class hierarchies, method signatures, interfaces, and types across 20+ languages without dumping full implementations:
   - TypeScript/JavaScript, Python, C# (.NET), Go, Rust, Java, Kotlin, Swift, Dart, C/C++, PHP, Ruby, etc.
   ```bash
   python .agents/scripts/sdd_repo_map.py src/
   ```
2. **Deterministic Terminal Trimmer (`sdd_trim_exec.py`)**:
   Shields the context window from terminal log pollution:
   - On success (`exit 0`): Compresses 100+ lines into a single clean summary line (`✅ [DoD OK] ...`).
   - On failure (`exit != 0`): Strips ANSI noise, isolating only the stack trace, failure assertion, and file/line.
   ```bash
   python .agents/scripts/sdd_trim_exec.py pytest tests/unit/
   python .agents/scripts/sdd_trim_exec.py npm test
   ```
3. **Architectural Boundary Verifier (`verify_architecture_boundaries.py`)**:
   Audits code imports against forbidden layer boundaries declared in `specs/STACK.md §3.2`.
   ```bash
   python .agents/scripts/verify_architecture_boundaries.py
   ```

---

### 🛡️ Framework Healthcheck

Audit the mechanical integrity of agent definitions, rules, and governance scripts at any time:
```bash
uv run python .agents/scripts/sdd_healthcheck.py
```

---

### ⚖️ Third-Party Notices & Attribution

This project incorporates, adapts, or is inspired by open-source works under permissive licenses:
- **Everything Claude Code (ECC)**: Copyright (c) 2026 Affaan Mustafa ([https://github.com/affaan-m/ecc](https://github.com/affaan-m/ecc)), licensed under the **MIT License**. Reviewer agents, prompt defense baselines, build resolvers, continuous learning v2, and language pattern packs are adapted from ECC. Full legal notice in [`THIRD_PARTY_NOTICES.md`](file:///c:/Projects/sdd-agentic-starter/THIRD_PARTY_NOTICES.md).
- **REA Framework**: Inspired by `morluto/rea` for Fail-Closed governance, Boundary Ownership, and Human Gate Ownership.

---
---

## 🇪🇸 Español (ES-ES)

Plantilla universal de desarrollo de software lista para producción, gobernada por **Spec-Driven Development (SDD)** y orquestación multi-agente. Integra patrones de alta rigurosidad en ingeniería de software provenientes de **Everything Claude Code (ECC)** bajo Licencia MIT.

---

### 🏛️ Visión General de la Arquitectura del Sistema

El framework estructura el desarrollo de software en una arquitectura por capas nítida inspirada en principios Hexagonales y Clean Architecture, separando la gobernanza de alto nivel, la construcción con límites de dominio, la auditoría especializada de código y las guardias mecánicas.

```mermaid
flowchart TD
    %% Clases Estilo Moderno ProcessOn
    classDef ideCard fill:#ffffff,stroke:#64748b,stroke-width:1.5px,color:#0f172a,rx:5px,font-size:12px;
    classDef coreCard fill:#ffffff,stroke:#6366f1,stroke-width:2px,color:#1e1b4b,rx:5px,font-weight:bold,font-size:12px;
    classDef buildCard fill:#ffffff,stroke:#10b981,stroke-width:2px,color:#064e3b,rx:5px,font-weight:bold,font-size:12px;
    classDef specCard fill:#ffffff,stroke:#0d9488,stroke-width:1.5px,color:#134e4a,rx:5px,font-size:11px;
    classDef stackCard fill:#ffffff,stroke:#f59e0b,stroke-width:1.5px,color:#78350f,rx:5px,font-size:11px;
    classDef catCard fill:#ffffff,stroke:#8b5cf6,stroke-width:1.5px,color:#4c1d95,rx:5px,font-size:11px;
    classDef toolCard fill:#ffffff,stroke:#0284c7,stroke-width:1.5px,color:#0369a1,rx:5px,font-size:11px;
    classDef guardCard fill:#ffffff,stroke:#e11d48,stroke-width:2px,color:#881337,rx:5px,font-weight:bold,font-size:11px;

    subgraph SYSTEM ["Arquitectura Universal Agéntica SDD · Blueprint Modular por Capas"]
        direction TB

        subgraph L0_IDE ["Interfaces de Cliente y Runtime Multi-IDE"]
            direction LR
            IDE1["Antigravity IDE"]:::ideCard
            IDE2["Claude Code CLI"]:::ideCard
            IDE3["Cursor Editor"]:::ideCard
            IDE4["Windsurf IDE"]:::ideCard
            IDE5["OpenAI Codex"]:::ideCard
            IDE6["Roo Code / Cline"]:::ideCard
        end

        subgraph L1_CORE ["Capa 1: Escuadrón Core de Gobernanza (Fijo y Agnóstico al Stack)"]
            direction LR
            ORCH["@orchestrator<br>Tech Lead & Master SDD"]:::coreCard
            FA["@functional-analyst<br>Gate 1 EARS & BDD"]:::coreCard
            ARCH["@architect<br>Gate 2 API & ADRs"]:::coreCard
            QA["@qa-tester<br>Gate 4 Verificación"]:::coreCard
            DOC["@documentator<br>Gate 5 Living Docs 0DD"]:::coreCard
            DEVOPS["@devops<br>CI/CD y Despliegue"]:::coreCard
        end

        subgraph L2_BUILD ["Capa 2: Constructores y Ownership Map (Autoridad Exclusiva de Escritura)"]
            direction LR
            DOM["@back-domain<br>Dominio y Casos de Uso"]:::buildCard
            INFRA["@back-infra<br>Adaptadores e I/O"]:::buildCard
            API["@back-api<br>Routers y DTOs"]:::buildCard
            DB["@db-specialist<br>DDL y Migraciones"]:::buildCard
            FUI["@front-ui<br>Componentes y CSS"]:::buildCard
            FLOG["@front-logic<br>Estado y Cliente API"]:::buildCard
            TEST["@back-test / @front-test<br>Suites Automatizadas"]:::buildCard
        end

        subgraph L3_SPEC ["Capa 3: Ultra-Especialistas (Revisores de Solo Lectura y Resolvers Quirúrgicos)"]
            direction TB
            subgraph L3A_UNIV ["20 Especialistas Universales ECC (Siempre Disponibles)"]
                direction LR
                SEC["@security-reviewer<br>OWASP y Cero Secretos"]:::specCard
                FAIL["@silent-failure-hunter<br>Caza Errores Ocultos"]:::specCard
                TYPE["@type-design-analyzer<br>Tipado Estricto"]:::specCard
                TDD["@tdd-guide<br>Red-Green-Refactor"]:::specCard
                OPT["@performance-optimizer<br>Memoria y Profiling"]:::specCard
                BFIX["@build-error-resolver<br>Reparación Mínimo Diff"]:::specCard
                GAN["@gan-planner · @gan-evaluator<br>Calidad Adversarial (>=8.5)"]:::specCard
            end

            subgraph L3B_STACK ["29 Especialistas Dinámicos de Stack en 18 Packs (Activados Bajo Demanda)"]
                direction LR
                PY["Python / FastAPI / Django<br>@python-reviewer<br>@fastapi-reviewer"]:::stackCard
                TS["TypeScript / React / Vue<br>@typescript-reviewer<br>@react-reviewer"]:::stackCard
                CS["C# / .NET 9<br>@csharp-reviewer"]:::stackCard
                GO["Go / Rust<br>@go-reviewer<br>@rust-reviewer"]:::stackCard
                JVM["Java / Kotlin<br>@java-reviewer<br>@kotlin-reviewer"]:::stackCard
                CAP["BD / Web / IA<br>@database-reviewer<br>@rag-pipeline-reviewer"]:::stackCard
            end
        end

        subgraph L4_CAT ["Capa 4: Catálogo Inerte y Base de Conocimiento (.sdd/catalog/ y docs/knowledge/)"]
            direction LR
            CAT_ARC["18 Arquetipos de Capa<br>domain, infra, api, db, ui..."]:::catCard
            CAT_SPC["20 Especialistas Universales<br>Wrappers de Prompt-Defense ECC"]:::catCard
            CAT_PCK["18 Stack Packs Dinámicos<br>Reglas, Agentes y Skills"]:::catCard
            CAT_KB["Base de Conocimiento Viva<br>SYSTEM_TOPOLOGY y API_CATALOG"]:::catCard
        end

        subgraph L5_TOOL ["Capa 5: Herramientas Deterministas y Motor AST (Cero Overhead de Descubrimiento)"]
            direction LR
            AST["sdd_repo_map.py<br>Esqueleto AST (20+ Lenguajes)"]:::toolCard
            TRIM["sdd_trim_exec.py<br>Recortador de Terminal"]:::toolCard
            TOK["sdd_token_usage.py<br>Telemetría Multi-IDE"]:::toolCard
            BOUND["verify_architecture_boundaries.py<br>Verificador AST de Imports"]:::toolCard
        end

        subgraph CROSS_GUARD ["Gobernanza Transversal SDD y Guardias Mecánicas"]
            direction LR
            HOOKS["Hooks Mecánicos PreToolUse<br>sdd_code_gate_guard.py<br>sdd_immutable_feature_guard.py"]:::guardCard
            LOCKS["Bloqueos de Puerta (Fail-Closed)<br>RN-SDD-GATE00-STACK-LOCK<br>RN-SDD-GATE2-CODE-LOCK<br>RN-SDD-IMMUTABLE-DONE"]:::guardCard
            LIMITS["Límites Estrictos de Modularidad<br>Techo Duro: 800 líneas/fichero<br>Alerta: 500 líneas/fichero"]:::guardCard
            SEMA["Semáforo de Salud de Contexto<br>Máx 15 Turnos / 2 Bloques DAG<br>Telemetría de Turno y Sesión"]:::guardCard
        end
    end

    %% Enlaces de Proceso y Gobernanza
    L0_IDE ==>|"Prompt y Contexto"| L1_CORE
    L1_CORE ==>|"1. Planifica DAG y Despacha Tareas"| L2_BUILD
    L2_BUILD -.->|"2. Peticiones de Revisión de Código"| L3_SPEC
    L3_SPEC -.->|"3. Comandos de Verificación DoD"| L5_TOOL
    CROSS_GUARD -.-|"Intercepción Mecánica en Cada Tool Call"| L2_BUILD
    CROSS_GUARD -.-|"Control de Puertas SDD"| L1_CORE
    L4_CAT -.->|"Materializa en Bootstrap"| L2_BUILD

    %% Estilos de Contenedores de Capa (ProcessOn Aesthetic)
    style SYSTEM fill:#f8fafc,stroke:#94a3b8,stroke-width:2px,color:#0f172a
    style L0_IDE fill:#f1f5f9,stroke:#cbd5e1,stroke-width:1.5px,color:#334155
    style L1_CORE fill:#eef2ff,stroke:#a5b4fc,stroke-width:2px,color:#312e81
    style L2_BUILD fill:#ecfdf5,stroke:#6ee7b7,stroke-width:2px,color:#065f46
    style L3_SPEC fill:#f0fdfa,stroke:#5eead4,stroke-width:2px,color:#115e59
    style L3A_UNIV fill:#ffffff,stroke:#99f6e4,stroke-width:1px,color:#134e4a
    style L3B_STACK fill:#ffffff,stroke:#fde68a,stroke-width:1px,color:#78350f
    style L4_CAT fill:#f5f3ff,stroke:#c4b5fd,stroke-width:2px,color:#5b21b6
    style L5_TOOL fill:#f0f9ff,stroke:#7dd3fc,stroke-width:2px,color:#075985
    style CROSS_GUARD fill:#fff1f2,stroke:#fda4af,stroke-width:2px,color:#9f1239
```

---

### 🚀 Cómo Iniciar un Nuevo Proyecto a partir de este Template

#### Paso 1: Clonar o Usar este Template
Crea un nuevo repositorio privado en GitHub a partir de esta plantilla:
```bash
gh repo create mi-nuevo-proyecto --template serchodm/sdd-agentic-starter --private
cd mi-nuevo-proyecto
```

#### Paso 2: El Repositorio Inicia BLOQUEADO (`Gate 00: Stack Lock`)
Para garantizar orden arquitectónico y compatibilidad, **el código de producción en `src/` está estrictamente bloqueado** por la regla `RN-SDD-GATE00-STACK-LOCK`. No se puede escribir código de producción ni tests hasta definir formalmente las tecnologías, el hosting, el Ownership Map y el escuadrón agéntico.

#### Paso 3: Habla con el `@orchestrator` en tu Asistente IA
Abre tu asistente de programación (Antigravity, Cursor, Claude Code, Windsurf o Codex) y comienza con:
> *"Hola @orchestrator. Iniciamos un nuevo proyecto en `sdd-agentic-starter`. Activa el asistente interactivo de Gate 00 para definir la topología, arquitectura, stack, agentes y convenciones."*

El `@orchestrator`:
1. Desplegará el **Asistente Interactivo de Gate 00 (`sdd-bootstrap`)** con poda dinámica en árbol:
   - **Infraestructura y Hosting**: Cloud Pública (AWS/Azure/GCP), Contenedores Docker o PaaS modernas (**Vercel**, Netlify, Railway).
   - **Alcance y Poda Dinámica**: Omite automáticamente preguntas irrelevantes (ej: sin estilos si es solo API, o sin backend si es SPA estática).
   - **Ownership Map (§3.2)**: Configura las fronteras deterministas de código, asignando cada zona física a un agente constructor con sus imports prohibidos y comandos DoD.
   - **Activación de Stack Packs**: Activa bajo demanda los paquetes de lenguaje, framework y capacidad desde `.sdd/catalog/packs/`.
   - **Comandos Deterministas de DoD (§2.5)**: Congela los comandos verificados de linting, pruebas unitarias acotadas (<1s en memoria), integración y build para eliminar el overhead de descubrimiento.
   - **Entorno Local**: Genera la configuración inicial de `docker-compose.yml` o `vercel.json`.
2. Rellenará formalmente **`specs/STACK.md`** y compilará el escuadrón con `python scripts/sdd_agent_generator.py --materialize`.
3. Te solicitará tu firma humana expresa: `[x] Gate 00 Approved (Human Sign-off)`.
4. Una vez aprobada, el código en `src/` se desbloqueará y comenzará el ciclo normal de desarrollo (Gate 0 -> Gate 5).

---

### 🏛️ El Ciclo de Vida SDD (Gate 00 a Gate 5)

El desarrollo sigue una progresión rigurosa de compuertas de calidad. Queda prohibido escribir código antes de aprobar Gate 2 y Gate 3, y ninguna tarea se considera terminada sin documentación viva.

```mermaid
flowchart TD
    classDef gateCard fill:#ffffff,stroke:#6366f1,stroke-width:2px,color:#1e1b4b,rx:5px,font-weight:bold,font-size:12px;
    classDef humanCard fill:#ffffff,stroke:#f59e0b,stroke-width:2px,color:#78350f,rx:5px,font-weight:bold,font-size:12px;
    classDef execCard fill:#ffffff,stroke:#10b981,stroke-width:2px,color:#064e3b,rx:5px,font-weight:bold,font-size:12px;
    classDef doneCard fill:#ffffff,stroke:#e11d48,stroke-width:2px,color:#881337,rx:5px,font-weight:bold,font-size:12px;

    G00["Gate 00: Stack Lock (specs/STACK.md)<br>• Topología y Hosting Definidos<br>• Ownership Map y Comandos DoD Configurados<br>• Stack Packs Materializados en .agents/"]:::gateCard
    H00{"Firma Humana<br>[x] Gate 00 Approved"}:::humanCard
    G0["Gate 0: Backlog Intake<br>• Registro de FEAT-XXX en specs/BACKLOG.md<br>• Inicialización de specs/features/FEAT-XXX/"]:::gateCard
    G1["Gate 1: Especificación Funcional (01-spec.md)<br>• Redactado por @functional-analyst<br>• Sintaxis formal EARS (Ubiquitous, Event, State)<br>• Criterios de Aceptación BDD Given-When-Then"]:::gateCard
    H1{"Firma Humana<br>[x] Gate 1 Approved"}:::humanCard
    G2["Gate 2: Especificación Técnica (02-tech-spec.md)<br>• Diseñado por @architect<br>• Contratos simétricos API y schemas DTO<br>• Registro de Decisiones de Arquitectura (ADRs)"]:::gateCard
    H2{"Firma Humana<br>[x] Gate 2 Approved"}:::humanCard
    G3["Gate 3: Grafo de Tareas DAG (03-tasks.md)<br>• Estructurado por @orchestrator<br>• Bloques de dependencia [PARALLEL] y [SEQUENTIAL]<br>• Definition of Ready (DoR): Agente, Zona, Comando DoD"]:::gateCard
    H3{"Firma Humana<br>[x] Gate 3 Approved"}:::humanCard
    G4["Gate 4: Ejecución y Verificación<br>• Despacho vía .agent-inbox/<agente>/<br>• Constructores implementan en sus zonas exclusivas<br>• Especialistas ECC auditan código y corrigen fallos<br>• @qa-tester ejecuta baterías de regresión"]:::execCard
    G5["Gate 5: Deuda Cero de Documentación (0DD)<br>• Ejecutado por @documentator<br>• Living docs bilingüe al día (docs/es/ y docs/en/)<br>• Catálogo de APIs y Modelos de Datos sincronizados<br>• Auditoría completa de TRACEABILITY-MATRIX.md"]:::gateCard
    DONE["DONE: Línea Base Inmutable<br>• specs/features/FEAT-XXX/ pasa a SOLO LECTURA<br>• Línea base RN-SDD-IMMUTABLE-DONE fijada<br>• Push de rama y PR a develop (RN-SDD-BRANCH-SYNC)"]:::doneCard

    G00 --> H00 --> G0 --> G1 --> H1 --> G2 --> H2 --> G3 --> H3 --> G4 --> G5 --> DONE
```

---

### 📦 Catálogo Inerte vs. Runtime Activo (Cero Sobrecarga de Tokens)

Para blindar la ventana de contexto del modelo frente al agotamiento de tokens y mantener disponibles más de 49 roles especializados, el framework utiliza una **separación inerte de catálogo**:

```mermaid
flowchart LR
    classDef catCard fill:#ffffff,stroke:#8b5cf6,stroke-width:1.5px,color:#4c1d95,rx:5px,font-size:12px;
    classDef genCard fill:#ffffff,stroke:#f59e0b,stroke-width:2px,color:#78350f,rx:5px,font-weight:bold,font-size:12px;
    classDef liveCard fill:#ffffff,stroke:#10b981,stroke-width:2px,color:#064e3b,rx:5px,font-weight:bold,font-size:12px;

    subgraph INERT [".sdd/catalog/ (CATÁLOGO INERTE · 0 TOKENS CONSUMIDOS)"]
        direction TB
        ARQC["18 Arquetipos de Capa<br>(domain, infra, api, db, test, tier, mobile, cli)"]:::catCard
        SPECC["20 Especialistas Universales ECC<br>(seguridad, fallos silenciosos, TDD, explorers, GAN)"]:::catCard
        PACKC["18 Stack Packs<br>(Python, TS, C#, Go, Rust, Java, React, Vue, BD, IA)"]:::catCard
        SKILLSC["314+ Skills Especializadas<br>(fastapi, react-perf, postgres, testing...)"]:::catCard
    end

    GEN["sdd_agent_generator.py<br>--materialize<br>Compilador de Ownership Map"]:::genCard

    subgraph RUNTIME [".agents/ (RUNTIME ACTIVO · DESCUBIERTO POR EL IDE)"]
        direction TB
        COREA["Capa 1: Escuadrón Core<br>(orchestrator, functional-analyst, architect,<br>qa-tester, documentator, devops)"]:::liveCard
        BUILDA["Capa 2: Constructores Materializados<br>(compilados estrictamente según el Ownership Map)"]:::liveCard
        SPECA["Capa 3: Especialistas Activos<br>(universales + revisores de packs seleccionados)"]:::liveCard
        OVERA[".agents/overrides/<br>(reglas de dominio específicas y overrides)"]:::liveCard
    end

    INERT -->|"1. Lee Recetas del Catálogo"| GEN
    GEN -->|"2. Emite squad.lock.json y Agentes"| RUNTIME

    style INERT fill:#f5f3ff,stroke:#c4b5fd,stroke-width:2px,color:#5b21b6
    style RUNTIME fill:#ecfdf5,stroke:#6ee7b7,stroke-width:2px,color:#065f46
```

1. **`.sdd/catalog/` (Catálogo Inerte)**: Reside fuera de `.agents/`. Los asistentes IA no lo inspeccionan de forma recursiva, consumiendo **0 tokens** durante las sesiones normales de trabajo.
2. **`.agents/` (Runtime Activo de Sesión)**: Contiene únicamente el escuadrón materializado para tu proyecto.
3. **`.agents/overrides/` (Personalizaciones del Proyecto)**: Coloca aquí instrucciones de dominio específicas (ej: `.agents/overrides/back-domain.md`). El generador respetará tus overrides sin ensuciar la plantilla upstream.

---

### 👥 Catálogo Completo de Agentes y Especialistas (49 Especialistas)

#### 1. Escuadrón Core de Gobernanza (6 Agentes Fijos)
| Agente | Rol Principal | Límite de Autoridad | Consulta Obligatoria |
| :--- | :--- | :--- | :--- |
| **`@orchestrator`** | Tech Lead, Scrum Master y Gatekeeper SDD | Planifica el DAG, despacha a `.agent-inbox/`. **Cero código en `src/`**. | `specs/BACKLOG.md`, `specs/STACK.md` |
| **`@functional-analyst`**| Estratega de Producto e Ingeniero de Requisitos | Redacta `01-spec.md` con EARS formal y BDD Given-When-Then. | `specs/SYSTEM_VISION.md` |
| **`@architect`** | Arquitecto de Software y Diseñador de APIs | Diseña `02-tech-spec.md`, contratos DTO, schemas DDL y ADRs. | `specs/STACK.md`, `docs/knowledge/` |
| **`@qa-tester`** | QA Lead y Auditor de Calidad | Ejecuta suites de pruebas, audita cobertura de mutación y verifica compuertas. | Gate 1 Given-When-Then |
| **`@documentator`** | Custodio de Living Docs 0DD | Mantiene la documentación viva bilingüe (`docs/es/`, `docs/en/`), catálogo de APIs y matriz. | `docs/`, `specs/` |
| **`@devops`** | Especialista en DevOps, Contenedores y CI/CD | Gestiona Docker, Kubernetes, Vercel/PaaS y scripts de despliegue. | `.github/`, `docker-compose.yml` |

#### 2. Especialistas Universales ECC (20 Agentes — Siempre Disponibles)
| Agente | Fase del SDD | Especialización y Misión |
| :--- | :--- | :--- |
| **`@code-explorer`** | Descubrimiento (Gate 0/1) | Trazador de flujos de ejecución end-to-end en solo lectura y mapa de dependencias. |
| **`@spec-miner`** | Descubrimiento (Gate 0/1) | Extractor de especificaciones latentes y restricciones en código existente. |
| **`@docs-lookup`** | Descubrimiento (Gate 0/1) | Búsqueda quirúrgica y lectura en documentación oficial de frameworks. |
| **`@code-architect`** | Diseño (Gate 2) | Diseñador de blueprints de implementación, límites de módulos y orden de compilación. |
| **`@type-design-analyzer`**| Diseño (Gate 2) | Auditor de tipado estricto; elimina `any`, casts inseguros y fugas de tipos en fronteras. |
| **`@tdd-guide`** | Ejecución (Gate 4) | Guía de Test-Driven Development; asegura ciclos Red-Green-Refactor rigurosos. |
| **`@build-error-resolver`**| Ejecución (Gate 4) | Reparador quirúrgico de errores de compilación y tests mediante el diff mínimo absoluto. |
| **`@security-reviewer`** | Auditoría (Gate 4) | Auditor OWASP Top 10, política de cero secretos y prevención de path-traversal. |
| **`@silent-failure-hunter`**| Auditoría (Gate 4) | Caza de errores silenciados (`catch {}`, `except: pass`), fallbacks engañosos y promesas huérfanas. |
| **`@performance-optimizer`**| Auditoría (Gate 4) | Detección de fugas de memoria, optimización de I/O asíncrono y eliminación de cuellos de botella. |
| **`@e2e-runner`** | Auditoría (Gate 4) | Ejecutor de flujos críticos End-to-End con Playwright/CLI; erradicación de tests flaky. |
| **`@pr-test-analyzer`** | Auditoría (Gate 4) | Análisis de cobertura y resiliencia de tests en pull requests. |
| **`@comment-analyzer`** | Auditoría (Gate 4) | Detección de comentarios obsoletos, documentación engañosa y TODOs podridos. |
| **`@code-simplifier`** | Higiene (Gate 4) | Simplificador post-implementación; eliminación de código muerto y reducción de complejidad. |
| **`@refactor-cleaner`** | Higiene (Gate 4) | Limpieza de imports no usados, helpers huérfanos y sintaxis obsoleta. |
| **`@gan-planner`** | Arnés GAN | Descompone entregables complejos en especificaciones para el generador adversarial. |
| **`@gan-generator`** | Arnés GAN | Produce implementaciones robustas respondiendo a la crítica adversarial. |
| **`@gan-evaluator`** | Arnés GAN | Evalúa entregables frente a una rúbrica ponderada (puntuación mínima de pase >= 8.5/10). |
| **`@conversation-analyzer`**| Aprendizaje | Extrae instintos atómicos (`continuous-learning-v2`) de las sesiones para `/learn` y `/evolve`. |
| **`@opensource-sanitizer`** | Higiene | Sanitiza nombres propietarios, credenciales y rutas locales antes de sincronizar con el framework. |

#### 3. Especialistas Dinámicos de Stack (29 Agentes en 18 Packs)
| Stack Pack | Agentes Incluidos | Misión y Responsabilidades |
| :--- | :--- | :--- |
| **`lang-python`** | `@python-reviewer` | Python 3.12+, tipado estático (`mypy`), seguridad con `asyncio`, inmutabilidad `dataclass(frozen=True)`. |
| **`framework-fastapi`** | `@fastapi-reviewer` | Routers asíncronos FastAPI, inyección `Depends`, DTOs Pydantic v2 camelCase, SSE/WebSocket lifespan. |
| **`framework-django`** | `@django-reviewer`<br>`@django-build-resolver` | Prevención de N+1 en Django ORM, seguridad CSRF/auth, tareas Celery, reparación de migraciones. |
| **`lang-typescript`** | `@typescript-reviewer` | TypeScript estricto, runtime Node/Bun, segregación de interfaces, `tsconfig` moderno. |
| **`framework-react`** | `@react-reviewer`<br>`@react-build-resolver` | React 19, dependencias de hooks (`useCallback`/`useMemo`), fluidez a 60 FPS, reparación de builds Vite. |
| **`framework-vue`** | `@vue-reviewer` | Vue 3 Composition API, stores Pinia, hidratación SSR en Nuxt 4, guardias en Vue Router. |
| **`lang-csharp`** | `@csharp-reviewer` | C# .NET 9, Nullable Reference Types, EF Core `AsNoTracking`, `ValueTask` asíncrono, scopes de DI. |
| **`lang-go`** | `@go-reviewer`<br>`@go-build-resolver` | Go idiomático, table-driven tests, prevención de fugas de goroutines, resolución de conflictos en `go.mod`. |
| **`lang-rust`** | `@rust-reviewer`<br>`@rust-build-resolver` | Borrow checker, seguridad de memoria en Rust, `Result`/`Option`, reparación de compilación en `cargo`. |
| **`lang-java`** | `@java-reviewer`<br>`@java-build-resolver` | Java 21+, Spring Boot 3, consultas Hibernate/JPA, resolución de fallos en Gradle/Maven. |
| **`lang-kotlin`** | `@kotlin-reviewer`<br>`@kotlin-build-resolver` | Corrutinas/flujos Kotlin, Ktor, Exposed ORM, Compose Multiplatform, reparación de Gradle Kotlin. |
| **`lang-swift`** | `@swift-reviewer`<br>`@swift-build-resolver` | Swift 6+, aislamiento de Actores, tipos `Sendable`, ciclo de vida SwiftUI, reparaciones en `xcodebuild`. |
| **`lang-dart`** | `@flutter-reviewer`<br>`@dart-build-resolver` | Árboles de widgets Flutter, estado reactivo (Riverpod/Bloc), layouts a 60 FPS, reparación en `dart analyze`. |
| **`lang-cpp`** | `@cpp-reviewer`<br>`@cpp-build-resolver` | C++20, RAII, punteros inteligentes (`std::unique_ptr`), prevención de fugas, reparación de builds CMake. |
| **`capability-database`** | `@database-reviewer` | Consultas SQL, índices HNSW/GIN/B-Tree, prevención de N+1, pooling asíncrono, migraciones DDL idempotentes. |
| **`capability-web-frontend`**| `@a11y-architect`<br>`@seo-specialist` | Accesibilidad WCAG 2.1 AA, navegación por teclado, roles WAI-ARIA, OpenGraph, Core Web Vitals, JSON-LD. |
| **`capability-ai-llm`** | `@rag-pipeline-reviewer`<br>`@mle-reviewer`<br>`@pytorch-build-resolver` | Chunking/re-ranking en RAG, mitigación de alucinaciones, entrenamiento ML reproducible, reparación de tensores PyTorch. |

---

### 🗺️ El Ownership Map y Ejecución Paralela sin Colisiones de Escritura

Definido en `specs/STACK.md §3.2`, el Ownership Map es la **fuente única de verdad** de permisos de código. Asigna cada directorio de código a un único agente constructor, posibilitando la ejecución paralela en el DAG sin colisiones ni condiciones de carrera:

```yaml
ownership:
  preset: granular-backend+compact-frontend
  zones:
    - id: backend-domain
      paths: ["src/backend/domain/**", "src/backend/application/**"]
      owner: back-domain
      archetype: layer-domain
      forbid_imports: ["fastapi", "sqlalchemy", "sqlmodel", "infrastructure", "api"]
      dod: { typecheck: "uv run mypy src/backend/domain", unit: "uv run pytest tests/unit/domain -q" }
    - id: backend-infra
      paths: ["src/backend/infrastructure/**"]
      owner: back-infra
      archetype: layer-infra
      dod: { integration: "uv run pytest tests/integration -q" }
    - id: backend-api
      paths: ["src/backend/api/**"]
      owner: back-api
      archetype: layer-api
      forbid_imports: ["sqlalchemy", "sqlmodel"]
      dod: { unit: "uv run pytest tests/unit/api -q" }
    - id: frontend
      paths: ["src/frontend/**"]
      owner: front-engineer
      archetype: tier-frontend
      dod: { typecheck: "npx tsc --noEmit", build: "npm run build" }
  unowned_policy: fail-closed
```

```mermaid
flowchart TD
    classDef orchCard fill:#ffffff,stroke:#6366f1,stroke-width:2px,color:#1e1b4b,rx:5px,font-weight:bold,font-size:12px;
    classDef taskCard fill:#ffffff,stroke:#0284c7,stroke-width:1.5px,color:#0369a1,rx:5px,font-size:12px;
    classDef agentCard fill:#ffffff,stroke:#10b981,stroke-width:2px,color:#064e3b,rx:5px,font-weight:bold,font-size:12px;
    classDef zoneCard fill:#ffffff,stroke:#f59e0b,stroke-width:1.5px,color:#78350f,rx:5px,font-size:12px;
    classDef guardCard fill:#ffffff,stroke:#e11d48,stroke-width:2px,color:#881337,rx:5px,font-weight:bold,font-size:12px;

    ORCH["@orchestrator<br>Parsea Bloque [PARALLEL] en 03-tasks.md"]:::orchCard

    subgraph INBOX [".agent-inbox/ Despacho Concurrente"]
        direction LR
        T1["Tarea 4.1: Modelos Dominio<br>Asignado: @back-domain"]:::taskCard
        T2["Tarea 4.2: Migraciones BD<br>Asignado: @db-specialist"]:::taskCard
        T3["Tarea 4.3: Componentes UI<br>Asignado: @front-ui"]:::taskCard
    end

    subgraph BUILDERS ["Especialistas Constructores Ejecutando en Paralelo"]
        direction LR
        A1["@back-domain"]:::agentCard
        A2["@db-specialist"]:::agentCard
        A3["@front-ui"]:::agentCard
    end

    subgraph ZONES ["Zonas Exclusivas del Ownership Map (specs/STACK.md)"]
        direction LR
        Z1["Zona: backend-domain<br>src/backend/domain/**<br>Prohíbe: fastapi, sqlalchemy"]:::zoneCard
        Z2["Zona: backend-db<br>src/backend/infrastructure/db/**<br>migrations/**"]:::zoneCard
        Z3["Zona: frontend-ui<br>src/frontend/components/**<br>Prohíbe: imports de backend"]:::zoneCard
    end

    subgraph GUARD ["Intercepción Mecánica PreToolUse (sdd_code_gate_guard.py)"]
        direction TB
        CHK{"¿Agente autorizado<br>en la ruta destino?"}:::guardCard
        ALLOW["✅ Tool Call Permitido<br>Edición Aplicada con Éxito"]:::agentCard
        DENY["🛑 Tool Call Denegado (Exit 1)<br>Protección de Frontera Fail-Closed"]:::guardCard
    end

    ORCH ==>|"Despacha tickets paralelos"| INBOX
    T1 --> A1
    T2 --> A2
    T3 --> A3
    A1 ==>|"Escribe exclusivamente en"| Z1
    A2 ==>|"Escribe exclusivamente en"| Z2
    A3 ==>|"Escribe exclusivamente en"| Z3
    Z1 -.->|"Evento Tool Call"| CHK
    Z2 -.->|"Evento Tool Call"| CHK
    Z3 -.->|"Evento Tool Call"| CHK
    CHK -->|"Coincide con Zona"| ALLOW
    CHK -->|"Fuera de Zona / No Asignado"| DENY

    style INBOX fill:#f0f9ff,stroke:#7dd3fc,stroke-width:2px,color:#075985
    style BUILDERS fill:#ecfdf5,stroke:#6ee7b7,stroke-width:2px,color:#065f46
    style ZONES fill:#fef3c7,stroke:#fcd34d,stroke-width:2px,color:#78350f
    style GUARD fill:#fff1f2,stroke:#fda4af,stroke-width:2px,color:#9f1239
```

- **Guardia Mecánica por Hook**: El hook `PreToolUse` (`sdd_code_gate_guard.py`) consulta `.agents/active_work_item.json`. Si un agente intenta editar ficheros fuera de su zona asignada, la acción es **inmediatamente bloqueada**.
- **Verificación de Fronteras Arquitectónicas**: Ejecuta `python .agents/scripts/verify_architecture_boundaries.py` para auditar imports prohibidos entre capas mediante inspección AST.

---

### 🧪 Motores Duales de Verificación de Calidad: Método Santa y Arnés GAN

Para eliminar "tests verdes sospechosos", complacencia y sesgos de confirmación en entregas complejas, el framework incorpora dos motores de verificación de alta rigurosidad adaptados de Everything Claude Code:

```mermaid
flowchart TD
    classDef startCard fill:#ffffff,stroke:#6366f1,stroke-width:2px,color:#1e1b4b,rx:5px,font-weight:bold,font-size:12px;
    classDef revCard fill:#ffffff,stroke:#0d9488,stroke-width:1.5px,color:#134e4a,rx:5px,font-size:12px;
    classDef checkCard fill:#ffffff,stroke:#f59e0b,stroke-width:2px,color:#78350f,rx:5px,font-weight:bold,font-size:12px;
    classDef passCard fill:#ffffff,stroke:#10b981,stroke-width:2px,color:#064e3b,rx:5px,font-weight:bold,font-size:12px;
    classDef failCard fill:#ffffff,stroke:#e11d48,stroke-width:2px,color:#881337,rx:5px,font-weight:bold,font-size:12px;

    subgraph SANTA ["Motor A: El Método Santa ('Checking It Twice' · /santa-loop)"]
        direction TB
        DELIV_A["Entregable de Tarea Enviado"]:::startCard
        subgraph ISOLATED ["Revisores Duales Aislados (Independientes y Paralelos)"]
            direction LR
            REV1["Revisor 1<br>(Seguridad y Corrección)"]:::revCard
            REV2["Revisor 2<br>(Tipado y Manejo de Errores)"]:::revCard
        end
        VERDICT{"¿Consenso Unánime?<br>Ambos Veredictos == NICE"}:::checkCard
        CERT_A["✅ Entregable Certificado<br>Supera Gate 4"]:::passCard
        REWORK_A["❌ Cambios Requeridos<br>Bucle de Vuelta al Constructor"]:::failCard

        DELIV_A --> ISOLATED
        REV1 --> VERDICT
        REV2 --> VERDICT
        VERDICT -->|"Ambos NICE"| CERT_A
        VERDICT -->|"Cualquier Fallo"| REWORK_A
        REWORK_A -.->|"Entregable Corregido"| DELIV_A
    end

    subgraph GAN ["Motor B: Arnés Adversarial Estilo GAN (/gan-build)"]
        direction TB
        PLAN["@gan-planner<br>Formula Blueprint del Entregable<br>y Rúbrica Ponderada de Evaluación"]:::startCard
        GEN["@gan-generator<br>Produce Código Blindado<br>Bajo Crítica Adversarial"]:::revCard
        EVAL["@gan-evaluator<br>Puntúa Objetivamente el Entregable<br>Rúbrica: Arquitectura, Seguridad, DoD"]:::checkCard
        SCORE{"Puntuación de Evaluación<br>>= 8.5 / 10.0?"}:::checkCard
        CERT_B["✅ Entregable Aceptado<br>Estándar Riguroso Alcanzado"]:::passCard
        CRITIQUE["❌ Crítica Adversarial<br>Feedback Accionable de Defectos"]:::failCard

        PLAN --> GEN
        GEN --> EVAL
        EVAL --> SCORE
        SCORE -->|"Pasa (Puntuación >= 8.5)"| CERT_B
        SCORE -->|"Falla (Puntuación < 8.5)"| CRITIQUE
        CRITIQUE -.->|"Refinar Código"| GEN
    end

    style SANTA fill:#f0fdfa,stroke:#5eead4,stroke-width:2px,color:#115e59
    style ISOLATED fill:#ffffff,stroke:#99f6e4,stroke-width:1px,color:#134e4a
    style GAN fill:#eef2ff,stroke:#a5b4fc,stroke-width:2px,color:#312e81
```

1. **El Método Santa (`/santa-loop`)**: Inspirado en el proverbio ("Hacer la lista y revisarla dos veces"). Un entregable debe recibir un veredicto unánime **`NICE`** de dos revisores completamente independientes y aislados antes de superar Gate 4.
2. **Arnés Adversarial Estilo GAN (`/gan-build`)**: Despliega una arquitectura generador-evaluador. `@gan-planner` establece una rúbrica objetiva, `@gan-generator` produce el código y `@gan-evaluator` lo puntúa rigurosamente hasta superar una nota de corte de **>= 8.5 / 10.0**.

---

### 🧠 Continuous Learning v2 y Motor de Evolución de Instintos

El framework cuenta con un ciclo de aprendizaje continuo basado en el motor de Instintos Atómicos de ECC (`continuous-learning-v2`), convirtiendo descubrimientos y soluciones de sesión en conocimiento institucional permanente:

```mermaid
flowchart LR
    classDef sessCard fill:#ffffff,stroke:#64748b,stroke-width:1.5px,color:#0f172a,rx:5px,font-size:12px;
    classDef learnCard fill:#ffffff,stroke:#6366f1,stroke-width:2px,color:#1e1b4b,rx:5px,font-weight:bold,font-size:12px;
    classDef instCard fill:#ffffff,stroke:#f59e0b,stroke-width:1.5px,color:#78350f,rx:5px,font-size:12px;
    classDef ruleCard fill:#ffffff,stroke:#10b981,stroke-width:2px,color:#064e3b,rx:5px,font-weight:bold,font-size:12px;

    subgraph SESSION ["Sesión de Ingeniería"]
        S1["Depuración, Refactorización<br>o Descubrimiento Arquitectónico"]:::sessCard
        S2["Patrón Reutilizable o<br>Solución de Framework Detectada"]:::sessCard
        S1 --> S2
    end

    subgraph LEARN ["Disparador /learn"]
        ANALYZER["@conversation-analyzer<br>Extrae Patrón Atómico"]:::learnCard
    end

    subgraph INSTINCTS ["Pool de Instintos (continuous-learning-v2)"]
        direction TB
        I1["Instinto #1<br>Confianza: 0.3 (Candidato)"]:::instCard
        I2["Instinto #2<br>Confianza: 0.6 (Reforzado)"]:::instCard
        I3["Instinto #3<br>Confianza: 0.9 (Consolidado)"]:::instCard
        I1 -.->|"Éxito Repetido"| I2
        I2 -.->|"Validación Inter-Sesión"| I3
    end

    subgraph EVOLVE ["Disparador /evolve"]
        EVOLVER["Motor de Evolución de Instintos<br>Agrupa Patrones Afines de Alta Confianza"]:::learnCard
    end

    subgraph PERM ["Activos Permanentes del Repositorio"]
        R1[".agents/rules/*.md<br>Reglas de Proyecto de Obligado Cumplimiento"]:::ruleCard
        R2[".agents/skills/*.md<br>Skills Autónomas Reutilizables"]:::ruleCard
    end

    S2 ==>|"Ejecuta /learn"| ANALYZER
    ANALYZER ==>|"Persiste instinto atómico"| I1
    I3 ==>|"Confianza >= 0.75"| EVOLVER
    EVOLVER ==>|"Genera"| R1
    EVOLVER ==>|"Empaqueta"| R2

    style SESSION fill:#f8fafc,stroke:#cbd5e1,stroke-width:1.5px,color:#334155
    style LEARN fill:#eef2ff,stroke:#a5b4fc,stroke-width:2px,color:#312e81
    style INSTINCTS fill:#fef3c7,stroke:#fcd34d,stroke-width:2px,color:#78350f
    style EVOLVE fill:#eef2ff,stroke:#a5b4fc,stroke-width:2px,color:#312e81
    style PERM fill:#ecfdf5,stroke:#6ee7b7,stroke-width:2px,color:#065f46
```

- **Puntuación de Confianza (`0.3` a `0.9`)**: Los patrones candidatos se registran con confianza `0.3`. Conforme el patrón se valida en subsiguientes sesiones, su confianza asciende a `0.6` y `0.9`.
- **Evolución Automática (`/evolve`)**: Al alcanzar confianza `>= 0.75`, el motor agrupa instintos semánticamente relacionados y sintetiza reglas `.agents/rules/*.md` o skills modulares `.agents/skills/*.md` de forma totalmente automatizada.

---

### 🔄 Los 12 Workflows de Comandos Slash

| Categoría | Comando | Agentes Asignados | Descripción |
| :--- | :--- | :--- | :--- |
| **Ciclo de Vida** | `/pipeline-run` | Orchestrator y Especialistas | Ejecuta de forma autónoma el pipeline de desarrollo SDD para una feature aprobada. |
| | `/opsx-delegate` | Orchestrator | El Tech Lead delega tareas atómicas a `.agent-inbox/<agente>/` aplicando DoR estricto. |
| | `/opsx-pickup` | Especialista Constructor | Recoge su tarea asignada, audita DoR, implementa código y valida DoD. |
| | `/gate5` | `@documentator` | Sesión dedicada y económica para living docs bilingüe y sincronización Git. |
| **Sesión** | `/checkpoint` | Estado de Sesión | Guarda las tareas pendientes en `.agents/ACTIVE_STATE.md` y prepara un traspaso de sesión limpio. |
| | `/continue` | Sesión Limpia | Reanuda el trabajo en un hilo limpio con contexto acotado (máx 4 ficheros), reiniciando turnos a `1/15`. |
| **Calidad** | `/santa-loop` | Revisores Independientes | Método Santa ("Checking It Twice"): bucle de revisión hasta lograr veredicto unánime NICE de dos revisores aislados. |
| | `/gan-build` | `@gan-planner` → `@gan-generator` → `@gan-evaluator` | Bucle adversarial Generador-Evaluador para entregables complejos con rúbrica ponderada (>= 8.5/10). |
| | `/build-fix` | Build Error Resolvers | Repara errores de compilación, linter o tests aplicando el diff mínimo quirúrgico. |
| | `/harness-audit` | Auditor del Arnés | Audita la salud de reglas, agentes, tickets en inbox y cumplimiento de fronteras. |
| **Aprendizaje** | `/learn` | Continuous Learning v2 | Extrae instintos atómicos de la sesión hacia `skills/` o `rules/`. |
| | `/evolve` | Motor de Instintos | Agrupa instintos de alta confianza (>= 0.75) y los evoluciona hacia reglas o skills permanentes. |

---

### 🚦 Semáforo de Salud de Contexto y Telemetría de Tokens (`RN-SDD-CONTEXT-SEMAPHORE`)

Para erradicar bucles de alucinación y degradación de contexto en tareas extensas, el `@orchestrator` monitoriza turnos y tokens en cada turno:

```text
---
🟢/🟡/🔴 Context Health: Turn X/15 | Blocks: Y/2 | Gate: Z
    ↳ Tokens (Last Turn): In X.Xk · Out X.Xk · Cache X.Xk
    ↳ Tokens (Session Total): In X.Xk · Out X.Xk · Cache X.Xk (Hit: XX.X%)
```

- 🟢 **Verde (`Turno 1-10` | `Bloques 0-1`)**: Ventana de ejecución óptima.
- 🟡 **Amarillo (`Turno 11-14` | `Bloques 2`)**: Umbral de aviso. Preparar traspaso de sesión.
- 🔴 **Rojo (`Turno 15+` | `Bloques 3+`)**: **Parada Obligatoria (*Stop-the-Line*)**. Detiene el despacho y ejecuta `/checkpoint` para forzar un `/continue` en hilo limpio.

Inspecciona el consumo de tokens en Antigravity, Claude Code, Cursor, Windsurf, Codex o Roo Code en cualquier momento:
```bash
python .agents/scripts/sdd_token_usage.py
```

---

### ⚡ Herramientas Deterministas (Cero Sobrecarga de Descubrimiento)

1. **Generador Universal de Mapa AST (`sdd_repo_map.py`)**:
   Extrae jerarquías de clases, firmas de métodos, interfaces y tipos en más de 20 lenguajes sin descargar implementaciones completas:
   - TypeScript/JavaScript, Python, C# (.NET), Go, Rust, Java, Kotlin, Swift, Dart, C/C++, PHP, Ruby, etc.
   ```bash
   python .agents/scripts/sdd_repo_map.py src/
   ```
2. **Recortador Determinista de Terminal (`sdd_trim_exec.py`)**:
   Protege la ventana de contexto de la contaminación de logs de terminal:
   - En éxito (`exit 0`): Comprime más de 100 líneas a un resumen limpio de una sola línea (`✅ [DoD OK] ...`).
   - En fallo (`exit != 0`): Elimina ruido ANSI, aislando únicamente la traza del error, la aserción fallida y fichero/línea.
   ```bash
   python .agents/scripts/sdd_trim_exec.py pytest tests/unit/
   python .agents/scripts/sdd_trim_exec.py npm test
   ```
3. **Verificador de Fronteras Arquitectónicas (`verify_architecture_boundaries.py`)**:
   Audita imports prohibidos según las reglas declaradas en `specs/STACK.md §3.2`.
   ```bash
   python .agents/scripts/verify_architecture_boundaries.py
   ```

---

### 🛡️ Verificación de Salud del Framework

Audita la integridad mecánica de los agentes, reglas y scripts de gobernanza en cualquier momento:
```bash
uv run python .agents/scripts/sdd_healthcheck.py
```

---

### ⚖️ Avisos de Terceros y Atribución Open Source

Este proyecto incorpora, adapta o se inspira en obras de código abierto bajo licencias permisivas:
- **Everything Claude Code (ECC)**: Copyright (c) 2026 Affaan Mustafa ([https://github.com/affaan-m/ecc](https://github.com/affaan-m/ecc)), publicado bajo **Licencia MIT**. Los agentes revisores, baselines de prompt defense, build resolvers, motor de aprendizaje continuo v2 y paquetes de patrones han sido adaptados de ECC. Consulta el aviso legal completo en [`THIRD_PARTY_NOTICES.md`](file:///c:/Projects/sdd-agentic-starter/THIRD_PARTY_NOTICES.md).
- **Framework REA**: Inspiración en `morluto/rea` para las compuertas de gobernanza Fail-Closed, Boundary Ownership y Human Gate Ownership.
