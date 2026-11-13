---
name: sdd-bootstrap
description: Executes the interactive Gate S0 Bootstrap Wizard to define system topology, hosting (Cloud/Docker/Vercel/PaaS), architecture, backend, frontend, persistence, testing, DevOps CI/CD, and project-specific expert agent activation in specs/STACK.md. Supports Spanish (ES-ES) and English (EN-GB).
---

# Skill: `sdd-bootstrap` (Gate S0 Architectural Bootstrap Wizard)

Used by `@orchestrator` to execute the mandatory **Gate S0 Bootstrap Session** before any code or feature specifications are created.

## 🎯 Purpose
Guides the user through an atomic, multi-round decision process covering the entire software lifecycle (infrastructure, hosting, CI/CD, architecture, languages, quality gates, and agent squad configuration) to deterministically generate `specs/STACK.md` and unlock `src/`.

---

## 🌐 1. Multilingual Support: Spanish (ES-ES) & English (EN-GB)

The Bootstrap Wizard natively supports **Español (ES-ES)** and **English (EN-GB)**:
1. **Auto-Detection & Initial Selector**:
   - `@orchestrator` automatically detects the user's conversation language, or offers a language selector if ambiguous:
     - `Español (ES-ES)`: Formularios, preguntas, opciones y `specs/STACK.md` redactados en español formal y técnico.
     - `English (EN-GB)`: Questions, options, artefacts, and `specs/STACK.md` drafted in formal British English technical terminology.
2. **0DD Alignment**: Ensures immediate consistency with the living documentation structure (`docs/es/` and `docs/en/`).

---

## ⚡ 2. Trigger Conditions
1. **Unapproved Gate S0**: `specs/STACK.md` contains `[ ] Gate S0 Approved (Human Sign-off)` (or legacy `[ ] Gate 00 Approved (Human Sign-off)`).
2. **User Initiation**: The user requests project start:
   - *ES-ES*: *"Hola @orchestrator. Iniciamos un nuevo proyecto. Activa el asistente de Gate S0."*
   - *EN-GB*: *"Hello @orchestrator. We are starting a new project. Launch the Gate S0 Bootstrap Wizard."*
3. **Fail-Closed Intercept**: If the user asks to write production code or create features while Gate S0 is locked, `@orchestrator` intercepts and triggers this skill.

---

## 🌳 3. Decision Tree & Conditional Branching Rules (Dynamic Pruning)

To eliminate cognitive fatigue and avoid nonsensical questions, `@orchestrator` enforces **Dynamic Tree Pruning**:

| Condición Detectada | Preguntas Podadas (Omitidas) | Impacto en Escuadrón Agéntico |
| :--- | :--- | :--- |
| **`Solo Backend / API Only`** | Framework visual, Estilos CSS, Estado cliente, Tests UI, Vercel Previews, todas las preguntas `uiux` (`ui-ux-pro-max`, `hifi_format`, `brand_constraints`) | `@front-engineer` -> **INACTIVO / INACTIVE (N/A)**; no se activan `capability-ui-design` ni `@ui-ux-designer` |
| **`Solo Frontend / Client Only`** | Framework backend, DTOs backend, ORM, Migraciones BD, Testcontainers backend | `@back-engineer` -> **INACTIVO / INACTIVE (N/A)**; mantiene preguntas `uiux` activas |
| **`CLI / Herramienta Local`** | Frontend, Hosting serverless/cloud, Contenedores de hosting, Vercel, todas las preguntas `uiux` (`ui-ux-pro-max`, `hifi_format`, `brand_constraints`) | `@front-engineer` -> **INACTIVO / INACTIVE (N/A)**; no se activan `capability-ui-design` ni `@ui-ux-designer` |
| **`Persistencia: N/A (Stateless)`** | Motor BD, ORM/Micro-ORM, Migraciones de esquema, Testcontainers de BD | - |
| **`Hosting: Vercel / Netlify / Cloudflare`** | Orquestadores Kubernetes, Docker Swarm, Registries de contenedores | Flujo CI/CD orientado a GitOps y Previews por PR |
| **`Hosting: Air-Gapped / Aislado`** | CDNs remotas, Gestores de secretos en nube pública | Assets 100% locales, variables `.env` o Vault on-prem |

---

## 🇪🇸 4. Catálogo de Preguntas: Español (ES-ES)

### 📍 Ronda 1: Alcance Macro, Infraestructura, Hosting y DevOps
1. **Macro-Alcance del Proyecto**:
   - `(Recommended) Fullstack (Backend API + Frontend Web)`
   - `Solo Backend (API REST / gRPC / Microservicio)`
   - `Solo Frontend (SPA / Jamstack / Aplicación Web Client-side)`
   - `Herramienta de Consola / CLI / Script de Automatización`
2. **Destino de Hosting & Runtime**:
   - `(Recommended) Cloud Pública (AWS, Azure, GCP)`
   - `PaaS / Edge Serverless (Vercel, Netlify, Cloudflare Pages/Workers)`
   - `Contenedores en PaaS (Railway, Render, Fly.io)`
   - `On-Premise (Servidores corporativos / Datacenter propio)`
   - `Máquina Local del Usuario (CLI / Desktop)`
3. **Entorno de Red & Conectividad**:
   - `(Recommended) Red estándar con acceso libre a Internet`
   - `Red corporativa con Proxy o VPN obligatoria`
   - `Red Air-Gapped (100% aislada, sin internet en runtime)`
4. **Plataforma de CI/CD**:
   - `(Recommended) GitHub Actions`
   - `GitLab CI/CD`
   - `Azure DevOps Pipelines`
   - `Scripts locales / Makefile (sin CI automatizado remoto)`
5. **Estrategia de Despliegue y Previews**:
   - `(Recommended) GitOps con Previews automáticas en PRs + Producción en main (Vercel/PaaS)`
   - `Despliegue automatizado continuo (CD directo)`
   - `Despliegue manual tras aprobación humana`
   - `Solo empaquetado de artefactos (sin despliegue automático)`
6. **Puertas Obligatorias en CI** *(Selección Múltiple)*:
   - `(Recommended) Linter estricto y Typecheck`
   - `(Recommended) Suite de tests unitarios en memoria`
   - `(Recommended) Tests de integración con dependencias auxiliares`
   - `(Recommended) Build de producción y verificación de empaquetado`
   - `Escaneo de seguridad (SAST / Trivy / Dependabot)`

### 📍 Ronda 2: Arquitectura del Sistema, Backend y Frontend (Poda Dinámica)
1. **Patrón Arquitectónico Base**:
   - `(Recommended) Clean Architecture / Hexagonal (Puertos y Adaptadores)`
   - `Vertical Slice Architecture (Features independientes con comandos/queries)`
   - `Monolito Modular (Módulos de negocio delimitados con contratos formales)`
   - `Layered / N-Capas Tradicional (Controllers -> Services -> Repositories)`
   - `Minimal / Flat (KISS: estructura plana sin capas intermedias)`
2. **Manejo de Errores y Flujo de Control**:
   - `(Recommended) Result Pattern tipado (Railway: Result<T, Error> explícito)`
   - `Excepciones de Dominio Jerárquicas (capturadas en boundary HTTP/API)`
   - `Códigos de estado y respuestas JSON estándar`
3. **Backend: Lenguaje y Framework** *(Omitido si es Solo Frontend)*:
   - `(Recommended) Python 3.12+ con FastAPI`
   - `C# .NET 9 con ASP.NET Core`
   - `TypeScript / Node.js 22 con NestJS o Fastify`
   - `Java 21 LTS con Spring Boot 3`
   - `Go 1.23+ con Gin o Chi`
4. **Backend: Validación de DTOs** *(Contextualizado al lenguaje)*:
   - Python: `Pydantic v2` | C#: `FluentValidation` | TS: `Zod / class-validator` | Java: `Bean Validation` | Go: `Tags nativos`
5. **Frontend: Framework Visual** *(Omitido si es Solo Backend / CLI)*:
   - `(Recommended) React 19 + TypeScript + Vite`
   - `Vue 3 + TypeScript + Vite`
   - `Svelte 5 + TypeScript + Vite`
   - `Next.js / Nuxt (Fullstack SSR con despliegue en Vercel)`
   - `HTML5 + CSS3 Vanilla + Web Components (Cero dependencias)`
6. **Frontend: Estilos y UI**:
   - `(Recommended) TailwindCSS (Utility-First)`
   - `Librería UI Headless (shadcn/ui, Radix, PrimeVue)`
   - `CSS Vanilla con metodología BEM`
   - `CSS Modules / Sass`
7. **Frontend: Gestión de Estado**:
   - `(Recommended) Servidor como Fuente de Verdad + Cache (TanStack Query / SWR)`
   - `Store Global Ligero (Zustand en React / Pinia en Vue)`
   - `Estado Reactivo Nativo (Hooks / Composables / Signals)`
   - `Redux Toolkit (RTK)`
8. **Sincronización de Contratos**:
   - `(Recommended) OpenAPI / Swagger v3 con exportación de tipos TypeScript`
   - `tRPC (Tipado extremo a extremo TS sin schemas intermediarios)`
   - `gRPC / Protocol Buffers (.proto)`
   - `GraphQL Schema-First`
   - `DTOs manuales desacoplados`
9. **Frontend: Inteligencia Visual y Design System (`uiux`)** *(Omitido si es Solo Backend / CLI)*:
   - `(Recommended) Activar ui-ux-pro-max (packs: capability-web-frontend + capability-ui-design, proveedor vendorizado offline + @ui-ux-designer en Gate 2)`
   - `Solo skills ECC de frontend (capability-web-frontend con @a11y-architect, sin proveedor externo; uiux.enabled: false)`
10. **Frontend: Formato de Prototipos Hi-Fi (`uiux.hifi_format`)** *(Omitido si es Solo Backend / CLI o si `uiux.enabled: false`)*:
    - `(Recommended) html (HTML/CSS navegable verificable offline / browser-qa)`
    - `figma (Enlace y artefactos Figma gobernados)`
    - `html+figma (Híbrido: prototipo HTML/CSS navegable + enlace Figma)`
11. **Frontend: Restricciones de Marca (`uiux.brand_constraints`)** *(Omitido si es Solo Backend / CLI o si `uiux.enabled: false`)*:
    - `(Recommended) Ninguna (sin fichero de marca previo)`
    - `Ruta relativa en el repositorio (p. ej. docs/design-system/BRAND.md)`

### 📍 Ronda 3: Persistencia, Calidad, Seguridad, Golden Samples y Agentes
1. **Motor de Base de Datos** *(Omitido si es Stateless)*:
   - `(Recommended) PostgreSQL 16` | `SQLite 3` | `SQL Server` | `MongoDB` | `Redis`
2. **Acceso a Datos**:
   - `(Recommended) ORM Tipado Asíncrono (SQLAlchemy 2.0 / EF Core 9 / Prisma / Hibernate)`
   - `Micro-ORM / Query Builder (Dapper / Knex / Kysely / sqlx)`
   - `Driver SQL nativo en crudo`
3. **Estrategia de Migraciones**:
   - `(Recommended) Migraciones declarativas versionadas (Alembic / EF Migrations / Prisma)`
   - `Scripts SQL versionados (Flyway / DbUp)`
   - `Sin migraciones formales`
4. **Aislamiento para Tests de Integración**:
   - `(Recommended) Testcontainers (Base de datos real efímera en Docker)`
   - `Base de datos SQLite / In-Memory dedicada para tests`
   - `Mocks / Stubs de repositorios`
5. **Autenticación y Seguridad**:
   - `(Recommended) JWT Bearer Tokens (Stateless)`
   - `Cookies de sesión HttpOnly con SameSite y CSRF`
   - `Proveedor Externo OAuth2/OIDC (Auth0 / Clerk / Firebase / Azure AD)`
   - `API Keys (Máquina a máquina)`
   - `N/A (Público / Sin Auth)`
6. **Gestión de Secretos**:
   - `(Recommended) Vercel / PaaS Environment Variables (Dev / Preview / Production)`
   - `Fichero .env estándar (12-Factor App) con .env.example tipado`
   - `Gestor de Secretos en Nube (Azure Key Vault / AWS Secrets Manager / HashiCorp Vault)`
7. **Golden Samples a Generar en `specs/STACK.md`** *(Selección Múltiple)*:
   - `(Recommended) Endpoints / Controllers: Routing limpio y DTOs vs mezclar lógica`
   - `(Recommended) Manejo de Errores: Result Pattern canónico vs capturas silenciosas`
   - `(Recommended) Servicios y Helpers: Inyección de dependencias vs clases estáticas acopladas`
   - `(Recommended) Acceso a Datos: Consultas limpias vs N+1 queries o leaks`
   - `(Recommended) Componente Frontend: Vista desacoplada vs fetch directo en templates`
   - `(Recommended) Entorno Local: docker-compose.yml o configuración local lista`
8. **Modalidad y Topología del Escuadrón Agéntico**:
   - `(Recommended) Escuadrón Especializado Granular (Alta Especialización: back-domain, back-infra, back-api, db-specialist, front-logic, front-ui, back-test, front-test, devops, documentator, architect, orchestrator)`
   - `Escuadrón Compacto (orchestrator, architect, back-engineer, front-engineer, qa-tester, devops, documentator)`
9. **Contexto Libre y Restricciones Específicas**:
   - `(Recommended) Sin restricciones adicionales`
   - `Tengo directrices de negocio concretas (Descríbelas en el campo libre 'Otro')`

---

## 🇬🇧 5. Question Catalog: English (EN-GB)

### 📍 Round 1: Scope, Infrastructure, Hosting & DevOps
1. **System Macro-Scope**:
   - `(Recommended) Fullstack (Backend API + Web Frontend)`
   - `Backend Only (REST API / gRPC / Microservice)`
   - `Frontend Only (SPA / Jamstack / Client-side Application)`
   - `CLI Tool / Console Application / Automation Script`
2. **Hosting Target & Runtime**:
   - `(Recommended) Public Cloud (AWS, Azure, GCP)`
   - `PaaS / Edge Serverless (Vercel, Netlify, Cloudflare Pages/Workers)`
   - `PaaS Containers (Railway, Render, Fly.io)`
   - `On-Premise (Private Servers / Corporate Datacentre)`
   - `Local Workstation (CLI / Desktop Tool)`
3. **Network Environment & Connectivity**:
   - `(Recommended) Standard network with open Internet access`
   - `Restricted corporate network with mandatory Proxy or VPN`
   - `Air-Gapped environment (100% isolated, no runtime Internet)`
4. **CI/CD Automation Platform**:
   - `(Recommended) GitHub Actions`
   - `GitLab CI/CD`
   - `Azure DevOps Pipelines`
   - `Local scripts / Makefile (No remote CI)`
5. **Deployment & Preview Strategy**:
   - `(Recommended) GitOps with automated PR Previews + Production on main (Vercel/PaaS)`
   - `Continuous automated deployment (Direct CD)`
   - `Manual deployment following human sign-off`
   - `Artefact packaging only (No automated infrastructure deployment)`
6. **Mandatory CI Quality Gates** *(Multi-select)*:
   - `(Recommended) Strict Linter & Static Typecheck`
   - `(Recommended) Fast in-memory Unit Test Suite`
   - `(Recommended) Integration Tests with auxiliary services`
   - `(Recommended) Production build & packaging verification`
   - `Security & Vulnerability Scanning (SAST / Trivy / Dependabot)`

### 📍 Round 2: System Architecture, Backend & Frontend (Dynamic Pruning)
1. **Core Architectural Pattern**:
   - `(Recommended) Clean / Hexagonal Architecture (Ports & Adapters)`
   - `Vertical Slice Architecture (Independent feature slices with commands/queries)`
   - `Modular Monolith (Bounded business modules with explicit contracts)`
   - `Traditional Layered / N-Tier (Controllers -> Services -> Repositories)`
   - `Minimal / Flat (KISS: unlayered structure for lean utilities)`
2. **Error Handling & Control Flow Strategy**:
   - `(Recommended) Typed Result Pattern (Railway Oriented: explicit Result<T, Error>)`
   - `Hierarchical Domain Exceptions (caught and mapped at the HTTP/API boundary)`
   - `Standard JSON error responses & status codes`
3. **Backend: Language & Framework** *(Skipped if Frontend Only)*:
   - `(Recommended) Python 3.12+ with FastAPI`
   - `C# .NET 9 with ASP.NET Core`
   - `TypeScript / Node.js 22 with NestJS or Fastify`
   - `Java 21 LTS with Spring Boot 3`
   - `Go 1.23+ with Gin or Chi`
4. **Backend: DTO Validation** *(Contextualised to selected language)*:
   - Python: `Pydantic v2` | C#: `FluentValidation` | TS: `Zod / class-validator` | Java: `Bean Validation` | Go: `Native tags`
5. **Frontend: Visual Framework** *(Skipped if Backend Only / CLI)*:
   - `(Recommended) React 19 + TypeScript + Vite`
   - `Vue 3 + TypeScript + Vite`
   - `Svelte 5 + TypeScript + Vite`
   - `Next.js / Nuxt (Fullstack SSR hosted on Vercel)`
   - `HTML5 + CSS3 Vanilla + Web Components (Zero dependencies)`
6. **Frontend: Styling & UI Strategy**:
   - `(Recommended) TailwindCSS (Utility-First)`
   - `Headless UI Component Library (shadcn/ui, Radix, PrimeVue)`
   - `Vanilla CSS with BEM methodology`
   - `CSS Modules / Sass`
7. **Frontend: Client State Management**:
   - `(Recommended) Server as Source of Truth + Cache (TanStack Query / SWR)`
   - `Lightweight Global Store (Zustand in React / Pinia in Vue)`
   - `Native Reactive State (React Hooks / Vue Composables / Signals)`
   - `Redux Toolkit (RTK)`
8. **Contract Synchronisation (Producing Boundaries)**:
   - `(Recommended) OpenAPI / Swagger v3 with automated TypeScript type generation`
   - `tRPC (End-to-end TS type safety without intermediate schemas)`
   - `gRPC / Protocol Buffers (.proto)`
   - `GraphQL Schema-First`
   - `Decoupled manual DTOs`
9. **Frontend: Visual Design Intelligence & Design System (`uiux`)** *(Skipped if Backend Only / CLI)*:
   - `(Recommended) Enable ui-ux-pro-max (packs: capability-web-frontend + capability-ui-design, offline vendored provider + @ui-ux-designer at Gate 2)`
   - `ECC frontend skills only (capability-web-frontend with @a11y-architect, no external provider; uiux.enabled: false)`
10. **Frontend: Hi-Fi Prototype Format (`uiux.hifi_format`)** *(Skipped if Backend Only / CLI or if `uiux.enabled: false`)*:
    - `(Recommended) html (Navigable HTML/CSS verifiable offline / via browser-qa)`
    - `figma (Governed Figma links and artefacts)`
    - `html+figma (Hybrid: navigable HTML/CSS prototype + Figma link)`
11. **Frontend: Brand Constraints (`uiux.brand_constraints`)** *(Skipped if Backend Only / CLI or if `uiux.enabled: false`)*:
    - `(Recommended) None (no pre-existing brand guidelines file)`
    - `Relative repository path (e.g. docs/design-system/BRAND.md)`

### 📍 Round 3: Persistence, Quality, Security, Golden Samples & Agents
1. **Database Engine** *(Skipped if Stateless)*:
   - `(Recommended) PostgreSQL 16` | `SQLite 3` | `SQL Server` | `MongoDB` | `Redis`
2. **Data Access Layer**:
   - `(Recommended) Typed Async ORM (SQLAlchemy 2.0 / EF Core 9 / Prisma / Hibernate)`
   - `High-performance Micro-ORM / Query Builder (Dapper / Knex / Kysely / sqlx)`
   - `Raw native SQL driver`
3. **Database Migration Strategy**:
   - `(Recommended) Declarative versioned migrations (Alembic / EF Migrations / Prisma)`
   - `Versioned SQL migration scripts (Flyway / DbUp)`
   - `No formal migrations`
4. **Integration Test Isolation**:
   - `(Recommended) Testcontainers (Ephemeral real database in Docker)`
   - `Dedicated SQLite / In-Memory database for testing`
   - `Repository mocks and stubs`
5. **Authentication & Security**:
   - `(Recommended) JWT Bearer Tokens (Stateless)`
   - `Secure HttpOnly Session Cookies with SameSite & CSRF protection`
   - `External OAuth2 / OIDC Provider (Auth0 / Clerk / Firebase / Azure AD)`
   - `API Keys (Machine-to-Machine)`
   - `N/A (Public / No Auth)`
6. **Secrets & Environment Management**:
   - `(Recommended) Vercel / PaaS Environment Variables (Dev / Preview / Production)`
   - `Standard .env (12-Factor App) with typed .env.example`
   - `Cloud Secrets Manager (Azure Key Vault / AWS Secrets Manager / HashiCorp Vault)`
7. **Golden Samples to Generate in `specs/STACK.md`** *(Multi-select)*:
   - `(Recommended) Endpoints / Routing: Clean controller/handler with DTOs vs inline business logic`
   - `(Recommended) Error Handling: Canonical Result Pattern vs generic swallowed exceptions`
   - `(Recommended) Services & Helpers: Dependency Injection vs tightly coupled static classes`
   - `(Recommended) Data Access: Clean queries vs N+1 queries or connection leaks`
   - `(Recommended) Frontend Component: Decoupled view consuming services vs raw fetch in templates`
   - `(Recommended) Local Environment: docker-compose.yml or local dev configuration ready`
8. **Agent Squad Topology & Specialisation Mode**:
   - `(Recommended) Specialised Granular Squad (High-Specialisation: back-domain, back-infra, back-api, db-specialist, front-logic, front-ui, back-test, front-test, devops, documentator, architect, orchestrator)`
   - `Compact Squad (orchestrator, architect, back-engineer, front-engineer, qa-tester, devops, documentator)`
9. **Free Context & Business Constraints**:
   - `(Recommended) No additional constraints (Follow framework defaults)`
   - `Specific requirements or domain context (Describe in 'Other' field)`

---

## 📝 6. Deterministic Output & Conversational Agent Generation
Upon receiving the user's responses in chat, `@orchestrator`:
1. Completes **`specs/STACK.md`** in the user's chosen language (ES-ES or EN-GB), using **`specs/templates/00-stack.template.md`**.
2. **Emits the Structured `sdd:stack-config` Block in `specs/STACK.md` (§3.3)**:
   - Sets `stack_approved: false` (and legacy `gate00_approved: false`) until explicit human sign-off, `preset` (`compact | granular | api-only | spa-only`), and `packs`.
   - When the project includes a UI (`Fullstack` or `Frontend Only`):
     - If visual intelligence is enabled (`uiux.enabled: true`), includes **`capability-web-frontend`** and **`capability-ui-design`** in `packs`, alongside the `uiux` section:
       ````markdown
       ```yaml sdd:stack-config
       stack_approved: false
       gate00_approved: false
       preset: <compact|granular|spa-only>
       packs:
         - <lang-pack>
         - <framework-pack>
         - capability-web-frontend
         - capability-ui-design
       uiux:
         enabled: true
         provider: ui-ux-pro-max
         version: "2.15.0"
         hifi_format: <html|figma|html+figma>
         # brand_constraints: docs/design-system/BRAND.md  # Optional relative path
       ```
       ````
     - If ECC frontend skills only are chosen (`uiux.enabled: false`), includes `capability-web-frontend` without `capability-ui-design` and sets `uiux: { enabled: false }` (keeping `@a11y-architect` and ECC skills without `@ui-ux-designer`).
   - When the project is `Backend Only / API Only` or `CLI`, omits `capability-ui-design` and sets `uiux.enabled: false` (or omits the `uiux` section).
3. Sets the **Agent Squad Table** (`ACTIVE` vs `INACTIVE (N/A)`), **Ownership Map (§3.2)**, and **Golden Samples (Do's & Don'ts)** in `specs/STACK.md`.
4. **Requests Human Sign-off (`RN-SDD-HUMAN-GATE-OWNERSHIP`)**: Informs the user in chat of the proposed stack and active squad, and asks for explicit approval to mark `[x] Gate S0 Approved (Human Sign-off)` (or legacy `[x] Gate 00 Approved (Human Sign-off)`) and set `stack_approved: true` (and `gate00_approved: true`).
5. **Materialises the Agent Squad After Gate S0 Approval**:
   - Runs `uv run python scripts/sdd_agent_generator.py --materialize` to compile the selected builders, universal specialists, and active stack packs into `.agents/` (including `.agents/agents/ui-ux-designer.md`, `.agents/skills/sdd-ui-design/`, `.agents/skills/ui-ux-pro-max/`, and `.agents/workflows/ui-design-review.md` when `uiux.enabled: true`) and initialise `.agent-inbox/`.
6. **Automatic `Design System Foundation` Backlog Registration (`RF-008`, `AMB-005`)**:
   - **ONLY if `uiux.enabled: true`** after Gate S0 approval: automatically registers a single row in `specs/BACKLOG.md` titled **`Design System Foundation`** with the **next sequential available `FEAT-XXX` ID** (e.g. `FEAT-002` if `FEAT-001` already exists), `Gate 0 (Intake)` = `[x]`, Gates 1–5 = `[ ]`, and `Estado Final` = `Backlog`.
   - Do **not** create `specs/features/FEAT-XXX-*/`, `docs/design-system/`, or any production code during Gate S0; the foundational feature executes its Gate 1–5 lifecycle in its own dedicated session (`RN-SDD-SESSION-LIFECYCLE`).
