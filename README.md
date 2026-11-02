# SDD Agentic Starter Template

[ 🇬🇧 English (EN-GB)](#-english-en-gb) | [ 🇪🇸 Español (ES-ES)](#-español-es-es)

---

## 🇬🇧 English (EN-GB)

Universal software development starter template governed by **Spec-Driven Development (SDD)** and multi-agent orchestration.

### 🚀 Getting Started with a New Project

#### 1. Clone or Use this Template
Create a new repository on GitHub by clicking **"Use this template"** or via the GitHub CLI:
```bash
gh repo create my-new-project --template <your-username>/sdd-agentic-starter --private
cd my-new-project
```

#### 2. Initial Repository Lock (`Gate 00: Stack Lock`)
To guarantee architectural consistency and prevent premature coding, **production code in `src/` is strictly locked** by rule `RN-SDD-GATE00-STACK-LOCK`. No production code or tests may be created until the technology stack, hosting topology, and agent squad are formally agreed upon.

#### 3. Converse with `@orchestrator` in your AI Assistant (Antigravity / Cursor / Claude Code)
Send this prompt to start the project:
> *"Hello @orchestrator. We are starting a new project based on `sdd-agentic-starter`. Please launch the interactive Gate 00 Bootstrap Wizard to define the system topology, architecture, technology stack, agent squad, and conventions."*

The `@orchestrator` will:
1. Deploy the interactive **Gate 00 Bootstrap Wizard (`sdd-bootstrap`)** with dynamic decision tree pruning:
   - **Infrastructure & Hosting**: Public Cloud (AWS/Azure/GCP), Docker Containers, or modern PaaS (**Vercel**, Netlify, Railway).
   - **Scope & Pruning**: Automatically prunes irrelevant questions (e.g. omits UI styling for API-only projects, or backend questions for client-only SPAs).
   - **Agent Squad Activation**: Dynamically sets roles to `ACTIVE` or `INACTIVE (N/A)` according to scope.
   - **Golden Samples**: Inserts canonical Do's & Don'ts (clean controllers/handlers, typed Result pattern error handling, and dependency injection).
   - **Deterministic DoD Commands**: Freezes verified commands for linting, fast in-memory unit tests (<1s), integration tests, and production build to eliminate agent discovery overhead.
   - **Local Environment**: Generates `docker-compose.yml` or `vercel.json` dev setup.
2. Complete **`specs/STACK.md`** and request your explicit human sign-off: `[x] Gate 00 Approved (Human Sign-off)`.
3. Once approved, `src/` unlocks and the normal SDD development lifecycle begins (Gate 0 -> Gate 5).

---

### 👥 Agent Squad Topologies (Configured in Gate 00)
The template supports two operational topologies depending on project complexity:
- **Specialised Granular Squad (High-Specialisation)**: 12 atomic roles with strict boundary isolation (`@back-domain`, `@back-infra`, `@back-api`, `@db-specialist`, `@back-test`, `@front-logic`, `@front-ui`, `@front-test`, `@devops`, `@documentator`, `@architect`, `@orchestrator`).
- **Compact Squad**: 7 core roles for leaner projects or MVPs (`@orchestrator`, `@architect`, `@back-engineer`, `@front-engineer`, `@qa-tester`, `@devops`, `@documentator`).

Generated conversationally by `@orchestrator` or inspected via CLI:
```bash
python scripts/sdd_agent_generator.py --list
python scripts/sdd_agent_generator.py --mode granular  # or --mode compact
```

---

### 🏛️ The SDD Lifecycle (Gate 00 to Gate 5)

```text
[ Gate 00: STACK.md ] ──► [ Gate 0: Backlog Intake ]
                                    │
                                    ▼
[ Gate 1: 01-spec.md (EARS) ] ──► [ Gate 2: 02-tech-spec.md (Contracts) ]
                                    │
                                    ▼
[ Gate 3: 03-tasks.md (DAG) ] ──► [ Subagent Execution (.agent-inbox/) ]
                                    │
                                    ▼
[ Gate 4: QA Verification ] ────► [ Gate 5: Living Docs 0DD (docs/) ] ──► DONE
```

---

### 🧠 Session Lifecycle, Context Governance & Handoff Workflows
To prevent context degradation, token exhaustion, and hallucination in long-running tasks, the framework enforces rigorous session hygiene and phase splitting:

#### 1. Phase Splitting & Model Tier Optimisation (`RN-SDD-SESSION-LIFECYCLE`)
Tasks are divided across clean, isolated conversation sessions matched to the optimal model tier:
- **Phase A — Architecture & Specs (Gates 00 to 3)**: Use high-reasoning models (e.g. Gemini Pro / Thinking, Claude Sonnet / Opus, OpenAI o1/o3) strictly for requirements gathering (`01-spec.md`), technical specifications (`02-tech-spec.md`), API/DTO contracts, and the atomic task DAG (`03-tasks.md`).
- **Phase B — Implementation & Verification (Gate 4)**: Open a fresh session using fast, cost-effective execution models (e.g. Gemini Flash, Claude Haiku) loading only `02-tech-spec.md`, `03-tasks.md`, and knowledge docs to implement code via specialist subagents.
- **Phase C — Living Docs & Closure (Gate 5)**: Execute `@documentator` in a dedicated low-cost thread to update bilingual living documentation (`docs/es/`, `docs/en/`), sync the traceability matrix, and run `git push origin main`.

#### 2. Active Session Pointer (`.agents/ACTIVE_STATE.md`)
The single source of truth for execution state between sessions. Caps mandatory context files to a maximum of 4 files to eliminate blind context bloat:
```markdown
- **Active Work Item:** FEAT-001 (or IDLE)
- **Current Gate:** Gate 03 (Tasks Ready for Execution)
- **Recommended Model Tier:** Execution (Flash/Sonnet)
- **Next Execution Target:** Dispatch Task 1.1 to @back-engineer
- **Mandatory Context Files:** specs/features/FEAT-001/02-tech-spec.md, ...
```

#### 3. Slash Command Handoff Workflows
- **`/checkpoint`**: Automatically captures the active state, snapshots pending tasks into `.agents/ACTIVE_STATE.md`, and prepares a safe session handoff.
- **`/continue`**: Resumes execution in a fresh session by loading exclusively `.agents/ACTIVE_STATE.md` and the bounded mandatory files, resetting the turn counter to `Turn 1/15`.
- **`/gate5`**: Directly launches a dedicated closing session for `@documentator` to update functional docs, sync `TRACEABILITY-MATRIX.md`, and execute `RN-SDD-GIT-SYNC`.

#### 4. Context Health Semaphore & Token Telemetry (`RN-SDD-CONTEXT-SEMAPHORE`)
The `@orchestrator` tracks turn depth, execution blocks, and token usage, attaching a telemetry footer to every turn:
- 🟢 **Green** (`Turn 1-10` | `Blocks 0-1`): Normal execution window.
- 🟡 **Yellow** (`Turn 11-14` | `Blocks 2`): Warning threshold; prepare for session handoff.
- 🔴 **Red** (`Turn 15+` | `Blocks 3+`): **Strict Stop-the-Line**. The agent halts subagent dispatch and triggers `/checkpoint` to force a clean handoff.

Inspect session token usage and prompt cache efficiency via:
```bash
python .agents/scripts/sdd_token_usage.py
```

---

### ⚡ Token-Optimised Deterministic Tooling
Minimise context token consumption by 90%+ with zero discovery overhead:

#### 1. AST Repo-Map Generator (`sdd_repo_map.py`)
Extracts class hierarchies, method signatures, types, interfaces, and component definitions without dumping full implementation bodies:
- **Python**: Parsed via native `ast` module.
- **TypeScript / JavaScript**: Parsed via deterministic regex AST.
```bash
# Generate compact signature map for a directory or specific file
python .agents/scripts/sdd_repo_map.py src/
```

#### 2. Deterministic Terminal Output Trimmer (`sdd_trim_exec.py`)
Wraps test, lint, and build commands to shield the agent's context window from terminal log pollution:
- **On Success (`exit 0`)**: Compresses 100+ lines of test output into a single clean summary line (`✅ [DoD OK] ...`).
- **On Failure (`exit != 0`)**: Strips ANSI noise, blank lines, and deprecation notices, isolating only the targeted stack trace, failure assertion, file, and line.
```bash
python .agents/scripts/sdd_trim_exec.py pytest tests/unit/test_auth.py
python .agents/scripts/sdd_trim_exec.py npm test
```

#### 3. Selective Context & Dynamic Rule Loading (`RN-SDD-SELECTIVE-CONTEXT`)
- Forbids recursive blind grepping. Agents consult `docs/knowledge/SYSTEM_TOPOLOGY.md`, `API_CATALOG.md`, and `DATA_MODELS.md` first.
- Governance rules in `.agents/rules/` are loaded conditionally per active Gate, never all at once.
- Deterministic DoD commands are pre-registered in `specs/STACK.md` during Gate 00 and passed directly to atomic tasks.

---

### 🛡️ Framework Healthcheck
Audit the mechanical integrity of agent definitions, rules, and governance scripts at any time:
```bash
python .agents/scripts/sdd_healthcheck.py
```

---

### 🔄 Bidirectional Framework Synchronisation (`sdd_sync.py`)
As you develop projects, you may discover improvements to agent rules (`.agents/rules/`), audit skills (`.agents/skills/`), or gate guards (`.agents/scripts/`). To prevent framework divergence without polluting the starter template with project-specific code:

1. **Check framework divergence status**:
   ```bash
   python scripts/sdd_sync.py --status
   ```
2. **Export improvements from this project to the starter template**:
   ```bash
   python scripts/sdd_sync.py --push-to-template C:/Projects/sdd-agentic-starter
   ```
   *(Surgically syncs only the core agentic framework, sanitising project names and safeguarding `src/`).*
3. **Pull starter template updates into this project**:
   ```bash
   python scripts/sdd_sync.py --pull-from-template C:/Projects/sdd-agentic-starter
   ```

---
---

## 🇪🇸 Español (ES-ES)

Plantilla universal de desarrollo de software guiado por especificaciones (**Spec-Driven Development - SDD**) y orquestación multi-agente.

### 🚀 Cómo Iniciar un Nuevo Proyecto a partir de este Template

#### 1. Clonar o Usar este Template
Crea un nuevo repositorio en GitHub haciendo clic en **"Use this template"** o mediante la CLI de GitHub:
```bash
gh repo create mi-nuevo-proyecto --template <tu-usuario>/sdd-agentic-starter --private
cd mi-nuevo-proyecto
```

#### 2. El Repositorio Inicia BLOQUEADO (`Gate 00: Stack Lock`)
Para garantizar orden arquitectónico y compatibilidad, **el código de producción en `src/` está estrictamente bloqueado** por la regla `RN-SDD-GATE00-STACK-LOCK`. No se puede escribir código de producción ni tests hasta definir las tecnologías, el hosting y el escuadrón agéntico.

#### 3. Habla con el `@orchestrator` en tu asistente IA (Antigravity / Cursor / Claude Code)
Envía este mensaje para iniciar el proyecto:
> *"Hola @orchestrator. Iniciamos un nuevo proyecto en `sdd-agentic-starter`. Activa el asistente interactivo de Gate 00 para definir la topología, arquitectura, stack, agentes y convenciones."*

El `@orchestrator`:
1. Desplegará el **Asistente Interactivo de Gate 00 (`sdd-bootstrap`)** con poda dinámica en árbol:
   - **Infraestructura y Hosting**: Cloud Pública (AWS/Azure/GCP), Contenedores Docker o PaaS modernas (**Vercel**, Netlify, Railway).
   - **Alcance y Poda Dinámica**: Omite automáticamente preguntas irrelevantes (ej: sin estilos si es solo API, o sin backend si es SPA estática).
   - **Activación del Escuadrón Agéntico**: Configura la matriz de agentes en `ACTIVO` o `INACTIVO (N/A)` según el alcance.
   - **Golden Samples**: Inserta ejemplos canónicos de Do's & Don'ts (enrutamiento limpio con DTOs, Result Pattern y desacoplamiento con inyección de dependencias).
   - **Comandos Deterministas de DoD**: Congela los comandos verificados de linting, pruebas unitarias acotadas (<1s en memoria), integración y build para eliminar el overhead de descubrimiento.
   - **Entorno Local**: Genera la configuración inicial de `docker-compose.yml` o `vercel.json`.
2. Rellenará formalmente **`specs/STACK.md`** y te solicitará tu firma humana expresa: `[x] Gate 00 Approved (Human Sign-off)`.
3. Una vez aprobada, el código en `src/` se desbloqueará y comenzará el ciclo normal de desarrollo (Gate 0 -> Gate 5).

---

### 👥 Topologías de Escuadrón Agéntico (Configurables en Gate 00)
La plantilla soporta dos modalidades operativas según la escala y complejidad del proyecto:
- **Escuadrón Especializado Granular (Alta Especialización)**: 12 roles atómicos con fronteras estrictas de aislamiento (`@back-domain`, `@back-infra`, `@back-api`, `@db-specialist`, `@back-test`, `@front-logic`, `@front-ui`, `@front-test`, `@devops`, `@documentator`, `@architect`, `@orchestrator`).
- **Escuadrón Compacto**: 7 roles core para proyectos ágiles o MVPs (`@orchestrator`, `@architect`, `@back-engineer`, `@front-engineer`, `@qa-tester`, `@devops`, `@documentator`).

Generable de forma conversacional por el `@orchestrator` o inspeccionable por consola:
```bash
python scripts/sdd_agent_generator.py --list
python scripts/sdd_agent_generator.py --mode granular  # o --mode compact
```

---

### 🏛️ Ciclo de Vida SDD (Gate 00 a Gate 5)

```text
[ Gate 00: STACK.md ] ──► [ Gate 0: Backlog Intake ]
                                    │
                                    ▼
[ Gate 1: 01-spec.md (EARS) ] ──► [ Gate 2: 02-tech-spec.md (Contratos) ]
                                    │
                                    ▼
[ Gate 3: 03-tasks.md (DAG) ] ──► [ Implementación Subagentes (.agent-inbox/) ]
                                    │
                                    ▼
[ Gate 4: Verificación QA ] ───► [ Gate 5: Living Docs 0DD (docs/) ] ──► DONE
```

---

### 🧠 Ciclo de Vida de Sesión, Gobernanza de Contexto y Workflows de Handoff
Para evitar la degradación de contexto, el agotamiento de tokens y los bucles de alucinación en tareas de largo recorrido, el framework aplica una higiene rigurosa de sesión y división por fases:

#### 1. División de Fases y Optimización por Niveles de Modelo (`RN-SDD-SESSION-LIFECYCLE`)
Las tareas se desacoplan en sesiones de conversación aisladas adaptadas al nivel de modelo óptimo:
- **Fase A — Arquitectura y Especificaciones (Gates 00 a 3)**: Modelos de alto razonamiento (ej: Gemini Pro / Thinking, Claude Sonnet / Opus, OpenAI o1/o3) dedicados exclusivamente a requisitos (`01-spec.md`), especificaciones técnicas (`02-tech-spec.md`), contratos DTO/API y el DAG de tareas atómicas (`03-tasks.md`).
- **Fase B — Implementación y Verificación (Gate 4)**: Sesión limpia con modelos rápidos y coste-eficientes (ej: Gemini Flash, Claude Haiku) cargando únicamente `02-tech-spec.md`, `03-tasks.md` y documentos de conocimiento para implementar código mediante subagentes especialistas.
- **Fase C — Documentación Viva y Cierre (Gate 5)**: Ejecución de `@documentator` en un hilo de bajo coste para actualizar la documentación funcional bilingüe (`docs/es/`, `docs/en/`), sincronizar la matriz de trazabilidad y ejecutar `git push origin main`.

#### 2. Puntero de Sesión Activa (`.agents/ACTIVE_STATE.md`)
Fuente única de verdad del estado de ejecución entre sesiones. Limita los archivos de contexto obligatorio a un máximo estricto de 4 archivos para eliminar la saturación ciega de contexto:
```markdown
- **Active Work Item:** FEAT-001 (o IDLE)
- **Current Gate:** Gate 03 (Tareas Listas para Ejecución)
- **Recommended Model Tier:** Execution (Flash/Sonnet)
- **Next Execution Target:** Despachar Tarea 1.1 a @back-engineer
- **Mandatory Context Files:** specs/features/FEAT-001/02-tech-spec.md, ...
```

#### 3. Workflows de Handoff mediante Comandos Slash
- **`/checkpoint`**: Captura automáticamente el estado activo, guarda las tareas pendientes en `.agents/ACTIVE_STATE.md` y prepara un traspaso de sesión seguro.
- **`/continue`**: Reanuda la ejecución en una sesión limpia cargando exclusivamente `.agents/ACTIVE_STATE.md` y los archivos acotados, reiniciando el contador a `Turno 1/15`.
- **`/gate5`**: Lanza directamente una sesión de cierre dedicada y económica para que el `@documentator` actualice la documentación funcional, sincronice `TRACEABILITY-MATRIX.md` y ejecute `RN-SDD-GIT-SYNC`.

#### 4. Semáforo de Salud de Contexto y Telemetría de Tokens (`RN-SDD-CONTEXT-SEMAPHORE`)
El `@orchestrator` monitoriza de forma continua el recuento de turnos, los bloques de subagentes y el consumo de tokens, adjuntando un pie de telemetría en cada respuesta:
- 🟢 **Verde** (`Turno 1-10` | `Bloques 0-1`): Ventana de ejecución óptima.
- 🟡 **Amarillo** (`Turno 11-14` | `Bloques 2`): Umbral de aviso; preparar traspaso de sesión.
- 🔴 **Rojo** (`Turno 15+` | `Bloques 3+`): **Parada Obligatoria (*Stop-the-Line*)**. El agente detiene el despacho de subagentes y ejecuta `/checkpoint` para forzar un handoff limpio.

Inspecciona el uso de tokens y la eficiencia del prompt caching con:
```bash
python .agents/scripts/sdd_token_usage.py
```

---

### ⚡ Herramientas Deterministas Optimizadas para Ahorro de Tokens
Reduce el consumo de tokens de contexto en más de un 90% con cero sobrecarga de descubrimiento (*zero discovery overhead*):

#### 1. Generador de Mapa de Repositorio AST (`sdd_repo_map.py`)
Extrae jerarquías de clases, firmas de métodos, tipos, interfaces y componentes sin cargar el cuerpo completo de los ficheros:
- **Python**: Analizado mediante el módulo nativo `ast`.
- **TypeScript / JavaScript**: Analizado mediante AST basado en expresiones regulares deterministas.
```bash
# Generar mapa compacto de firmas para un directorio o archivo
python .agents/scripts/sdd_repo_map.py src/
```

#### 2. Recortador Determinista de Salida de Terminal (`sdd_trim_exec.py`)
Envuelve comandos de test, lint y build para evitar la saturación de la ventana de contexto con logs excesivos:
- **En Éxito (`exit 0`)**: Comprime más de 100 líneas de salida en un resumen limpio de una sola línea (`✅ [DoD OK] ...`).
- **En Fallo (`exit != 0`)**: Elimina ruido de ANSI, líneas en blanco y avisos de obsolescencia, aislando únicamente la traza del error, la aserción fallida, el fichero y la línea afectada.
```bash
python .agents/scripts/sdd_trim_exec.py pytest tests/unit/test_auth.py
python .agents/scripts/sdd_trim_exec.py npm test
```

#### 3. Contexto Selectivo y Carga Perezosa de Reglas (`RN-SDD-SELECTIVE-CONTEXT`)
- Prohibida la búsqueda ciega con grep recursivo. Los agentes consultan primero `docs/knowledge/SYSTEM_TOPOLOGY.md`, `API_CATALOG.md` y `DATA_MODELS.md`.
- Las reglas de `.agents/rules/` se cargan bajo demanda según el Gate activo, nunca de forma masiva.
- Los comandos deterministas de DoD se congelan en `specs/STACK.md` durante el Gate 00 y se transfieren directamente a las tareas atómicas.

---

### 🛡️ Verificación de Salud del Framework
Audita en cualquier momento la integridad mecánica de las reglas, agentes y scripts de gobernanza:
```bash
python .agents/scripts/sdd_healthcheck.py
```

---

### 🔄 Sincronización Bidireccional con la Plantilla (`sdd_sync.py`)
A medida que desarrolles proyectos, es natural que descubras mejoras en las reglas (`.agents/rules/`), en las skills de auditoría (`.agents/skills/`) o en los scripts de guardia (`.agents/scripts/`). Para evitar la divergencia del framework sin contaminar la plantilla con código de negocio:

1. **Ver el estado de divergencia del framework**:
   ```bash
   python scripts/sdd_sync.py --status
   ```
2. **Exportar mejoras de este proyecto hacia la plantilla**:
   ```bash
   python scripts/sdd_sync.py --push-to-template C:/Projects/sdd-agentic-starter
   ```
   *(Sincroniza quirúrgicamente sólo el core agéntico, sanitizando referencias a nombres propios y protegiendo tu código en `src/`).*
3. **Traer actualizaciones de la plantilla hacia este proyecto**:
   ```bash
   python scripts/sdd_sync.py --pull-from-template C:/Projects/sdd-agentic-starter
   ```
