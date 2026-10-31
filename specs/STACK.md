# Especificación del Stack Tecnológico (Gate 00: Stack Definition)

> **ESTADO DE LA PUERTA:** `[ ] Gate 00 Approved (Human Sign-off)`
> *(El código de producción permanece bloqueado hasta que esta casilla esté marcada con [x] tras el acuerdo con el usuario).*

---

## 1. Identificación del Proyecto
- **Nombre del Proyecto**: `[Nombre del Proyecto]`
- **Tipo de Aplicación**: Web Fullstack / SPA / API Microservicios / Mobile / CLI / Monolito
- **Arquitectura Base**: Hexagonal / Clean Architecture / Modular / MVC / Monorepo

---

## 2. Tecnologías y Herramientas Seleccionadas

### 2.1. Backend
- **Lenguaje y Versión**: `[ej: C# .NET 9 | Java 21 Spring Boot 3 | Python 3.12 | Go 1.23 | Node.js 22 TypeScript | N/A]`
- **Framework Principal**: `[ej: ASP.NET Core Minimal APIs | Spring Boot Web | FastAPI | Gin | NestJS]`
- **Gestor de Paquetes**: `[ej: dotnet CLI | Maven/Gradle | uv/poetry | go mod | pnpm/npm]`
- **Estructura de Directorios**: `src/backend/...` (o según corresponda)

### 2.2. Frontend
- **Tecnología**: `[ej: HTML5 + CSS3 vanilla | React 19 + TypeScript | Vue 3 + Vite | Blazor | Flutter | N/A]`
- **Framework de Estilos**: `[ej: CSS Vanilla BEM | TailwindCSS | Sass | Bootstrap]`
- **Gestor de Estado**: `[ej: Vanilla Custom Events / Store | Zustand | Pinia | Redux Toolkit]`
- **Estructura de Directorios**: `src/frontend/...` (o según corresponda)

### 2.3. Persistencia y Almacenamiento
- **Base de Datos Principal**: `[ej: PostgreSQL 16 | SQL Server | MongoDB | SQLite | Redis | N/A]`
- **ORM / Capa de Acceso a Datos**: `[ej: EF Core | Hibernate/JPA | SQLAlchemy | Dapper | Prisma | Driver Nativo]`
- **Estrategia de Migraciones**: `[ej: EF Core Migrations | Flyway | Alembic | Atlas]`

### 2.4. Calidad, Testing y Verificación
- **Comando de Test Backend**: `[ej: dotnet test | mvn test | pytest | go test ./... | npm test]`
- **Comando de Test Frontend**: `[ej: npm run test | npx vitest run | npx playwright test | N/A]`
- **Linter / Formatter**: `[ej: dotnet format | checkstyle | ruff | golangci-lint | eslint + prettier]`

### 2.5. Infraestructura y Despliegue
- **Contenedores**: `[ej: Dockerfile multi-stage, docker-compose.yml]`
- **Entorno Local**: `[ej: Docker Compose con DB y local services]`

---

## 3. Firmas de Aprobación de Gate 00
- [ ] `@orchestrator`: Especificación del stack validada técnica y operativamente.
- [ ] **Usuario Humano**: `[ ] Gate 00 Approved (Human Sign-off)`
