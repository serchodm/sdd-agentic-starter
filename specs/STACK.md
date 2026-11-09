# Especificación del Stack Tecnológico (Gate 00: Stack Definition)

> **ESTADO DE LA PUERTA:** `[ ] Gate 00 Approved (Human Sign-off)`
> *(El código de producción permanece bloqueado hasta que esta casilla esté marcada con [x] tras el acuerdo formal con el usuario).*

---

## 🏛️ 1. Identificación y Topología del Sistema
- **Nombre del Proyecto**: `[Nombre del Proyecto]`
- **Tipo de Aplicación**: `[Web Fullstack / SPA / API Microservicios / Mobile / CLI / Monolito Modular]`
- **Arquitectura Base**: `[Hexagonal / Clean Architecture / Capas / Vertical Slice / Monorepo]`
- **Destino de Hosting / Despliegue**: `[PaaS (Vercel / Netlify / Railway) | Contenedores Docker / Kubernetes | Cloud Nativo (AWS / Azure / GCP)]`
- **Gestión del Entorno**: `[docker-compose.yml local / devcontainer / vercel dev / CLI local]`

---

## 🛠️ 2. Tecnologías y Librerías Core (Golden Path)

### 2.1. Backend `[o N/A si es solo Frontend]`
- **Lenguaje y Versión**: `[ej: Python 3.12+ | C# .NET 9 | TypeScript Node 22 / Bun | Go 1.23 | Java 21 | N/A]`
- **Framework Web / API**: `[ej: FastAPI / ASP.NET Core Minimal APIs / Express / NestJS / Gin / Spring Boot]`
- **Gestor de Paquetes / Dependencias**: `[ej: uv / dotnet CLI / pnpm / go mod / maven / gradle]`
- **Validación de Schemas / DTOs**: `[ej: Pydantic v2 / FluentValidation / Zod / Jakarta Bean Validation]`
- **Estructura de Directorios**: `src/backend/...` (o según corresponda)

### 2.2. Frontend `[o N/A si es solo Backend/CLI]`
- **Librería / Framework**: `[ej: React 19 + TypeScript + Vite | Vue 3 + Vite | Next.js 15 | Blazor | Svelte 5 | N/A]`
- **Framework de Estilos & UI**: `[ej: TailwindCSS + shadcn/ui | CSS Modules | Vanilla CSS BEM | Material UI]`
- **Gestión de Estado**: `[ej: TanStack Query + Cache | Zustand / Pinia | Estado Reactivo Nativo | Redux Toolkit | N/A]`
- **Estructura de Directorios**: `src/frontend/...` (o según corresponda)

### 2.3. Persistencia y Almacenamiento `[o N/A si es Stateless]`
- **Base de Datos Principal**: `[ej: PostgreSQL 16 | SQL Server | SQLite / LibSQL | Redis | MongoDB | N/A]`
- **ORM / Query Builder**: `[ej: SQLAlchemy 2.0 Async / EF Core / Dapper / Prisma / Drizzle / Driver Nativo]`
- **Estrategia de Migraciones**: `[ej: Alembic / EF Core Migrations / Atlas / Flyway]`
- **Estructura de Scripts**: `src/backend/migrations/...` (o según corresponda)

### 2.4. DevOps, CI/CD y Calidad
- **CI/CD Pipeline**: `[ej: GitHub Actions / GitLab CI / Vercel Deploy Hooks]`
- **Linter & Formatter**: `[ej: ruff + mypy / dotnet format / eslint + prettier / golangci-lint]`
- **Framework de Pruebas Unitarias**: `[ej: pytest + pytest-asyncio / xUnit + FluentAssertions / Vitest / Go test]`
- **Framework de Pruebas de Integración**: `[ej: Testcontainers / Fixtures locales / Mock services]`
- **Gestión de Secretos**: `[ej: Vercel Environment Variables / .env con .env.example tipado / Azure Key Vault / AWS Secrets Manager]`

### 2.5. Comandos Deterministas de Verificación DoD (Zero Discovery Overhead)
*(Definir obligatoriamente en Gate 00 para que ningún subagente queme tokens descubriendo comandos o explorando configuraciones)*:
- **Lint & Typecheck:** `[ej: cd backend && ruff check . && mypy . | cd frontend && npx tsc --noEmit]`
- **Prueba Unitaria Acotada (In-memory, mocks, 0 DB externa):** `[ej: pytest <path/to/test.py> -q | npx vitest run <path/to/test.ts>]`
- **Prueba de Integración (Con servicios auxiliares/BD levantada):** `[ej: pytest tests/integration/<path/to/test.py> -q]`
- **Suite Completa de Tests:** `[ej: pytest tests/unit/ | npm test]`
- **Build de Producción:** `[ej: npm run build | cargo build --release | dotnet publish]`
- **Verificación de Entorno / Infraestructura:** `[ej: docker compose config | terraform validate]`

---

## 👥 3. Escuadrón Agéntico: Asignación y Características Operativas

- **Modalidad Seleccionada**: `[Escuadrón Especializado Granular (Alta Especialización) / Escuadrón Compacto / Custom]`

### 3.1. Matriz de Roles y Asignaciones
*(Se genera automáticamente mediante `scripts/sdd_agent_generator.py` según la modalidad elegida)*:

| Agente | Estado | Perfil & Especialidad en este Proyecto | Ámbito de Edición Permitido | Comandos / CLI Asignados |
| :--- | :---: | :--- | :--- | :--- |
| **`@orchestrator`** | **ACTIVO** | Tech Lead y auditor de puertas SDD. Despacha tareas DAG a `.agent-inbox/`. Cero código en `src/`. | `specs/`, `.agent-inbox/`, `scripts/` | Guardias SDD, Git |
| **`@architect`** | **ACTIVO** | Diseñador de contratos de API, schemas DTO, ADRs y límites de módulos/capas. | `specs/`, contratos/schemas | Validadores de schemas |
| **`@devops`** | **ACTIVO** | Especialista en Docker, Vercel/PaaS, CI/CD, variables y entornos. | `.github/`, `docker-compose.yml`, `vercel.json` | Comandos de build/deploy |
| **`@documentator`** | **ACTIVO** | Custodio de living docs bilingüe (0DD), catálogo de APIs y matriz de trazabilidad. | `docs/es/`, `docs/en/`, `docs/knowledge/` | Validadores de docs |
| **`[Especialistas de Backend]`** | `[ACTIVOS]` | `[back-engineer en Compacto] O [back-domain, back-infra, back-api, db-specialist, back-test en Granular]` | `src/backend/` | `[Comandos de backend]` |
| **`[Especialistas de Frontend]`** | `[ACTIVOS]` | `[front-engineer en Compacto] O [front-logic, front-ui, front-test en Granular]` | `src/frontend/` | `[Comandos de frontend]` |
| **`@qa-tester`** | **ACTIVO** | Auditor de calidad, tests y ejecución de skills de auditoría (Gate 4). | `tests/` | `[Comandos de test]` |

> **Nota de Desactivación Dinámica:** Si el proyecto no requiere Frontend (API pura / CLI), los especialistas de Frontend se marcan como `INACTIVO (N/A)`. Si es un frontend estático sin backend propio, los especialistas de Backend se marcan como `INACTIVO (N/A)`.

### 3.2. Ownership Map (Mapeo Declarativo de Zonas y Fronteras de Código)
*(Fuente única de verdad para permisos de escritura, asignación de tareas DAG en Gate 3 y verificación de límites por hooks)*:

| Zona (ID) | Rutas Físicas (Glob) | Agente Dueño (`owner`) | Arquetipo Base | Imports Prohibidos (`forbid_imports`) | Comandos DoD Asignados |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `[zona-id]` | `[ej: src/backend/domain/**]` | `[@back-domain / @back-engineer]` | `[layer-domain / tier-backend]` | `[web_framework, orm, etc.]` | `[Comando DoD de verificación]` |
| `[zona-id]` | `[ej: src/frontend/**]` | `[@front-engineer]` | `[tier-frontend]` | `[backend, direct DB]` | `[Comando DoD de verificación]` |

> **Política ante Rutas Huérfanas (`unowned_policy`):** `fail-closed` (Cualquier fichero de código que no esté asignado a una zona del Ownership Map bloquea la aprobación de Gate 3).

### 3.3. Stack Packs Activos (Catálogo `.sdd/catalog/packs/`)
*(Packs de lenguaje, framework y capacidad activados desde el catálogo inerte bajo licencia MIT de ECC)*:
- `[ej: lang-python, framework-fastapi, capability-database, capability-devops]`
- *(Se materializan en la sesión mediante `python scripts/sdd_agent_generator.py --materialize`)*.

---

## 📁 4. Estructura Canónica de Directorios (`src/`)

```text
src/
[Estructura canónica de carpetas adaptada al patrón arquitectónico acordado]
```

---

## 🌟 5. Golden Samples Canónicos (Do's & Don'ts)

### 5.1. Endpoints / Routing
- ✅ **DO (Permitido / Recomendado):**
  - Controladores delgados que delegan en casos de uso o servicios.
  - Validación de entrada mediante DTOs fuertemente tipados.
- ❌ **DON'T (Prohibido):**
  - Lógica de negocio en controladores o consultas SQL directas en routers.

### 5.2. Manejo de Errores y Excepciones
- ✅ **DO (Permitido / Recomendado):**
  - Patrón Result (`Result<T, DomainError>`) para fallos de dominio esperados.
- ❌ **DON'T (Prohibido):**
  - Tragar excepciones (`catch` o `except` vacíos).

### 5.3. Servicios y Helpers
- ✅ **DO (Permitido / Recomendado):**
  - Inyección de dependencias mediante interfaces o constructores.
- ❌ **DON'T (Prohibido):**
  - Singletons mutables globales sin protección de concurrencia.

---

## 🐳 6. Entorno Local de Desarrollo
*(Definir cómo levantar el proyecto localmente en menos de 5 minutos)*:
```bash
# Comandos canónicos de arranque local
```

---

## ✍️ 7. Firmas de Aprobación de Gate 00
- [ ] `@orchestrator`: Especificación del stack, Ownership Map y comandos DoD validados técnica y operativamente.
- [ ] **Usuario Humano**: `[ ] Gate 00 Approved (Human Sign-off)`
