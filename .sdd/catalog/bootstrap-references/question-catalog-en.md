# `sdd-bootstrap` Reference: Question Catalog English (EN-GB)

## 📍 Round 1: Scope, Infrastructure, Hosting & DevOps
1. **System Macro-Scope**:
   - `(Recommended) Fullstack (Backend API + Web Frontend)`
   - `Backend Only (REST API / gRPC / Microservice)`
   - `Frontend Only (SPA / Jamstack / Client-side Application)`
   - `CLI Tool / Console Application / Automation Script`
2. **Hosting Target & Runtime**:
   - `(Recommended) Public Cloud (AWS, Azure, GCP)`
   - `PaaS / Edge Serverless (Vercel, Netlify, Cloudflare Pages/Workers)`
   - `PaaS Containers (Railway, Render, Fly.io)` | `On-Premise` | `Local Workstation (CLI / Desktop)`
3. **Network Environment & Connectivity**:
   - `(Recommended) Standard network with open Internet access`
   - `Restricted corporate network (Proxy / VPN)` | `Air-Gapped (100% isolated)`
4. **CI/CD Automation Platform**:
   - `(Recommended) GitHub Actions` | `GitLab CI/CD` | `Azure DevOps Pipelines` | `Local scripts / Makefile`
5. **Deployment & Preview Strategy**:
   - `(Recommended) GitOps with automated PR Previews + Production on main`
   - `Direct CD` | `Manual sign-off deployment` | `Artefact packaging only`
6. **Mandatory CI Quality Gates** *(Multi-select)*:
   - `(Recommended) Strict Linter & Static Typecheck`
   - `(Recommended) Fast in-memory Unit Test Suite`
   - `(Recommended) Integration Tests with auxiliary services`
   - `(Recommended) Production build & packaging verification`
   - `Security & Vulnerability Scanning (SAST / Trivy / Dependabot)`
7. **IaC, Cloud & GitOps Provisioning**:
   - `Terraform / OpenTofu + IAM/FinOps` (`capability-iac-cloud`)
   - `Kubernetes + Helm / ArgoCD / Flux` (`capability-devops`)
   - `No declarative IaC`

## 📍 Round 2: System Architecture, Backend & Frontend (Dynamic Pruning)
1. **Core Architectural Pattern**:
   - `(Recommended) Clean / Hexagonal Architecture (Ports & Adapters)`
   - `Vertical Slice` | `Modular Monolith` | `Traditional Layered / N-Tier` | `Minimal / Flat (KISS)`
2. **Error Handling & Control Flow Strategy**:
   - `(Recommended) Typed Result Pattern (Railway Oriented: Result<T, Error>)`
   - `Hierarchical Domain Exceptions (HTTP/API boundary)` | `Standard JSON error responses`
3. **Backend: Language & Framework** *(Skipped if Frontend Only)*:
   - `(Recommended) Python 3.12+ with FastAPI`
   - `C# .NET 9 (ASP.NET Core)` | `TypeScript / Node.js 22 with NestJS` (`lang-typescript` + `framework-nestjs`) | `Java 21 LTS (Spring Boot 3)` | `Go 1.23+ (Gin/Chi)`
4. **Backend: DTO Validation** *(Contextualised)*:
   - Python: `Pydantic v2` | C#: `FluentValidation` | TS: `Zod / class-validator` | Java: `Bean Validation` | Go: `Native tags`
5. **Frontend: Visual Framework** *(Skipped if Backend Only / CLI)*:
   - `(Recommended) React 19 + TypeScript + Vite`
   - `Next.js (App Router + RSC)` (`lang-typescript` + `framework-react` + `framework-nextjs`) | `Vue 3 + TS + Vite` | `Svelte 5 + TS + Vite` | `HTML5 + CSS3 Vanilla + Web Components`
6. **Frontend: Styling & UI Strategy**:
   - `(Recommended) TailwindCSS (Utility-First)` | `Headless UI (shadcn/ui, Radix, PrimeVue)` | `Vanilla CSS (BEM)` | `CSS Modules / Sass`
7. **Frontend: Client State Management**:
   - `(Recommended) Server as Source of Truth + Cache (TanStack Query / SWR)`
   - `Lightweight Store (Zustand / Pinia)` | `Native Reactive State (Hooks / Composables / Signals)` | `Redux Toolkit`
8. **Contract Synchronisation & API Governance**:
   - `(Recommended) OpenAPI 3.1 / gRPC Buf / AsyncAPI 3.0` (`capability-api-governance`)
   - `tRPC` | `GraphQL Schema-First` | `Decoupled manual DTOs`
9. **Frontend: Visual Design Intelligence & Design System (`uiux`)** *(Skipped if Backend Only / CLI)*:
   - `(Recommended) Enable ui-ux-pro-max (packs: capability-web-frontend + capability-ui-design, offline vendored provider + @ui-ux-designer at Gate 2)`
   - `ECC frontend skills only (capability-web-frontend with @a11y-architect, no external provider; uiux.enabled: false)`
10. **Frontend: Hi-Fi Prototype Format (`uiux.hifi_format`)** *(Skipped if `uiux.enabled: false` or no UI)*:
    - `(Recommended) html (Navigable HTML/CSS verifiable offline / via browser-qa)` | `figma` | `html+figma`
11. **Frontend: Brand Constraints (`uiux.brand_constraints`)** *(Skipped if `uiux.enabled: false` or no UI)*:
    - `(Recommended) None` | `Relative repository path (e.g. docs/design-system/BRAND.md)`
12. **Event-Driven Architecture & Async Messaging** *(Skipped if Frontend Only / Local CLI)*:
    - `Kafka / RabbitMQ / SQS / NATS + Outbox/Sagas` (`capability-event-driven`) | `N/A — Synchronous communication only`

## 📍 Round 3: Persistence, Quality, Security, Golden Samples & Agents
1. **Database Engine** *(Skipped if Stateless)*: `(Recommended) PostgreSQL 16` | `SQLite 3` | `SQL Server` | `MongoDB` | `Redis`
2. **Data Access Layer**: `(Recommended) Typed Async ORM (SQLAlchemy 2.0 / EF Core 9 / Prisma / Hibernate)` | `Micro-ORM (Dapper / Knex / Kysely / sqlx)` | `Raw SQL driver`
3. **Database Migration Strategy**: `(Recommended) Declarative versioned migrations (Alembic / EF / Prisma)` | `SQL scripts (Flyway / DbUp)` | `No formal migrations`
4. **Multi-Tenant Isolation** *(Skipped if Stateless / CLI)*: `Strict multi-tenant with RLS / tenant_id` (`capability-database` with `multi-tenant-isolation`) | `Single-tenant`
5. **Data Engineering & Analytics Pipelines** *(Skipped if Frontend Only)*: `dbt / Airflow / Data Quality Contracts` (`capability-data-engineering`) | `N/A`
6. **Integration Test Isolation**: `(Recommended) Testcontainers` | `Dedicated SQLite / In-Memory` | `Repository mocks and stubs`
7. **Authentication & Security**: `(Recommended) JWT Bearer Tokens` | `HttpOnly Session Cookies (SameSite/CSRF)` | `OAuth2 / OIDC` | `API Keys` | `N/A`
8. **Secrets & Environment Management**: `(Recommended) PaaS Environment Variables` | `Standard .env + typed .env.example` | `Cloud Secrets Manager / Vault`
9. **Golden Samples in `specs/STACK.md`**: Endpoints/Routing, Error Handling (Result Pattern), DI Services, Data Access (anti-N+1), Decoupled Frontend Component, Local Environment (`docker-compose.yml`).
10. **Agent Squad Topology & Specialisation Mode**:
    - `Compact Squad (orchestrator, functional-analyst, architect, back-engineer, front-engineer, qa-tester, devops, documentator, security-reviewer)`
    - `Specialised Granular Squad (back-domain, back-infra, back-api, db-specialist, front-logic, front-ui, back-test, front-test, core...)`
11. **Free Context & Business Constraints**: Framework defaults or domain context in `'Other'`.
