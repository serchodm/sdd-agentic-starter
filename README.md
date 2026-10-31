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
