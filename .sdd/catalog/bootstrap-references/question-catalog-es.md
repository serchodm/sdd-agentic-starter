# `sdd-bootstrap` Reference: Catálogo de Preguntas Español (ES-ES)

## 📍 Ronda 1: Alcance Macro, Infraestructura, Hosting y DevOps
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
   - `(Recommended) GitHub Actions` | `GitLab CI/CD` | `Azure DevOps Pipelines` | `Scripts locales / Makefile`
5. **Estrategia de Despliegue y Previews**:
   - `(Recommended) GitOps con Previews automáticas en PRs + Producción en main (Vercel/PaaS)`
   - `Despliegue automatizado continuo (CD directo)` | `Manual tras aprobación humana` | `Solo empaquetado de artefactos`
6. **Puertas Obligatorias en CI** *(Selección Múltiple)*:
   - `(Recommended) Linter estricto y Typecheck`
   - `(Recommended) Suite de tests unitarios en memoria`
   - `(Recommended) Tests de integración con dependencias auxiliares`
   - `(Recommended) Build de producción y verificación de empaquetado`
   - `Escaneo de seguridad (SAST / Trivy / Dependabot)`

## 📍 Ronda 2: Arquitectura del Sistema, Backend y Frontend (Poda Dinámica)
1. **Patrón Arquitectónico Base**:
   - `(Recommended) Clean Architecture / Hexagonal (Puertos y Adaptadores)`
   - `Vertical Slice Architecture` | `Monolito Modular` | `Layered / N-Capas Tradicional` | `Minimal / Flat (KISS)`
2. **Manejo de Errores y Flujo de Control**:
   - `(Recommended) Result Pattern tipado (Railway: Result<T, Error> explícito)`
   - `Excepciones de Dominio Jerárquicas (capturadas en boundary HTTP/API)`
   - `Códigos de estado y respuestas JSON estándar`
3. **Backend: Lenguaje y Framework** *(Omitido si es Solo Frontend)*:
   - `(Recommended) Python 3.12+ con FastAPI`
   - `C# .NET 9 con ASP.NET Core` | `TypeScript / Node.js 22 (NestJS/Fastify)` | `Java 21 LTS (Spring Boot 3)` | `Go 1.23+ (Gin/Chi)`
4. **Backend: Validación de DTOs** *(Contextualizado al lenguaje)*:
   - Python: `Pydantic v2` | C#: `FluentValidation` | TS: `Zod / class-validator` | Java: `Bean Validation` | Go: `Tags nativos`
5. **Frontend: Framework Visual** *(Omitido si es Solo Backend / CLI)*:
   - `(Recommended) React 19 + TypeScript + Vite`
   - `Vue 3 + TS + Vite` | `Svelte 5 + TS + Vite` | `Next.js / Nuxt (SSR Vercel)` | `HTML5 + CSS3 Vanilla + Web Components`
6. **Frontend: Estilos y UI**:
   - `(Recommended) TailwindCSS (Utility-First)` | `Headless UI (shadcn/ui, Radix, PrimeVue)` | `CSS Vanilla BEM` | `CSS Modules / Sass`
7. **Frontend: Gestión de Estado**:
   - `(Recommended) Servidor como Fuente de Verdad + Cache (TanStack Query / SWR)`
   - `Store Global Ligero (Zustand / Pinia)` | `Estado Reactivo Nativo (Hooks / Composables / Signals)` | `Redux Toolkit`
8. **Sincronización de Contratos**:
   - `(Recommended) OpenAPI / Swagger v3 con exportación de tipos TypeScript`
   - `tRPC` | `gRPC / Protocol Buffers (.proto)` | `GraphQL Schema-First` | `DTOs manuales desacoplados`
9. **Frontend: Inteligencia Visual y Design System (`uiux`)** *(Omitido si es Solo Backend / CLI)*:
   - `(Recommended) Activar ui-ux-pro-max (packs: capability-web-frontend + capability-ui-design, proveedor vendorizado offline + @ui-ux-designer en Gate 2)`
   - `Solo skills ECC de frontend (capability-web-frontend con @a11y-architect, sin proveedor externo; uiux.enabled: false)`
10. **Frontend: Formato de Prototipos Hi-Fi (`uiux.hifi_format`)** *(Omitido si `uiux.enabled: false` o sin UI)*:
    - `(Recommended) html (HTML/CSS navegable verificable offline / browser-qa)` | `figma` | `html+figma`
11. **Frontend: Restricciones de Marca (`uiux.brand_constraints`)** *(Omitido si `uiux.enabled: false` o sin UI)*:
    - `(Recommended) Ninguna` | `Ruta relativa en el repositorio (ej. docs/design-system/BRAND.md)`

## 📍 Ronda 3: Persistencia, Calidad, Seguridad, Golden Samples y Agentes
1. **Motor de Base de Datos** *(Omitido si es Stateless)*: `(Recommended) PostgreSQL 16` | `SQLite 3` | `SQL Server` | `MongoDB` | `Redis`
2. **Acceso a Datos**: `(Recommended) ORM Tipado Asíncrono (SQLAlchemy 2.0 / EF Core 9 / Prisma / Hibernate)` | `Micro-ORM (Dapper / Knex / Kysely / sqlx)` | `Driver SQL nativo`
3. **Estrategia de Migraciones**: `(Recommended) Migraciones declarativas versionadas (Alembic / EF / Prisma)` | `Scripts SQL (Flyway / DbUp)` | `Sin migraciones`
4. **Aislamiento para Tests de Integración**: `(Recommended) Testcontainers` | `SQLite / In-Memory` | `Mocks / Stubs`
5. **Autenticación y Seguridad**: `(Recommended) JWT Bearer Tokens` | `Cookies HttpOnly SameSite/CSRF` | `OAuth2/OIDC` | `API Keys` | `N/A`
6. **Gestión de Secretos**: `(Recommended) PaaS Env Vars` | `Fichero .env (12-Factor) + .env.example tipado` | `Cloud Secrets Manager / Vault`
7. **Golden Samples a Generar en `specs/STACK.md`**: Endpoints/Controllers, Error Handling (Result Pattern), Servicios/DI, Acceso a Datos (anti-N+1), Componente Frontend desacoplado, Entorno Local (`docker-compose.yml`).
8. **Modalidad y Topología del Escuadrón Agéntico**:
   - `Escuadrón Compacto (orchestrator, functional-analyst, architect, back-engineer, front-engineer, qa-tester, devops, documentator, security-reviewer)`
   - `Escuadrón Especializado Granular (back-domain, back-infra, back-api, db-specialist, front-logic, front-ui, back-test, front-test, core...)`
9. **Contexto Libre y Restricciones Específicas**: Sin restricciones adicionales o directrices concretas en `'Otro'`.
