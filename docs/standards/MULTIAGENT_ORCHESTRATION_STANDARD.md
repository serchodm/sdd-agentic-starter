# Regla 09: Estándar de Orquestación Multi-Agente y Grafo de Tareas (OpenSpec / Harness Engineering)

> **ESTÁNDAR NORMATIVO OBLIGATORIO (ALWAYS ON):** Esta regla define el modelo operativo de desarrollo multi-agente en Project, basado en los principios de *OpenSpec* y *Harness Engineering*. Rige la interacción entre el Agente Orquestador (`@orchestrator`), los Agentes de Código especializados (`Code Agents`) y la base de conocimiento vivo del proyecto.

---

## 🏛️ 1. Principio Fundamental: Desacoplamiento de Roles del Escuadrón Completo

Queda terminantemente prohibido reducir la ejecución a un subconjunto genérico de agentes. El escuadrón completo de 14 especialistas debe ser convocado e instanciado explícitamente según el dominio de cada tarea:

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                             01. OpenSpec                                               │
│    @functional-analyst & @ai-architect ──► 01-spec.md (Qué)                                            │
│    @orchestrator ──► 02-tech-spec.md (Cómo) ──► 03-tasks.md (Grafo de Tareas DAG: Quién y En qué Orden)     │
└───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                    │
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   02. Orquestador (@orchestrator)                                            │
│   - Tech Lead & Scrum Master: NO programa código de producción.                                        │
│   - Despacha cada tarea a su especialista exacto mediante runSubAgent(agente, tarea, contexto, DoD).  │
│   - Gobierna la sincronización de bloques paralelos y la secuenciación de dependencias.               │
└────────┬──────────────────────────────────────────┼───────────────────────────────────────────┬────────┘
         │                                          │                                           │
         ▼                                          ▼                                           ▼
┌──────────────────────┐                  ┌──────────────────────┐                    ┌──────────────────────┐
│   CAPA DE DATOS      │                  │    CAPA BACKEND      │                    │    CAPA FRONTEND     │
│  @db-specialist      │                  │  @back-domain        │                    │  @front-logic        │
│  (DDL, pgvector,     │                  │  (Entidades puras,   │                    │  (TypeScript espejo, │
│   índices en DDBB/)  │                  │   Use Cases)         │                    │   Zustand, API / SSE)│
└────────┬─────────────┘                  │  @back-infra         │                    │  @front-ui           │
         │                                │  (SQLModel Repos,    │                    │  (React 19, Tailwind,│
         │                                │   MCP Clients, ACP)  │                    │   Three.js 3D Canvas)│
         │                                │  @back-api           │                    │  @front-test         │
         │                                │  (Routers FastAPI,   │                    │  (Vitest, RTL,       │
         │                                │   DTOs camelCase)    │                    │   Typecheck tsc)     │
         │                                │  @audio-voice        │                    └──────────┬───────────┘
         │                                │  (TTS, Web Audio)    │                               │
         │                                │  @back-test          │                               │
         │                                │  (Pytest unit & int) │                               │
         │                                └──────────┬───────────┘                               │
         │                                           │                                           │
         └───────────────────────────────────────────┼───────────────────────────────────────────┘
                                                     ▼
                                    ┌───────────────────────────────────┐
                                    │    ROLES TRANSVERSALES & DEVOPS   │
                                    │  @devops (Docker, Redes, Puertos) │
                                    │  @qa-auditor (Boundary / rea/ecc) │
                                    └────────────────┬──────────────────┘
                                                     ▼
                                      [Barrera de Sincronización]
                                                     ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               03. Consolidación de Conocimiento Vivo                                   │
│   Al validar Gate 5 con 100% verde:                                                                    │
│   @documentator consolida docs/es/, docs/en/ y la Base de Conocimiento en docs/knowledge/:             │
│   API_CATALOG.md · DATA_MODELS.md · ADRS.md · SYSTEM_TOPOLOGY.md                                       │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛑 2. Regla `RN-SDD-ORCHESTRATOR-SUBAGENTS` (Orquestador Estricto)

1. **Inviolabilidad del Ámbito del Orquestador:**
   - El agente orquestador (`@orchestrator` o la IA en rol de Tech Lead) **nunca debe escribir, editar o borrar código de producción** directamente en el hilo principal de orquestación.
   - Su única vía para modificar código es despachar un subagente especializado (`runSubAgent` / `invoke_subagent`) asignándole la tarea concreta.
2. **Aislamiento de Contexto de Subagente (*Zero Context Pollution*):**
   - Cada subagente debe invocarse con un contexto acotado y autosuficiente:
     - La tarea atómica asignada de `03-tasks.md`.
     - El extracto relevante de contratos de `02-tech-spec.md`.
     - La regla técnica específica que le aplica (`01-python-backend.md`, `02-frontend-react.md`, etc.).
     - El comando determinista de verificación (DoD).
   - El subagente **nunca debe recibir el historial conversacional completo** ni archivos ajenos a su ámbito.
3. **Devolución de Evidencias Concisas:**
   - Al finalizar, el subagente devuelve exclusivamente:
     - Lista de archivos creados/modificados.
     - Salida textual del comando de verificación (DoD) demostrando 100% de éxito en verde.
     - Breve resumen de 1 a 2 líneas de lo implementado.
4. **Prohibición de Reducción o Agrupación Perezosa (Uso Obligatorio del Escuadrón Completo):**
   - Queda terminantemente prohibido agrupar tareas bajo uno o dos agentes comodín para abreviar.
   - Cada tarea en `03-tasks.md` debe estar rotulada con su subagente exacto:
     - `@db-specialist` para scripts SQL, índices y migraciones `pgvector`.
     - `@back-domain` para entidades puras, Value Objects y casos de uso.
     - `@back-infra` para repositorios SQLModel, conectores y clientes MCP.
     - `@back-api` para routers FastAPI, WebSockets, SSE y DTOs Pydantic camelCase.
     - `@audio-voice` para síntesis TTS y pipelines de Web Audio API.
     - `@back-test` para suites de pytest unitarias y de integración.
     - `@front-logic` para interfaces TypeScript espejo, Zustand stores y clientes de datos.
     - `@front-ui` para componentes React 19, shaders y escenas Three.js.
     - `@front-test` para pruebas Vitest, testing-library y typecheck.
     - `@devops` para Docker Compose, Dockerfiles y salud de red.
     - `@documentator` para living docs bilingües y base de Conocimiento Vivo en `docs/knowledge/`.
     - `@qa-auditor` para auditorías independientes de arquitectura y cero fallos silenciosos.

---

## 🚦 3. Estructura del Grafo de Tareas (DAG) en `03-tasks.md`

Todo archivo `03-tasks.md` debe estructurarse obligatoriamente en **Bloques de Ejecución**, clasificando explícitamente qué tareas son concurrentes y cuáles tienen dependencias estrictas:

### 3.1. Bloques Paralelos (`[PARALLEL]`)
- Agrupan tareas que **no comparten dependencias de escritura** ni bloqueos mutuos.
- *Ejemplo típico:* Crear entidades de backend (`@back-domain`) y crear interfaces TypeScript espejo (`@front-logic`). Ambas se basan en el mismo contrato sellado en `02-tech-spec.md` y pueden ejecutarse **simultáneamente** en dos subagentes independientes.
- El orquestador ejecuta los subagentes en paralelo y espera en una **Barrera de Sincronización** a que todos reporten DoD verde antes de avanzar.

### 3.2. Bloques Secuenciales (`[SEQUENTIAL]`)
- Agrupan tareas que **requieren obligatoriamente la culminación verificada** del bloque anterior.
- *Ejemplo típico:* La integración de un componente UI (`@front-ui`) requiere que los tipos TypeScript (`@front-logic`) y el endpoint backend (`@back-api`) estén implementados y compilando limpiamente.
- Si una tarea secuencial falla, se detiene la línea (*Stop-the-Line*) de inmediato.

### 3.3. Formato Normativo de Cada Tarea
Toda tarea individual en `03-tasks.md` debe contener:
```markdown
- [ ] **Tarea X.Y** [`@agente`]: `[Título Descriptivo]`
  - *Ámbito permitido*: `[Ruta de carpeta autorizada]`
  - *Archivos exactos*: `[Rutas físicas exactas]`
  - *Contrato de referencia*: `[Sección exacta de 02-tech-spec.md]`
  - *Comando de verificación DoD*: `[Comando determinista de prueba/compilación]`
```

---

## 👥 4. Matriz de Especialistas (`Code Agents`)

Rige la asignación biunívoca entre la naturaleza de la tarea y el agente especializado definido en `.agents/agents/`:

| Agente | Archivo de Identidad | Ámbito Autorizado | Herramientas & Quality Gates |
|---|---|---|---|
| `@orchestrator` | `.agents/agents/jarvis.md` | `specs/`, `.agents/`, gestión de pipeline | Orquestación, delegación `runSubAgent`, verificación holística |
| `@db-specialist` | `.agents/agents/db-specialist.md` | `DDBB/scripts/` | PostgreSQL 16, pgvector, DDL versionado, scripts idempotentes |
| `@back-domain` | `.agents/agents/back-domain.md` | `backend/src/domain/`, `backend/tests/unit/domain/` | Entidades puras, Value Objects, Casos de Uso, pytest |
| `@back-infra` | `.agents/agents/back-infra.md` | `backend/src/infrastructure/`, `backend/tests/unit/infra/` | Repositorios SQLModel, clientes MCP, conectores externos, pytest |
| `@back-api` | `.agents/agents/back-api.md` | `backend/src/api/`, `backend/tests/unit/api/` | Routers FastAPI, DTOs Pydantic camelCase, WebSockets, SSE |
| `@audio-voice` | `.agents/agents/audio-voice.md` | `backend/src/infrastructure/audio/`, `frontend/src/services/audio/` | Adaptadores TTS (EdgeTTS, ElevenLabs, Piper), Web Audio API |
| `@back-test` | `.agents/agents/back-test.md` | `backend/tests/` | Pytest, cobertura BDD, fixtures herméticas, mocks de infraestructura |
| `@front-logic` | `.agents/agents/front-logic.md` | `frontend/src/types/`, `frontend/src/store/`, `frontend/src/api/` | TypeScript interfaces espejo, Zustand stores, clientes HTTP/SSE |
| `@front-ui` | `.agents/agents/front-ui.md` | `frontend/src/components/`, `frontend/src/views/` | React 19, Tailwind CSS, Three.js / R3F, canvas holográfico |
| `@front-test` | `.agents/agents/front-test.md` | `frontend/src/**/*.test.{ts,tsx}` | Vitest, React Testing Library, ESLint, typecheck tsc |
| `@devops` | `.agents/agents/devops.md` | `docker-compose*.yml`, `Dockerfile*`, `.env*` | Docker, healthchecks, puertos, redes aisladas |
| `@documentator` | `.agents/agents/documentator.md` | `docs/es/`, `docs/en/`, `docs/knowledge/` | Living docs bilingües, matrices de trazabilidad, Catálogo vivo |
| `@functional-analyst` | `.agents/agents/functional-analyst.md` | `specs/features/*/01-spec.md`, `specs/changes/*/01-spec.md` | Requisitos funcionales EARS, criterios Gherkin, fuentes SRC |
| `@ai-architect` | `.agents/agents/ai-architect.md` | `specs/architecture/`, perfiles cognitivos | Viabilidad de modelos LLM, RAG híbrido, arquitectura cognitiva |

---

## 🔄 5. Ciclo de Delivery de 6 Fases (OpenSpec Delivery Lifecycle)

Todo requerimiento funcional transita obligatoriamente por estas 6 fases continuas:

```text
1. Solicitar ──► 2. Especificar ──► 3. Delegar ──► 4. Implementar ──► 5. Validar ──► 6. Consolidar
  (Backlog)     (01-spec / 02)     (03-tasks)      (Subagentes)        (CI/DoD)     (Living Docs)
```

1. **Solicitar:** El usuario plantea la necesidad; `@functional-analyst` registra el ticket en `specs/BACKLOG.md` (Gate 0).
2. **Especificar:** Redacción de `01-spec.md` (Gate 1 - Aprobación funcional humana) y `02-tech-spec.md` (Gate 2 - Aprobación técnica humana con contratos biunívocos sellados).
3. **Delegar:** `@orchestrator` genera `03-tasks.md` organizando las tareas en bloques `[PARALLEL]` y `[SEQUENTIAL]` con asignación estricta de agente (Gate 3 - Aprobación humana de tareas).
4. **Implementar:** `@orchestrator` ejecuta `runSubAgent` bloque a bloque. Los subagentes operan en contextos aislados y ejecutan sus comandos de verificación locales.
5. **Validar:** Verificación holística de regresión: tests unitarios, tests de componentes, typechecking, linter y auditoría de límites arquitectónicos.
6. **Consolidar:** `@documentator` actualiza la documentación funcional viva y el directorio `docs/knowledge/` (Catálogo de APIs, Esquemas DB y ADRs). Sincronización obligatoria con la rama de trabajo o `develop` (`RN-SDD-BRANCH-SYNC`). Prohibido comitear directo a `main`.

---

## 🛡️ 6. Integración del Arnés Ultra-Especialista `affaan-m/ECC` (`search-first`, Revisores de Stack y Puertas GAN/Santa)

1. **Fase 0 Obligatoria — *Research & Reuse (`search-first`)*:**
   - Antes de diseñar `02-tech-spec.md` o crear nuevos módulos, `@orchestrator` y los subagentes aplican la skill `.agents/skills/search-first/SKILL.md` (y `@code-explorer` / `@spec-miner` / `@code-architect`), consultando primero `docs/knowledge/` para reutilizar o extender contratos existentes antes de construir desde cero.
2. **Escuadrón de 20 Agentes Ultra-Especialistas (`.agents/agents/`):**
   - `@orchestrator` complementa a los agentes constructores con los revisores y especialistas de ECC:
     - **Exploración y Diseño**: `@code-architect`, `@code-explorer`, `@spec-miner`.
     - **Revisión por Stack**: `@fastapi-reviewer`, `@python-reviewer`, `@react-reviewer`, `@typescript-reviewer`, `@database-reviewer`, `@rag-pipeline-reviewer`.
     - **Calidad, Seguridad y Rendimiento**: `@security-reviewer`, `@silent-failure-hunter`, `@type-design-analyzer`, `@code-simplifier`, `@performance-optimizer`, `@a11y-architect`.
     - **Build, Testing y Verificación Adversaria**: `@build-error-resolver`, `@e2e-runner`, `@tdd-guide`, `@gan-evaluator`, `@conversation-analyzer`.
3. **Puertas de Verificación Adversaria (`/gan-build` & `/santa-loop`) y Aprendizaje Continuo (`/learn` & `/evolve`):**
   - Para cambios de alta complejidad, `@orchestrator` emplea la separación Generador $\neq$ Evaluador (`@gan-evaluator` con rúbrica $\ge 8.5/10$) y la doble revisión independiente del *Santa Method* (*Checking It Twice*) antes de autorizar el cierre en Gate 5, consolidando los instintos aprendidos mediante `continuous-learning-v2`.
