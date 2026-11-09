# Especificación del Stack Tecnológico (Gate 00: Stack Definition)

> **ESTADO DE LA PUERTA:** `[ ] Gate 00 Approved (Human Sign-off)`  
> *(El código de producción en `src/` permanece estrictamente BLOQUEADO por la regla RN-SDD-GATE00-STACK-LOCK hasta que esta casilla cuente con la firma explícita del usuario tras su revisión).*

---

## 🏛️ 1. Identificación y Topología del Sistema

- **Nombre del Proyecto**: `[Nombre del Proyecto]`
- **Macro-Alcance**: `[Fullstack / Solo Backend (API) / Solo Frontend (SPA) / CLI / Monolito]`
- **Patrón Arquitectónico Base**: `[Clean Architecture (Hexagonal) / Vertical Slice / Monolito Modular / Layered MVC / Minimal Flat]`
- **Destino de Ejecución (Hosting)**: `[Cloud Pública (AWS/Azure/GCP) / PaaS Serverless (Vercel/Netlify/Cloudflare) / Contenedores PaaS (Railway/Render) / On-Premise / Local]`
- **Unidad de Empaquetado & Runtime**: `[Contenedores Docker / Serverless Edge / Binario Nativo / Proceso OS]`
- **Entorno de Red & Conectividad**: `[Red abierta a Internet / Red corporativa con Proxy/VPN / Air-Gapped]`
- **Protocolo de Comunicación / Contratos**: `[REST OpenAPI v3 / gRPC Protocol Buffers / tRPC / GraphQL / DTOs manuales]`

---

## 🛠️ 2. Tecnologías y Librerías Core (Golden Path)

### 2.1. Backend `[o N/A si es solo Frontend]`
- **Lenguaje y Versión**: `[ej: Python 3.12+ | C# .NET 9 | TypeScript Node 22 | Java 21 | Go 1.23 | N/A]`
- **Framework Web / API**: `[ej: FastAPI | ASP.NET Core | NestJS / Fastify | Spring Boot 3 | Gin | N/A]`
- **Validación de DTOs**: `[ej: Pydantic v2 | FluentValidation | Zod | Jakarta Bean Validation | Struct tags]`
- **Control de Flujo y Errores**: `[Result Pattern tipado (ej: Result<T, Error>) / Excepciones de Dominio / JSON estándar]`
- **Inyección de Dependencias**: `[IoC nativo del framework / Inyección manual]`

### 2.2. Frontend `[o N/A si es solo Backend/CLI]`
- **Runtime y Lenguaje**: `[ej: TypeScript 5.6+ (Modo Estricto) | JavaScript Moderno | N/A]`
- **Framework Visual**: `[ej: React 19 + Vite | Vue 3 + Vite | Svelte 5 | HTML5 Vanilla + Web Components | Next.js / Nuxt | N/A]`
- **Librería de Componentes y Estilos**: `[ej: TailwindCSS | shadcn/ui + Tailwind | CSS Vanilla BEM | CSS Modules / Sass | N/A]`
- **Gestión de Estado**: `[ej: TanStack Query + Cache | Zustand / Pinia | Estado Reactivo Nativo | Redux Toolkit | N/A]`
- **Cliente de API / Contratos**: `[ej: Cliente tipado generado por OpenAPI / gRPC-web / tRPC client / Fetch nativo]`

### 2.3. Persistencia y Almacenamiento `[o N/A si es Stateless]`
- **Motor de Base de Datos**: `[ej: PostgreSQL 16 | SQLite 3 | SQL Server | MongoDB | Redis | N/A]`
- **Capa de Acceso a Datos**: `[ej: ORM Asíncrono (SQLAlchemy 2.0 / EF Core 9 / Prisma / Hibernate) | Micro-ORM (Dapper / Knex) | Driver SQL nativo | N/A]`
- **Migraciones de Esquema**: `[ej: Migraciones declarativas (Alembic / EF Migrations / Prisma) | Scripts SQL (Flyway / DbUp) | N/A]`

### 2.4. DevOps, CI/CD y Calidad
- **Plataforma de CI/CD**: `[ej: GitHub Actions | GitLab CI/CD | Azure DevOps | Scripts locales]`
- **Estrategia de Despliegue y Previews**: `[ej: GitOps con Vercel Previews automáticas en PRs + Prod en main / Docker en Cloud / Manual]`
- **Gates Obligatorios en Pipeline**:
  1. `[Linter & Typecheck]`
  2. `[Suite de Tests Unitarios en memoria]`
  3. `[Tests de Integración con dependencias auxiliares]`
  4. `[Build de producción / Comprobación de empaquetado]`
  5. `[Escaneo de seguridad SAST / Dependabot]`
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

- **Modalidad Seleccionada**: `[Escuadrón Especializado Granular (Alta Especialización) / Escuadrón Compacto]`

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
- ✅ **DO (Código Canónico):**
```text
[Ejemplo representativo del endpoint/controlador con DTOs y validación limpia]
```
- ❌ **DON'T (Antipatrón Prohibido):**
```text
[Ejemplo del antipatrón prohibido (mezclar lógica de negocio, acceso a BD directo o falta de validación)]
```

### 5.2. Manejo de Errores y Excepciones
- ✅ **DO:** `[Uso canónico de Result Pattern o Excepciones de Dominio con mapeo en boundary]`
- ❌ **DON'T:** `[Prohibido capturar excepciones genéricas de forma silenciosa (empty catch / try-except pass)]`

### 5.3. Servicios y Helpers
- ✅ **DO:** `[Inyección de dependencias desacoplada y reutilizable]`
- ❌ **DON'T:** `[Clases estáticas rígidas, dependencias acopladas o código duplicado]`

---

## 🐳 6. Entorno Local de Desarrollo

`[Configuración de docker-compose.yml con BD local, o instrucciones de vercel.json / local dev]`

---

## ✍️ 7. Firmas de Aprobación de Gate 00

- [ ] `@orchestrator`: Especificación del stack, arquitectura, contratos y escuadrón agéntico validados formalmente.
- [ ] **Usuario Humano**: `[ ] Gate 00 Approved (Human Sign-off)`
